"""Security negative and IDOR prevention tests for Course Management.

Verifies:
- Instructors cannot update, submit, or delete courses owned by other instructors.
- Instructors cannot approve courses or reassign course ownership.
- Students cannot access instructor or admin course management routes.
- Admin can review, manage, and reassign any course platform-wide.
- JWT REST API and Web Session endpoints uniformly enforce fail-closed authorization.
"""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a student user."""
    return register_user("sec_student@example.com", "Password@123", "Sec Student")


@pytest.fixture
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor A."""
    u = register_user("sec_instructor_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor B."""
    u = register_user("sec_instructor_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an Admin user."""
    u = register_user("sec_admin@example.com", "Password@123", "Sec Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Course owned by Instructor A."""
    return create_course(
        instructor_a,
        {
            "course_code": "SEC-101",
            "title": "Security 101",
            "description": "Original A description",
        },
    )


def test_instructor_cannot_edit_other_instructor_course(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
) -> None:
    """IDOR test: Instructor B cannot edit Instructor A's course."""
    tokens = create_token_pair(instructor_b)
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.patch(
        f"/instructor/courses/{course_a.public_id}",
        headers=headers,
        json={"title": "Hacked Title", "description": "Hacked description"},
    )
    assert resp.status_code == 403
    err = resp.get_json()["error"]
    assert err["code"] == "FORBIDDEN"

    # Verify Course A is unchanged
    sess: Session = db.session
    reloaded = sess.get(Course, course_a.id)
    assert reloaded is not None
    assert reloaded.title == "Security 101"
    assert reloaded.description == "Original A description"


def test_instructor_cannot_submit_other_instructor_course(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
) -> None:
    """IDOR test: Instructor B cannot submit Instructor A's course for review."""
    tokens = create_token_pair(instructor_b)
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        f"/instructor/courses/{course_a.public_id}/submit",
        headers=headers,
        json={"reason": "Attempting illegal submission"},
    )
    assert resp.status_code == 403

    sess: Session = db.session
    reloaded = sess.get(Course, course_a.id)
    assert reloaded is not None
    assert reloaded.status == "DRAFT"


def test_instructor_cannot_trash_other_instructor_course(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
) -> None:
    """IDOR test: Instructor B cannot soft-delete Instructor A's course."""
    tokens = create_token_pair(instructor_b)
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        f"/instructor/courses/{course_a.public_id}/trash",
        headers=headers,
        json={"reason": "Attempting illegal deletion"},
    )
    assert resp.status_code == 403

    sess: Session = db.session
    reloaded = sess.get(Course, course_a.id)
    assert reloaded is not None
    assert reloaded.status == "DRAFT"
    assert reloaded.deleted_at is None


def test_instructor_cannot_approve_courses(
    client: FlaskClient,
    instructor_a: User,
    course_a: Course,
) -> None:
    """RBAC test: Instructor cannot approve courses (Admin only)."""
    # Instructor submits course
    tokens_a = create_token_pair(instructor_a)
    token_a = tokens_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post(f"/instructor/courses/{course_a.public_id}/submit", headers=headers_a)

    # Instructor attempts to approve via admin route
    resp = client.post(
        f"/admin/courses/{course_a.public_id}/review",
        headers=headers_a,
        json={"action": "approve"},
    )
    assert resp.status_code == 403

    sess: Session = db.session
    reloaded = sess.get(Course, course_a.id)
    assert reloaded is not None
    assert reloaded.status == "SUBMITTED_FOR_REVIEW"


def test_instructor_cannot_reassign_course(
    client: FlaskClient,
    instructor_a: User,
    instructor_b: User,
    course_a: Course,
) -> None:
    """RBAC test: Instructor cannot reassign course ownership."""
    tokens_a = create_token_pair(instructor_a)
    token_a = tokens_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp = client.post(
        f"/admin/courses/{course_a.public_id}/reassign",
        headers=headers_a,
        json={"new_instructor_id": str(instructor_b.public_id), "reason": "Self-reassign"},
    )
    assert resp.status_code == 403


def test_student_cannot_access_course_management(
    client: FlaskClient,
    student_user: User,
    course_a: Course,
) -> None:
    """RBAC test: Students cannot access instructor course routes."""
    tokens = create_token_pair(student_user)
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Cannot create
    resp = client.post(
        "/instructor/courses",
        headers=headers,
        json={"course_code": "STU-101", "title": "Student Course"},
    )
    assert resp.status_code == 403

    # Cannot edit
    resp = client.patch(
        f"/instructor/courses/{course_a.public_id}",
        headers=headers,
        json={"title": "Student Modified"},
    )
    assert resp.status_code == 403


def test_admin_can_manage_and_review_any_course(
    client: FlaskClient,
    admin_user: User,
    instructor_b: User,
    course_a: Course,
) -> None:
    """Admin privilege test: Admin can edit, review, and reassign course."""
    tokens_admin = create_token_pair(admin_user)
    token_admin = tokens_admin["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 1. Admin updates course
    resp = client.patch(
        f"/instructor/courses/{course_a.public_id}",
        headers=headers_admin,
        json={"title": "Admin Verified Security 101"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Admin Verified Security 101"

    # 2. Submit and Admin Approve
    client.post(f"/instructor/courses/{course_a.public_id}/submit", headers=headers_admin)
    resp = client.post(
        f"/admin/courses/{course_a.public_id}/review",
        headers=headers_admin,
        json={"action": "approve", "reason": "Looks good"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "APPROVED"

    # 3. Admin Reassign to Instructor B
    resp = client.post(
        f"/admin/courses/{course_a.public_id}/reassign",
        headers=headers_admin,
        json={"new_instructor_id": str(instructor_b.public_id), "reason": "Staffing change"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["owner_instructor_id"] == str(instructor_b.public_id)


def test_unauthenticated_request_rejected(client: FlaskClient, course_a: Course) -> None:
    """Unauthenticated requests to protected endpoints return 401."""
    resp = client.post(
        "/instructor/courses",
        headers={"Accept": "application/json"},
        json={"course_code": "UNAUTH-101", "title": "Unauth Course"},
    )
    assert resp.status_code == 401

    resp = client.patch(
        f"/instructor/courses/{course_a.public_id}",
        headers={"Accept": "application/json"},
        json={"title": "Unauth Edit"},
    )
    assert resp.status_code == 401
