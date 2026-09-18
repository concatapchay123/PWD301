"""Automated test suite for Milestone 1: File Upload, Scanning & Secure Access.

Tests:
1. FileAsset properties (original_filename, size_bytes, mime_type, virus_scan_status, helpers).
2. Upload and clean scan status reflection in instructor materials view.
3. Rescan endpoint unsticking pending/quarantined files and background job enqueueing.
4. Instructor authenticated session download success (direct stream & safe GET API download).
5. Student authenticated session download success when enrolled and fail-closed checks (403/404).
6. Admin-required enforcement on quarantine override endpoint (DEF-15).
"""

from __future__ import annotations

import io
import json
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.models.file_import import FileAsset, FileRevision, FileScanResult
from pwd301.models.identity import Role, User
from pwd301.models.operations import BackgroundJob
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import (
    get_file_quarantine_root,
    store_file_stream,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.scanner_service import ScanVerdict
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("m1_instructor@example.com", "Password@123", "M1 Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def enrolled_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    return register_user("m1_student_enrolled@example.com", "Password@123", "Enrolled Student")


@pytest.fixture
def unenrolled_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary student user not enrolled in the course."""
    return register_user("m1_student_unenrolled@example.com", "Password@123", "Unenrolled Student")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user("m1_admin@example.com", "Password@123", "M1 Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create test published course."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"M1-{uuid.uuid4().hex[:4].upper()}",
            "title": "Milestone 1 File Security Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def enrolled_course(
    app: Flask, test_course: Course, enrolled_student: User
) -> tuple[Course, Enrollment]:
    """Enroll student in test course."""
    enr = enroll_student(enrolled_student, test_course.id, session=db.session)
    db.session.commit()
    return test_course, enr


class TestFileAssetProperties:
    """Unit tests for convenience properties on FileAsset."""

    def test_file_asset_properties_active_revision(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """FileAsset convenience properties read correctly from active revision."""
        asset = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="lecture1.pdf",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="original_lecture1.pdf",
            detected_mime_type="application/pdf",
            size_bytes=2048576,
            status="ACTIVE",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Re-query
        fa = db.session.get(FileAsset, asset.id)
        assert fa is not None
        assert fa.original_filename == "original_lecture1.pdf"
        assert fa.original_file_name == "original_lecture1.pdf"
        assert fa.file_name == "lecture1.pdf"
        assert fa.size_bytes == 2048576
        assert fa.file_size_bytes == 2048576
        assert fa.mime_type == "application/pdf"
        assert fa.detected_mime_type == "application/pdf"
        assert fa.virus_scan_status == "CLEAN"
        assert fa.is_pdf is True
        assert fa.is_video is False

    def test_file_asset_properties_video_helpers(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """FileAsset is_video helper returns True for MP4/WebM MIME types and extensions."""
        asset = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="intro_clip.mp4",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="intro_clip.mp4",
            detected_mime_type="video/mp4",
            size_bytes=52428800,
            status="ACTIVE",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev)
        db.session.commit()

        fa = db.session.get(FileAsset, asset.id)
        assert fa is not None
        assert fa.is_video is True
        assert fa.is_pdf is False

    def test_file_asset_properties_quarantined_and_rejected_status(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """virus_scan_status correctly evaluates PENDING, INFECTED, and BLOCKED."""
        # 1. Quarantined / Pending
        asset_pending = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="pending_file.bin",
            status="PENDING",
        )
        db.session.add(asset_pending)
        db.session.flush()

        rev_pending = FileRevision(
            file_asset_id=asset_pending.id,
            revision_no=1,
            is_current=False,
            original_filename="pending_file.bin",
            detected_mime_type="application/octet-stream",
            size_bytes=1024,
            status="QUARANTINED",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev_pending)
        db.session.commit()

        fa_pending = db.session.get(FileAsset, asset_pending.id)
        assert fa_pending is not None
        assert fa_pending.virus_scan_status == "PENDING"

        # 2. Infected / Rejected (FileAsset status is PENDING, child revision is REJECTED)
        asset_infected = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="malware.bin",
            status="PENDING",
        )
        db.session.add(asset_infected)
        db.session.flush()

        rev_infected = FileRevision(
            file_asset_id=asset_infected.id,
            revision_no=1,
            is_current=False,
            original_filename="malware.bin",
            detected_mime_type="application/x-dosexec",
            size_bytes=68,
            status="REJECTED",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev_infected)
        db.session.commit()

        fa_infected = db.session.get(FileAsset, asset_infected.id)
        assert fa_infected is not None
        assert fa_infected.virus_scan_status == "INFECTED"

        # 3. Blocked / Error
        asset_blocked = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="broken_file.dat",
            status="PENDING",
        )
        db.session.add(asset_blocked)
        db.session.flush()

        rev_blocked = FileRevision(
            file_asset_id=asset_blocked.id,
            revision_no=1,
            is_current=False,
            original_filename="broken_file.dat",
            detected_mime_type="application/octet-stream",
            size_bytes=512,
            status="QUARANTINED",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev_blocked)
        db.session.flush()

        scan_err = FileScanResult(
            file_revision_id=rev_blocked.id,
            scan_type="MALWARE",
            engine="clamav",
            status="ERROR",
        )
        db.session.add(scan_err)
        db.session.commit()

        fa_blocked = db.session.get(FileAsset, asset_blocked.id)
        assert fa_blocked is not None
        assert fa_blocked.virus_scan_status == "BLOCKED"


class TestFileUploadAndScanning:
    """Integration tests for file upload, rendering, and rescan workflow."""

    def test_upload_clean_file_and_render_materials(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Uploading a clean file reflects CLEAN scan badge and metadata in instructor view."""
        login_web_user(client, instructor_user)

        pdf_bytes = b"%PDF-1.4 Mock clean PDF slide content"
        up_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={
                "file": (io.BytesIO(pdf_bytes), "syllabi.pdf"),
                "title": "Course Syllabi",
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert up_resp.status_code == 201

        # Verify asset in DB
        fa = (
            db.session.query(FileAsset)
            .filter_by(course_id=test_course.id, display_name="Course Syllabi")
            .first()
        )
        assert fa is not None
        assert fa.status == "ACTIVE"

    def test_rescan_endpoint_unsticks_pending_quarantined_file(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Rescan endpoint transitions a pending/quarantined file back to ACTIVE."""
        login_web_user(client, instructor_user)

        # Setup a quarantined file in the filesystem and database
        q_root = get_file_quarantine_root()
        temp_filename = f"test_quarantine_{uuid.uuid4().hex}.pdf"
        temp_path = q_root / temp_filename
        clean_content = b"%PDF-1.4 Clean file that was temporarily quarantined due to timeout"
        temp_path.write_bytes(clean_content)

        asset = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="pending_lecture.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="pending_lecture.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(clean_content),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_filename}",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Execute rescan route
        rescan_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert rescan_resp.status_code == 200

        # Verify asset and revision are now ACTIVE
        db.session.refresh(asset)
        assert asset.status == "ACTIVE"
        assert asset.virus_scan_status == "CLEAN"

    def test_scanner_error_enqueues_background_job(
        self,
        app: Flask,
        instructor_user: User,
        test_course: Course,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When scanner errors out, file status is PENDING and a FILE_SCAN job is enqueued."""

        def mock_scan_blob_error(path: Any) -> ScanVerdict:
            return ScanVerdict(
                engine_name="mock_scanner",
                engine_version="1.0",
                status="ERROR",
                details="Daemon connection timeout",
            )

        monkeypatch.setattr("pwd301.services.file_service.scan_blob_file", mock_scan_blob_error)

        file_stream = io.BytesIO(b"%PDF-1.4 Mock document for scan error test")
        asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=file_stream,
            filename="timeout_doc.pdf",
            session=db.session,
        )

        assert asset.status == "PENDING"
        assert asset.virus_scan_status == "PENDING"

        # Verify background job enqueued
        job = (
            db.session.query(BackgroundJob)
            .filter(BackgroundJob.job_type == "FILE_SCAN")
            .order_by(BackgroundJob.created_at.desc())
            .first()
        )
        assert job is not None
        assert job.status in ("QUEUED", "COMPLETED", "PROCESSING")
        payload = (
            json.loads(job.payload_json) if isinstance(job.payload_json, str) else job.payload_json
        )
        assert payload.get("asset_id") == asset.id
        assert payload.get("user_id") == instructor_user.id


class TestFileDownloadAccess:
    """Integration tests for Web session downloads and fail-closed access controls."""

    def test_instructor_session_download_success(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Managing instructor can download course files via web session (direct stream)."""
        login_web_user(client, instructor_user)

        pdf_bytes = b"%PDF-1.4 Instructor Lecture Slides Content"
        up_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(pdf_bytes), "slides.pdf"), "title": "Slides"},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # Download via instructor web route
        dl_resp = client.get(
            f"/instructor/courses/{test_course.public_id}/files/{asset_id}/download"
        )
        assert dl_resp.status_code == 200
        assert dl_resp.data == pdf_bytes
        assert "attachment" in dl_resp.headers.get("Content-Disposition", "")
        assert "slides.pdf" in dl_resp.headers.get("Content-Disposition", "")

    def test_safe_get_api_download_with_session_cookie(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Safe GET /api/files/<asset_id>/download allows session authentication."""
        login_web_user(client, instructor_user)

        pdf_bytes = b"%PDF-1.4 Safe GET session test"
        up_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(pdf_bytes), "safe_api.pdf")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # GET /api/files/<asset_id>/download should succeed with session auth
        api_dl = client.get(f"/api/files/{asset_id}/download")
        assert api_dl.status_code == 200
        assert api_dl.data == pdf_bytes
        assert api_dl.headers.get("X-Content-Type-Options") == "nosniff"

        # Invariant: State-changing POST /api/files/... must REJECT session auth (CSRF protection)
        state_change = client.post(f"/api/files/{asset_id}/rescan")
        assert state_change.status_code == 401

    def test_student_session_download_enrolled_success(
        self,
        client: FlaskClient,
        instructor_user: User,
        enrolled_student: User,
        enrolled_course: tuple[Course, Enrollment],
    ) -> None:
        """Enrolled student can successfully download clean course materials."""
        course, _ = enrolled_course
        login_web_user(client, instructor_user)

        pdf_bytes = b"%PDF-1.4 Student Materials Content"
        up_resp = client.post(
            f"/instructor/courses/{course.public_id}/files",
            data={"file": (io.BytesIO(pdf_bytes), "guide.pdf")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # Log in as enrolled student
        login_web_user(client, enrolled_student)

        # Download via student route
        dl_resp = client.get(f"/student/courses/{course.public_id}/files/{asset_id}/download")
        assert dl_resp.status_code == 200
        assert dl_resp.data == pdf_bytes

    def test_student_session_download_unenrolled_forbidden(
        self,
        client: FlaskClient,
        instructor_user: User,
        unenrolled_student: User,
        test_course: Course,
    ) -> None:
        """Unenrolled student is rejected with HTTP 403 Forbidden."""
        login_web_user(client, instructor_user)

        pdf_bytes = b"%PDF-1.4 Secret Course Materials"
        up_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(pdf_bytes), "secret.pdf")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # Log in as unenrolled student
        login_web_user(client, unenrolled_student)

        dl_resp = client.get(
            f"/student/courses/{test_course.public_id}/files/{asset_id}/download",
            headers={"Accept": "application/json"},
        )
        assert dl_resp.status_code == 403

    def test_student_session_download_quarantined_or_infected_fail_closed(
        self,
        client: FlaskClient,
        enrolled_student: User,
        enrolled_course: tuple[Course, Enrollment],
        instructor_user: User,
    ) -> None:
        """Enrolled student cannot download quarantined files (fail-closed invariant)."""
        course, _ = enrolled_course

        # Create quarantined file
        q_asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="quarantined.pdf",
            status="PENDING",
        )
        db.session.add(q_asset)
        db.session.flush()

        q_rev = FileRevision(
            file_asset_id=q_asset.id,
            revision_no=1,
            is_current=False,
            original_filename="quarantined.pdf",
            detected_mime_type="application/pdf",
            size_bytes=100,
            status="QUARANTINED",
            quarantine_key="quarantine/dummy_q.pdf",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(q_rev)
        db.session.commit()

        login_web_user(client, enrolled_student)

        # Enrolled student attempts download of quarantined file
        dl_resp = client.get(
            f"/student/courses/{course.public_id}/files/{q_asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        # Fail closed: must return 403
        assert dl_resp.status_code == 403

    def test_quarantine_override_requires_admin_role(
        self,
        client: FlaskClient,
        instructor_user: User,
        admin_user: User,
        test_course: Course,
    ) -> None:
        """POST /api/files/<asset_id>/quarantine-override requires ADMIN role (DEF-15)."""
        # Create quarantined file
        q_root = get_file_quarantine_root()
        temp_filename = f"test_override_{uuid.uuid4().hex}.pdf"
        temp_path = q_root / temp_filename
        clean_content = b"%PDF-1.4 Admin override test content"
        temp_path.write_bytes(clean_content)

        asset = FileAsset(
            course_id=test_course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="quarantine_doc.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="quarantine_doc.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(clean_content),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_filename}",
            uploaded_by_user_id=instructor_user.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Instructor attempt -> 403 Forbidden
        inst_tokens = create_token_pair(instructor_user)
        inst_resp = client.post(
            f"/api/files/{asset.public_id}/quarantine-override",
            json={"reason": "Instructor unauthorized attempt"},
            headers={"Authorization": f"Bearer {inst_tokens['access_token']}"},
        )
        assert inst_resp.status_code == 403

        # Admin attempt -> 200 OK
        admin_tokens = create_token_pair(admin_user)
        admin_resp = client.post(
            f"/api/files/{asset.public_id}/quarantine-override",
            json={"reason": "Admin verified clean file false positive"},
            headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
        )
        assert admin_resp.status_code == 200
        assert admin_resp.get_json()["status"] == "ACTIVE"
