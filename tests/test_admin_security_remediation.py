"""Regression and security verification tests for Admin role remediation."""

import pytest

from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.services.exceptions import (
    AdminActionForbiddenError,
    InvalidRoleAssignmentError,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def student_user(app):
    with app.app_context():
        user = register_user(
            email="student_attacker@example.com",
            password="Password123!",
            display_name="Attacker Student",
        )
        db.session.commit()
        yield user


@pytest.fixture
def primary_admin(app):
    with app.app_context():
        admin = register_user(
            email="primary_admin@example.com",
            password="SuperPassword123!",
            display_name="Primary Super Admin",
        )
        # Assign ADMIN with SUB_ROLE:ADMIN_PRIMARY
        admin_role = db.session.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Admin")
            db.session.add(admin_role)
            db.session.flush()
        admin.roles.append(admin_role)
        db.session.flush()
        link = (
            db.session.query(UserRole)
            .filter(
                UserRole.user_id == admin.id,
                UserRole.role_id == admin_role.id,
            )
            .first()
        )
        link.assignment_reason = "SUB_ROLE:ADMIN_PRIMARY | Baseline setup"
        db.session.commit()
        yield admin


@pytest.fixture
def subordinate_admin(app, primary_admin):
    with app.app_context():
        sub_admin = register_user(
            email="sub_admin@example.com",
            password="SubPassword123!",
            display_name="Subordinate Admin",
        )
        admin_role = db.session.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Admin")
            db.session.add(admin_role)
            db.session.flush()
        sub_admin.roles.append(admin_role)
        db.session.flush()
        link = (
            db.session.query(UserRole)
            .filter(
                UserRole.user_id == sub_admin.id,
                UserRole.role_id == admin_role.id,
            )
            .first()
        )
        link.assignment_reason = "SUB_ROLE:ADMIN_SYSTEM_MONITORING | Assigned for monitoring"
        db.session.commit()
        yield sub_admin


# --- Task 1: SEC-01 & SEC-02 Tests ---


def test_regular_user_cannot_self_assign_admin(app, student_user):
    """SEC-01: A regular student cannot elevate themselves to admin or primary admin."""
    with app.app_context():
        sess_student = db.session.get(User, student_user.id)
        with pytest.raises(AdminActionForbiddenError):
            assign_role_to_user(
                user_id=sess_student.id,
                role_code="ADMIN",
                assigned_by_user_id=sess_student.id,
                reason="Self promotion attack",
                session=db.session,
            )


def test_subordinate_admin_cannot_assign_admin_role(app, subordinate_admin, student_user):
    """SEC-01: A subordinate admin (non-primary) cannot grant ADMIN role to anyone."""
    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_student = db.session.get(User, student_user.id)
        with pytest.raises(AdminActionForbiddenError):
            assign_role_to_user(
                user_id=sess_student.id,
                role_code="ADMIN",
                admin_sub_role="ADMIN_COURSE_REVIEW",
                assigned_by_user_id=sess_sub.id,
                reason="Subordinate attempting role assignment",
                session=db.session,
            )


def test_missing_subrole_does_not_default_to_primary_admin(app):
    """SEC-02: If UserRole has no SUB_ROLE, it must NEVER default to ADMIN_PRIMARY."""
    with app.app_context():
        user = register_user(
            email="blank_admin@example.com",
            password="Password123!",
            display_name="Blank Reason Admin",
        )
        admin_role = db.session.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            admin_role = Role(code="ADMIN", name="Admin")
            db.session.add(admin_role)
            db.session.flush()
        user.roles.append(admin_role)
        db.session.flush()
        link = (
            db.session.query(UserRole)
            .filter(
                UserRole.user_id == user.id,
                UserRole.role_id == admin_role.id,
            )
            .first()
        )
        link.assignment_reason = "Legacy reason without subrole prefix"
        db.session.commit()

        # Reload
        reloaded = db.session.get(User, user.id)
        assert reloaded.is_admin is True
        assert reloaded.admin_sub_role != "ADMIN_PRIMARY"
        assert reloaded.is_primary_admin is False


def test_primary_admin_can_assign_valid_subordinate_admin(app, primary_admin, student_user):
    """SEC-01: Primary admin can assign an allowed subordinate admin role."""
    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        sess_student = db.session.get(User, student_user.id)
        updated = assign_role_to_user(
            user_id=sess_student.id,
            role_code="ADMIN",
            admin_sub_role="ADMIN_COURSE_REVIEW",
            assigned_by_user_id=sess_primary.id,
            reason="Appointed for course review duties",
            session=db.session,
        )
        db.session.commit()

        reloaded = db.session.get(User, updated.id)
        assert reloaded.is_admin is True
        assert reloaded.admin_sub_role == "ADMIN_COURSE_REVIEW"
        assert reloaded.is_primary_admin is False
        assert reloaded.has_admin_permission("COURSE_REVIEW") is True
        assert reloaded.has_admin_permission("INSTRUCTOR_REVIEW") is False


def test_cannot_assign_primary_admin_through_api(app, primary_admin, student_user):
    """SEC-01: ADMIN_PRIMARY can NEVER be granted through ordinary role assignment."""
    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        sess_student = db.session.get(User, student_user.id)
        with pytest.raises(InvalidRoleAssignmentError):
            assign_role_to_user(
                user_id=sess_student.id,
                role_code="ADMIN",
                admin_sub_role="ADMIN_PRIMARY",
                assigned_by_user_id=sess_primary.id,
                reason="Attempting to grant primary admin",
                session=db.session,
            )


# --- Task 2: SEC-03 Super Admin Invariant & Safe Suspension Tests ---


def test_subordinate_admin_cannot_suspend_primary_admin(app, subordinate_admin, primary_admin):
    """SEC-03: Subordinate admin cannot suspend primary super admin."""
    from pwd301.services.audit_service import suspend_user_account

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_primary = db.session.get(User, primary_admin.id)

        with pytest.raises(AdminActionForbiddenError):
            suspend_user_account(
                admin_actor=sess_sub,
                target_user_id=sess_primary.id,
                reason="Attempting to suspend Super Admin",
                session=db.session,
            )


def test_subordinate_admin_cannot_suspend_another_admin(app, subordinate_admin, primary_admin):
    """SEC-03: Subordinate admin cannot suspend another admin."""
    from pwd301.services.audit_service import suspend_user_account

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_primary = db.session.get(User, primary_admin.id)

        # Create another subordinate admin
        another_admin = register_user(
            email="another_sub@example.com",
            password="Password123!",
            display_name="Another Sub Admin",
        )
        assign_role_to_user(
            user_id=another_admin.id,
            role_code="ADMIN",
            admin_sub_role="ADMIN_COURSE_REVIEW",
            assigned_by_user_id=sess_primary.id,
            reason="Created another sub admin",
            session=db.session,
        )
        db.session.commit()

        with pytest.raises(AdminActionForbiddenError):
            suspend_user_account(
                admin_actor=sess_sub,
                target_user_id=another_admin.id,
                reason="Attempting to suspend peer admin",
                session=db.session,
            )


def test_subordinate_admin_cannot_revoke_primary_admin_sessions(
    app, subordinate_admin, primary_admin
):
    """SEC-03: Subordinate admin cannot revoke primary admin's sessions."""
    from pwd301.services.audit_service import force_revoke_user_sessions

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_primary = db.session.get(User, primary_admin.id)

        with pytest.raises(AdminActionForbiddenError):
            force_revoke_user_sessions(
                admin_actor=sess_sub,
                target_user_id=sess_primary.id,
                reason="Attempting to revoke Super Admin session",
                session=db.session,
            )


def test_user_service_suspend_protects_primary_admin(app, primary_admin):
    """SEC-03: Direct call to user_service.suspend_user on primary admin must be rejected."""
    from pwd301.services.user_service import suspend_user

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        with pytest.raises(AdminActionForbiddenError):
            suspend_user(
                user_id=sess_primary.id,
                reason="Direct service suspension attack",
                session=db.session,
            )


# --- Task 3: BFLA REST API & Sub-role Decorators Tests ---


def test_subordinate_admin_jwt_blocked_from_unauthorized_endpoints(
    app, client, subordinate_admin, primary_admin
):
    """API-01: Subordinate admin with SYSTEM_MONITORING cannot call reassign or user roles."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        tokens = create_token_pair(sess_sub)
        token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Attempt to call POST /api/admin/courses/dummy-id/reassign (requires TEACHING_ASSIGNMENT)
        res_reassign = client.post(
            "/api/admin/courses/00000000-0000-0000-0000-000000000001/reassign",
            json={"new_instructor_id": "00000000-0000-0000-0000-000000000002"},
            headers=headers,
        )
        assert res_reassign.status_code == 403

        # 2. Attempt to call POST /api/admin/users/dummy-id/roles (requires PRIMARY_ADMIN)
        res_roles = client.post(
            "/api/admin/users/00000000-0000-0000-0000-000000000001/roles",
            json={"action": "assign", "role": "INSTRUCTOR", "reason": "Test reason 123"},
            headers=headers,
        )
        assert res_roles.status_code == 403

        # 3. Attempt to call GET /api/admin/backups (requires PRIMARY_ADMIN)
        res_backups = client.get("/api/admin/backups", headers=headers)
        assert res_backups.status_code == 403


def test_primary_admin_jwt_allowed_access_to_admin_endpoints(app, client, primary_admin):
    """API-01: Primary admin JWT can access backups."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        res = client.get("/api/admin/backups", headers=headers)
        assert res.status_code == 200


def test_course_status_approval_requires_course_review_permission(
    app, subordinate_admin, primary_admin
):
    """API-02 / SEC-06: Monitoring admin cannot approve courses, but primary admin can."""
    from pwd301.models.course import Course
    from pwd301.services.course_service import change_course_status
    from pwd301.services.exceptions import ForbiddenError

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_primary = db.session.get(User, primary_admin.id)

        course = Course(
            course_code="TEST101",
            course_code_normalized="TEST101",
            title="Test Course",
            title_normalized="test course",
            status="SUBMITTED_FOR_REVIEW",
            owner_instructor_id=sess_primary.id,
        )
        db.session.add(course)
        db.session.commit()

        # Monitoring admin tries to approve -> must fail
        with pytest.raises(ForbiddenError):
            change_course_status(
                course_id=course.id,
                new_status="APPROVED",
                actor=sess_sub,
                reason="Monitoring admin attempting approval",
                session=db.session,
            )


def test_subordinate_admin_maintenance_and_job_restrictions(app, client, subordinate_admin):
    """API-01: Subordinate admin with SYSTEM_MONITORING cannot trigger maintenance/job retry/instructor review."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        tokens = create_token_pair(sess_sub)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 1. POST /api/admin/maintenance/start (requires PRIMARY_ADMIN) -> 403
        res_maint = client.post(
            "/api/admin/maintenance/start",
            json={"reason": "Unauthorized maintenance", "estimated_duration_minutes": 30},
            headers=headers,
        )
        assert res_maint.status_code == 403

        # 2. POST /api/admin/operations/jobs/fake-id/retry (requires PRIMARY_ADMIN) -> 403
        res_retry = client.post(
            "/api/admin/operations/jobs/fake-id/retry",
            json={},
            headers=headers,
        )
        assert res_retry.status_code == 403

        # 3. POST /api/admin/instructor-applications/fake-id/review (requires INSTRUCTOR_REVIEW) -> 403
        res_app_review = client.post(
            "/api/admin/instructor-applications/fake-id/review",
            json={"action": "approve", "reason": "Unauthorized review"},
            headers=headers,
        )
        assert res_app_review.status_code == 403

        # 4. GET /api/admin/maintenance/status (allowed for SYSTEM_MONITORING) -> 200
        res_maint_status = client.get("/api/admin/maintenance/status", headers=headers)
        assert res_maint_status.status_code == 200

        # 5. GET /api/admin/operations/jobs (allowed for SYSTEM_MONITORING) -> 200
        res_jobs = client.get("/api/admin/operations/jobs", headers=headers)
        assert res_jobs.status_code == 200


# --- Task 4: SEC-04 & SEC-05 ClamAV & Quarantine Security Tests ---


def test_quarantine_override_requires_primary_admin(app, subordinate_admin, primary_admin):
    """SEC-04: Subordinate admin cannot call quarantine_override; must require is_primary_admin."""
    from pwd301.models.course import Course
    from pwd301.models.file_import import FileAsset, FileRevision
    from pwd301.services.exceptions import FileAccessDeniedError
    from pwd301.services.file_service import quarantine_override

    with app.app_context():
        sess_sub = db.session.get(User, subordinate_admin.id)
        sess_primary = db.session.get(User, primary_admin.id)

        course = Course(
            course_code="FILE101",
            course_code_normalized="FILE101",
            title="File Course",
            title_normalized="file course",
            status="PUBLISHED",
            owner_instructor_id=sess_primary.id,
        )
        db.session.add(course)
        db.session.flush()

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=sess_primary.id,
            asset_type="RESOURCE",
            display_name="Quarantined File",
            status="PENDING",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=False,
            original_filename="test_file.txt",
            declared_mime_type="text/plain",
            detected_mime_type="text/plain",
            size_bytes=100,
            status="QUARANTINED",
            quarantine_key="quarantine/test_file.txt",
            uploaded_by_user_id=sess_primary.id,
        )
        db.session.add(rev)
        db.session.commit()

        # Subordinate admin attempt must raise FileAccessDeniedError
        with pytest.raises(FileAccessDeniedError):
            quarantine_override(
                admin_actor=sess_sub,
                asset_id=asset.id,
                reason="Subordinate attempting quarantine override",
                session=db.session,
            )


def test_instructor_application_evidence_rejects_malware(app, client, primary_admin, tmp_path):
    """SEC-05: Downloading evidence containing malware (EICAR) must be blocked fail-closed."""
    import json
    from pathlib import Path

    from flask import current_app

    from pwd301.models.identity import InstructorApplication
    from pwd301.services.jwt_auth_service import create_token_pair
    from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create an infected evidence file
        storage_root = Path(current_app.config.get("FILE_STORAGE_ROOT", "./storage")).resolve()
        evidence_dir = storage_root / "instructor_applications" / str(sess_primary.public_id)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_file = evidence_dir / "eicar_test.txt"
        evidence_file.write_bytes(EICAR_SIGNATURE_BYTES)

        # Create instructor application referencing this evidence file
        details = {
            "attached_files": [
                {
                    "saved_filename": "eicar_test.txt",
                    "original_name": "resume_cv.txt",
                }
            ]
        }
        app_record = InstructorApplication(
            applicant_user_id=sess_primary.id,
            status="PENDING",
            application_note=json.dumps(details),
        )
        db.session.add(app_record)
        db.session.commit()

        # Try to download the evidence
        res = client.get(
            f"/api/admin/instructor-applications/{app_record.public_id}/evidence/eicar_test.txt",
            headers=headers,
        )
        # Fail-closed: Must be blocked (403 Forbidden)
        assert res.status_code == 403


# --- Task 5: BIZ-01 Sensitive Action Fresh Re-authentication Tests ---


def test_suspend_user_requires_fresh_reauth(app, client, primary_admin):
    """BIZ-01: Suspending a user requires fresh admin password confirmation."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create a target regular user
        target = register_user(
            email="victim_suspend@example.com",
            password="UserPass123!",
            display_name="Victim User",
        )
        db.session.commit()

        # 1. Without password -> 401
        res_no_pw = client.post(
            f"/api/admin/users/{target.public_id}/suspend",
            json={"reason": "Test suspension without password"},
            headers=headers,
        )
        assert res_no_pw.status_code == 401

        # 2. With wrong password -> 401
        res_wrong_pw = client.post(
            f"/api/admin/users/{target.public_id}/suspend",
            json={"reason": "Test suspension with wrong password", "password": "WrongPassword!"},
            headers=headers,
        )
        assert res_wrong_pw.status_code == 401

        # 3. With correct admin password -> 200
        res_ok = client.post(
            f"/api/admin/users/{target.public_id}/suspend",
            json={
                "reason": "Test suspension with correct password",
                "password": "SuperPassword123!",
            },
            headers=headers,
        )
        assert res_ok.status_code == 200


def test_maintenance_start_requires_fresh_reauth(app, client, primary_admin):
    """BIZ-01: Starting maintenance window requires fresh admin password confirmation."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 1. Without password -> 401
        res_no_pw = client.post(
            "/api/admin/maintenance/start",
            json={"reason": "Scheduled maintenance", "estimated_duration_minutes": 30},
            headers=headers,
        )
        assert res_no_pw.status_code == 401

        # 2. With correct password -> 201
        res_ok = client.post(
            "/api/admin/maintenance/start",
            json={
                "reason": "Scheduled maintenance",
                "estimated_duration_minutes": 30,
                "password": "SuperPassword123!",
            },
            headers=headers,
        )
        assert res_ok.status_code == 201


def test_trash_course_requires_fresh_reauth(app, client, primary_admin):
    """BIZ-01: Trashing a course requires fresh admin password confirmation."""
    from pwd301.models.course import Course
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        course = Course(
            course_code="TRASH101",
            course_code_normalized="TRASH101",
            title="Course to Trash",
            title_normalized="course to trash",
            status="PUBLISHED",
            owner_instructor_id=sess_primary.id,
        )
        db.session.add(course)
        db.session.commit()

        # 1. Without password -> 401
        res_no_pw = client.post(
            f"/api/admin/courses/{course.public_id}/trash",
            json={"reason": "Trashing without password"},
            headers=headers,
        )
        assert res_no_pw.status_code == 401

        # 2. With correct password -> 200
        res_ok = client.post(
            f"/api/admin/courses/{course.public_id}/trash",
            json={"reason": "Trashing with password", "password": "SuperPassword123!"},
            headers=headers,
        )
        assert res_ok.status_code == 200


def test_revoke_sessions_requires_fresh_reauth(app, client, primary_admin):
    """BIZ-01: Revoking all user sessions requires fresh admin password confirmation."""
    from pwd301.services.jwt_auth_service import create_token_pair

    with app.app_context():
        sess_primary = db.session.get(User, primary_admin.id)
        tokens = create_token_pair(sess_primary)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        target = register_user(
            email="victim_revoke@example.com",
            password="UserPass123!",
            display_name="Victim Revoke",
        )
        db.session.commit()

        # 1. Without password -> 401
        res_no_pw = client.post(
            f"/api/admin/users/{target.public_id}/revoke-sessions",
            json={"reason": "Revoking without password"},
            headers=headers,
        )
        assert res_no_pw.status_code == 401

        # 2. With correct password -> 200
        res_ok = client.post(
            f"/api/admin/users/{target.public_id}/revoke-sessions",
            json={"reason": "Revoking with password", "password": "SuperPassword123!"},
            headers=headers,
        )
        assert res_ok.status_code == 200


# --- Task 6: OPS-01 & ARCH-01 Authentic Telemetry & Pure Headless Tests ---


def test_system_health_telemetry_contains_no_fake_metrics(app):
    """OPS-01: Health check services matrix must not contain fake mock services or hardcoded latencies."""
    from pwd301.services.operations_service import check_system_health

    with app.app_context():
        report = check_system_health(include_details=True, session=db.session)
        services = report.get("services", {})

        # Must not contain unconfigured/fake services
        assert "qdrant_vector" not in services, "Qdrant vector is fake/unconfigured in PWD301"
        assert "redis_tokens" not in services, "Redis tokens is fake/unconfigured in PWD301"

        # Must contain real operational services
        assert "database" in services or "mssql" in services
        assert "clamav" in services
        assert "storage" in services or "storage_minio" in services
        assert "workers" in services
        assert "mail_queue" in services
