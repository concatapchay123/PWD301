"""Adversarial stress-testing harness for Milestone 1 file authorization and security.

Executed by Empirical Challenger 1.
Tests targeted vectors:
1. Unauthorized student access: Student A downloading files from foreign Course B.
2. Malicious/unscanned file statuses: Student attempting to download PENDING/QUARANTINED/INFECTED.
3. Cross-instructor authorization isolation: Instructor 2 accessing Course 1 files.
4. Edge vectors: Historical infected revisions, status overrides, and IDOR route manipulations.
"""

from __future__ import annotations

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
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import (
    get_file_storage_root,
    store_file_stream,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
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
def instructor_1(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Primary course owner instructor."""
    u = register_user("adv_inst_1@example.com", "Password@123", "Instructor 1")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_2(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Rival/unassigned instructor."""
    u = register_user("adv_inst_2@example.com", "Password@123", "Instructor 2")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Student enrolled exclusively in Course 1."""
    u = register_user("adv_student_a@example.com", "Password@123", "Student A")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Student enrolled exclusively in Course 2."""
    u = register_user("adv_student_b@example.com", "Password@123", "Student B")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_unenrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Student with zero course enrollments."""
    u = register_user("adv_student_unenrolled@example.com", "Password@123", "Unenrolled Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """System administrator."""
    u = register_user("adv_admin@example.com", "Password@123", "System Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_1(app: Flask, instructor_1: User) -> Course:
    """Published course owned by Instructor 1."""
    c = create_course(
        instructor_1,
        {
            "course_code": f"C1-{uuid.uuid4().hex[:4].upper()}",
            "title": "Course 1 - Database Systems",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def course_2(app: Flask, instructor_2: User) -> Course:
    """Published course owned by Instructor 2."""
    c = create_course(
        instructor_2,
        {
            "course_code": f"C2-{uuid.uuid4().hex[:4].upper()}",
            "title": "Course 2 - Cloud Security",
            "category": "Security",
            "difficulty": "ADVANCED",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def enrolled_course_1(app: Flask, course_1: Course, student_a: User) -> tuple[Course, Enrollment]:
    """Enroll student A in course 1."""
    enr = enroll_student(student_a, course_1.id, session=db.session)
    db.session.commit()
    return course_1, enr


@pytest.fixture
def enrolled_course_2(app: Flask, course_2: Course, student_b: User) -> tuple[Course, Enrollment]:
    """Enroll student B in course 2."""
    enr = enroll_student(student_b, course_2.id, session=db.session)
    db.session.commit()
    return course_2, enr


@pytest.fixture
def clean_file_course_1(app: Flask, instructor_1: User, course_1: Course) -> FileAsset:
    """Store a clean PDF file in Course 1."""
    content = b"%PDF-1.4 Course 1 Secret Materials"
    asset = store_file_stream(
        actor=instructor_1,
        course_id=course_1.id,
        file_stream=io.BytesIO(content),
        filename="course_1_secret.pdf",
        session=db.session,
    )
    db.session.commit()
    return asset


@pytest.fixture
def clean_file_course_2(app: Flask, instructor_2: User, course_2: Course) -> FileAsset:
    """Store a clean PDF file in Course 2."""
    content = b"%PDF-1.4 Course 2 Proprietary Guide"
    asset = store_file_stream(
        actor=instructor_2,
        course_id=course_2.id,
        file_stream=io.BytesIO(content),
        filename="course_2_guide.pdf",
        session=db.session,
    )
    db.session.commit()
    return asset


class TestVector1UnauthorizedStudentAccess:
    """Adversarial testing: Can student A download files from Course B where not enrolled?"""

    def test_student_cannot_download_foreign_course_file_via_course_route(
        self,
        client: FlaskClient,
        student_a: User,
        course_2: Course,
        clean_file_course_2: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student A (enrolled in Course 1) attempts download from Course 2 via student route.

        Must fail with HTTP 403 Forbidden.
        """
        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course_2.public_id}/files/{clean_file_course_2.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] in ("FORBIDDEN", "FILE_ACCESS_DENIED")

    def test_student_cannot_download_foreign_course_file_via_unscoped_route(
        self,
        client: FlaskClient,
        student_a: User,
        clean_file_course_2: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student A attempts to bypass course URL scoping via /student/files/<asset_id>/download.

        Must fail with HTTP 403 Forbidden.
        """
        login_web_user(client, student_a)
        resp = client.get(
            f"/student/files/{clean_file_course_2.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_foreign_file_via_api_session_auth(
        self,
        client: FlaskClient,
        student_a: User,
        clean_file_course_2: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student A attempts safe GET /api/files/<asset_id>/download with session cookie.

        Must fail with HTTP 403 Forbidden.
        """
        login_web_user(client, student_a)
        resp = client.get(
            f"/api/files/{clean_file_course_2.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_foreign_file_via_api_jwt(
        self,
        client: FlaskClient,
        student_a: User,
        clean_file_course_2: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student A attempts download via API using JWT Bearer token for foreign course file.

        Must fail with HTTP 403 Forbidden.
        """
        tokens = create_token_pair(student_a)
        resp = client.get(
            f"/api/files/{clean_file_course_2.public_id}/download",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
                "Accept": "application/json",
            },
        )
        assert resp.status_code == 403

    def test_student_cross_course_idor_url_mismatch_rejected(
        self,
        client: FlaskClient,
        student_a: User,
        course_1: Course,
        clean_file_course_2: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """IDOR probe: Student A calls student course download with mismatched course/file IDs.

        Student A is enrolled in Course 1, but file belongs to Course 2.
        Must fail with HTTP 403 or 404 (defense-in-depth rejects before or at course scoping).
        """
        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course_1.public_id}/files/{clean_file_course_2.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code in (403, 404)

    def test_unenrolled_student_cannot_download_any_course_file(
        self,
        client: FlaskClient,
        student_unenrolled: User,
        course_1: Course,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Student with zero enrollments cannot download files from published courses."""
        login_web_user(client, student_unenrolled)
        resp = client.get(
            f"/student/courses/{course_1.public_id}/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_with_dropped_enrollment_cannot_download(
        self,
        client: FlaskClient,
        student_a: User,
        course_1: Course,
        clean_file_course_1: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student whose enrollment is LEFT is blocked from downloading course materials."""
        _, enr = enrolled_course_1
        enr.status = "LEFT"
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course_1.public_id}/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_from_draft_course(
        self,
        client: FlaskClient,
        instructor_1: User,
        student_a: User,
    ) -> None:
        """Student cannot download files if parent course status is DRAFT."""
        draft_c = create_course(
            instructor_1,
            {
                "course_code": f"DRF-{uuid.uuid4().hex[:4].upper()}",
                "title": "Draft Security Course",
                "category": "Security",
                "difficulty": "BEGINNER",
            },
        )
        draft_asset = store_file_stream(
            actor=instructor_1,
            course_id=draft_c.id,
            file_stream=io.BytesIO(b"Draft Material Content"),
            filename="draft_notes.pdf",
            session=db.session,
        )
        # Create enrollment in draft course
        enr = Enrollment(
            course_id=draft_c.id,
            student_user_id=student_a.id,
            status="ACTIVE",
        )
        db.session.add(enr)
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{draft_c.public_id}/files/{draft_asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403


class TestVector2MaliciousUnscannedFileStatuses:
    """Adversarial testing: Can a student download PENDING, QUARANTINED, or INFECTED files?"""

    def test_student_cannot_download_pending_file_asset(
        self,
        client: FlaskClient,
        student_a: User,
        instructor_1: User,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot download an asset with status PENDING."""
        course, _ = enrolled_course_1
        pending_asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_1.id,
            asset_type="RESOURCE",
            display_name="pending_scan.pdf",
            status="PENDING",
        )
        db.session.add(pending_asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=pending_asset.id,
            revision_no=1,
            is_current=False,
            original_filename="pending_scan.pdf",
            detected_mime_type="application/pdf",
            size_bytes=100,
            status="QUARANTINED",
            quarantine_key="quarantine/pending_scan.pdf",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add(rev)
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course.public_id}/files/{pending_asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_quarantined_file(
        self,
        client: FlaskClient,
        student_a: User,
        instructor_1: User,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot download a file marked QUARANTINED due to scanner timeout."""
        course, _ = enrolled_course_1
        q_asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_1.id,
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
            size_bytes=256,
            status="QUARANTINED",
            quarantine_key="quarantine/quarantined.pdf",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add(q_rev)
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course.public_id}/files/{q_asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_infected_file(
        self,
        client: FlaskClient,
        student_a: User,
        instructor_1: User,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot download an INFECTED / REJECTED file."""
        course, _ = enrolled_course_1
        inf_asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_1.id,
            asset_type="RESOURCE",
            display_name="eicar_malware.pdf",
            status="PENDING",
        )
        db.session.add(inf_asset)
        db.session.flush()

        inf_rev = FileRevision(
            file_asset_id=inf_asset.id,
            revision_no=1,
            is_current=False,
            original_filename="eicar_malware.pdf",
            detected_mime_type="application/octet-stream",
            size_bytes=68,
            status="REJECTED",
            rejection_reason="Infected: EICAR-Test-Signature",
            quarantine_key="infected/eicar_hash",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add(inf_rev)
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course.public_id}/files/{inf_asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_file_with_failing_scan_result(
        self,
        client: FlaskClient,
        student_a: User,
        instructor_1: User,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot download a file whose scan results indicate FAIL or ERROR."""
        course, _ = enrolled_course_1
        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_1.id,
            asset_type="RESOURCE",
            display_name="scan_fail.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="scan_fail.pdf",
            detected_mime_type="application/pdf",
            size_bytes=512,
            status="QUARANTINED",
            quarantine_key="quarantine/scan_fail.pdf",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add(rev)
        db.session.flush()

        scan_result = FileScanResult(
            file_revision_id=rev.id,
            scan_type="MALWARE",
            engine="clamav",
            status="FAIL",
            details_json='{"threat": "Trojan.Generic"}',
        )
        db.session.add(scan_result)
        db.session.commit()

        login_web_user(client, student_a)
        resp = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_student_cannot_download_historical_infected_revision(
        self,
        client: FlaskClient,
        student_a: User,
        instructor_1: User,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot download infected rev 1 via ?version=1 even if rev 2 is clean."""
        course, _ = enrolled_course_1

        # Setup real physical blob for clean rev 2
        storage_root = get_file_storage_root()
        clean_storage_key = f"blobs/clean_{uuid.uuid4().hex[:8]}.pdf"
        clean_file_path = storage_root / clean_storage_key
        clean_file_path.parent.mkdir(parents=True, exist_ok=True)
        clean_file_path.write_bytes(b"%PDF-1.4 Clean Revision 2 Content")

        clean_blob = FileBlob(
            storage_key=clean_storage_key,
            sha256=b"0" * 32,
            size_bytes=32,
            detected_mime_type="application/pdf",
            status="PRESENT",
        )
        db.session.add(clean_blob)
        db.session.flush()

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_1.id,
            asset_type="RESOURCE",
            display_name="multi_rev.pdf",
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        # Rev 1: Infected / Rejected
        rev1 = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="infected_rev1.pdf",
            detected_mime_type="application/octet-stream",
            size_bytes=68,
            status="REJECTED",
            rejection_reason="Infected: Trojan",
            quarantine_key="infected/trojan_hash",
            uploaded_by_user_id=instructor_1.id,
        )
        # Rev 2: Clean / Active
        rev2 = FileRevision(
            file_asset_id=asset.id,
            revision_no=2,
            is_current=True,
            blob_id=clean_blob.id,
            original_filename="multi_rev_clean.pdf",
            detected_mime_type="application/pdf",
            size_bytes=32,
            status="ACTIVE",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add_all([rev1, rev2])
        db.session.commit()

        login_web_user(client, student_a)

        # 1. Accessing current revision 2 succeeds
        resp_clean = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp_clean.status_code == 200

        # 2. Accessing historical revision 1 (?version=1) fails closed with 403
        resp_infected = client.get(
            f"/student/courses/{course.public_id}/files/{asset.public_id}/download?version=1",
            headers={"Accept": "application/json"},
        )
        assert resp_infected.status_code == 403

    def test_instructor_cannot_download_infected_or_quarantined_file(
        self,
        client: FlaskClient,
        instructor_1: User,
        course_1: Course,
    ) -> None:
        """Managing instructor cannot download infected/quarantined files (fail-closed)."""
        asset = FileAsset(
            course_id=course_1.id,
            created_by_user_id=instructor_1.id,
            asset_type="RESOURCE",
            display_name="instructor_infected.pdf",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="instructor_infected.pdf",
            detected_mime_type="application/octet-stream",
            size_bytes=68,
            status="REJECTED",
            rejection_reason="Infected malware",
            quarantine_key="infected/hash123",
            uploaded_by_user_id=instructor_1.id,
        )
        db.session.add(rev)
        db.session.commit()

        login_web_user(client, instructor_1)
        resp = client.get(
            f"/instructor/courses/{course_1.public_id}/files/{asset.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403


class TestVector3CrossInstructorAuthorizationIsolation:
    """Adversarial testing: Can an instructor download files from another instructor's course?"""

    def test_foreign_instructor_cannot_download_via_course_route(
        self,
        client: FlaskClient,
        instructor_2: User,
        course_1: Course,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Instructor 2 attempts to download Course 1's file via instructor course download route.

        Must fail with HTTP 403 Forbidden (require_course_manager raises ForbiddenError).
        """
        login_web_user(client, instructor_2)
        resp = client.get(
            f"/instructor/courses/{course_1.public_id}/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_foreign_instructor_cannot_download_via_cross_course_idor(
        self,
        client: FlaskClient,
        instructor_2: User,
        course_2: Course,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Cross-course IDOR: Instructor 2 calls /instructor/courses/<c2_id>/files/<f1_id>/download.

        Instructor 2 owns Course 2, but f1 belongs to Course 1.
        Must fail with HTTP 403 Forbidden (get_file_for_download checks asset's course owner).
        """
        login_web_user(client, instructor_2)
        resp = client.get(
            f"/instructor/courses/{course_2.public_id}/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_foreign_instructor_cannot_download_via_api_session(
        self,
        client: FlaskClient,
        instructor_2: User,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Instructor 2 attempts GET /api/files/<f1_id>/download with session cookie.

        Must fail with HTTP 403 Forbidden.
        """
        login_web_user(client, instructor_2)
        resp = client.get(
            f"/api/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403

    def test_foreign_instructor_cannot_download_via_api_jwt(
        self,
        client: FlaskClient,
        instructor_2: User,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Instructor 2 attempts GET /api/files/<f1_id>/download with JWT Bearer token.

        Must fail with HTTP 403 Forbidden.
        """
        tokens = create_token_pair(instructor_2)
        resp = client.get(
            f"/api/files/{clean_file_course_1.public_id}/download",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
                "Accept": "application/json",
            },
        )
        assert resp.status_code == 403

    def test_foreign_instructor_cannot_rescan_course_file_direct_route(
        self,
        client: FlaskClient,
        instructor_2: User,
        course_1: Course,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Instructor 2 cannot trigger rescan on Course 1 via direct course route (403)."""
        login_web_user(client, instructor_2)
        resp_direct = client.post(
            f"/instructor/courses/{course_1.public_id}/files/{clean_file_course_1.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp_direct.status_code == 403

    def test_idor_rescan_route_swallows_forbidden_error_returning_200_defect(
        self,
        client: FlaskClient,
        instructor_2: User,
        course_1: Course,
        course_2: Course,
        clean_file_course_1: FileAsset,
    ) -> None:
        """VULNERABILITY PROBE: IDOR on rescan route swallows ForbiddenError and returns 200 OK.

        When Instructor 2 targets Course 1's file through Course 2's URL:
        `POST /instructor/courses/<c2_id>/files/<c1_file_id>/rescan`
        Expected secure behavior: HTTP 403 Forbidden (or 404 ResourceNotFoundError).
        Observed defect in `rescan_course_file_route`: The route catches `Exception as exc`,
        rolls back DB session, but falls through to line 748 returning HTTP 200 OK
        `{"message": "Rescan completed", "asset_id": ...}` for JSON requests.
        """
        login_web_user(client, instructor_2)

        # IDOR route using Course 2 ID with Course 1 Asset ID
        resp_idor = client.post(
            f"/instructor/courses/{course_2.public_id}/files/{clean_file_course_1.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        # Verified secure behavior: The endpoint returns 403 Forbidden
        # (require_course_manager raises ForbiddenError)
        assert resp_idor.status_code in (403, 404), (
            f"Expected secure behavior (returns 403 or 404): got {resp_idor.status_code}"
        )

        # Verify DB rollback occurred and file was not modified
        db.session.refresh(clean_file_course_1)
        assert clean_file_course_1.course_id == course_1.id

    def test_foreign_instructor_cannot_quarantine_override(
        self,
        client: FlaskClient,
        instructor_2: User,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Instructor 2 cannot override quarantine on Course 1's file (DEF-15: admin only)."""
        tokens = create_token_pair(instructor_2)
        resp = client.post(
            f"/api/files/{clean_file_course_1.public_id}/quarantine-override",
            json={"reason": "Unauthorized foreign instructor attempt"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 403


class TestVector4DefenseInDepthEdgeCases:
    """Additional edge cases: unauthenticated access, non-existent assets, and role boundaries."""

    def test_unauthenticated_api_download_rejected(
        self,
        client: FlaskClient,
        clean_file_course_1: FileAsset,
    ) -> None:
        """Anonymous request to /api/files/<asset_id>/download is rejected with 401 or 403."""
        resp = client.get(
            f"/api/files/{clean_file_course_1.public_id}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code in (401, 403)

    def test_nonexistent_file_download_returns_404(
        self,
        client: FlaskClient,
        student_a: User,
        course_1: Course,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Requesting a non-existent asset UUID returns 404 Not Found."""
        login_web_user(client, student_a)
        random_uuid = str(uuid.uuid4())
        resp = client.get(
            f"/student/courses/{course_1.public_id}/files/{random_uuid}/download",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 404

    def test_student_cannot_call_instructor_rescan_route(
        self,
        client: FlaskClient,
        student_a: User,
        course_1: Course,
        clean_file_course_1: FileAsset,
        enrolled_course_1: tuple[Course, Enrollment],
    ) -> None:
        """Student cannot call POST /instructor/courses/<cid>/files/<fid>/rescan."""
        login_web_user(client, student_a)
        resp = client.post(
            f"/instructor/courses/{course_1.public_id}/files/{clean_file_course_1.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403
