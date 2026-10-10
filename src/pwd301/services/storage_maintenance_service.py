"""Checkpointed staging-only migration and conservative orphan reconciliation."""

from __future__ import annotations

import hashlib
from datetime import timedelta

from flask import current_app

from pwd301.extensions import db
from pwd301.models.file_import import FileBlob, FileRevision
from pwd301.models.types import utc_now
from pwd301.services.exceptions import FileStorageError
from pwd301.services.file_service import (
    cleanup_storage_cache,
    get_file_storage_root,
    latest_file_scan_results,
)
from pwd301.services.storage_adapter import get_s3_client, upload_blob_to_cloud, verify_cloud_blob


def _source(blob):
    root = get_file_storage_root().resolve()
    raw_path = root / blob.storage_key
    path = raw_path.resolve()
    if not path.is_relative_to(root) or raw_path.is_symlink():
        raise FileStorageError("Blob path is outside the authorized storage root.")
    return path


def maintain_storage(action, session=None, after_id=0):
    if action not in ("inventory", "dry-run", "migrate", "verify", "prune"):
        raise FileStorageError("Unknown storage maintenance action.")
    if action not in ("inventory", "dry-run") and not current_app.config.get(
        "STORAGE_MAINTENANCE_STAGING", False
    ):
        raise FileStorageError("Storage mutations require an isolated staging target.")
    sess = session if session is not None else db.session
    results = []
    for blob in (
        sess.query(FileBlob)
        .filter(FileBlob.id > after_id, FileBlob.status == "PRESENT")
        .order_by(FileBlob.id)
        .all()
    ):
        source = _source(blob)
        result = {
            "id": blob.id,
            "sha256": blob.sha256_hex,
            "size_bytes": blob.size_bytes,
            "backend": blob.storage_backend,
            "local_exists": source.is_file(),
            "result": "inventory",
        }
        if action == "dry-run":
            result["result"] = (
                "would_migrate"
                if blob.storage_backend == "local" and source.is_file()
                else "unchanged"
            )
        elif action == "migrate":
            if blob.storage_backend == "s3":
                result["result"] = "already_cloud"
            else:
                # All references, including historical revisions, must be cleared for serving.
                revisions = sess.query(FileRevision).filter(FileRevision.blob_id == blob.id).all()
                safe = (
                    not blob.detected_mime_type.startswith("video/")
                    and revisions
                    and all(
                        rev.status in ("ACTIVE", "REPLACED")
                        and rev.scan_results
                        and any(
                            scan.scan_type == "MALWARE" and scan.status == "PASS"
                            for scan in latest_file_scan_results(rev)
                        )
                        and all(scan.status == "PASS" for scan in latest_file_scan_results(rev))
                        for rev in revisions
                    )
                )
                if not safe or not source.is_file():
                    result["result"] = "ineligible"
                else:
                    digest = hashlib.sha256()
                    with source.open("rb") as stream:
                        while chunk := stream.read(64 * 1024):
                            digest.update(chunk)
                    if (
                        source.stat().st_size != blob.size_bytes
                        or digest.hexdigest() != blob.sha256_hex
                    ):
                        raise FileStorageError("Local blob integrity check failed.")
                    if not upload_blob_to_cloud(source, blob.storage_key):
                        raise FileStorageError(
                            "Cloud migration verification failed; local source retained."
                        )
                    blob.storage_backend = "s3"
                    blob.cloud_verified_at = utc_now()
                    sess.commit()  # Durable per-blob checkpoint; restart safely skips it.
                    result["result"] = "migrated"
        elif action in ("verify", "prune"):
            if blob.storage_backend != "s3" or blob.cloud_verified_at is None:
                result["result"] = "not_cloud"
            elif not verify_cloud_blob(blob.storage_key, blob.sha256_hex, blob.size_bytes):
                raise FileStorageError("Cloud integrity check failed; local source retained.")
            else:
                result["result"] = "verified"
                if action == "prune" and source.is_file():
                    source.unlink()
                    result["result"] = "pruned"
        results.append(result)
    return results


def reconcile_storage(session=None, delete_orphans=False):
    sess = session if session is not None else db.session
    removed_cache = cleanup_storage_cache()
    client, bucket = get_s3_client()
    if client is None:
        return {"cache_removed": removed_cache, "orphan_candidates": 0, "orphans_removed": 0}
    if delete_orphans and (
        not current_app.config.get("STORAGE_MAINTENANCE_STAGING")
        or "staging" not in str(bucket).lower()
    ):
        raise FileStorageError("Orphan deletion requires an isolated staging bucket.")
    cutoff = utc_now() - timedelta(hours=24)
    candidates = removed = 0
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="blobs/"):
        for item in page.get("Contents", []):
            key = item["Key"]
            modified = item["LastModified"].replace(tzinfo=None)
            if modified >= cutoff:
                continue
            blob = sess.query(FileBlob).filter(FileBlob.storage_key == key).first()
            # Even a stale refcount cannot erase an object with a historical revision.
            if blob is not None and (
                blob.reference_count
                or sess.query(FileRevision.id).filter(FileRevision.blob_id == blob.id).first()
            ):
                continue
            candidates += 1
            if delete_orphans:
                client.delete_object(Bucket=bucket, Key=key)
                removed += 1
    return {
        "cache_removed": removed_cache,
        "orphan_candidates": candidates,
        "orphans_removed": removed,
    }
