"""Unit tests for Decoupled Cloud Storage Adapter and fallback mechanics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from flask import Flask

from pwd301.services.storage_adapter import (
    delete_blob_from_cloud,
    download_blob_from_cloud,
    get_s3_client,
    is_cloud_storage_enabled,
    upload_blob_to_cloud,
)


def test_storage_adapter_disabled_by_default(app: Flask) -> None:
    """Verify that cloud storage is disabled by default (local disk backend)."""
    with app.app_context():
        app.config["STORAGE_BACKEND"] = "local"
        assert is_cloud_storage_enabled() is False
        client, bucket = get_s3_client()
        assert client is None
        assert bucket is None

        # Upload attempt gracefully returns False
        tmp = Path("test_dummy.txt")
        assert upload_blob_to_cloud(tmp, "blobs/12/34/dummy") is False


def test_storage_adapter_missing_credentials(app: Flask) -> None:
    """Verify that setting backend to s3 without credentials logs warning and returns None."""
    with app.app_context():
        app.config["STORAGE_BACKEND"] = "s3"
        app.config["S3_BUCKET_NAME"] = None
        app.config["S3_ACCESS_KEY_ID"] = None
        app.config["S3_SECRET_ACCESS_KEY"] = None

        assert is_cloud_storage_enabled() is True
        client, bucket = get_s3_client()
        assert client is None
        assert bucket is None


def test_storage_adapter_mock_boto3_operations(app: Flask, tmp_path: Path) -> None:
    """Verify upload, download, and delete flows when S3 client is active."""
    with app.app_context():
        app.config["STORAGE_BACKEND"] = "s3"
        app.config["S3_BUCKET_NAME"] = "test-bucket"
        app.config["S3_ACCESS_KEY_ID"] = "test-key"
        app.config["S3_SECRET_ACCESS_KEY"] = "test-secret"
        app.config["S3_ENDPOINT_URL"] = "https://s3.example.com"

        mock_s3 = MagicMock()
        with patch("pwd301.services.storage_adapter.get_s3_client", return_value=(mock_s3, "test-bucket")):
            # 1. Test upload
            local_file = tmp_path / "sample.bin"
            local_file.write_bytes(b"hello world")
            assert upload_blob_to_cloud(local_file, "blobs/ab/cd/hash") is True
            mock_s3.upload_file.assert_called_once_with(str(local_file), "test-bucket", "blobs/ab/cd/hash")

            # 2. Test download
            dest_file = tmp_path / "downloaded.bin"
            assert download_blob_from_cloud("blobs/ab/cd/hash", dest_file) is True
            mock_s3.download_file.assert_called_once_with("test-bucket", "blobs/ab/cd/hash", str(dest_file))

            # 3. Test delete
            assert delete_blob_from_cloud("blobs/ab/cd/hash") is True
            mock_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key="blobs/ab/cd/hash")
