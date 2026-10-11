import io

import pytest
from flask import Flask

from pwd301.services import storage_adapter as storage
from pwd301.services.exceptions import FileStorageError


def test_s3_missing_configuration_fails_closed(monkeypatch):
    app = Flask(__name__)
    app.config["STORAGE_BACKEND"] = "s3"
    with app.app_context(), pytest.raises(FileStorageError):
        storage.get_s3_client()


def test_upload_readback_mismatch_is_not_success(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config["STORAGE_BACKEND"] = "s3"
    file = tmp_path / "file"
    file.write_bytes(b"clean document")

    class Client:
        def upload_file(self, *args, **kwargs):
            pass

        def get_object(self, **kwargs):
            return {"Body": io.BytesIO(b"corrupted"), "ContentLength": 9}

    monkeypatch.setattr(storage, "get_s3_client", lambda: (Client(), "bucket"))
    with app.app_context():
        assert storage.upload_blob_to_cloud(file, "blobs/key") is False


def test_upload_verifies_stream_hash_and_size(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config["STORAGE_BACKEND"] = "s3"
    file = tmp_path / "file"
    file.write_bytes(b"clean document")

    class Client:
        def upload_file(self, *args, **kwargs):
            pass

        def get_object(self, **kwargs):
            return {"Body": io.BytesIO(file.read_bytes()), "ContentLength": file.stat().st_size}

    monkeypatch.setattr(storage, "get_s3_client", lambda: (Client(), "bucket"))
    with app.app_context():
        assert storage.upload_blob_to_cloud(file, "blobs/key") is True


from tests import test_files as file_fixtures

setup_roles = file_fixtures.setup_roles
file_instructor = file_fixtures.file_instructor
file_course = file_fixtures.file_course
from pwd301.extensions import db
from pwd301.models.file_import import FileAsset, FileBlob
from pwd301.services import file_service


def test_failed_cloud_upload_cannot_activate(app, file_instructor, file_course, monkeypatch):
    app.config["STORAGE_BACKEND"] = "s3"
    monkeypatch.setattr(file_service, "upload_blob_to_cloud", lambda *args: False)
    with pytest.raises(FileStorageError):
        file_service.store_file_stream(
            file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 release failure"), "failure.pdf"
        )
    assert db.session.query(FileAsset).count() == 0
    assert db.session.query(FileBlob).count() == 0


def test_cloud_commit_removes_local_and_ticket_does_not_materialize(
    app, file_instructor, file_course, monkeypatch
):
    app.config["STORAGE_BACKEND"] = "s3"
    monkeypatch.setattr(file_service, "upload_blob_to_cloud", lambda *args: True)
    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 cloud document"), "Tai lieu.pdf"
    )
    blob = asset.current_revision.blob
    assert blob.storage_backend == "s3"
    assert blob.cloud_verified_at is not None
    assert not (file_service.get_file_storage_root() / blob.storage_key).exists()
    monkeypatch.setattr(
        file_service, "create_download_url", lambda *args: "https://isolated.invalid/ticket"
    )
    ticket = file_service.get_file_download_ticket(file_instructor, asset.public_id)
    assert ticket == {"url": "https://isolated.invalid/ticket", "expires_in": 60}
    asset.current_revision.status = "QUARANTINED"
    db.session.commit()
    from pwd301.services.exceptions import FileSecurityQuarantineError

    with pytest.raises(FileSecurityQuarantineError):
        file_service.get_file_download_ticket(file_instructor, asset.public_id)


def test_cache_cleanup_preserves_quarantine_and_symlinks(app, tmp_path):
    import os

    root = file_service.get_file_storage_root()
    cached = root / "cache" / "old"
    cached.parent.mkdir()
    cached.write_bytes(b"cache")
    os.utime(cached, (0, 0))
    quarantine = file_service.get_file_quarantine_root() / "evidence"
    quarantine.write_bytes(b"pending evidence")
    assert file_service.cleanup_storage_cache() == 1
    assert quarantine.exists()


def test_storage_maintenance_refuses_non_staging(app):
    from pwd301.services.storage_maintenance_service import maintain_storage

    with pytest.raises(FileStorageError):
        maintain_storage("migrate", session=db.session)


def test_storage_migration_is_resumable_and_preserves_source_until_prune(
    app, file_instructor, file_course, monkeypatch
):
    from pwd301.services import storage_maintenance_service as maintenance

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 migrate document"), "migrate.pdf"
    )
    blob = asset.current_revision.blob
    source = file_service.get_file_storage_root() / blob.storage_key
    app.config["STORAGE_MAINTENANCE_STAGING"] = True
    app.config["STORAGE_BACKEND"] = "s3"
    monkeypatch.setattr(maintenance, "upload_blob_to_cloud", lambda *args: True)
    monkeypatch.setattr(maintenance, "verify_cloud_blob", lambda *args: True)
    assert maintenance.maintain_storage("migrate", db.session)[0]["result"] == "migrated"
    assert source.exists()
    assert maintenance.maintain_storage("migrate", db.session)[0]["result"] == "already_cloud"
    assert maintenance.maintain_storage("prune", db.session)[0]["result"] == "pruned"
    assert not source.exists()


