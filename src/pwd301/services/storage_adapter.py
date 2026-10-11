"""Verified private S3 storage; a configured cloud backend never falls back silently."""

from __future__ import annotations

import hashlib
import importlib
import logging
import uuid
from pathlib import Path
from typing import Any

from flask import current_app

from pwd301.services.exceptions import FileStorageError

logger = logging.getLogger(__name__)
_boto3_module: Any | None = None
_boto3_imported = False


def _get_boto3() -> Any | None:
    global _boto3_module, _boto3_imported
    if not _boto3_imported:
        _boto3_imported = True
        try:
            _boto3_module = importlib.import_module("boto3")
        except ImportError:
            _boto3_module = None
    return _boto3_module


def is_cloud_storage_enabled() -> bool:
    backend = str(current_app.config.get("STORAGE_BACKEND", "local")).strip().lower()
    if backend not in ("local", "s3"):
        raise FileStorageError("Unsupported storage backend.")
    return backend == "s3"


def get_s3_client() -> tuple[Any | None, str | None]:
    if not is_cloud_storage_enabled():
        return None, None
    keys = (
        "S3_BUCKET_NAME",
        "S3_ENDPOINT_URL",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "S3_REGION_NAME",
    )
    if any(not current_app.config.get(key) for key in keys):
        raise FileStorageError("Private cloud storage configuration is incomplete.")
    boto3 = _get_boto3()
    if boto3 is None:
        raise FileStorageError("Cloud storage dependency is unavailable.")
    try:
        Config = importlib.import_module("botocore.config").Config

        return boto3.client(
            "s3",
            endpoint_url=current_app.config["S3_ENDPOINT_URL"],
            aws_access_key_id=current_app.config["S3_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["S3_SECRET_ACCESS_KEY"],
            region_name=current_app.config["S3_REGION_NAME"],
            config=Config(
                signature_version="s3v4",
                connect_timeout=10,
                read_timeout=30,
                retries={"max_attempts": 2},
            ),
        ), current_app.config["S3_BUCKET_NAME"]
    except Exception:
        raise FileStorageError("Cannot initialize private cloud storage.") from None


def verify_cloud_blob(storage_key: str, expected_sha256: str, expected_size: int) -> bool:
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False
    body = None
    try:
        obj = client.get_object(Bucket=bucket, Key=storage_key)
        body = obj["Body"]
        if int(obj["ContentLength"]) != expected_size:
            return False
        digest, size = hashlib.sha256(), 0
        while chunk := body.read(64 * 1024):
            size += len(chunk)
            if size > expected_size:
                return False
            digest.update(chunk)
        return size == expected_size and digest.hexdigest() == expected_sha256
    except Exception:
        logger.warning("Cloud blob verification failed.")
        return False
    finally:
        if body is not None:
            body.close()


def upload_blob_to_cloud(local_path: Path, storage_key: str) -> bool:
    client, bucket = get_s3_client()
    if client is None or bucket is None or not local_path.is_file():
        return False
    digest = hashlib.sha256()
    with local_path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            digest.update(chunk)
    try:
        client.upload_file(str(local_path), bucket, storage_key)
        return verify_cloud_blob(storage_key, digest.hexdigest(), local_path.stat().st_size)
    except Exception:
        logger.warning("Cloud upload failed; file remains unavailable.")
        return False


def download_blob_from_cloud(storage_key: str, dest_path: Path) -> bool:
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False
    temp = dest_path.with_name(dest_path.name + "." + uuid.uuid4().hex + ".partial")
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, storage_key, str(temp))
        temp.replace(dest_path)
        return True
    except Exception:
        temp.unlink(missing_ok=True)
        logger.warning("Cloud download failed.")
        return False


def create_download_url(storage_key: str, filename: str, mime_type: str, disposition: str) -> str:
    from urllib.parse import quote

    client, bucket = get_s3_client()
    if client is None or bucket is None:
        raise FileStorageError("Private cloud storage is unavailable.")
    ascii_name = filename.encode("ascii", "ignore").decode("ascii").replace('"', "") or "file"
    try:
        return str(
            client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": storage_key,
                    "ResponseContentType": mime_type,
                    "ResponseContentDisposition": f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}",
                },
                ExpiresIn=60,
            )
        )
    except Exception:
        raise FileStorageError("Cannot issue download ticket.") from None


def delete_blob_from_cloud(storage_key: str) -> bool:
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False
    try:
        client.delete_object(Bucket=bucket, Key=storage_key)
        return True
    except Exception:
        logger.warning("Cloud deletion failed.")
        return False
