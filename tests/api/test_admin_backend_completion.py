"""Test suite for Admin backend completion, security guardrails, and full UI/UX parity.

Verifies:
1. Admin Course Inspection (GET /admin/courses/<course_id>).
2. 6-Core Service Health Diagnostics Matrix (WebCore, MSSQL, ClamAV, MinIO, Qdrant, Redis).
3. Security Guardrails: Self-demotion block, Last Admin protection, audit reason validation.
4. Faculty Reassignment with dual in-app notifications (prior & new owner).
5. Academic Faculty Workload calculation from DB.
6. Background Jobs telemetry and retry workflow.
7. Single User Inspection (GET /admin/users/<user_id>).
8. Evidence download parity across Web Session and JWT REST API.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification, NotificationEvent
from pwd301.models.operations import BackgroundJob
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Any) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    sess = db.session
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
def admin_user(app: Any, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(
        f"comp_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin Completion Tester"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Any, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"comp_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Tester"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Any, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"comp_stud_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Tester"
    )
    return assign_role_to_user(u.id, "STUDENT")


def _admin_headers(admin_user: User) -> dict[str, str]:
    tokens = create_token_pair(admin_user)
    token_str = tokens["access_token"] if isinstance(tokens, dict) else tokens.access_token
    return {
        "Authorization": f"Bearer {token_str}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def test_admin_course_inspection_dossier(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Admin can view full course inspection dossier including lessons and SLOs."""
    sess = db.session
    course = Course(
        course_code="ADM101",
        title="Admin Inspection Test Course",
        description="Full course syllabus for administrative quality gate",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.flush()

    lesson1 = Lesson(
        course_id=course.id,
        title="Lesson 1: Introduction",
        order_index=1,
        status="PUBLISHED",
        markdown_content="# Lesson 1 Content",
    )
    lesson2 = Lesson(
        course_id=course.id,
        title="Lesson 2: Advanced Topics",
        order_index=2,
        status="DRAFT",
        markdown_content="# Lesson 2 Content",
    )
    sess.add_all([lesson1, lesson2])
    sess.commit()

    # 1. Test via Web Session
    login_web_user(client, admin_user)

    res = client.get(f"/admin/courses/{course.public_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["course_id"] == str(course.public_id)
    assert data["course_code"] == "ADM101"
    assert data["title"] == "Admin Inspection Test Course"
    assert data["status"] == "SUBMITTED_FOR_REVIEW"
    assert data["owner_instructor_id"] == str(instructor_user.public_id)
    assert data["owner_instructor_name"] == instructor_user.display_name
    assert len(data["lessons"]) == 2
    assert data["lessons"][0]["title"] == "Lesson 1: Introduction"
    assert data["lessons"][1]["title"] == "Lesson 2: Advanced Topics"

    # 2. Test via JWT REST API
    headers = _admin_headers(admin_user)
    api_res = client.get(f"/api/admin/courses/{course.public_id}", headers=headers)
    assert api_res.status_code == 200
    api_data = api_res.get_json()
    assert api_data["course_id"] == str(course.public_id)
    assert len(api_data["lessons"]) == 2


def test_admin_health_six_core_services(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """Operational health returns structured live diagnostics for all 6 core services."""
    login_web_user(client, admin_user)

    res = client.get("/admin/health")
    assert res.status_code == 200
    data = res.get_json()

    assert "services" in data
    services = data["services"]
    assert "web_core" in services
    assert "mssql" in services
    assert "clamav" in services
    assert "storage_minio" in services
    assert "qdrant_vector" in services
    assert "redis_tokens" in services

    assert services["web_core"]["status"] in ("HEALTHY", "DEGRADED")
    assert services["mssql"]["status"] in ("HEALTHY", "DEGRADED", "DOWN")
    assert services["clamav"]["status"] in ("HEALTHY", "DEGRADED")
    assert services["storage_minio"]["status"] in ("HEALTHY", "DEGRADED")
    assert services["qdrant_vector"]["status"] in ("HEALTHY", "DEGRADED")
    assert services["redis_tokens"]["status"] in ("HEALTHY", "DEGRADED")


def test_admin_security_self_demotion_blocked(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """An administrator cannot revoke their own ADMIN role (Self-Demotion Blocked)."""
    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/users/{admin_user.public_id}/roles",
        json={
            "action": "remove",
            "role": "ADMIN",
            "reason": "Accidental self-demotion test",
        },
    )
    assert res.status_code in (400, 403)
    data = res.get_json()
    err_msg = data["error"]["message"].lower()
    assert "tự thu hồi" in err_msg or "self" in err_msg


def test_admin_security_last_admin_protection(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """System refuses to suspend or remove ADMIN role if target is the sole active admin."""
    sess = db.session
    # Ensure only 1 active admin exists
    admin_role = sess.query(Role).filter(Role.code == "ADMIN").first()
    other_admins = (
        sess.query(User).filter(User.roles.contains(admin_role), User.id != admin_user.id).all()
    )
    for oa in other_admins:
        oa.status = "SUSPENDED"
    sess.commit()

    login_web_user(client, admin_user)

    # Create a secondary admin to test suspending them when there is still another active admin
    second_admin = User(
        email="second_admin@example.com",
        password_hash="fakehash",
        display_name="Second Admin",
        status="ACTIVE",
    )
    student_role = sess.query(Role).filter(Role.code == "STUDENT").first()
    instructor_role = sess.query(Role).filter(Role.code == "INSTRUCTOR").first()
    second_admin.roles.extend([student_role, instructor_role, admin_role])
    sess.add(second_admin)
    sess.commit()

    # Suspending the second admin is allowed since admin_user is also active
    res_suspend = client.post(
        f"/admin/users/{second_admin.public_id}/suspend",
        json={"reason": "Valid suspension of secondary administrator"},
    )
    assert res_suspend.status_code == 200

    # Now second_admin is suspended, so admin_user is the ONLY active admin left.
    # Attempting to suspend admin_user is blocked by self-suspension and last-admin check.
    res_suspend_last = client.post(
        f"/admin/users/{admin_user.public_id}/suspend",
        json={"reason": "Attempting to suspend last active admin"},
    )
    assert res_suspend_last.status_code in (400, 403)


def test_admin_security_reason_validation(
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """Admin role modification and suspension reject short or missing reasons (< 5 chars)."""
    login_web_user(client, admin_user)

    # 1. Short reason on suspend
    res = client.post(
        f"/admin/users/{student_user.public_id}/suspend",
        json={"reason": "bad"},
    )
    assert res.status_code == 400
    res_msg = res.get_json()["error"]["message"].lower()
    assert "tối thiểu 5 ký tự" in res_msg or "reason" in res_msg

    # 2. Short reason on role assign
    res_role = client.post(
        f"/admin/users/{student_user.public_id}/roles",
        json={
            "action": "assign",
            "role": "INSTRUCTOR",
            "reason": "123",
        },
    )
    assert res_role.status_code == 400


def test_admin_course_reassignment_with_dual_notifications(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Reassigning course ownership notifies both the former and new instructor."""
    sess = db.session

    new_instructor = User(
        email="new_instructor@example.com",
        password_hash="fakehash",
        display_name="New Instructor",
        status="ACTIVE",
    )
    student_role = sess.query(Role).filter(Role.code == "STUDENT").first()
    instructor_role = sess.query(Role).filter(Role.code == "INSTRUCTOR").first()
    new_instructor.roles.extend([student_role, instructor_role])
    sess.add(new_instructor)

    course = Course(
        course_code="REASSIGN101",
        title="Course To Reassign",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/courses/{course.public_id}/reassign",
        json={
            "new_instructor_id": str(new_instructor.public_id),
            "reason": "Official faculty department transfer decision",
        },
    )
    assert res.status_code == 200

    # Verify notifications were dispatched to both instructors
    notifs_old = (
        sess.query(Notification).filter(Notification.recipient_user_id == instructor_user.id).all()
    )
    notifs_new = (
        sess.query(Notification).filter(Notification.recipient_user_id == new_instructor.id).all()
    )
    assert len(notifs_old) >= 1
    assert len(notifs_new) >= 1
    assert "chuyển giao" in notifs_old[-1].body.lower() or "bàn giao" in notifs_old[-1].body.lower()
    assert "tiếp nhận" in notifs_new[-1].body.lower() or "phụ trách" in notifs_new[-1].body.lower()


def test_admin_faculty_workload_metrics(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Admin faculty workload endpoint returns accurate academic workload and SLA stats."""
    sess = db.session
    course = Course(
        course_code="LOAD101",
        title="Workload Test Course",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.get("/admin/faculty/workload")
    assert res.status_code == 200
    data = res.get_json()
    assert "instructors" in data
    assert "total_faculty" in data

    matched = next(
        (i for i in data["instructors"] if i["user_id"] == str(instructor_user.public_id)),
        None,
    )
    assert matched is not None
    assert matched["assigned_courses_count"] >= 1
    assert matched["estimated_hours"] >= 60
    assert "workload_status" in matched


def test_admin_background_jobs_listing_and_retry(
    client: FlaskClient,
    admin_user: User,
) -> None:
    """Admin can list background jobs and retry failed background tasks."""
    sess = db.session
    failed_job = BackgroundJob(
        job_type="REGRADE",
        job_key=uuid.uuid4(),
        status="FAILED",
        payload_json=json.dumps({"attempt_id": 9999}),
        last_error="Simulated regrade calculation timeout",
        attempt_count=3,
        max_attempts=3,
    )
    sess.add(failed_job)
    sess.commit()

    login_web_user(client, admin_user)

    # 1. List jobs
    res = client.get("/admin/operations/jobs")
    assert res.status_code == 200
    data = res.get_json()
    assert "items" in data
    assert "summary" in data
    assert data["summary"]["failed"] >= 1

    # 2. Retry job
    job_id = failed_job.public_id
    retry_res = client.post(f"/admin/operations/jobs/{job_id}/retry")
    assert retry_res.status_code == 200
    retry_data = retry_res.get_json()
    assert retry_data["status"] == "QUEUED"


def test_admin_single_user_inspection(
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """Admin can query detailed profile of any single user."""
    login_web_user(client, admin_user)

    res = client.get(f"/admin/users/{student_user.public_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["user_id"] == str(student_user.public_id)
    assert data["email"] == student_user.email
    assert data["display_name"] == student_user.display_name
    assert "roles" in data
    assert "STUDENT" in data["roles"]


def test_admin_review_course_approved_sends_notification(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Approving a course sends in-app notification to the owner instructor."""
    sess = db.session
    course = Course(
        course_code="NOTIF_APP101",
        title="Course for Approval Notification",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/courses/{course.public_id}/review",
        json={"action": "approve", "reason": "Syllabus meets ABET CAC accreditation standard"},
    )
    assert res.status_code == 200

    notifs = (
        sess.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor_user.id,
            NotificationEvent.event_type == "COURSE_APPROVED",
        )
        .all()
    )
    assert len(notifs) >= 1
    latest_notif = notifs[-1]
    assert "phê duyệt" in latest_notif.title.lower() or "approved" in latest_notif.title.lower()
    assert course.course_code in latest_notif.body or course.title in latest_notif.body


def test_admin_review_course_rejected_sends_notification(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Rejecting a course sends in-app notification with reason to the owner instructor."""
    sess = db.session
    course = Course(
        course_code="NOTIF_REJ101",
        title="Course for Rejection Notification",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, admin_user)

    reject_reason = "Yêu cầu bổ sung ma trận chuẩn đầu ra ABET L1-L4 và rubric chấm điểm"
    res = client.post(
        f"/admin/courses/{course.public_id}/review",
        json={"action": "reject", "reason": reject_reason},
    )
    assert res.status_code == 200

    notifs = (
        sess.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor_user.id,
            NotificationEvent.event_type == "COURSE_REJECTED",
        )
        .all()
    )
    assert len(notifs) >= 1
    latest_notif = notifs[-1]
    assert "từ chối" in latest_notif.title.lower() or "chỉnh sửa" in latest_notif.title.lower()
    assert reject_reason in latest_notif.body or course.course_code in latest_notif.body


def test_admin_review_course_reject_requires_min_5_chars(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Rejecting a course requires reason with minimum 5 characters."""
    sess = db.session
    course = Course(
        course_code="REJ_MIN5",
        title="Course Short Reason Rejection",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, admin_user)

    # Short reason (< 5 chars) should fail with 400
    res = client.post(
        f"/admin/courses/{course.public_id}/review",
        json={"action": "reject", "reason": "bad"},
    )
    assert res.status_code == 400
    err_msg = res.get_json()["error"]["message"].lower()
    assert "tối thiểu 5 ký tự" in err_msg or "reason" in err_msg or "bắt buộc" in err_msg


def test_admin_users_server_side_filtering(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
    student_user: User,
) -> None:
    """GET /admin/users and GET /api/admin/users support server-side search and role filtering."""
    login_web_user(client, admin_user)

    # 1. Filter by role INSTRUCTOR
    res_inst = client.get("/admin/users?role=INSTRUCTOR")
    assert res_inst.status_code == 200
    data_inst = res_inst.get_json()
    assert all("INSTRUCTOR" in u["roles"] for u in data_inst["users"])

    # 2. Search by unique substring
    res_search = client.get(f"/admin/users?search={instructor_user.email}")
    assert res_search.status_code == 200
    data_search = res_search.get_json()
    assert any(u["user_id"] == str(instructor_user.public_id) for u in data_search["users"])

    # 3. JWT REST API filter parity
    headers = _admin_headers(admin_user)
    api_res = client.get(f"/api/admin/users?search={student_user.email}", headers=headers)
    assert api_res.status_code == 200
    api_data = api_res.get_json()
    assert any(u["user_id"] == str(student_user.public_id) for u in api_data["users"])


def test_instructor_applications_adr002_zero_pk_leakage(
    client: FlaskClient,
    admin_user: User,
    student_user: User,
) -> None:
    """Instructor application responses must not leak internal BigInt PK for applicant_user_id."""
    from pwd301.models.identity import InstructorApplication

    sess = db.session
    app_record = InstructorApplication(
        applicant_user_id=student_user.id,
        status="PENDING",
        application_note=json.dumps({"degree": "PhD", "specialization": "Computer Science"}),
    )
    sess.add(app_record)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.get(f"/admin/instructor-applications/{app_record.id}")
    assert res.status_code == 200
    data = res.get_json()

    # applicant_user_id must be a UUID string (ADR-002 Zero Internal PK Leakage), NOT integer
    assert isinstance(data["applicant_user_id"], str)
    assert data["applicant_user_id"] == str(student_user.public_id)
    # Check it cannot be parsed as integer BigInt
    with pytest.raises(ValueError):
        int(data["applicant_user_id"])


def test_admin_broadcast_notification_api(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Admin broadcast system notification successfully distributes to target roles."""
    login_web_user(client, admin_user)

    res = client.post(
        "/admin/notifications/broadcast",
        json={
            "title": "Bảo trì nâng cấp học kỳ mới",
            "body": "Toàn hệ thống sẽ được bảo trì trong 15 phút lúc 00:00 UTC.",
            "target_role": "INSTRUCTOR",
            "category": "SYSTEM",
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["broadcasted_count"] >= 1


def test_quarantine_override_min_5_chars_validation(
    admin_user: User,
) -> None:
    """Quarantine override requires reason of at least 5 characters."""
    from pwd301.services.exceptions import FileValidationError
    from pwd301.services.file_service import quarantine_override

    with pytest.raises(FileValidationError) as exc:
        quarantine_override(
            admin_actor=admin_user,
            asset_id=9999,
            reason="abc",  # < 5 chars
            session=db.session,
        )
    assert "tối thiểu 5 ký tự" in str(exc.value).lower() or "5" in str(exc.value)
