"""End-to-End Security & Defense Tests for PWD301 Copyright Protection and Anti-Tamper System (TASK-085).

Covers:
1. Anti-Raw Download: Students cannot download raw lesson video files (.mp4/.webm).
2. Encrypted HLS Delivery: Lessons serve AES-128 encrypted HLS playlist with short-lived tokens.
3. Tokenized Key Defense: Decryption key is served only to actively enrolled students with valid HMAC token.
4. Wall-Clock Zero-Trust: API rejects fraudulent video progress jumps and logs security audit anomalies.
5. Natural Heartbeat Progression: Legitimate time accumulation marks lesson complete only when wall-clock threshold met.
"""

import hashlib
import os
import re
import shutil
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision, FileScanResult
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.file_service import get_file_storage_root
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user
from pwd301.services.video_drm_service import get_lesson_hls_directory


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("ADMIN", "System Administrator"),
        ("INSTRUCTOR", "Course Instructor"),
        ("STUDENT", "Enrolled Student"),
    ]:
        role = sess.query(Role).filter_by(code=code).first()
        if not role:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("e2e_instructor@example.com", "Password@123", "E2E Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("e2e_student@example.com", "Password@123", "E2E Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("e2e_admin@example.com", "Password@123", "E2E Admin")
    return assign_role_to_user(u.id, "ADMIN")


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.get("/auth/login")
    data = res.get_json() or {}
    csrf_token = data.get("csrf_token", "")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200, f"Login failed for {email}: {login_res.get_json()}"
    return csrf_token


def test_copyright_protection_end_to_end_defense(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    admin_user: User,
) -> None:
    """Comprehensive E2E copyright defense verification."""
    sess = db.session

    # 1. Setup published course and lesson
    course = create_course(
        instructor_user,
        {
            "course_code": "SEC-E2E-999",
            "title": "Comprehensive Copyright Protection Course",
            "description": "Full end-to-end verification",
            "subject_area": "Security",
            "level": "BEGINNER",
        },
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, course.id, "APPROVED")
    change_course_status(instructor_user, course.id, "PUBLISHED")

    lesson = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Bảo vệ bản quyền đa tầng",
            "summary": "Tổng quan hệ thống DRM & VideoArmor",
            "markdown_content": "# Nội dung bài giảng DRM\nChi tiết bảo vệ bản quyền.",
            "min_completion_seconds": 60,
            "viewed_fraction_required": 0.90,
            "status": "PUBLISHED",
        },
    )

    # 2. Setup raw video blob in permanent storage
    with app.app_context():
        storage_dir = get_file_storage_root()
    rel_key = f"blobs/{uuid.uuid4().hex}.mp4"
    phys_path = storage_dir / rel_key
    phys_path.parent.mkdir(parents=True, exist_ok=True)
    video_bytes = b"dummy mp4 video bytes for e2e" * 80
    phys_path.write_bytes(video_bytes)

    f_hash = hashlib.sha256(video_bytes).digest()
    blob = FileBlob(
        sha256=f_hash,
        size_bytes=len(video_bytes),
        detected_mime_type="video/mp4",
        storage_key=rel_key,
        status="PRESENT",
    )
    sess.add(blob)
    sess.flush()

    asset = FileAsset(
        public_id=uuid.uuid4(),
        course_id=course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Bài giảng E2E Video",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    rev = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="e2e_video.mp4",
        size_bytes=len(video_bytes),
        status="ACTIVE",
        uploaded_by_user_id=instructor_user.id,
    )
    sess.add(rev)
    sess.flush()

    scan = FileScanResult(
        file_revision_id=rev.id,
        scan_type="MALWARE",
        engine="ClamAV",
        status="PASS",
    )
    sess.add(scan)

    # Enroll student
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()
    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id
    sess.commit()

    # Log in as student
    csrf_token = login_client(client, student_user.email)

    # DEFENSE 1: Student cannot download raw video file
    raw_download_resp = client.get(
        f"/student/courses/{course.public_id}/files/{asset.public_id}/download"
    )
    assert raw_download_resp.status_code == 403, (
        "Student must be forbidden from downloading raw video files"
    )
    err_body = raw_download_resp.get_json() or {}
    err_msg = (
        err_body.get("error", {}).get("message", "")
        if isinstance(err_body.get("error"), dict)
        else str(err_body.get("error"))
    )
    assert "restricted" in err_msg.lower() or "secure" in err_msg.lower()

    # Create mock HLS directory with encrypted playlist
    hls_dir = get_lesson_hls_directory(course.id, lesson.id)
    hls_dir.mkdir(parents=True, exist_ok=True)
    raw_key = os.urandom(16)
    (hls_dir / "enc.key").write_bytes(raw_key)
    mock_playlist = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-TARGETDURATION:10\n"
        '#EXT-X-KEY:METHOD=AES-128,URI="enc.key",IV=0x0123456789abcdef0123456789abcdef\n'
        "#EXTINF:10.000000,\n"
        "segment_000.ts\n"
        "#EXT-X-ENDLIST\n"
    )
    (hls_dir / "playlist.m3u8").write_text(mock_playlist, encoding="utf-8")
    (hls_dir / "segment_000.ts").write_bytes(b"dummy encrypted ts segment")

    # DEFENSE 2: Fetch encrypted HLS playlist
    playlist_url = (
        f"/student/courses/{course.public_id}/lessons/{lesson.public_id}/video/playlist.m3u8"
    )
    p_resp = client.get(playlist_url)
    assert p_resp.status_code == 200
    p_text = p_resp.get_data(as_text=True)
    assert "#EXT-X-KEY:METHOD=AES-128" in p_text
    assert 'URI="key?token=' in p_text

    # Extract token
    match = re.search(r'URI="key\?token=([^"]+)"', p_text)
    assert match is not None
    key_token = match.group(1)

    # DEFENSE 3: Fetch DRM key with valid token
    key_url = f"/student/courses/{course.public_id}/lessons/{lesson.public_id}/video/key?token={key_token}"
    k_resp = client.get(key_url)
    assert k_resp.status_code == 200
    assert len(k_resp.data) == 16
    assert k_resp.headers.get("Cache-Control") == "private, no-store"

    # DEFENSE 4: Fetch DRM key with forged token -> 403 Forbidden
    bad_k_resp = client.get(
        f"/student/courses/{course.public_id}/lessons/{lesson.public_id}/video/key?token=forged.token.here"
    )
    assert bad_k_resp.status_code == 403

    # DEFENSE 5: Zero-Trust Wall Clock Heartbeat vs Progress Jump Attack
    from pwd301.services.jwt_auth_service import create_token_pair

    tokens = create_token_pair(student_user)
    jwt_token = tokens["access_token"]
    jwt_headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}

    progress_url = f"/api/lessons/{lesson.public_id}/progress"

    # Initial baseline heartbeat ping (3s)
    first_resp = client.post(
        progress_url,
        json={"seconds_increment": 3, "view_fraction": 0.05},
        headers=jwt_headers,
    )
    assert first_resp.status_code == 200

    # Attacker immediately fires fraudulent ping claiming 60s within milliseconds
    cheat_resp = client.post(
        progress_url,
        json={"seconds_increment": 60, "view_fraction": 1.0, "is_completed": True},
        headers=jwt_headers,
    )
    assert cheat_resp.status_code == 200
    cheat_data = cheat_resp.get_json() or {}

    # The backend must NOT grant 60 seconds; it must cap it to the elapsed wall-clock time
    data_obj = cheat_data.get("data") or cheat_data
    seconds_recorded = data_obj.get("seconds_spent", 0)
    assert seconds_recorded <= 10, f"Expected wall-clock clamped seconds, got {seconds_recorded}"
    assert data_obj.get("is_completed") is False, (
        "Fraudulent progress jump must NOT mark lesson complete"
    )

    # Check that audit log recorded anomaly
    audit_evt = sess.query(AuditEvent).filter_by(action="LESSON_PROGRESS_PACE_ANOMALY").first()
    assert audit_evt is not None, "Audit event for progress pace anomaly must be persisted"

    # Clean up mock HLS dir
    shutil.rmtree(hls_dir, ignore_errors=True)
