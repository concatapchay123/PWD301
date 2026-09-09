"""Security and IDOR prevention tests for Assessment Builder & Engine (TASK-012)."""

from __future__ import annotations

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    delete_section,
    get_assessment_detail,
    publish_assessment,
    trash_assessment,
    update_assessment,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    AssessmentNotFoundError,
    AssessmentValidationError,
    ForbiddenError,
)
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student user."""
    u = register_user("idor_student@example.com", "Password@123", "Student User")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin user."""
    u = register_user("idor_admin@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Course owned by Instructor Alpha."""
    c = create_course(
        instructor_a,
        {
            "course_code": "COURSE-A",
            "title": "Course Alpha",
            "summary": "Alpha",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def course_b(app: Flask, instructor_b: User) -> Course:
    """Course owned by Instructor Beta."""
    c = create_course(
        instructor_b,
        {
            "course_code": "COURSE-B",
            "title": "Course Beta",
            "summary": "Beta",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def assessment_a(app: Flask, instructor_a: User, course_a: Course) -> Assessment:
    """Draft assessment in Course Alpha."""
    a = create_assessment(
        instructor_a,
        course_a.id,
        {"title": "Alpha Draft Quiz", "assessment_type": "QUIZ"},
    )
    db.session.commit()
    return a


def test_student_cannot_manage_or_view_draft_assessment(
    app: Flask, student_user: User, course_a: Course, assessment_a: Assessment
) -> None:
    """Students cannot create assessments or view draft assessments."""
    # Student cannot create assessment
    with pytest.raises(ForbiddenError):
        create_assessment(
            student_user,
            course_a.id,
            {"title": "Student Quiz", "assessment_type": "QUIZ"},
        )

    # Student cannot view draft assessment (fail-closed 404)
    with pytest.raises(AssessmentNotFoundError):
        get_assessment_detail(student_user, assessment_a.public_id)

    # Student cannot update assessment
    with pytest.raises(ForbiddenError):
        update_assessment(
            student_user,
            assessment_a.public_id,
            {"title": "Hacked Title"},
        )

    # Student cannot publish assessment
    with pytest.raises(ForbiddenError):
        publish_assessment(student_user, assessment_a.public_id)

    # Student cannot trash assessment
    with pytest.raises(ForbiddenError):
        trash_assessment(student_user, assessment_a.public_id)


def test_cross_instructor_idor_blocked(
    app: Flask, instructor_b: User, course_a: Course, assessment_a: Assessment
) -> None:
    """Instructor B cannot access or modify Instructor A's assessment."""
    # Cannot create assessment in course A
    with pytest.raises(ForbiddenError):
        create_assessment(
            instructor_b,
            course_a.id,
            {"title": "Beta in Alpha", "assessment_type": "QUIZ"},
        )

    # Cannot view draft assessment of course A (fail-closed 404)
    with pytest.raises(AssessmentNotFoundError):
        get_assessment_detail(instructor_b, assessment_a.public_id)

    # Cannot update course A's assessment
    with pytest.raises(ForbiddenError):
        update_assessment(
            instructor_b,
            assessment_a.public_id,
            {"title": "Modified by Beta"},
        )

    # Cannot create section in course A's assessment
    with pytest.raises(ForbiddenError):
        create_section(
            instructor_b,
            assessment_a.public_id,
            {"title": "Beta Section", "position": 1},
        )

    # Cannot publish course A's assessment
    with pytest.raises(ForbiddenError):
        publish_assessment(instructor_b, assessment_a.public_id)

    # Cannot trash course A's assessment
    with pytest.raises(ForbiddenError):
        trash_assessment(instructor_b, assessment_a.public_id)


def test_cross_course_question_injection_blocked(
    app: Flask,
    instructor_a: User,
    instructor_b: User,
    course_a: Course,
    course_b: Course,
    assessment_a: Assessment,
) -> None:
    """Instructor A cannot assign questions belonging to Course B into Course A assessment."""
    q_b = create_question(
        instructor_b,
        course_b.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Beta Question Content",
            "default_points": 1.0,
            "choices": [
                {"content": "Yes", "is_correct": True, "position": 1},
                {"content": "No", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
    )
    db.session.commit()

    with pytest.raises(
        AssessmentValidationError, match="Cannot assign question from a different course"
    ):
        assign_question(
            instructor_a,
            assessment_a.public_id,
            {"question_id": str(q_b.public_id)},
        )


def test_admin_can_manage_any_assessment(
    app: Flask, admin_user: User, course_a: Course, assessment_a: Assessment
) -> None:
    """Admins possess superuser privileges to manage any course assessment."""
    # Admin can view draft
    detail = get_assessment_detail(admin_user, assessment_a.public_id)
    assert detail["title"] == "Alpha Draft Quiz"

    # Admin can update
    updated = update_assessment(
        admin_user,
        assessment_a.public_id,
        {"title": "Admin Overridden Title"},
    )
    db.session.commit()
    assert updated.title == "Admin Overridden Title"

    # Admin can add section
    sec = create_section(
        admin_user,
        assessment_a.public_id,
        {"title": "Admin Section", "position": 1},
    )
    db.session.commit()
    assert sec.id is not None

    # Admin can delete section
    deleted = delete_section(admin_user, assessment_a.public_id, sec.id)
    db.session.commit()
    assert deleted is True
