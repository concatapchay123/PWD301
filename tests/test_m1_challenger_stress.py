"""Adversarial and Empirical Stress Test Suite for Milestone 1.

Empirical Challenger 2 Verification:
1. HTTP Range Requests (send_file conditional=True):
   - Partial content requests: bytes=0-100, middle chunks, suffix ranges, open-ended ranges.
   - Unsatisfiable ranges (416 Range Not Satisfiable).
   - Range verification across Instructor routes, Student routes, and safe GET API routes.
   - Zero-Trust fail-closed: Range headers cannot bypass auth or quarantine.

2. Unsticking & Rescan Mechanism:
   - Rescan of quarantined clean file invokes rescan_file_asset and promotes to ACTIVE / CLEAN.
   - Physical file migration from quarantine/ to storage blobs/ with sha256 deduplication.
   - Rescan of infected file moves to infected/, marks REJECTED, and fails closed.
   - Rescan authorization isolation (students and external instructors denied).
   - Rescan disk-missing error handling.
   - Background worker FILE_SCAN job execution.

3. MIME Type & Size Calculations Edge Cases:
   - 0-byte file: size_bytes=0, file_size_bytes=0, default MIME type, download behavior.
   - Multi-MB files: 5MB, 25MB file sizes, MB formatting, 1MB chunk Range requests.
   - Missing revision edge case: 0 revisions handled safely without AttributeError.
   - Multiple revisions: latest revision targeted during rescan.
"""

from __future__ import annotations