def test_download_uses_latest_scanner_verdict_not_stale_error(app, file_instructor, file_course):
    from datetime import timedelta

    from pwd301.models.file_import import FileScanResult
    from pwd301.models.types import utc_now

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 scan retry"), "retry.pdf"
    )
    rev = asset.current_revision
    malware = next(scan for scan in rev.scan_results if scan.scan_type == "MALWARE")
    malware.status = "ERROR"
    db.session.add(
        FileScanResult(
            file_revision_id=rev.id,
            scan_type="MALWARE",
            engine=malware.engine,
            engine_version="retry",
            status="PASS",
            started_at=utc_now() + timedelta(seconds=1),
            completed_at=utc_now() + timedelta(seconds=1),
        )
    )
    db.session.commit()
    assert (
        file_service.get_file_download_ticket(file_instructor, asset.public_id)["expires_in"]
        is None
    )
    assert asset.virus_scan_status == "CLEAN"
    assert asset.has_passed_malware_scan


def test_tickets_require_authentication_and_cloud_verification(
    app, file_instructor, file_course, monkeypatch
):
    from pwd301.services.exceptions import FileAccessDeniedError

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 authorization"), "auth.pdf"
    )
    with pytest.raises(FileAccessDeniedError):
        file_service.get_file_download_ticket(None, asset.public_id)
    asset.current_revision.blob.storage_backend = "s3"
    asset.current_revision.blob.cloud_verified_at = None
    db.session.commit()
    with pytest.raises(FileStorageError):
        file_service.get_file_download_ticket(file_instructor, asset.public_id)


def test_raw_video_never_receives_ticket(app, monkeypatch):
    from types import SimpleNamespace

    from pwd301.services.exceptions import FileAccessDeniedError

    asset = SimpleNamespace(is_video=True)
    blob = SimpleNamespace(detected_mime_type="video/mp4")
    monkeypatch.setattr(file_service, "authorize_file_download", lambda *args: (asset, blob, None))
    with pytest.raises(FileAccessDeniedError):
        file_service.get_file_download_ticket(None, "video")


def test_document_ticket_route_supports_web_session(client, file_instructor, file_course):
    from tests.conftest import login_web_user

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 web ticket"), "web.pdf"
    )
    login_web_user(client, file_instructor)
    response = client.post(f"/api/files/{asset.public_id}/download-ticket", json={})
    assert response.status_code == 200
    assert response.get_json()["url"].startswith("/api/files/")
    assert response.headers["Cache-Control"] == "no-store"


def test_document_ticket_web_post_requires_csrf(app, client, file_instructor, file_course):
    from tests.conftest import login_web_user

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 csrf"), "csrf.pdf"
    )
    login_web_user(client, file_instructor)
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post(f"/api/files/{asset.public_id}/download-ticket", json={})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "CSRF_ERROR"


def test_parallel_temporary_writes_share_a_process_safe_budget(app, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from pwd301.services.file_service import with_storage_budget

    root = tmp_path / "limited"
    root.mkdir()
    app.config["FILE_QUARANTINE_MAX_BYTES"] = 15
    start = Barrier(2)

    @with_storage_budget
    def write_file(name):
        file_service.reserve_storage_space(root, 10)
        (root / name).write_bytes(b"0123456789")

    def attempt(name):
        with app.app_context():
            start.wait()
            try:
                write_file(name)
                return True
            except FileStorageError:
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["a", "b"]))
    assert sorted(results) == [False, True]
    assert sum(path.stat().st_size for path in root.iterdir()) == 10


def test_document_migration_never_moves_raw_video(app, file_instructor, file_course, monkeypatch):
    from pwd301.services import storage_maintenance_service as maintenance

    asset = file_service.store_file_stream(
        file_instructor,
        file_course.id,
        io.BytesIO(b"%PDF-1.4 video migration exclusion"),
        "video.pdf",
    )
    asset.current_revision.blob.detected_mime_type = "video/mp4"
    db.session.commit()
    app.config["STORAGE_MAINTENANCE_STAGING"] = True
    monkeypatch.setattr(maintenance, "upload_blob_to_cloud", lambda *args: True)
    assert maintenance.maintain_storage("migrate", db.session)[0]["result"] == "ineligible"


@pytest.mark.parametrize("auth", ["session", "jwt"])
def test_learner_api_raw_video_download_is_denied(client, file_instructor, file_course, auth):
    from pwd301.services.enrollment_service import enroll_student
    from pwd301.services.jwt_auth_service import create_token_pair
    from pwd301.services.user_service import register_user
    from tests.conftest import login_web_user

    student = register_user("raw-video@example.com", "Password@123", "Student")
    enroll_student(student, file_course.id, session=db.session)
    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 raw video boundary"), "raw.pdf"
    )
    revision = asset.current_revision
    revision.original_filename = "lesson.mp4"
    revision.detected_mime_type = "video/mp4"
    revision.blob.detected_mime_type = "video/mp4"
    db.session.commit()
    if auth == "session":
        login_web_user(client, student)
        headers = {}
    else:
        headers = {"Authorization": "Bearer " + create_token_pair(student)["access_token"]}
    response = client.get(f"/api/files/{asset.public_id}/download", headers=headers)
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FORBIDDEN"
    assert file_service.get_file_for_download(file_instructor, asset.public_id)[2].is_file()


@pytest.mark.parametrize("payload", [[], [1], True, "invalid"])
def test_download_ticket_requires_json_object(client, file_instructor, file_course, payload):
    from tests.conftest import login_web_user

    asset = file_service.store_file_stream(
        file_instructor, file_course.id, io.BytesIO(b"%PDF-1.4 payload shape"), "shape.pdf"
    )
    login_web_user(client, file_instructor)
    response = client.post(f"/api/files/{asset.public_id}/download-ticket", json=payload)
    assert response.status_code == 400
