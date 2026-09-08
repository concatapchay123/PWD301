"""Security negative and IDOR prevention tests for Enrollment and Prerequisites."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
    get_course_enrollments,
    get_student_enrollments,
    leave_course,
)
from pwd301.services.exceptions import (
    AccountNotActiveError,
    ForbiddenError,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import (
    assign_role_to_user,
    register_user,
    suspend_user,
)


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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Alpha."""
    u = register_user("idor_inst_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Beta."""
    u = register_user("idor_inst_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student Alpha."""
    u = register_user("idor_stud_a@example.com", "Password@123", "Student Alpha")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student Beta."""
    u = register_user("idor_stud_b@example.com", "Password@123", "Student Beta")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create System Administrator."""
    u = register_user("idor_admin_enr@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User, admin_user: User) -> Course:
    """Published course owned by Instructor A."""
    course = create_course(
        instructor_a,
        {
            "course_code": "SEC-ENR-A",
            "title": "Security Course Alpha",
            "description": "Owned by Alpha",
        },
    )
    course = change_course_status(instructor_a, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(admin_user, course.id, "APPROVED")
    course = change_course_status(instructor_a, course.id, "PUBLISHED")
    db.session.commit()
    return course


@pytest.fixture
def course_b(app: Flask, instructor_b: User, admin_user: User) -> Course:
    """Published course owned by Instructor B."""
    course = create_course(
        instructor_b,
        {
            "course_code": "SEC-ENR-B",
            "title": "Security Course Beta",
            "description": "Owned by Beta",
        },
    )
    course = change_course_status(instructor_b, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(admin_user, course.id, "APPROVED")
    course = change_course_status(instructor_b, course.id, "PUBLISHED")
    db.session.commit()
    return course


def test_student_cannot_leave_another_students_enrollment(
    app: Flask,
    course_a: Course,
    student_a: User,
    student_b: User,
) -> None:
    """IDOR: Student A cannot withdraw Student B from a course."""
    sess = db.session
    enroll_student(actor=student_b, course_id=course_a.id, session=sess)
    sess.commit()

    with pytest.raises(ForbiddenError, match="do not have permission to withdraw this student"):
        leave_course(
            actor=student_a,
            course_id=course_a.id,
            student_id=student_b.id,
            session=sess,
        )


def test_student_cannot_view_another_students_enrollments(
    app: Flask,
    course_a: Course,
    student_a: User,
    student_b: User,
) -> None:
    """IDOR: Student A cannot view private enrollment list of Student B."""
    sess = db.session
    enroll_student(actor=student_b, course_id=course_a.id, session=sess)
    sess.commit()

    with pytest.raises(ForbiddenError, match="not authorized to view this student's enrollments"):
        get_student_enrollments(
            actor=student_a,
            student_id=student_b.id,
            session=sess,
        )


def test_instructor_b_cannot_add_prerequisite_to_instructor_a_course(
    client: FlaskClient,
    course_a: Course,
    course_b: Course,
    instructor_b: User,
) -> None:
    """IDOR: Instructor B cannot mutate prerequisites on Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/instructor/courses/{course_a.public_id}/prerequisites",
        headers=headers,
        json={"prerequisite_course_id": str(course_b.public_id)},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_remove_prerequisite_from_instructor_a_course(
    client: FlaskClient,
    course_a: Course,
    course_b: Course,
    instructor_a: User,
    instructor_b: User,
) -> None:
    """IDOR: Instructor B cannot delete a prerequisite from Course A."""
    sess = db.session
    add_course_prerequisite(instructor_a, course_a.id, course_b.id, session=sess)
    sess.commit()

    tokens = create_token_pair(instructor_b)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    resp = client.delete(
        f"/instructor/courses/{course_a.public_id}/prerequisites/{course_b.public_id}",
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_view_students_of_instructor_a_course(
    client: FlaskClient,
    course_a: Course,
    instructor_b: User,
) -> None:
    """IDOR: Instructor B cannot view student roster of Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    resp = client.get(
        f"/instructor/courses/{course_a.public_id}/students",
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_suspended_account_cannot_enroll(
    app: Flask,
    course_a: Course,
    student_a: User,
    admin_user: User,
) -> None:
    """Security: Suspended user cannot enroll in any course."""
    sess = db.session
    suspend_user(student_a.id, reason="Policy violation", session=sess)
    sess.commit()

    with pytest.raises(AccountNotActiveError, match="Inactive or suspended accounts cannot enroll"):
        enroll_student(actor=student_a, course_id=course_a.id, session=sess)


def test_admin_has_platform_wide_oversight(
    app: Flask,
    course_a: Course,
    course_b: Course,
    student_a: User,
    admin_user: User,
) -> None:
    """Security verification: Admin can oversee enrollments, prerequisites, and rosters."""
    sess = db.session
    # Admin enrolls student
    enrollment = enroll_student(
        actor=admin_user,
        course_id=course_a.id,
        student_id=student_a.id,
        session=sess,
    )
    sess.commit()
    assert enrollment.status == "ACTIVE"

    # Admin adds prerequisite
    link = add_course_prerequisite(
        actor=admin_user,
        course_id=course_a.id,
        prerequisite_course_id=course_b.id,
        session=sess,
    )
    sess.commit()
    assert link is not None

    # Admin views course enrollments
    items, total = get_course_enrollments(
        actor=admin_user,
        course_id=course_a.id,
        session=sess,
    )
    assert total == 1

    # Admin views student enrollments
    stud_items = get_student_enrollments(
        actor=admin_user,
        student_id=student_a.id,
        session=sess,
    )
    assert len(stud_items) == 1
