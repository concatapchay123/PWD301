"""API tests for Video DRM HLS delivery, tokenized key exchange and raw download lockout (TASK-085)."""

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod
from pwd301.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user
from pwd301.services.video_drm_service import (
    get_asset_hls_directory,
    transcode_to_encrypted_hls,
)


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
    u = register_user("drm_instructor@example.com", "Password@123", "DRM Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("drm_student@example.com", "Password@123", "DRM Student")
    return assign_role_to_user(u.id, "STUDENT")


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.get("/auth/login")
    data = res.get_json() or {}
    csrf_token = data.get("csrf_token", "")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.get_json()}"
    return csrf_token


@pytest.fixture
def course_sample(app: Flask, instructor_user: User) -> Course:
    return create_course(
        instructor_user,
        {
            "course_code": "SEC-DRM-201",
            "title": "Encrypted Video Streaming Course",
            "description": "Course for DRM API testing",
            "subject_area": "Security",
            "level": "BEGINNER",
        },
    )


def test_student_cannot_download_raw_lesson_video(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Enrolled student attempting to download raw video file is rejected fail-closed."""
    sess = db.session

    admin = register_user("drm_admin@example.com", "Password@123", "DRM Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    # Create dummy video file on disk in app FILE_STORAGE_ROOT
    from pwd301.services.file_service import get_file_storage_root

    with app.app_context():
        storage_dir = get_file_storage_root()
    storage_dir.mkdir(parents=True, exist_ok=True)
    rel_key = f"blobs/{uuid.uuid4().hex}.mp4"
    phys_path = storage_dir / rel_key
    phys_path.parent.mkdir(parents=True, exist_ok=True)
    video_bytes = b"dummy mp4 video bytes" * 50
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
        course_id=course_sample.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Bài giảng Video 1",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    rev = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="lesson_vid.mp4",
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

    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_sample.id,
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
    login_client(client, student_user.email)

    # Try downloading raw video
    resp = client.get(
        f"/student/courses/{course_sample.public_id}/files/{asset.public_id}/download"
    )
    assert resp.status_code == 403, (
        f"Expected 403 Forbidden for raw video download, got {resp.status_code}: {resp.data.decode('utf-8', errors='ignore')}"
    )
    data = resp.get_json() or {}
    error_obj = data.get("error")
    msg = error_obj.get("message", "") if isinstance(error_obj, dict) else str(error_obj)
    assert "protected video playback" in msg.lower()


def test_student_can_fetch_drm_playlist_and_key(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Enrolled student can stream HLS playlist and retrieve short-lived AES key."""
    sess = db.session

    admin = register_user("drm_admin2@example.com", "Password@123", "DRM Admin 2")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    # Generate 1s test mp4 via ffmpeg
    temp_dir = tempfile.mkdtemp(prefix="pwd301_drm_api_")
    test_mp4 = os.path.join(temp_dir, "test.mp4")
    gen_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=1:size=320x240:rate=1",
        "-f",
        "lavfi",
        "-i",
        "sine=duration=1",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        test_mp4,
    ]
    subprocess.run(gen_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "HLS Protected Lesson",
            "markdown_content": "# Lesson Content",
            "status": "PUBLISHED",
        },
    )

    # Streaming fixtures require an attached, active and scanned video revision.
    video_bytes = Path(test_mp4).read_bytes()
    blob = FileBlob(
        sha256=hashlib.sha256(video_bytes).digest(),
        size_bytes=len(video_bytes),
        detected_mime_type="video/mp4",
        storage_key=f"fixture/{uuid.uuid4()}.mp4",
        status="PRESENT",
    )
    sess.add(blob)
    sess.flush()
    asset = FileAsset(
        course_id=course_sample.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Protected MP4",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()
    revision = FileRevision(
        file_asset_id=asset.id,
        blob_id=blob.id,
        revision_no=1,
        is_current=True,
        original_filename="test.mp4",
        detected_mime_type="video/mp4",
        size_bytes=len(video_bytes),
        status="ACTIVE",
        uploaded_by_user_id=instructor_user.id,
    )
    sess.add(revision)
    sess.flush()
    sess.add(
        FileScanResult(
            file_revision_id=revision.id,
            scan_type="MALWARE",
            engine="fixture-scanner",
            status="PASS",
        )
    )
    sess.add(
        LessonResource(
            lesson_id=lesson.id, file_asset_id=asset.id, position=1, label="Protected MP4"
        )
    )
    sess.flush()
    hls_dir = get_asset_hls_directory(lesson, asset, revision)
    transcode_to_encrypted_hls(
        input_path=test_mp4,
        output_dir=str(hls_dir),
        key_uri_relative="key",
        segment_duration_seconds=1,
    )

    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=course_sample.id,
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
    login_client(client, student_user.email)

    # 1. Fetch playlist
    playlist_url = (
        f"/student/courses/{course_sample.public_id}/lessons/{lesson.public_id}/video/playlist.m3u8"
    )
    resp = client.get(playlist_url)
    assert resp.status_code == 200, f"Expected 200 OK for playlist, got {resp.status_code}"
    playlist_text = resp.get_data(as_text=True)

    assert "#EXT-X-KEY:METHOD=AES-128" in playlist_text
    assert f"/video/{asset.public_id}/key?token=" in playlist_text

    # Extract token
    match = re.search(r'URI="([^\"]+/key\?token=[^\"]+)"', playlist_text)
    assert match is not None
    key_url = match.group(1)

    # 2. Fetch key using valid token
    key_resp = client.get(key_url)
    assert key_resp.status_code == 200, f"Expected 200 OK for DRM key, got {key_resp.status_code}"
    assert len(key_resp.data) == 16, f"Expected 16 bytes AES key, got {len(key_resp.data)}"
    assert key_resp.headers.get("Cache-Control") == "private, no-store"

    # 3. Fetch key with tampered token -> 403 Forbidden
    bad_key_resp = client.get(
        f"/student/courses/{course_sample.public_id}/lessons/{lesson.public_id}/video/key?token=badtoken"
    )
    assert bad_key_resp.status_code == 403

    shutil.rmtree(temp_dir, ignore_errors=True)
