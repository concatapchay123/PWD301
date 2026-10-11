"""Reviewer byte streaming uses real file bytes and persisted security decisions."""

import hashlib

import pytest

from pwd301.extensions import db
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision, FileScanResult
from pwd301.models.identity import Role, UserRole
from pwd301.models.types import utc_now
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def video_env(app):
    for code in ("STUDENT", "INSTRUCTOR", "ADMIN"):
        db.session.add(Role(code=code, name=code))
    db.session.commit()
    users = {}
    for name, role in (
        ("owner", "INSTRUCTOR"),
        ("foreign", "INSTRUCTOR"),
        ("reviewer", "ADMIN"),
        ("monitor", "ADMIN"),
        ("student", "STUDENT"),
    ):
        user = register_user(f"{name}@stream.test", "Password123!", name)
        assign_role_to_user(user.id, role)
        if role == "ADMIN":
            assignment = (
                db.session.query(UserRole)
                .filter_by(
                    user_id=user.id, role_id=db.session.query(Role).filter_by(code="ADMIN").one().id
                )
                .one()
            )
            assignment.assignment_reason = (
                "SUB_ROLE:ADMIN_COURSE_REVIEW"
                if name == "reviewer"
                else "SUB_ROLE:ADMIN_SYSTEM_MONITORING"
            )
        users[name] = user
    course = create_course(users["owner"], {"course_code": "STREAM090", "title": "Video reviewer"})
    content = bytes(range(256)) * 4
    root = app.config["FILE_STORAGE_ROOT"]
    root.mkdir(parents=True, exist_ok=True)
    (root / "review.mp4").write_bytes(content)
    blob = FileBlob(
        sha256=hashlib.sha256(content).digest(),
        size_bytes=len(content),
        detected_mime_type="video/mp4",
        storage_key="review.mp4",
        status="PRESENT",
    )
    asset = FileAsset(
        course_id=course.id,
        created_by_user_id=users["owner"].id,
        asset_type="RESOURCE",
        display_name="Bài giảng.mp4",
        status="ACTIVE",
    )
    db.session.add_all([blob, asset])
    db.session.flush()
    revision = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="Bài giảng.mp4",
        size_bytes=len(content),
        detected_mime_type="video/mp4",
        status="ACTIVE",
        uploaded_by_user_id=users["owner"].id,
    )
    db.session.add(revision)
    db.session.flush()
    scan = FileScanResult(
        file_revision_id=revision.id,
        scan_type="MALWARE",
        engine="fixture",
        status="PASS",
        started_at=utc_now(),
    )
    db.session.add(scan)
    db.session.commit()
    return users, asset, revision, scan, content


@pytest.mark.parametrize("role", ["owner", "reviewer"])
def test_reviewer_full_stream_is_inline_and_private(client, video_env, role):
    users, asset, _, _, content = video_env
    login_web_user(client, users[role])
    response = client.get(f"/api/files/{asset.public_id}/stream")
    assert response.status_code == 200
    assert response.data == content
    assert response.headers["Accept-Ranges"] == "bytes"
    assert response.headers["Content-Type"] == "video/mp4"
    assert response.headers["Content-Disposition"].startswith("inline;")
    assert "no-store" in response.headers["Cache-Control"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("bytes=10-19", bytes(range(10, 20))),
        ("bytes=-4", bytes(range(252, 256))),
        ("bytes=1020-", bytes(range(252, 256))),
    ],
)
def test_reviewer_partial_range(client, video_env, value, expected):
    users, asset, _, _, _ = video_env
    login_web_user(client, users["owner"])
    response = client.get(f"/api/files/{asset.public_id}/stream", headers={"Range": value})
    assert response.status_code == 206
    assert response.data == expected
    assert response.headers["Content-Range"].endswith("/1024")
    assert int(response.headers["Content-Length"]) == len(expected)


@pytest.mark.parametrize("value", ["bytes=1024-", "bytes=50-10", "bytes=bad", "bytes=0-1,4-5"])
def test_invalid_range_returns_416(client, video_env, value):
    users, asset, _, _, _ = video_env
    login_web_user(client, users["owner"])
    assert (
        client.get(f"/api/files/{asset.public_id}/stream", headers={"Range": value}).status_code
        == 416
    )


@pytest.mark.parametrize("role", ["foreign", "monitor", "student"])
def test_non_reviewers_cannot_stream_raw_video(client, video_env, role):
    users, asset, _, _, content = video_env
    login_web_user(client, users[role])
    response = client.get(f"/api/files/{asset.public_id}/stream", headers={"Range": "bytes=0-5"})
    assert response.status_code == 403
    assert response.data != content[:6]


@pytest.mark.parametrize("version", ["0", "-1", "abc", "1.5"])
def test_invalid_revision_is_not_silently_current(client, video_env, version):
    users, asset, _, _, _ = video_env
    login_web_user(client, users["owner"])
    assert client.get(f"/api/files/{asset.public_id}/stream?version={version}").status_code == 400


@pytest.mark.parametrize("unsafe", ["pending", "quarantine", "scan_error", "no_scan"])
def test_reviewer_scan_security_fail_closed(client, video_env, unsafe):
    users, asset, revision, scan, _ = video_env
    if unsafe == "pending":
        asset.status = "PENDING"
    elif unsafe == "quarantine":
        # SQL Server forbids an unsafe revision from remaining the current revision.
        revision.is_current = False
        revision.status = "QUARANTINED"
    elif unsafe == "scan_error":
        scan.status = "ERROR"
    else:
        db.session.delete(scan)
    db.session.commit()
    login_web_user(client, users["reviewer"])
    assert client.get(f"/api/files/{asset.public_id}/stream").status_code == 403


def test_invalid_bearer_never_falls_back_to_reviewer_cookie(client, video_env):
    users, asset, _, _, _ = video_env
    login_web_user(client, users["reviewer"])
    assert client.get(
        f"/api/files/{asset.public_id}/stream", headers={"Authorization": "Bearer invalid"}
    ).status_code in (401, 403)
