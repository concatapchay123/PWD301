"""Authenticated cloud backup groups and conservative verified-copy retention."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from flask import current_app, has_app_context
from sqlalchemy.orm import Session, scoped_session

from pwd301.models.identity import User
from pwd301.services.backup_cipher import _key, decrypt_backup, encrypt_backup

BACKUP_NAME = re.compile(r"pwd301_db_[0-9]{8}_[0-9]{6}_[a-f0-9]{8}\.bak")
MAX_RECEIPT = 64 * 1024


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _signed_receipt(payload: dict[str, Any], key: str) -> dict[str, Any]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    secret = hmac.new(_key(key), b"PWD301_ARCHIVE_RECEIPT_KEY_V1", hashlib.sha256).digest()
    signature = hmac.new(
        secret, b"PWD301_ARCHIVE_RECEIPT_V1\0" + encoded, hashlib.sha256
    ).hexdigest()
    return {"payload": payload, "signature": signature}


def _verified_receipt(data: bytes, key: str, prefix: str) -> dict[str, Any]:
    if len(data) > MAX_RECEIPT:
        raise ValueError("Archive receipt exceeds its bounded size.")
    envelope = json.loads(data)
    if not isinstance(envelope, dict):
        raise ValueError("Invalid archive receipt envelope.")
    payload = envelope["payload"]
    if not isinstance(payload, dict):
        raise ValueError("Invalid archive receipt.")
    expected = _signed_receipt(payload, key)["signature"]
    if not hmac.compare_digest(str(envelope["signature"]), expected):
        raise ValueError("Archive receipt authentication failed.")
    name = payload["backup_name"]
    if not isinstance(name, str) or not BACKUP_NAME.fullmatch(name) or payload["prefix"] != prefix:
        raise ValueError("Archive group identity mismatch.")
    filenames = {name + ".encrypted", name + ".manifest.json.encrypted"}
    if (
        not isinstance(payload.get("objects"), dict)
        or set(payload["objects"]) != filenames
        or payload.get("version") != 1
    ):
        raise ValueError("Archive group is incomplete.")
    for metadata in payload["objects"].values():
        if (
            not isinstance(metadata["size"], int)
            or metadata["size"] <= 0
            or not re.fullmatch("[a-f0-9]{64}", metadata["sha256"])
        ):
            raise ValueError("Invalid archive object metadata.")
    return payload


def _upload_verified(client: Any, bucket: str, object_key: str, path: Path) -> dict[str, Any]:
    expected, size = _digest(path), path.stat().st_size
    client.upload_file(str(path), bucket, object_key, ExtraArgs={"Metadata": {"sha256": expected}})
    response = client.get_object(Bucket=bucket, Key=object_key)
    actual, total = hashlib.sha256(), 0
    try:
        if int(response["ContentLength"]) != size:
            raise ValueError("Cloud backup size mismatch; local files retained.")
        while chunk := response["Body"].read(1024 * 1024):
            total += len(chunk)
            if total > size:
                raise ValueError("Cloud backup readback exceeds expected size.")
            actual.update(chunk)
    finally:
        response["Body"].close()
    if total != size or actual.hexdigest() != expected:
        raise ValueError("Cloud backup verification failed; local files retained.")
    return {"size": size, "sha256": expected}


def _ensure_encrypted(source: Path, key: str) -> Path:
    destination = source.with_name(source.name + ".encrypted")
    if destination.exists():
        # Failed/partial runs are resumable only after authenticating the existing ciphertext.
        with tempfile.TemporaryDirectory(dir=source.parent) as temporary:
            plain = Path(temporary) / "verified"
            decrypt_backup(destination, plain, key)
            if _digest(plain) != _digest(source):
                raise ValueError("Existing encrypted archive does not match its source.")
    else:
        if shutil.disk_usage(source.parent).free < source.stat().st_size + 128 * 1024 * 1024:
            raise ValueError(
                "Insufficient disk reserve for safe backup encryption; plaintext retained."
            )
        encrypt_backup(source, destination, key)
    return destination


def archive_backup(backup: Any, key: str, client: Any, bucket: str) -> dict[str, Any]:
    source = Path(backup.storage_location)
    root = (
        Path(current_app.config["FILE_BACKUP_ROOT"]).resolve()
        if has_app_context()
        else source.parent.resolve()
    )
    if (
        source.is_symlink()
        or not source.resolve().is_relative_to(root)
        or not BACKUP_NAME.fullmatch(source.name)
    ):
        raise ValueError("Backup source is outside the managed archive namespace.")
    manifest = source.with_name(source.name + ".manifest.json")
    if not source.is_file() or not manifest.is_file() or manifest.is_symlink():
        raise ValueError("Backup and companion manifest are both required.")
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if (
        metadata.get("sha256") != _digest(source)
        or metadata.get("file_size") != source.stat().st_size
        or metadata.get("database_backup_name") != source.name
    ):
        raise ValueError("Physical backup does not match its companion manifest.")
    files = [_ensure_encrypted(source, key), _ensure_encrypted(manifest, key)]
    daily = "daily/" + source.name + "/"
    prefixes = [daily]
    if backup.started_at.weekday() == 6:
        week = backup.started_at.isocalendar()
        prefixes.append(f"weekly/{week.year}-W{week.week:02d}/{source.name}/")
    receipts = []
    for prefix in prefixes:
        objects = {
            path.name: _upload_verified(client, bucket, prefix + path.name, path) for path in files
        }
        payload = {
            "version": 1,
            "backup_name": source.name,
            "backup_id": str(backup.public_id),
            "created_at": backup.started_at.isoformat(),
            "prefix": prefix,
            "objects": objects,
        }
        receipt = _signed_receipt(payload, key)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            local = Path(temporary) / "receipt.json"
            local.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            _upload_verified(client, bucket, prefix + "receipt.json", local)
        receipts.append(receipt)
    # Durable local marker is written only after every required archive group is verified.
    marker = source.with_name(source.name + ".archive-receipt.json")
    temporary_marker = marker.with_name(marker.name + "." + uuid.uuid4().hex + ".tmp")
    temporary_marker.write_text(json.dumps(receipts[0], sort_keys=True), encoding="utf-8")
    temporary_marker.replace(marker)
    for path in files:
        path.unlink(
            missing_ok=True
        )  # Unreferenced ciphertext is safely persisted in verified cloud groups.
    return {"daily_prefix": daily, "weekly_prefix": prefixes[1] if len(prefixes) == 2 else None}


def _load_cloud_groups(client: Any, bucket: str, key: str, category: str) -> list[dict[str, Any]]:
    groups = []
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=category + "/"
    ):
        for obj in page.get("Contents", []):
            object_key = obj["Key"]
            if not object_key.endswith("/receipt.json"):
                continue
            prefix = object_key.removesuffix("receipt.json")
            pattern = (
                r"daily/(pwd301_db_[0-9]{8}_[0-9]{6}_[a-f0-9]{8}\.bak)/"
                if category == "daily"
                else r"weekly/[0-9]{4}-W[0-9]{2}/(pwd301_db_[0-9]{8}_[0-9]{6}_[a-f0-9]{8}\.bak)/"
            )
            if not re.fullmatch(pattern, prefix):
                continue
            body = None
            try:
                response = client.get_object(Bucket=bucket, Key=object_key)
                body = response["Body"]
                payload = _verified_receipt(body.read(MAX_RECEIPT + 1), key, prefix)
                for filename, metadata in payload["objects"].items():
                    head = client.head_object(Bucket=bucket, Key=prefix + filename)
                    if (
                        int(head["ContentLength"]) != metadata["size"]
                        or head.get("Metadata", {}).get("sha256") != metadata["sha256"]
                    ):
                        raise ValueError("Archive group no longer matches its verified receipt.")
                groups.append(payload)
            except (ValueError, KeyError, TypeError, OSError):
                continue
            finally:
                if body is not None:
                    body.close()
    return sorted(groups, key=lambda group: group["backup_name"], reverse=True)


def prune_cloud_archives(client: Any, bucket: str, key: str) -> dict[str, int]:
    result = {}
    for category, keep in [("daily", 7), ("weekly", 4)]:
        groups = _load_cloud_groups(client, bucket, key, category)
        deleted = 0
        for payload in groups[keep:]:
            # Exact receipt-bound filenames only; unrelated/partial/unauthenticated data is preserved.
            for filename in payload["objects"]:
                client.delete_object(Bucket=bucket, Key=payload["prefix"] + filename)
            client.delete_object(Bucket=bucket, Key=payload["prefix"] + "receipt.json")
            deleted += 1
        result[category + "_deleted"] = deleted
    return result


def prune_local_archives(
    actor: User, key: str, client: Any, bucket: str, session: Session | scoped_session[Any]
) -> int:
    from pwd301.models.operations import BackupRun
    from pwd301.services.audit_service import record_audit_event
    from pwd301.services.operations_service import _require_admin

    _require_admin(actor)
    root = Path(current_app.config["FILE_BACKUP_ROOT"]).resolve()
    cloud = {
        group["backup_id"]: group for group in _load_cloud_groups(client, bucket, key, "daily")
    }
    candidates = []
    for backup in (
        session.query(BackupRun)
        .filter_by(status="SUCCEEDED", backup_type="AUTOMATIC")
        .order_by(BackupRun.started_at.desc())
        .all()
    ):
        source = Path(backup.storage_location)
        marker = source.with_name(source.name + ".archive-receipt.json")
        if (
            not source.resolve().is_relative_to(root)
            or source.is_symlink()
            or not source.is_file()
            or not marker.is_file()
            or str(backup.public_id) not in cloud
        ):
            continue
        try:
            receipt = _verified_receipt(marker.read_bytes(), key, "daily/" + source.name + "/")
            if receipt["backup_id"] != str(backup.public_id):
                continue
        except (ValueError, KeyError, TypeError):
            continue
        candidates.append((backup, source))
    if len(candidates) <= 2:
        return 0
    paths = []
    try:
        for backup, source in candidates[2:]:
            receipt = cloud[str(backup.public_id)]
            record_audit_event(
                actor=actor,
                action="DATABASE_BACKUP_LOCAL_PRUNED",
                target_type="BACKUP",
                target_id=backup.public_id,
                performed_as_admin=True,
                details={
                    "backup_id": str(backup.public_id),
                    "archive_prefix": receipt["prefix"],
                    "backup_name": source.name,
                    "objects": receipt["objects"],
                },
                session=session,
            )
            paths.extend(
                [
                    source,
                    source.with_name(source.name + ".manifest.json"),
                    source.with_name(source.name + ".encrypted"),
                    source.with_name(source.name + ".manifest.json.encrypted"),
                    source.with_name(source.name + ".archive-receipt.json"),
                ]
            )
            session.delete(backup)
        session.commit()  # Never unlink bytes while a DB reference could roll back.
    except Exception:
        session.rollback()
        raise
    protected = set()
    for remaining in session.query(BackupRun).all():
        source = Path(remaining.storage_location).resolve()
        protected.add(source)
        protected.add(source.with_name(source.name + ".manifest.json"))
    for path in paths:
        if path.resolve() in protected:
            continue
        if path.resolve().is_relative_to(root) and not path.is_symlink():
            path.unlink(missing_ok=True)
    return len(candidates) - 2
