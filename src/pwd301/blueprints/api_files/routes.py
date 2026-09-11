"""REST API route handlers for File Assets and Revisions per ADR-008 and 09_FILE_IMPORT_API.md."""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

from flask import Response, current_app, jsonify, make_response, request, send_file

from pwd301.blueprints.api_files import api_file_bp
from pwd301.extensions import db
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    require_authenticated_actor,
)
from pwd301.services.exceptions import (
    FileSizeLimitExceededError,
    FileValidationError,
)
from pwd301.services.file_service import (
    LimitingStream,
    _serialize_file_asset,
    add_file_revision,
    get_file_for_download,
    get_file_scan_history,
    quarantine_override,
    rescan_file_asset,
    restore_file_asset,
    sanitize_filename,
    store_file_stream,
    trash_file_asset,
)
from pwd301.services.jwt_auth_service import jwt_required


@api_file_bp.route("/<asset_id>", methods=["GET"])
def get_file_metadata_api(asset_id: str) -> tuple[Response, int] | Response:
    """Retrieve FileAsset metadata conforming to ADR-002 (zero internal PK leakage)."""
    actor = get_authenticated_actor()
    # Check download/view permissions to ensure authorized viewer
    asset, blob, _ = get_file_for_download(actor, asset_id, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@api_file_bp.route("/<asset_id>/download", methods=["GET"])
def download_file_api(asset_id: str) -> Response:
    """Download or stream file content with fail-closed security and secure headers.

    Supports both JWT Bearer authorization and Web session authentication.
    Applies defensive headers:
    - X-Content-Type-Options: nosniff
    - Content-Disposition with sanitized filename
    - Accurate Content-Type
    """
    actor = get_authenticated_actor()
    version_param = request.args.get("version")
    revision_no = int(version_param) if version_param and version_param.isdigit() else None
    asset, blob, physical_path = get_file_for_download(
        actor, asset_id, revision_no=revision_no, session=db.session
    )

    if revision_no is not None:
        target_rev = next((r for r in asset.revisions if r.revision_no == revision_no), None)
    else:
        target_rev = asset.current_revision or (asset.revisions[-1] if asset.revisions else None)
    clean_filename = sanitize_filename(
        target_rev.original_filename if target_rev else asset.display_name
    )

    disposition = request.args.get("disposition", "attachment").lower()
    if disposition not in ("inline", "attachment"):
        disposition = "attachment"

    # Reverse proxy offload (Nginx X-Accel-Redirect) for large video/asset streaming
    if current_app.config.get("USE_X_ACCEL_REDIRECT", False):
        accel_prefix = current_app.config.get("ACCEL_REDIRECT_PREFIX", "/internal-storage")
        storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage")).resolve()
        try:
            rel_path = Path(physical_path).resolve().relative_to(storage_root)
            accel_path = f"{accel_prefix.rstrip('/')}/{rel_path.as_posix()}"
            resp = make_response("", 200)
            resp.headers["X-Accel-Redirect"] = accel_path
            resp.headers["X-Content-Type-Options"] = "nosniff"
            ascii_fallback = clean_filename.encode("ascii", "ignore").decode("ascii") or "file"
            encoded_filename = urllib.parse.quote(clean_filename, safe="")
            resp.headers["Content-Disposition"] = (
                f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_filename}"
            )
            resp.headers["Content-Type"] = blob.detected_mime_type
            return resp
        except (ValueError, Exception):
            pass

    # Standard streaming fallback with HTTP range requests (conditional=True)
    resp = make_response(
        send_file(
            physical_path,
            mimetype=blob.detected_mime_type,
            as_attachment=(disposition == "attachment"),
            download_name=clean_filename,
            conditional=True,
        )
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    ascii_fallback = clean_filename.encode("ascii", "ignore").decode("ascii") or "file"
    encoded_filename = urllib.parse.quote(clean_filename, safe="")
    resp.headers["Content-Disposition"] = (
        f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_filename}"
    )
    resp.headers["Content-Type"] = blob.detected_mime_type
    return resp


