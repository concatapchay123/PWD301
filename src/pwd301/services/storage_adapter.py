"""Decoupled Cloud Storage Adapter for PWD301.

Provides optional offloading of physical file blobs to S3-compatible cloud storage
(AWS S3, Cloudflare R2, MinIO, Wasabi) to support low-disk VPS environments.

Adheres to:
- ADR-008 Physical Blob and Logical Asset separation.
- Fail-safe fallback to local disk storage if cloud credentials or boto3 are absent.
- Full output enforcement without truncations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import current_app

logger = logging.getLogger(__name__)

_boto3_module: Any | None = None
_boto3_imported: bool = False


def _get_boto3() -> Any | None:
    """Lazy import of boto3 to prevent unnecessary runtime overhead when local storage is used."""
    global _boto3_module, _boto3_imported
    if not _boto3_imported:
        _boto3_imported = True
        try:
            import boto3

            _boto3_module = boto3
        except ImportError:
            _boto3_module = None
            logger.info("boto3 is not installed. Cloud storage offloading disabled, using local disk.")
    return _boto3_module


def is_cloud_storage_enabled() -> bool:
    """Return True if cloud storage backend is configured and enabled."""
    backend = current_app.config.get("STORAGE_BACKEND", "local")
    return str(backend).strip().lower() == "s3"


def get_s3_client() -> tuple[Any | None, str | None]:
    """Return initialized boto3 S3 client and configured bucket name, or (None, None)."""
    if not is_cloud_storage_enabled():
        return None, None

    boto3 = _get_boto3()
    if boto3 is None:
        return None, None

    bucket = current_app.config.get("S3_BUCKET_NAME")
    endpoint_url = current_app.config.get("S3_ENDPOINT_URL")
    access_key = current_app.config.get("S3_ACCESS_KEY_ID")
    secret_key = current_app.config.get("S3_SECRET_ACCESS_KEY")
    region_name = current_app.config.get("S3_REGION_NAME", "auto")

    if not bucket or not access_key or not secret_key:
        logger.warning(
            "Cloud storage is set to 's3' but S3_BUCKET_NAME, S3_ACCESS_KEY_ID or "
            "S3_SECRET_ACCESS_KEY is missing. Falling back to local disk storage."
        )
        return None, None

    try:
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )
        return client, bucket
    except Exception as exc:
        logger.error("Failed to initialize boto3 S3 client: %s", exc)
        return None, None


def upload_blob_to_cloud(local_path: Path, storage_key: str) -> bool:
    """Upload a verified physical blob file to cloud storage.

    Returns True if uploaded successfully, False otherwise.
    """
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False

    if not local_path.exists() or not local_path.is_file():
        logger.warning("Local blob path %s does not exist; skipping cloud upload.", local_path)
        return False

    try:
        client.upload_file(str(local_path), bucket, storage_key)
        logger.info("Successfully mirrored blob %s to cloud bucket %s", storage_key, bucket)
        return True
    except Exception as exc:
        logger.error("Failed to upload blob %s to cloud bucket %s: %s", storage_key, bucket, exc)
        return False


def download_blob_from_cloud(storage_key: str, dest_path: Path) -> bool:
    """Download a physical blob from cloud storage to local disk cache.

    Returns True if downloaded successfully, False otherwise.
    """
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, storage_key, str(dest_path))
        logger.info("Successfully fetched blob %s from cloud bucket %s to %s", storage_key, bucket, dest_path)
        return True
    except Exception as exc:
        logger.warning("Failed to download blob %s from cloud bucket %s: %s", storage_key, bucket, exc)
        return False


def delete_blob_from_cloud(storage_key: str) -> bool:
    """Delete a physical blob from cloud storage.

    Returns True if deleted or ignored, False on error.
    """
    client, bucket = get_s3_client()
    if client is None or bucket is None:
        return False

    try:
        client.delete_object(Bucket=bucket, Key=storage_key)
        logger.info("Deleted blob %s from cloud bucket %s", storage_key, bucket)
        return True
    except Exception as exc:
        logger.error("Failed to delete blob %s from cloud bucket %s: %s", storage_key, bucket, exc)
        return False
