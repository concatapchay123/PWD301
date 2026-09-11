"""REST API route handlers for DOCX/PDF assessment import engine per 09_FILE_IMPORT_API.md."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.api_import import api_import_bp
from pwd301.extensions import db
from pwd301.services.authorization_service import (
    instructor_required,
    require_authenticated_actor,
)
from pwd301.services.exceptions import ValidationError
from pwd301.services.import_service import (
    cancel_import_job,
    commit_import_job,
    create_import_job,
    get_import_job_detail,
    process_import_job,
    set_import_question_decision,
    update_import_question,
)
from pwd301.services.jwt_auth_service import jwt_required


@api_import_bp.route("", methods=["POST"])
@jwt_required
@instructor_required
def create_import_api() -> tuple[Response, int] | Response:
    """Start DOCX/PDF import job per 09_FILE_IMPORT_API.md.

    Accepts:
    - course_id: UUID or identifier of the target course.
    - file_asset_id: UUID or identifier of the security-cleared file asset.
    - auto_process: (Optional, default True) Process parsing and duplicate detection immediately.
    """
    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or request.form.to_dict()

    course_id = data.get("course_id")
    file_asset_id = data.get("file_asset_id")

    if not course_id:
        raise ValidationError("Field 'course_id' is required.")
    if not file_asset_id:
        raise ValidationError("Field 'file_asset_id' is required.")

    auto_process = data.get("auto_process", True)
    if isinstance(auto_process, str):
        auto_process = auto_process.lower() in ("true", "1", "yes")

    job = create_import_job(
        actor=actor,
        course_id=course_id,
        file_asset_id=file_asset_id,
        session=db.session,
    )

    if auto_process:
        job = process_import_job(
            actor=actor,
            job_id=job.public_id,
            session=db.session,
        )

    detail = get_import_job_detail(actor, job.public_id, session=db.session)
    return jsonify(detail), 202


@api_import_bp.route("/<job_id>", methods=["GET"])
@jwt_required
@instructor_required
def get_import_api(job_id: str) -> tuple[Response, int] | Response:
    """View progress, summary, and extracted questions for an import job."""
    actor = require_authenticated_actor()
    detail = get_import_job_detail(actor, job_id, session=db.session)
    return jsonify(detail), 200


@api_import_bp.route("/<job_id>/process", methods=["POST"])
@jwt_required
@instructor_required
def process_import_api(job_id: str) -> tuple[Response, int] | Response:
    """Trigger or re-trigger processing of an import job."""
    actor = require_authenticated_actor()
    process_import_job(actor=actor, job_id=job_id, session=db.session)
    detail = get_import_job_detail(actor, job_id, session=db.session)
    return jsonify(detail), 200


@api_import_bp.route("/<job_id>/questions/<temp_id>", methods=["PATCH"])
@jwt_required
@instructor_required
def update_question_api(job_id: str, temp_id: str) -> tuple[Response, int] | Response:
    """Review and edit an extracted import question draft."""
    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or {}

    # Check if a decision was included in the PATCH body
    decision = data.get("decision") or data.get("action")
    if decision:
        set_import_question_decision(
            actor=actor,
            job_id=job_id,
            temp_id=temp_id,
            decision=str(decision),
            session=db.session,
        )

    updated = update_import_question(
        actor=actor,
        job_id=job_id,
        temp_id=temp_id,
        payload=data,
        session=db.session,
    )
    return jsonify(updated), 200


@api_import_bp.route("/<job_id>/questions/<temp_id>/decision", methods=["POST"])
@jwt_required
@instructor_required
def set_question_decision_api(job_id: str, temp_id: str) -> tuple[Response, int] | Response:
    """Approve (ACCEPTED) or reject (REJECTED) an extracted question draft."""
    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or {}
    decision = data.get("action") or data.get("decision")
    if not decision:
        raise ValidationError("Field 'action' or 'decision' is required (ACCEPTED / REJECTED).")

    updated = set_import_question_decision(
        actor=actor,
        job_id=job_id,
        temp_id=temp_id,
        decision=str(decision),
        session=db.session,
    )
    return jsonify(updated), 200


@api_import_bp.route("/<job_id>/commit", methods=["POST"])
@jwt_required
@instructor_required
def commit_import_api(job_id: str) -> tuple[Response, int] | Response:
    """Atomically commit all ACCEPTED questions into the Course Question Bank."""
    actor = require_authenticated_actor()
    result = commit_import_job(actor, job_id, session=db.session)
    return jsonify(result), 200


@api_import_bp.route("/<job_id>/cancel", methods=["POST"])
@jwt_required
@instructor_required
def cancel_import_api(job_id: str) -> tuple[Response, int] | Response:
    """Cancel an in-progress import job."""
    actor = require_authenticated_actor()
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")
    job = cancel_import_job(actor, job_id, reason=reason, session=db.session)
    detail = get_import_job_detail(actor, job.public_id, session=db.session)
    return jsonify(detail), 200
