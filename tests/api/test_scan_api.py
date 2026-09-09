"""REST API test suite for File Security, Scanning, Rescan, and Quarantine Override (TASK-019).

Validates:
- GET /api/files/<asset_id>/scans returns 200 with scan history for course instructor or admin.
- GET /api/files/<asset_id>/scan-results returns 200 as an alias endpoint.
- Students and foreign instructors receive 403 when accessing scan results.
- Unauthenticated requests to scan endpoints receive 401.
- POST /api/files/<asset_id>/rescan triggers on-demand physical re-scan for instructor/admin.
- Students receive 403 when attempting to trigger a rescan.
- POST /api/files/<asset_id>/quarantine-override enables Admin to release
  quarantined file with reason.
- POST /api/admin/files/<asset_id>/quarantine-override operates via the /api/admin endpoint.
- POST /admin/files/<asset_id>/quarantine-override operates via Web session for admin.
- Quarantine override fails with 403 for non-admins and 400 for empty justification reason.
- Zero internal PK leakage and physical path exposure per ADR-002.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.file_service import store_file_stream
from pwd301.services.jwt_auth_service import create_token_pair
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
    """Create primary test instructor."""
    u = register_user(
        f"scan_api_inst_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Scan API Instructor",
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def foreign_instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create external instructor not managing the course."""
    u = register_user(
        f"scan_api_other_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Foreign Instructor",
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user(
        f"scan_api_stu_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Scan API Student",
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user(
        f"scan_api_adm_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Scan API Admin",
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create test course owned by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"SEC-{uuid.uuid4().hex[:4].upper()}",
            "title": "Malware Scanning Architecture",
            "category": "Computer Science",
            "difficulty": "ADVANCED",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def clean_file_asset(instructor_user: User, test_course: Course) -> FileAsset:
    """Upload a clean file asset."""
    content = b"%PDF-1.4\nClean lecture slides content\n%%EOF"
    asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.public_id,
        file_stream=io.BytesIO(content),
        filename="lecture_clean.pdf",
        content_type="application/pdf",
        session=db.session,
    )
    return asset


class TestScanHistoryApi:
    """Test suite for GET /api/files/<asset_id>/scans and scan-results."""

    def test_get_scans_authorized_instructor(
        self, client: FlaskClient, instructor_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Managing instructor can retrieve scan history via GET /api/files/<asset_id>/scans."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.get(f"/api/files/{clean_file_asset.public_id}/scans", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["asset_id"] == str(clean_file_asset.public_id)
        assert "scans" in data
        assert len(data["scans"]) >= 1

        scan_item = data["scans"][0]
        assert "scan_id" in scan_item
        assert "engine" in scan_item
        assert "status" in scan_item
        assert scan_item["status"] == "PASS"

        # ADR-002 Zero Internal PK Leakage verification
        assert "id" not in scan_item
        assert "blob_id" not in scan_item
        assert "file_revision_id" not in scan_item
        assert "storage_path" not in scan_item

    def test_get_scans_alias_scan_results(
        self, client: FlaskClient, instructor_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Alias GET /api/files/<asset_id>/scan-results returns same scan data."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.get(f"/api/files/{clean_file_asset.public_id}/scan-results", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["asset_id"] == str(clean_file_asset.public_id)
        assert len(data["scans"]) >= 1

    def test_get_scans_student_forbidden(
        self, client: FlaskClient, student_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Students are forbidden from inspecting internal scan diagnostics."""
        tokens = create_token_pair(student_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.get(f"/api/files/{clean_file_asset.public_id}/scans", headers=headers)
        assert resp.status_code == 403

    def test_get_scans_foreign_instructor_forbidden(
        self, client: FlaskClient, foreign_instructor_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Instructors not managing the course receive 403 IDOR rejection."""
        tokens = create_token_pair(foreign_instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.get(f"/api/files/{clean_file_asset.public_id}/scans", headers=headers)
        assert resp.status_code == 403

    def test_get_scans_unauthenticated(
        self, client: FlaskClient, clean_file_asset: FileAsset
    ) -> None:
        """Unauthenticated requests receive 401 Unauthorized."""
        resp = client.get(f"/api/files/{clean_file_asset.public_id}/scans")
        assert resp.status_code == 401


class TestRescanApi:
    """Test suite for POST /api/files/<asset_id>/rescan."""

    def test_rescan_file_by_instructor_success(
        self, client: FlaskClient, instructor_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Instructor triggers physical byte rescan successfully."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(f"/api/files/{clean_file_asset.public_id}/rescan", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["asset_id"] == str(clean_file_asset.public_id)
        assert data["status"] == "ACTIVE"

        # Verify new scan record was appended to history
        scans_resp = client.get(f"/api/files/{clean_file_asset.public_id}/scans", headers=headers)
        assert scans_resp.status_code == 200
        assert len(scans_resp.get_json()["scans"]) >= 2

    def test_rescan_file_by_student_forbidden(
        self, client: FlaskClient, student_user: User, clean_file_asset: FileAsset
    ) -> None:
        """Student cannot trigger a file rescan."""
        tokens = create_token_pair(student_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(f"/api/files/{clean_file_asset.public_id}/rescan", headers=headers)
        assert resp.status_code == 403

    def test_rescan_file_unauthenticated(
        self, client: FlaskClient, clean_file_asset: FileAsset
    ) -> None:
        """Unauthenticated request to rescan is rejected with 401."""
        resp = client.post(f"/api/files/{clean_file_asset.public_id}/rescan")
        assert resp.status_code == 401


class TestQuarantineOverrideApi:
    """Test suite for Admin quarantine override endpoints."""

    def test_quarantine_override_via_api_files(
        self,
        client: FlaskClient,
        admin_user: User,
        clean_file_asset: FileAsset,
    ) -> None:
        """Admin overrides quarantine via POST /api/files/<asset_id>/quarantine-override."""
        # Set revision to QUARANTINED
        rev = clean_file_asset.current_revision
        rev.status = "QUARANTINED"
        clean_file_asset.status = "PENDING"
        db.session.commit()

        tokens = create_token_pair(admin_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {"reason": "SecOps verified file content is a benign false-positive."}
        resp = client.post(
            f"/api/files/{clean_file_asset.public_id}/quarantine-override",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ACTIVE"

    def test_quarantine_override_via_api_admin(
        self,
        client: FlaskClient,
        admin_user: User,
        clean_file_asset: FileAsset,
    ) -> None:
        """Admin overrides quarantine via POST /api/admin/files/<asset_id>/quarantine-override."""
        rev = clean_file_asset.current_revision
        rev.status = "QUARANTINED"
        clean_file_asset.status = "PENDING"
        db.session.commit()

        tokens = create_token_pair(admin_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {"reason": "Approved after manual sandbox analysis."}
        resp = client.post(
            f"/api/admin/files/{clean_file_asset.public_id}/quarantine-override",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ACTIVE"

    def test_quarantine_override_via_web_admin_session(
        self,
        client: FlaskClient,
        admin_user: User,
        clean_file_asset: FileAsset,
    ) -> None:
        """Admin overrides quarantine via /admin/files/<asset_id>/quarantine-override."""
        login_web_user(client, admin_user)

        rev = clean_file_asset.current_revision
        rev.status = "QUARANTINED"
        clean_file_asset.status = "PENDING"
        db.session.commit()

        payload = {"reason": "Admin session authorized override."}
        resp = client.post(
            f"/admin/files/{clean_file_asset.public_id}/quarantine-override",
            json=payload,
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ACTIVE"

    def test_quarantine_override_non_admin_forbidden(
        self,
        client: FlaskClient,
        instructor_user: User,
        clean_file_asset: FileAsset,
    ) -> None:
        """Non-admin (instructor) receives 403 when attempting quarantine override."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        payload = {"reason": "Instructor trying to force release."}
        resp = client.post(
            f"/api/files/{clean_file_asset.public_id}/quarantine-override",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 403

    def test_quarantine_override_empty_reason_rejected(
        self,
        client: FlaskClient,
        admin_user: User,
        clean_file_asset: FileAsset,
    ) -> None:
        """Quarantine override fails with 400 when reason is missing or empty."""
        tokens = create_token_pair(admin_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(
            f"/api/files/{clean_file_asset.public_id}/quarantine-override",
            json={"reason": "   "},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "reason" in resp.get_json()["error"]["message"].lower()