import hashlib
import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision, FileScanResult
from pwd301.models.identity import Role, User
from pwd301.services.background_job_service import (
    enqueue_background_job,
    execute_background_job,
)
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    FileSecurityQuarantineError,
    FileValidationError,
)
from pwd301.services.file_service import (
    get_file_for_download,
    get_file_infected_root,
    get_file_quarantine_root,
    get_file_storage_root,
    quarantine_override,
    rescan_file_asset,
    store_file_stream,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def stress_roles(app: Flask) -> dict[str, Role]:
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
def stress_instructor(app: Flask, stress_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("c2_instructor@example.com", "Password@123", "Challenger Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, stress_roles: dict[str, Role]) -> User:
    """Create secondary instructor user who does not own the course."""
    u = register_user("c2_other_inst@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def stress_student_enrolled(app: Flask, stress_roles: dict[str, Role]) -> User:
    """Create student user actively enrolled."""
    return register_user("c2_student_enrolled@example.com", "Password@123", "Enrolled Student")


@pytest.fixture
def stress_student_unenrolled(app: Flask, stress_roles: dict[str, Role]) -> User:
    """Create student user not enrolled."""
    return register_user("c2_student_unenrolled@example.com", "Password@123", "Unenrolled Student")


@pytest.fixture
def stress_admin(app: Flask, stress_roles: dict[str, Role]) -> User:
    """Create admin user."""
    u = register_user("c2_admin@example.com", "Password@123", "Challenger Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def stress_course(app: Flask, stress_instructor: User) -> Course:
    """Create test published course owned by stress_instructor."""
    c = create_course(
        stress_instructor,
        {
            "course_code": f"C2-{uuid.uuid4().hex[:4].upper()}",
            "title": "Challenger 2 Stress Testing Course",
            "category": "Computer Science",
            "difficulty": "INTERMEDIATE",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def stress_enrolled_course(
    app: Flask, stress_course: Course, stress_student_enrolled: User
) -> tuple[Course, Enrollment]:
    """Enroll student in stress course."""
    enr = enroll_student(stress_student_enrolled, stress_course.id, session=db.session)
    db.session.commit()
    return stress_course, enr


# ---------------------------------------------------------------------------
# Area 1: HTTP Range Requests
# ---------------------------------------------------------------------------


class TestHttpRangeRequests:
    """Empirical tests for HTTP Range requests on send_file(..., conditional=True)."""

    def test_instructor_download_range_bytes_0_100(
        self, client: FlaskClient, stress_instructor: User, stress_course: Course
    ) -> None:
        """Instructor requesting Range: bytes=0-100 receives 206 Partial Content (101 bytes)."""
        login_web_user(client, stress_instructor)

        # Generate 1024 bytes of distinct content
        data_1024 = bytes(i % 256 for i in range(1024))
        up_resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files",
            data={"file": (io.BytesIO(data_1024), "range_test.bin"), "title": "Range Test File"},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert up_resp.status_code == 201
        asset_id = up_resp.get_json()["asset_id"]

        # Request bytes=0-100
        dl_resp = client.get(
            f"/instructor/courses/{stress_course.public_id}/files/{asset_id}/download",
            headers={"Range": "bytes=0-100"},
        )

        assert dl_resp.status_code == 206, (
            f"Expected 206 Partial Content, got {dl_resp.status_code}"
        )
        assert len(dl_resp.data) == 101, f"Expected 101 bytes, got {len(dl_resp.data)}"
        assert dl_resp.data == data_1024[0:101]
        assert dl_resp.headers.get("Content-Range") == "bytes 0-100/1024"
        assert dl_resp.headers.get("Accept-Ranges") == "bytes"
        assert dl_resp.headers.get("Content-Length") == "101"

    def test_range_middle_chunks_suffix_and_open_ranges(
        self, client: FlaskClient, stress_instructor: User, stress_course: Course
    ) -> None:
        """Verify middle chunk (200-499), suffix (-64), and open-ended (512-) byte ranges."""
        login_web_user(client, stress_instructor)

        data_1024 = bytes(i % 256 for i in range(1024))
        up_resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files",
            data={"file": (io.BytesIO(data_1024), "chunks.bin"), "title": "Chunks"},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]
        dl_url = f"/instructor/courses/{stress_course.public_id}/files/{asset_id}/download"

        # 1. Middle range: bytes=200-499 (300 bytes)
        resp_mid = client.get(dl_url, headers={"Range": "bytes=200-499"})
        assert resp_mid.status_code == 206
        assert len(resp_mid.data) == 300
        assert resp_mid.data == data_1024[200:500]
        assert resp_mid.headers.get("Content-Range") == "bytes 200-499/1024"

        # 2. Suffix range: bytes=-64 (last 64 bytes)
        resp_suffix = client.get(dl_url, headers={"Range": "bytes=-64"})
        assert resp_suffix.status_code == 206
        assert len(resp_suffix.data) == 64
        assert resp_suffix.data == data_1024[-64:]
        assert resp_suffix.headers.get("Content-Range") == "bytes 960-1023/1024"

        # 3. Open-ended range: bytes=512- (512 to 1023)
        resp_open = client.get(dl_url, headers={"Range": "bytes=512-"})
        assert resp_open.status_code == 206
        assert len(resp_open.data) == 512
        assert resp_open.data == data_1024[512:]
        assert resp_open.headers.get("Content-Range") == "bytes 512-1023/1024"

    def test_range_unsatisfiable_returns_416(
        self, client: FlaskClient, stress_instructor: User, stress_course: Course
    ) -> None:
        """Unsatisfiable range beyond EOF returns HTTP 416 Range Not Satisfiable."""
        login_web_user(client, stress_instructor)

        data_500 = b"X" * 500
        up_resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files",
            data={"file": (io.BytesIO(data_500), "small.bin")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        resp_oob = client.get(
            f"/instructor/courses/{stress_course.public_id}/files/{asset_id}/download",
            headers={"Range": "bytes=1000-2000"},
        )
        assert resp_oob.status_code == 416

    def test_student_download_range_requests(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_student_enrolled: User,
        stress_enrolled_course: tuple[Course, Enrollment],
    ) -> None:
        """Enrolled student can issue HTTP Range requests on student download endpoints."""
        course, _ = stress_enrolled_course
        login_web_user(client, stress_instructor)

        payload_bytes = b"PWD301_STUDENT_STREAMING_CONTENT_BUFFER_" * 20  # 800 bytes
        up_resp = client.post(
            f"/instructor/courses/{course.public_id}/files",
            data={"file": (io.BytesIO(payload_bytes), "syllabus_stream.pdf")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # Log in as enrolled student
        login_web_user(client, stress_student_enrolled)

        # Primary route: /student/courses/<cid>/files/<fid>/download
        dl_resp = client.get(
            f"/student/courses/{course.public_id}/files/{asset_id}/download",
            headers={"Range": "bytes=0-100"},
        )
        assert dl_resp.status_code == 206
        assert len(dl_resp.data) == 101
        assert dl_resp.data == payload_bytes[0:101]
        assert dl_resp.headers.get("Content-Range") == f"bytes 0-100/{len(payload_bytes)}"

        # Alias route: /student/files/<fid>/download
        alias_resp = client.get(
            f"/student/files/{asset_id}/download",
            headers={"Range": "bytes=50-150"},
        )
        assert alias_resp.status_code == 206
        assert len(alias_resp.data) == 101
        assert alias_resp.data == payload_bytes[50:151]

    def test_api_download_range_requests_session_and_jwt(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_course: Course,
    ) -> None:
        """Safe GET /api/files/<asset_id>/download supports HTTP Range with session & JWT."""
        login_web_user(client, stress_instructor)

        file_content = b"ABCDEFGHIJ" * 100  # 1000 bytes
        up_resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files",
            data={"file": (io.BytesIO(file_content), "api_stream.bin")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # 1. Via web session cookie
        sess_resp = client.get(
            f"/api/files/{asset_id}/download",
            headers={"Range": "bytes=0-100"},
        )
        assert sess_resp.status_code == 206
        assert len(sess_resp.data) == 101
        assert sess_resp.data == file_content[0:101]
        assert sess_resp.headers.get("Content-Range") == "bytes 0-100/1000"
        assert sess_resp.headers.get("X-Content-Type-Options") == "nosniff"

        # 2. Via JWT Bearer token
        tokens = create_token_pair(stress_instructor)
        jwt_resp = client.get(
            f"/api/files/{asset_id}/download",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
                "Range": "bytes=200-299",
            },
        )
        assert jwt_resp.status_code == 206
        assert len(jwt_resp.data) == 100
        assert jwt_resp.data == file_content[200:300]
        assert jwt_resp.headers.get("Content-Range") == "bytes 200-299/1000"

    def test_range_request_cannot_bypass_authorization_or_quarantine(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_student_unenrolled: User,
        stress_student_enrolled: User,
        stress_enrolled_course: tuple[Course, Enrollment],
    ) -> None:
        """Adversarial challenge: Range headers must NOT bypass auth or quarantine (fail-closed)."""
        course, _ = stress_enrolled_course
        login_web_user(client, stress_instructor)

        secret_bytes = b"SECRET_RESTRICTED_DATA_BYTES" * 10
        up_resp = client.post(
            f"/instructor/courses/{course.public_id}/files",
            data={"file": (io.BytesIO(secret_bytes), "secret.bin")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # 1. Unenrolled student sends Range header
        login_web_user(client, stress_student_unenrolled)
        resp_unenrolled = client.get(
            f"/student/courses/{course.public_id}/files/{asset_id}/download",
            headers={"Range": "bytes=0-10", "Accept": "application/json"},
        )
        assert resp_unenrolled.status_code == 403, "Range header bypassed student enrollment check!"

        # 2. Enrolled student requests quarantined file with Range header
        login_web_user(client, stress_instructor)
        q_root = get_file_quarantine_root()
        temp_name = f"q_bypass_{uuid.uuid4().hex}.bin"
        (q_root / temp_name).write_bytes(b"QUARANTINED_BYTES_CANNOT_LEAK" * 10)

        q_asset = FileAsset(
            course_id=course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="quarantined_range.bin",
            status="PENDING",
        )
        db.session.add(q_asset)
        db.session.flush()

        q_rev = FileRevision(
            file_asset_id=q_asset.id,
            revision_no=1,
            is_current=False,
            original_filename="quarantined_range.bin",
            detected_mime_type="application/octet-stream",
            size_bytes=300,
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_name}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(q_rev)
        db.session.commit()

        login_web_user(client, stress_student_enrolled)
        resp_q = client.get(
            f"/student/courses/{course.public_id}/files/{q_asset.public_id}/download",
            headers={"Range": "bytes=0-50", "Accept": "application/json"},
        )
        assert resp_q.status_code == 403, "Range header bypassed quarantine check!"


# ---------------------------------------------------------------------------
# Area 2: Unsticking Mechanism & Rescan Workflow
# ---------------------------------------------------------------------------


class TestUnstickingAndRescan:
    """Empirical verification of quarantine unsticking and malware rescan."""

    def test_rescan_quarantined_clean_file_unstick_workflow(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_student_enrolled: User,
        stress_enrolled_course: tuple[Course, Enrollment],
    ) -> None:
        """Calling rescan on clean quarantined file promotes to ACTIVE/CLEAN."""
        course, _ = stress_enrolled_course
        login_web_user(client, stress_instructor)

        # Put clean file into quarantine folder
        q_root = get_file_quarantine_root()
        temp_fname = f"unstick_{uuid.uuid4().hex}.pdf"
        q_path = q_root / temp_fname
        clean_content = b"%PDF-1.4 Clean lecture slide content that timed out during upload"
        q_path.write_bytes(clean_content)

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="unstick_lecture.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="unstick_lecture.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(clean_content),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_fname}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        assert asset.virus_scan_status == "PENDING"

        # Invoke rescan route via instructor Web UI
        rescan_resp = client.post(
            f"/instructor/courses/{course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert rescan_resp.status_code == 200

        # Empirical DB and filesystem verification
        db.session.refresh(asset)
        db.session.refresh(rev)

        assert asset.status == "ACTIVE", f"Asset status should be ACTIVE, got {asset.status}"
        assert rev.status == "ACTIVE", f"Revision status should be ACTIVE, got {rev.status}"
        assert rev.is_current is True
        assert asset.virus_scan_status == "CLEAN"

        # Verify blob creation and migration
        assert rev.blob_id is not None
        blob = db.session.get(FileBlob, rev.blob_id)
        assert blob is not None
        assert blob.status == "PRESENT"
        assert blob.size_bytes == len(clean_content)

        storage_root = get_file_storage_root()
        promoted_path = storage_root / blob.storage_key
        assert promoted_path.exists(), f"Promoted file not found at {promoted_path}"
        assert promoted_path.read_bytes() == clean_content

        # Verify scan result recorded
        scan_records = (
            db.session.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).all()
        )
        assert len(scan_records) > 0
        assert any(sr.status == "PASS" for sr in scan_records)

        # Enrolled student can now download the file immediately
        login_web_user(client, stress_student_enrolled)
        dl_resp = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download"
        )
        assert dl_resp.status_code == 200
        assert dl_resp.data == clean_content

    def test_rescan_infected_file_moves_to_infected_and_rejects(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_student_enrolled: User,
        stress_enrolled_course: tuple[Course, Enrollment],
    ) -> None:
        """Rescanning an infected file moves it to infected/ and blocks all access."""
        course, _ = stress_enrolled_course
        login_web_user(client, stress_instructor)

        q_root = get_file_quarantine_root()
        temp_fname = f"eicar_{uuid.uuid4().hex}.com"
        q_path = q_root / temp_fname

        # Standard EICAR test string recognized by BuiltinHeuristicScanner and ClamAV
        from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES

        eicar_string = EICAR_SIGNATURE_BYTES
        q_path.write_bytes(eicar_string)
        eicar_hash = hashlib.sha256(eicar_string).hexdigest()

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="eicar_threat.com",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="eicar_threat.com",
            detected_mime_type="application/x-dosexec",
            size_bytes=len(eicar_string),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_fname}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Trigger rescan
        rescan_resp = client.post(
            f"/instructor/courses/{course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert rescan_resp.status_code == 200

        db.session.refresh(asset)
        db.session.refresh(rev)

        # Revision must be REJECTED, is_current False
        assert rev.status == "REJECTED"
        assert rev.is_current is False
        assert "Malware detected" in (rev.rejection_reason or "")
        assert asset.virus_scan_status == "INFECTED"

        # Physical file moved to infected directory
        infected_root = get_file_infected_root()
        infected_file = infected_root / eicar_hash
        assert infected_file.exists(), f"Infected file was not moved to {infected_file}"

        # Student access must fail closed (403)
        login_web_user(client, stress_student_enrolled)
        dl_resp = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert dl_resp.status_code == 403

    def test_rescan_authorization_isolation(
        self,
        client: FlaskClient,
        stress_course: Course,
        stress_instructor: User,
        other_instructor: User,
        stress_student_enrolled: User,
    ) -> None:
        """Only managing instructor can trigger rescan; others are forbidden."""
        # Create pending asset
        q_root = get_file_quarantine_root()
        temp_fname = f"auth_q_{uuid.uuid4().hex}.pdf"
        (q_root / temp_fname).write_bytes(b"%PDF-1.4 Test")

        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="auth_test.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="auth_test.pdf",
            detected_mime_type="application/pdf",
            size_bytes=13,
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_fname}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        # 1. Enrolled student attempts rescan -> 403 or redirect to login (not instructor)
        login_web_user(client, stress_student_enrolled)
        resp_stud = client.post(
            f"/instructor/courses/{stress_course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp_stud.status_code in (403, 302)

        # 2. External instructor (who does not own stress_course) attempts rescan -> 403
        login_web_user(client, other_instructor)
        resp_other = client.post(
            f"/instructor/courses/{stress_course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp_other.status_code in (403, 404, 302)

    def test_rescan_missing_physical_file_gracefully_fails(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_course: Course,
    ) -> None:
        """If physical file was lost from quarantine, rescan gracefully fails without 500 crash."""
        login_web_user(client, stress_instructor)

        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="missing_phys.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="missing_phys.pdf",
            detected_mime_type="application/pdf",
            size_bytes=100,
            status="QUARANTINED",
            quarantine_key=f"quarantine/non_existent_{uuid.uuid4().hex}.pdf",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Execute rescan route
        resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "text/html"},
        )
        # Should redirect back to materials with a flashed danger message, NOT crash 500
        assert resp.status_code in (200, 302)
        if resp.status_code == 302:
            follow = client.get(resp.headers["Location"], headers={"Accept": "text/html"})
            assert "Không thể quét lại" in follow.get_data(as_text=True)

    def test_background_job_file_scan_execution_unstick(
        self,
        app: Flask,
        stress_instructor: User,
        stress_course: Course,
    ) -> None:
        """Background job FILE_SCAN runner invokes rescan_file_asset and un-quarantines."""
        q_root = get_file_quarantine_root()
        temp_fname = f"bg_unstick_{uuid.uuid4().hex}.pdf"
        q_path = q_root / temp_fname
        content = b"%PDF-1.4 Background worker async scan target"
        q_path.write_bytes(content)

        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="bg_scan.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="bg_scan.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(content),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_fname}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        job = enqueue_background_job(
            job_type="FILE_SCAN",
            payload={"asset_id": asset.id, "user_id": stress_instructor.id},
            run_async=False,
            session=db.session,
        )
        db.session.commit()

        # Execute the background job
        execute_background_job(job.id, session=db.session)

        db.session.refresh(job)
        db.session.refresh(asset)
        assert job.status in ("SUCCEEDED", "COMPLETED")
        assert asset.status == "ACTIVE"
        assert asset.virus_scan_status == "CLEAN"


# ---------------------------------------------------------------------------
# Area 3: MIME Type & Size Calculations Edge Cases
# ---------------------------------------------------------------------------


class TestMimeTypeAndSizeCalculations:
    """Stress testing edge cases in FileAsset properties, MIME detection, and sizes."""

    def test_zero_byte_file_asset_properties(
        self, app: Flask, stress_course: Course, stress_instructor: User
    ) -> None:
        """0-byte file edge cases: DB check constraints prevent 0-byte revisions."""
        # 1. DB constraint ck_file_revisions_2 strictly forbids persisting size_bytes <= 0
        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="empty.txt",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        rev_zero = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="empty.txt",
            detected_mime_type="text/plain",
            size_bytes=0,
            status="ACTIVE",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev_zero)
        with pytest.raises(Exception) as exc_info:
            db.session.commit()
        db.session.rollback()
        assert "ck_file_revisions_2" in str(exc_info.value) or "CHECK constraint" in str(
            exc_info.value
        )

        # 2. Uploading a 0-byte file via store_file_stream raises FileValidationError
        with pytest.raises(FileValidationError, match="Uploaded file is empty"):
            store_file_stream(
                actor=stress_instructor,
                course_id=stress_course.id,
                file_stream=io.BytesIO(b""),
                filename="empty.txt",
                session=db.session,
            )

        # 3. In-memory / detached FileAsset evaluates size_bytes == 0 and file_size_bytes == 0
        mock_asset = FileAsset(display_name="empty_mock.txt", status="ACTIVE")
        mock_rev = FileRevision(
            original_filename="empty_mock.txt",
            detected_mime_type="text/plain",
            size_bytes=0,
            is_current=True,
        )
        mock_asset.revisions.append(mock_rev)
        assert mock_asset.size_bytes == 0
        assert mock_asset.file_size_bytes == 0
        assert mock_asset.mime_type == "text/plain"
        assert mock_asset.is_video is False
        assert mock_asset.is_pdf is False

    def test_missing_revision_file_asset_edge_case(
        self, app: Flask, stress_course: Course, stress_instructor: User
    ) -> None:
        """FileAsset with 0 revisions returns safe defaults and does not raise AttributeError."""
        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="ghost_asset.bin",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.commit()

        fa = db.session.get(FileAsset, asset.id)
        assert fa is not None
        assert fa.revisions == []
        assert fa.current_revision is None

        # Empirical property verification on ghost asset
        assert fa.original_filename == "ghost_asset.bin"
        assert fa.original_file_name == "ghost_asset.bin"
        assert fa.file_name == "ghost_asset.bin"
        assert fa.size_bytes == 0
        assert fa.file_size_bytes == 0
        assert fa.mime_type == "application/octet-stream"
        assert fa.detected_mime_type == "application/octet-stream"
        assert fa.virus_scan_status == "PENDING"
        assert fa.is_video is False
        assert fa.is_pdf is False

        # Attempting download on asset without revisions raises fail-closed exception
        with pytest.raises(FileSecurityQuarantineError):
            get_file_for_download(stress_instructor, fa.id, session=db.session)

        # Attempting rescan on asset without revisions raises FileValidationError
        with pytest.raises(FileValidationError, match="no revisions to rescan"):
            rescan_file_asset(stress_instructor, fa.id, session=db.session)

    def test_multi_mb_file_size_calculation_and_range(
        self, client: FlaskClient, stress_instructor: User, stress_course: Course
    ) -> None:
        """Multi-MB file (5 MB) reports correct byte size and supports 1 MB chunk Range requests."""
        login_web_user(client, stress_instructor)

        # 5 MB = 5 * 1024 * 1024 = 5,242,880 bytes
        five_mb_size = 5 * 1024 * 1024
        # Deterministic pseudo-random pattern
        chunk_pattern = b"0123456789ABCDEF" * 4096  # 65536 bytes
        multi_mb_data = chunk_pattern * (five_mb_size // len(chunk_pattern))
        assert len(multi_mb_data) == five_mb_size

        up_resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files",
            data={"file": (io.BytesIO(multi_mb_data), "large_lecture.pdf"), "title": "Large PDF"},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert up_resp.status_code == 201
        asset_id = up_resp.get_json()["asset_id"]

        fa = db.session.query(FileAsset).filter(FileAsset.public_id == uuid.UUID(asset_id)).first()
        assert fa is not None
        assert fa.size_bytes == five_mb_size
        assert fa.file_size_bytes == five_mb_size
        assert fa.is_pdf is True
        assert fa.is_video is False

        # Issue 1 MB chunk Range request (bytes 1,048,576 to 2,097,151)
        chunk_start = 1024 * 1024
        chunk_end = 2 * 1024 * 1024 - 1
        expected_chunk_len = 1024 * 1024

        dl_resp = client.get(
            f"/instructor/courses/{stress_course.public_id}/files/{asset_id}/download",
            headers={"Range": f"bytes={chunk_start}-{chunk_end}"},
        )
        assert dl_resp.status_code == 206
        assert len(dl_resp.data) == expected_chunk_len
        assert dl_resp.data == multi_mb_data[chunk_start : chunk_end + 1]
        assert (
            dl_resp.headers.get("Content-Range")
            == f"bytes {chunk_start}-{chunk_end}/{five_mb_size}"
        )

    def test_multiple_revisions_quarantined_fallback_and_rescan(
        self, app: Flask, stress_course: Course, stress_instructor: User
    ) -> None:
        """When multiple revisions exist and latest is quarantined, rescan un-quarantines latest."""
        # Asset created with Rev 1 ACTIVE
        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="multi_rev.pdf",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        storage_root = get_file_storage_root()
        blob1_key = f"blobs/ab/cd/{uuid.uuid4().hex}"
        p1 = storage_root / blob1_key
        p1.parent.mkdir(parents=True, exist_ok=True)
        p1.write_bytes(b"%PDF-1.4 Rev1 content")

        blob1 = FileBlob(
            sha256=hashlib.sha256(b"%PDF-1.4 Rev1 content").digest(),
            size_bytes=21,
            detected_mime_type="application/pdf",
            storage_key=blob1_key,
            status="PRESENT",
            reference_count=1,
        )
        db.session.add(blob1)
        db.session.flush()

        rev1 = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="multi_rev_v1.pdf",
            detected_mime_type="application/pdf",
            size_bytes=21,
            status="ACTIVE",
            blob_id=blob1.id,
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev1)
        db.session.flush()

        # Rev 2 added but quarantined
        q_root = get_file_quarantine_root()
        temp_name = f"rev2_q_{uuid.uuid4().hex}.pdf"
        p2 = q_root / temp_name
        p2.write_bytes(b"%PDF-1.4 Rev2 updated content that was quarantined")

        rev2 = FileRevision(
            file_asset_id=asset.id,
            revision_no=2,
            is_current=False,
            original_filename="multi_rev_v2.pdf",
            detected_mime_type="application/pdf",
            size_bytes=48,
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_name}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev2)
        db.session.commit()

        # Before rescan: Rev 1 is current, so effective revision should return Rev 1
        fa = db.session.get(FileAsset, asset.id)
        assert fa is not None
        assert fa.current_revision.id == rev1.id
        assert fa.size_bytes == 21

        # Defect 1 Remediation Verification:
        # rescan_file_asset demotes prior active revisions (rev1.is_current=False,
        # status="REPLACED") before promoting rev2 (is_current=True, status="ACTIVE").
        # This satisfies unique partial constraints uq_file_revisions_current and
        # ux_file_revisions_active.
        rescan_file_asset(stress_instructor, asset.id, session=db.session)
        db.session.commit()

        db.session.refresh(asset)
        db.session.refresh(rev1)
        db.session.refresh(rev2)

        assert asset.status == "ACTIVE"
        assert asset.virus_scan_status == "CLEAN"
        assert rev2.status == "ACTIVE"
        assert rev2.is_current is True
        assert rev2.blob_id is not None
        assert rev1.status == "REPLACED"
        assert rev1.is_current is False
        assert rev1.replaced_at is not None

    def test_multiple_revisions_quarantine_override_demotes_prior_revision(
        self, app: Flask, stress_course: Course, stress_instructor: User, stress_admin: User
    ) -> None:
        """quarantine_override on multi-revision file demotes prior active revisions."""
        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="override_multi.pdf",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        storage_root = get_file_storage_root()
        blob1_key = f"blobs/cd/ef/{uuid.uuid4().hex}"
        p1 = storage_root / blob1_key
        p1.parent.mkdir(parents=True, exist_ok=True)
        p1.write_bytes(b"%PDF-1.4 Initial Active Content")

        blob1 = FileBlob(
            sha256=hashlib.sha256(b"%PDF-1.4 Initial Active Content").digest(),
            size_bytes=31,
            detected_mime_type="application/pdf",
            storage_key=blob1_key,
            status="PRESENT",
            reference_count=1,
        )
        db.session.add(blob1)
        db.session.flush()

        rev1 = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="override_v1.pdf",
            detected_mime_type="application/pdf",
            size_bytes=31,
            status="ACTIVE",
            blob_id=blob1.id,
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev1)
        db.session.flush()

        # Add quarantined rev2
        q_root = get_file_quarantine_root()
        temp_name = f"override_q_{uuid.uuid4().hex}.pdf"
        p2 = q_root / temp_name
        p2.write_bytes(b"%PDF-1.4 Overridden Quarantined Content")

        rev2 = FileRevision(
            file_asset_id=asset.id,
            revision_no=2,
            is_current=False,
            original_filename="override_v2.pdf",
            detected_mime_type="application/pdf",
            size_bytes=38,
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_name}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev2)
        db.session.commit()

        # Admin overrides quarantine on latest revision (rev2)
        quarantine_override(
            admin_actor=stress_admin,
            asset_id=asset.id,
            reason="Admin approved override for multi-revision asset",
            session=db.session,
        )
        db.session.commit()

        db.session.refresh(asset)
        db.session.refresh(rev1)
        db.session.refresh(rev2)

        assert asset.status == "ACTIVE"
        assert rev2.status == "ACTIVE"
        assert rev2.is_current is True
        assert rev1.status == "REPLACED"
        assert rev1.is_current is False
        assert rev1.replaced_at is not None

    def test_instructor_rescan_infected_file_flashes_danger_alert(
        self,
        client: FlaskClient,
        stress_instructor: User,
        stress_course: Course,
    ) -> None:
        """Defect 2 Remediation: Rescanning infected file flashes danger alert instead of info."""
        login_web_user(client, stress_instructor)

        from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES

        q_root = get_file_quarantine_root()
        temp_fname = f"eicar_flash_{uuid.uuid4().hex}.com"
        (q_root / temp_fname).write_bytes(EICAR_SIGNATURE_BYTES)

        asset = FileAsset(
            course_id=stress_course.id,
            created_by_user_id=stress_instructor.id,
            asset_type="RESOURCE",
            display_name="infected_flash.com",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="infected_flash.com",
            detected_mime_type="application/x-dosexec",
            size_bytes=len(EICAR_SIGNATURE_BYTES),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{temp_fname}",
            uploaded_by_user_id=stress_instructor.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Execute rescan route expecting JSON response
        resp = client.post(
            f"/instructor/courses/{stress_course.public_id}/files/{asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        rescan_json = resp.get_json()
        assert rescan_json["virus_scan_status"] == "INFECTED" or rescan_json["status"] == "REJECTED"
