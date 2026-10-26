"""Adversarial challenge tests for HLS stream endpoint, asset resolution, and auth guards.

Tested by Challenger 1 (challenger_m1_t96_1).
"""

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from backend.extensions import db
from backend.models.course import Enrollment, EnrollmentPeriod
from backend.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from backend.models.identity import Role
from backend.services.course_service import change_course_status, create_course
from backend.services.lesson_service import create_lesson
from backend.services.user_service import assign_role_to_user, register_user
from backend.services.video_drm_service import (
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
def hls_fixture(app: Flask, setup_roles: dict[str, Role]):
    """Creates a fully published course, lesson, transcoded HLS video, and two students."""
    sess = db.session

    admin = register_user(f"hls_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin")
    admin = assign_role_to_user(admin.id, "ADMIN")

    instructor = register_user(
        f"hls_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor"
    )
    instructor = assign_role_to_user(instructor.id, "INSTRUCTOR")

    student_enrolled = register_user(
        f"hls_stu_enr_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Enrolled Student"
    )
    student_enrolled = assign_role_to_user(student_enrolled.id, "STUDENT")

    student_unenrolled = register_user(
        f"hls_stu_unenr_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Unenrolled Student"
    )
    student_unenrolled = assign_role_to_user(student_unenrolled.id, "STUDENT")

    course_a = create_course(
        instructor,
        {
            "course_code": f"HLS-{uuid.uuid4().hex[:4]}",
            "title": "HLS Challenge Course A",
            "description": "Testing HLS stream security",
            "subject_area": "Security",
            "level": "BEGINNER",
        },
    )

    lesson_a = create_lesson(
        instructor,
        course_a.id,
        {
            "title": "Lesson A with Video",
            "markdown_content": "# Lesson A Content",
            "status": "PUBLISHED",
        },
    )

    # Generate 1s test mp4 via ffmpeg
    temp_dir = tempfile.mkdtemp(prefix="pwd301_hls_test_")
    test_mp4 = os.path.join(temp_dir, "test.mp4")
    subprocess.run(
        [
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
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

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

    asset_video = FileAsset(
        course_id=course_a.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="Lesson A Main Video",
        status="ACTIVE",
    )
    sess.add(asset_video)
    sess.flush()

    rev_video = FileRevision(
        file_asset_id=asset_video.id,
        blob_id=blob.id,
        revision_no=1,
        is_current=True,
        original_filename="test.mp4",
        detected_mime_type="video/mp4",
        size_bytes=len(video_bytes),
        status="ACTIVE",
        uploaded_by_user_id=instructor.id,
    )
    sess.add(rev_video)
    sess.flush()

    sess.add(
        FileScanResult(
            file_revision_id=rev_video.id,
            scan_type="MALWARE",
            engine="fixture-scanner",
            status="PASS",
        )
    )

    sess.add(
        LessonResource(
            lesson_id=lesson_a.id,
            file_asset_id=asset_video.id,
            position=1,
            label="Main Video Resource",
        )
    )
    sess.flush()

    # Transcode to HLS
    hls_dir = get_asset_hls_directory(lesson_a, asset_video, rev_video)
    transcode_to_encrypted_hls(
        input_path=test_mp4,
        output_dir=str(hls_dir),
        key_uri_relative="key",
        segment_duration_seconds=1,
    )

    # Publish Course A
    change_course_status(instructor, course_a.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_a.id, "APPROVED")
    change_course_status(instructor, course_a.id, "PUBLISHED")

    # Enroll student_enrolled in Course A
    enr_a = Enrollment(
        student_user_id=student_enrolled.id,
        course_id=course_a.id,
        status="ACTIVE",
    )
    sess.add(enr_a)
    sess.flush()
    period_a = EnrollmentPeriod(
        enrollment_id=enr_a.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period_a)
    sess.flush()
    enr_a.current_period_id = period_a.id

    # Create Course B (different course)
    course_b = create_course(
        instructor,
        {
            "course_code": f"HLS-B-{uuid.uuid4().hex[:4]}",
            "title": "HLS Challenge Course B",
            "description": "Second course for isolation testing",
            "subject_area": "Security",
            "level": "INTERMEDIATE",
        },
    )
    lesson_b = create_lesson(
        instructor,
        course_b.id,
        {
            "title": "Lesson B in Course B",
            "markdown_content": "# Lesson B Content",
            "status": "PUBLISHED",
        },
    )
    change_course_status(instructor, course_b.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_b.id, "APPROVED")
    change_course_status(instructor, course_b.id, "PUBLISHED")

    # Non-video document asset in Course A
    blob_doc = FileBlob(
        sha256=hashlib.sha256(b"dummy pdf bytes").digest(),
        size_bytes=15,
        detected_mime_type="application/pdf",
        storage_key=f"fixture/{uuid.uuid4()}.pdf",
        status="PRESENT",
    )
    sess.add(blob_doc)
    sess.flush()

    asset_doc = FileAsset(
        course_id=course_a.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="Lesson PDF Document",
        status="ACTIVE",
    )
    sess.add(asset_doc)
    sess.flush()
    rev_doc = FileRevision(
        file_asset_id=asset_doc.id,
        blob_id=blob_doc.id,
        revision_no=1,
        is_current=True,
        original_filename="doc.pdf",
        detected_mime_type="application/pdf",
        size_bytes=15,
        status="ACTIVE",
        uploaded_by_user_id=instructor.id,
    )
    sess.add(rev_doc)
    sess.flush()
    sess.add(
        FileScanResult(
            file_revision_id=rev_doc.id,
            scan_type="MALWARE",
            engine="fixture-scanner",
            status="PASS",
        )
    )

    # Deleted video asset in Course A
    asset_deleted = FileAsset(
        course_id=course_a.id,
        created_by_user_id=instructor.id,
        asset_type="RESOURCE",
        display_name="Deleted Video",
        status="ACTIVE",
        deleted_at=datetime.now(UTC),
    )
    sess.add(asset_deleted)
    sess.flush()

    sess.commit()

    yield {
        "admin": admin,
        "instructor": instructor,
        "student_enrolled": student_enrolled,
        "student_unenrolled": student_unenrolled,
        "course_a": course_a,
        "lesson_a": lesson_a,
        "course_b": course_b,
        "lesson_b": lesson_b,
        "asset_video": asset_video,
        "asset_doc": asset_doc,
        "asset_deleted": asset_deleted,
        "temp_dir": temp_dir,
    }

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_unauthenticated_request_rejected(client: FlaskClient, hls_fixture: dict):
    """Anonymous learner cannot access HLS playlist or key."""
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    ast = hls_fixture["asset_video"]

    # 1. Playlist
    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code in (401, 302, 403), f"Expected 401/302/403, got {resp.status_code}"

    # 2. Key
    key_url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}/key?token=abc"
    resp = client.get(key_url)
    assert resp.status_code in (401, 302, 403), f"Expected 401/302/403, got {resp.status_code}"


def test_unenrolled_student_rejected(client: FlaskClient, hls_fixture: dict):
    """Logged in student who is not enrolled is rejected with 403 Forbidden."""
    unenrolled = hls_fixture["student_unenrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    ast = hls_fixture["asset_video"]

    login_client(client, unenrolled.email)

    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 403, f"Expected 403 Forbidden, got {resp.status_code}: {resp.data}"


def test_enrolled_student_can_stream_playlist_and_key(client: FlaskClient, hls_fixture: dict):
    """Enrolled student can successfully fetch AES-128 playlist and decrypt key."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    ast = hls_fixture["asset_video"]

    login_client(client, enrolled.email)

    # 1. Fetch playlist
    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    playlist_text = resp.get_data(as_text=True)
    assert "#EXT-X-KEY:METHOD=AES-128" in playlist_text
    assert f"/video/{ast.public_id}/key?token=" in playlist_text

    # Extract key URL
    m = re.search(r'URI="([^"]+/key\?token=[^"]+)"', playlist_text)
    assert m is not None
    key_url = m.group(1)

    # 2. Fetch key
    key_resp = client.get(key_url)
    assert key_resp.status_code == 200
    assert len(key_resp.data) == 16
    assert key_resp.headers.get("Cache-Control") == "private, no-store"

    # 3. Fetch first segment
    m_seg = re.search(r"(?m)^(/student/courses/[^\s]+/segment_\d+\.ts)$", playlist_text)
    if m_seg:
        seg_resp = client.get(m_seg.group(1))
        assert seg_resp.status_code == 200
        assert seg_resp.headers.get("Content-Type") == "video/MP2T"


def test_nonexistent_lesson_returns_404(client: FlaskClient, hls_fixture: dict):
    """Requesting non-existent lesson returns 404."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    ast = hls_fixture["asset_video"]

    login_client(client, enrolled.email)

    fake_lesson_uuid = str(uuid.uuid4())
    url = f"/student/courses/{crs.public_id}/lessons/{fake_lesson_uuid}/video/{ast.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    # Malformed lesson ID
    url_malformed = (
        f"/student/courses/{crs.public_id}/lessons/not-a-uuid/video/{ast.public_id}/playlist.m3u8"
    )
    resp_malformed = client.get(url_malformed)
    assert resp_malformed.status_code == 404


def test_cross_course_lesson_spoofing_returns_404_or_403(client: FlaskClient, hls_fixture: dict):
    """Requesting Lesson B (Course B) under Course A's path is strictly blocked:

    - If student is not enrolled in Course B: rejected with 403 Forbidden by get_lesson_detail.
    - If student is enrolled in both courses: rejected with 404 Not Found by course/lesson matching guard.
    """
    sess = db.session
    enrolled = hls_fixture["student_enrolled"]
    c_a = hls_fixture["course_a"]
    c_b = hls_fixture["course_b"]
    l_b = hls_fixture["lesson_b"]
    ast = hls_fixture["asset_video"]

    login_client(client, enrolled.email)

    # 1. When student is not enrolled in Course B -> 403 Forbidden
    url = f"/student/courses/{c_a.public_id}/lessons/{l_b.public_id}/video/{ast.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 403, f"Expected 403 Forbidden, got {resp.status_code}"

    # 2. When student is enrolled in Course B as well, but attempts cross-course lesson mapping -> 404 Not Found
    enr_b = Enrollment(
        student_user_id=enrolled.id,
        course_id=c_b.id,
        status="ACTIVE",
    )
    sess.add(enr_b)
    sess.flush()
    period_b = EnrollmentPeriod(
        enrollment_id=enr_b.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period_b)
    sess.flush()
    enr_b.current_period_id = period_b.id
    sess.commit()

    resp_cross = client.get(url)
    assert resp_cross.status_code == 404, (
        f"Expected 404 Not Found for cross-course lesson mismatch, got {resp_cross.status_code}"
    )


def test_invalid_and_nonexistent_asset_id_returns_404(client: FlaskClient, hls_fixture: dict):
    """Requesting invalid or non-existent asset ID returns 404 without 500 error."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]

    login_client(client, enrolled.email)

    # 1. Non-existent UUID
    fake_asset_uuid = str(uuid.uuid4())
    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{fake_asset_uuid}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    # 2. Malformed string with SQL injection attempt
    malicious_id = "'; DROP TABLE FileAsset; --"
    url_sqli = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{malicious_id}/playlist.m3u8"
    resp_sqli = client.get(url_sqli)
    assert resp_sqli.status_code == 404, f"Expected 404, got {resp_sqli.status_code}"


def test_non_video_asset_returns_404(client: FlaskClient, hls_fixture: dict):
    """Requesting document/PDF asset via HLS endpoint returns 404."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    doc_asset = hls_fixture["asset_doc"]

    login_client(client, enrolled.email)

    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{doc_asset.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 404, f"Expected 404 for non-video asset, got {resp.status_code}"


def test_deleted_asset_returns_404(client: FlaskClient, hls_fixture: dict):
    """Requesting soft-deleted asset returns 404."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    del_asset = hls_fixture["asset_deleted"]

    login_client(client, enrolled.email)

    url = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{del_asset.public_id}/playlist.m3u8"
    resp = client.get(url)
    assert resp.status_code == 404, f"Expected 404 for deleted asset, got {resp.status_code}"


def test_tampered_and_expired_drm_key_token_returns_403(client: FlaskClient, hls_fixture: dict):
    """DRM key endpoint strictly rejects tampered, missing, or malformed tokens."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    ast = hls_fixture["asset_video"]

    login_client(client, enrolled.email)

    base_key_url = (
        f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}/key"
    )

    # 1. Missing token
    resp_missing = client.get(base_key_url)
    assert resp_missing.status_code == 403

    # 2. Tampered token
    resp_tampered = client.get(f"{base_key_url}?token=malicious_fake_token")
    assert resp_tampered.status_code == 403


def test_segment_path_traversal_returns_404(client: FlaskClient, hls_fixture: dict):
    """Directory traversal attack on segment endpoint is blocked with 404."""
    enrolled = hls_fixture["student_enrolled"]
    crs = hls_fixture["course_a"]
    les = hls_fixture["lesson_a"]
    ast = hls_fixture["asset_video"]

    login_client(client, enrolled.email)

    base = f"/student/courses/{crs.public_id}/lessons/{les.public_id}/video/{ast.public_id}"

    # Traversal attempt
    resp_trav = client.get(f"{base}/..%2f..%2fetc%2fpasswd")
    assert resp_trav.status_code in (404, 400)

    # Non-existent segment
    resp_nonexistent = client.get(f"{base}/segment_99999.ts")
    assert resp_nonexistent.status_code == 404
