"""Regression coverage for test-worker filesystem isolation."""

from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient


def test_app_fixture_does_not_share_runtime_storage(
    app: Flask, client: FlaskClient, tmp_path: Path
) -> None:
    """A restore marker from another worker must not block an isolated API test."""
    roots = [
        Path(app.config[key]).resolve()
        for key in ("FILE_STORAGE_ROOT", "FILE_QUARANTINE_ROOT", "FILE_BACKUP_ROOT")
    ]
    assert all(root.is_relative_to(tmp_path.resolve()) for root in roots), roots
    assert len(set(roots)) == 3
    response = client.get("/api/notifications/unread-count")
    assert response.status_code == 401, response.get_json()