def _extract_upload_stream() -> tuple[Any, str, str | None]:
    """Safely extract upload stream using chunked streaming without loading RAM."""
    cl = request.content_length
    if cl is not None and cl >= 1_000_000_000:
        raise FileSizeLimitExceededError(
            "File size exceeds maximum allowed limit of 1,000,000,000 bytes."
        )

    if request.files and "file" in request.files:
        upload = request.files["file"]
        return (
            LimitingStream(upload.stream, max_bytes=1_000_000_000),
            upload.filename or "unnamed_file",
            upload.mimetype or request.content_type,
        )

    filename = request.headers.get("X-File-Name") or "unnamed_file"
    is_chunked = request.environ.get("HTTP_TRANSFER_ENCODING", "").lower() == "chunked"
    if (cl is not None and cl > 0) or is_chunked:
        stream = LimitingStream(request.stream, max_bytes=1_000_000_000)
        return stream, filename, request.content_type

    raise FileValidationError("No file content provided in request.")


@api_file_bp.route("/<asset_id>/revisions", methods=["POST"])
@jwt_required
def add_file_revision_api(asset_id: str) -> tuple[Response, int] | Response:
    """Upload a new revision for an existing FileAsset (JWT required)."""
    actor = require_authenticated_actor()

    file_stream, filename, content_type = _extract_upload_stream()

    revision = add_file_revision(
        actor=actor,
        asset_id=asset_id,
        file_stream=file_stream,
        filename=filename,
        content_type=content_type,
        session=db.session,
    )
    asset = revision.file_asset
    return jsonify(_serialize_file_asset(asset)), 201


@api_file_bp.route("/<asset_id>", methods=["DELETE"])
@jwt_required
def delete_file_asset_api(asset_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a FileAsset into TRASH status (JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")

    asset = trash_file_asset(actor=actor, asset_id=asset_id, reason=reason, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@api_file_bp.route("/<asset_id>/restore", methods=["POST"])
@jwt_required
def restore_file_asset_api(asset_id: str) -> tuple[Response, int] | Response:
    """Restore a soft-deleted FileAsset from TRASH to ACTIVE status (JWT required)."""
    actor = require_authenticated_actor()
    asset = restore_file_asset(actor=actor, asset_id=asset_id, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@api_file_bp.route("", methods=["POST"])
@jwt_required
def upload_file_generic_api() -> tuple[Response, int] | Response:
    """Upload a new FileAsset via /api/files (JWT required)."""
    actor = require_authenticated_actor()

    cl = request.content_length
    if cl is not None and cl >= 1_000_000_000:
        raise FileSizeLimitExceededError(
            "File size exceeds maximum allowed limit of 1,000,000,000 bytes."
        )

    course_id = request.form.get("course_id") or request.args.get("course_id")
    if not course_id:
        json_body = request.get_json(silent=True) or {}
        course_id = json_body.get("course_id")

    if not course_id:
        raise FileValidationError("course_id is required to upload a file.")

    asset_type = request.form.get("asset_type", "RESOURCE")
    title = request.form.get("title")

    file_stream, filename, content_type = _extract_upload_stream()

    asset = store_file_stream(
        actor=actor,
        course_id=course_id,
        file_stream=file_stream,
        filename=filename,
        content_type=content_type,
        asset_type=asset_type,
        title=title,
        session=db.session,
    )
    return jsonify(_serialize_file_asset(asset)), 201


@api_file_bp.route("/<asset_id>/scans", methods=["GET"])
@api_file_bp.route("/<asset_id>/scan-results", methods=["GET"])
@jwt_required
def get_file_scans_api(asset_id: str) -> tuple[Response, int] | Response:
    """Retrieve malware and security scan history for a FileAsset (JWT required)."""
    actor = require_authenticated_actor()
    history = get_file_scan_history(actor=actor, asset_id=asset_id, session=db.session)
    return jsonify({"asset_id": asset_id, "scans": history, "scan_history": history}), 200


@api_file_bp.route("/<asset_id>/rescan", methods=["POST"])
@jwt_required
def rescan_file_api(asset_id: str) -> tuple[Response, int] | Response:
    """Trigger an on-demand malware rescan of a FileAsset (JWT required)."""
    actor = require_authenticated_actor()
    asset = rescan_file_asset(actor=actor, asset_id=asset_id, session=db.session)
    return jsonify(_serialize_file_asset(asset)), 200


@api_file_bp.route("/<asset_id>/quarantine-override", methods=["POST"])
@jwt_required
def quarantine_override_api(asset_id: str) -> tuple[Response, int] | Response:
    """Admin override to release a quarantined/rejected file asset (Admin JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason", "")
    asset = quarantine_override(
        admin_actor=actor, asset_id=asset_id, reason=reason, session=db.session
    )
    return jsonify(_serialize_file_asset(asset)), 200
