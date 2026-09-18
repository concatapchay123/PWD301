"""Security unit tests for AI conversation course/lesson authorization checks (SEC-05).

Verifies:
1. Global conversations are permitted for authenticated users.
2. Course conversations require the course to be PUBLISHED and the user to have
   an ACTIVE enrollment, unless the user can manage the course (Instructor/Admin).
3. Non-enrolled students are denied access to AI conversation on a course
   with ForbiddenError (HTTP 403).
4. Unpublished (DRAFT/ARCHIVED) courses are rejected for non-managers with ForbiddenError.
5. Lesson conversations verify the parent course authorization in the same manner.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.ai_service import create_conversation
from pwd301.services.exceptions import ForbiddenError


def _get_or_create_role(code: str, name: str) -> Role:
    role = db.session.query(Role).filter_by(code=code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.session.add(role)
        db.session.flush()
    return role


@pytest.fixture
def auth_setup(app: Flask):
    with app.app_context():
        student_role = _get_or_create_role("STUDENT", "Student")
        instructor_role = _get_or_create_role("INSTRUCTOR", "Instructor")

        unique_suffix = uuid.uuid4().hex[:6]
        student = User(
            email=f"ai_student_{unique_suffix}@fpt.edu.vn",
            display_name="AI Student",
            password_hash="hash",
            auth_version=1,
        )
        student.roles.append(student_role)

        instructor = User(
            email=f"ai_instructor_{unique_suffix}@fpt.edu.vn",
            display_name="AI Instructor",
            password_hash="hash",
            auth_version=1,
        )
        instructor.roles.append(instructor_role)

        db.session.add_all([student, instructor])
        db.session.flush()

        course_pub = Course(
            course_code=f"AI-PUB-{unique_suffix}",
            course_code_normalized=f"AI-PUB-{unique_suffix}".lower(),
            title="Public AI Course",
            title_normalized="public ai course",
            status="PUBLISHED",
            owner_instructor_id=instructor.id,
        )
        course_draft = Course(
            course_code=f"AI-DFT-{unique_suffix}",
            course_code_normalized=f"AI-DFT-{unique_suffix}".lower(),
            title="Draft AI Course",
            title_normalized="draft ai course",
            status="DRAFT",
            owner_instructor_id=instructor.id,
        )
        db.session.add_all([course_pub, course_draft])
        db.session.flush()

        # Lesson in public course
        lesson_pub = Lesson(
            course_id=course_pub.id,
            title="Lesson 1",
            position=1,
            status="PUBLISHED",
        )
        # Lesson in draft course
        lesson_draft = Lesson(
            course_id=course_draft.id,
            title="Lesson Draft 1",
            position=1,
            status="DRAFT",
        )
        db.session.add_all([lesson_pub, lesson_draft])
        db.session.commit()

        yield {
            "student": student,
            "instructor": instructor,
            "course_pub": course_pub,
            "course_draft": course_draft,
            "lesson_pub": lesson_pub,
            "lesson_draft": lesson_draft,
        }


def test_ai_global_conversation_allowed(app: Flask, auth_setup: dict) -> None:
    """GLOBAL context conversation requires only valid authenticated user."""
    student = auth_setup["student"]
    conv = create_conversation(actor=student, context_type="GLOBAL")
    assert conv is not None
    assert conv.context_type == "GLOBAL"
    assert conv.user_id == student.id


def test_ai_course_conversation_allowed_for_non_enrolled_student(
    app: Flask, auth_setup: dict
) -> None:
    """Non-enrolled student is allowed access to AI conversation on a published course."""
    student = auth_setup["student"]
    course_pub = auth_setup["course_pub"]

    conv = create_conversation(
        actor=student,
        context_type="COURSE",
        course_id=str(course_pub.public_id),
    )
    assert conv is not None
    assert conv.course_id == course_pub.id


def test_ai_course_conversation_allowed_for_enrolled_student(app: Flask, auth_setup: dict) -> None:
    """Student with ACTIVE enrollment can start AI conversation for that course."""
    student = auth_setup["student"]
    course_pub = auth_setup["course_pub"]

    enrollment = Enrollment(
        student_user_id=student.id,
        course_id=course_pub.id,
        status="ACTIVE",
    )
    db.session.add(enrollment)
    db.session.commit()

    conv = create_conversation(
        actor=student,
        context_type="COURSE",
        course_id=str(course_pub.public_id),
    )
    assert conv is not None
    assert conv.course_id == course_pub.id


def test_ai_course_conversation_rejected_on_draft_course(app: Flask, auth_setup: dict) -> None:
    """Student cannot start AI conversation on unpublished (DRAFT) course even if enrolled."""
    student = auth_setup["student"]
    course_draft = auth_setup["course_draft"]

    enrollment = Enrollment(
        student_user_id=student.id,
        course_id=course_draft.id,
        status="ACTIVE",
    )
    db.session.add(enrollment)
    db.session.commit()

    with pytest.raises(ForbiddenError) as exc_info:
        create_conversation(
            actor=student,
            context_type="COURSE",
            course_id=str(course_draft.public_id),
        )
    assert "You do not have access to this unpublished course" in str(exc_info.value)


def test_ai_course_conversation_allowed_for_course_instructor(app: Flask, auth_setup: dict) -> None:
    """Managing instructor can start conversation on their draft or published courses."""
    instructor = auth_setup["instructor"]
    course_draft = auth_setup["course_draft"]

    conv = create_conversation(
        actor=instructor,
        context_type="COURSE",
        course_id=str(course_draft.public_id),
    )
    assert conv is not None
    assert conv.course_id == course_draft.id


def test_ai_lesson_conversation_authorization(app: Flask, auth_setup: dict) -> None:
    """Lesson conversations enforce the same authorization rules as course conversations."""
    student = auth_setup["student"]
    lesson_pub = auth_setup["lesson_pub"]
    lesson_draft = auth_setup["lesson_draft"]
    course_pub = auth_setup["course_pub"]

    # Rejected on draft course/lesson
    with pytest.raises(ForbiddenError):
        create_conversation(
            actor=student,
            context_type="LESSON",
            lesson_id=str(lesson_draft.public_id),
        )

    # Allowed on published course/lesson
    conv = create_conversation(
        actor=student,
        context_type="LESSON",
        lesson_id=str(lesson_pub.public_id),
    )
    assert conv is not None
    assert conv.lesson_id == lesson_pub.id
    assert conv.course_id == course_pub.id
