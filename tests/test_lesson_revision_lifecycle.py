"""Tests for Lesson Revisioning, Working Draft Continuity, and Graceful In-Flight Progress."""

from __future__ import annotations

import json
import uuid
import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Enrollment, Lesson, LessonProgress
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import LessonStateViolationError
from pwd301.services.lesson_service import (
    approve_course_change_request,
    create_learning_unit,
    create_lesson,
    create_lesson_change_request,
    discard_lesson_working_draft,
    get_lesson_detail,
    get_lesson_detail_with_draft,
    opt_in_newer_lesson_revision,
    record_lesson_progress,
    reject_course_change_request,
)
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
    unique_suffix = uuid.uuid4().hex[:6]
    user = register_user(
        email=f"inst_{unique_suffix}@pwd301.local",
        password="Password123!",
        display_name="Instructor Alice",
        session=db.session,
    )
    assign_role_to_user(user.id, "INSTRUCTOR", session=db.session)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique_suffix = uuid.uuid4().hex[:6]
    user = register_user(
        email=f"admin_{unique_suffix}@pwd301.local",
        password="Password123!",
        display_name="Admin Bob",
        session=db.session,
    )
    assign_role_to_user(user.id, "ADMIN", session=db.session)
    db.session.commit()
    return user


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique_suffix = uuid.uuid4().hex[:6]
    user = register_user(
        email=f"student_{unique_suffix}@pwd301.local",
        password="Password123!",
        display_name="Student Charlie",
        session=db.session,
    )
    assign_role_to_user(user.id, "STUDENT", session=db.session)
    db.session.commit()
    return user


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> tuple[Course, Lesson]:
    unique_suffix = uuid.uuid4().hex[:6]
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"REV{unique_suffix.upper()}",
            "title": f"Revision Lifecycle Test Course {unique_suffix}",
            "description": "Testing lesson revisions and draft continuity",
        },
        session=db.session,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Chương 1"}, session=db.session)
    lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Bài 1: Khởi động",
            "learning_unit_id": str(unit.public_id),
            "markdown_content": "# Bài 1\nNội dung ban đầu của bài 1.",
            "status": "PUBLISHED",
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8,
        },
        session=db.session,
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=db.session)
    change_course_status(admin_user, course.id, "APPROVED", session=db.session)
    change_course_status(admin_user, course.id, "PUBLISHED", session=db.session)
    db.session.commit()
    return course, lesson


def test_working_draft_continuity_after_rejection(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """When admin rejects an edit, the proposal is preserved as an Active Working Draft."""
    course, lesson = published_course

    # Instructor submits edit via CourseChangeRequest
    req, staged_lesson = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Bản sửa)",
            "summary": "Tóm tắt mới",
            "markdown_content": "# Bài 1 Sửa\nNội dung 3000 từ giảng viên đã soạn.",
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "position": lesson.position,
        },
        session=db.session,
    )

    # Admin rejects change request
    reject_reason = "Video chưa có bản quyền, yêu cầu thay video trường."
    reject_course_change_request(
        actor=admin_user,
        change_request_id=req.id,
        review_reason=reject_reason,
        session=db.session,
    )

    # 1. Lesson itself remains PUBLISHED and original content intact
    assert lesson.status == "PUBLISHED"
    assert "Nội dung ban đầu" in lesson.markdown_content

    # 2. Instructor loads lesson with working draft
    les, draft_info = get_lesson_detail_with_draft(instructor_user, lesson.id, session=db.session)
    assert les.id == lesson.id
    assert draft_info is not None
    assert draft_info["status"] == "REJECTED"
    assert draft_info["review_reason"] == reject_reason
    assert "3000 từ giảng viên đã soạn" in draft_info["payload"]["markdown_content"]

    # 3. Instructor discards working draft
    discarded = discard_lesson_working_draft(instructor_user, lesson.id, session=db.session)
    assert discarded is True

    # 4. Working draft is now cleared
    _, draft_info_after = get_lesson_detail_with_draft(instructor_user, lesson.id, session=db.session)
    assert draft_info_after is None


def test_in_flight_student_progress_on_historical_lesson(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """An in-flight student can continue recording heartbeat progress on a HISTORICAL lesson."""
    course, lesson_v1 = published_course
    enroll_student(actor=admin_user, student_id=student_user.id, course_id=course.id, session=db.session)
    db.session.commit()

    # Student starts learning lesson_v1 (records first ping)
    progress_v1 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson_v1.id,
        seconds_increment=10,
        view_fraction=0.5,
        session=db.session,
    )
    assert progress_v1.seconds_spent == 10

    # Admin approves a new lesson revision (promotes staged lesson, v1 becomes HISTORICAL)
    req, staged_v2 = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Revision 2)",
            "summary": "Tóm tắt v2",
            "markdown_content": "# Bài 1 v2\nNội dung v2 mới nhất.",
            "learning_unit_id": str(lesson_v1.learning_unit.public_id),
            "position": lesson_v1.position,
        },
        session=db.session,
    )
    approve_course_change_request(
        actor=admin_user,
        change_request_id=req.id,
        review_reason="Đã duyệt bản sửa đổi",
        session=db.session,
    )

    db.session.expire_all()
    assert lesson_v1.status == "HISTORICAL"
    assert staged_v2.status == "PUBLISHED"
    assert staged_v2.revision_no == 2
    assert staged_v2.previous_lesson_id == lesson_v1.id

    # In-flight student continues learning lesson_v1: PING SUCCEEDS!
    updated_progress = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson_v1.id,
        seconds_increment=15,
        view_fraction=0.9,
        session=db.session,
    )
    assert updated_progress.seconds_spent == 25
    assert float(updated_progress.max_view_fraction) == 0.9

    # Another student who NEVER learned lesson_v1 cannot start a HISTORICAL lesson
    other_student = register_user(
        email=f"other_{uuid.uuid4().hex[:6]}@pwd301.local",
        password="Password123!",
        display_name="Other Student",
        session=db.session,
    )
    assign_role_to_user(other_student.id, "STUDENT", session=db.session)
    enroll_student(actor=admin_user, student_id=other_student.id, course_id=course.id, session=db.session)
    db.session.commit()

    with pytest.raises(LessonStateViolationError, match="historical"):
        record_lesson_progress(
            actor=other_student,
            lesson_id=lesson_v1.id,
            seconds_increment=10,
            view_fraction=0.5,
            session=db.session,
        )


def test_student_opt_in_with_carry_over(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """When a student opts in to a newer revision, completion status is carried over."""
    course, lesson_v1 = published_course
    enroll_student(actor=admin_user, student_id=student_user.id, course_id=course.id, session=db.session)
    db.session.commit()

    # Student completes lesson_v1
    progress_v1 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson_v1.id,
        seconds_increment=35,
        view_fraction=1.0,
        session=db.session,
    )
    assert progress_v1.completed_at is not None

    # Promote revision 2
    req, staged_v2 = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Revision 2)",
            "summary": "Tóm tắt v2",
            "markdown_content": "# Bài 1 v2\nNội dung v2 mới nhất.",
            "learning_unit_id": str(lesson_v1.learning_unit.public_id),
            "position": lesson_v1.position,
        },
        session=db.session,
    )
    approve_course_change_request(
        actor=admin_user,
        change_request_id=req.id,
        review_reason="Đã duyệt",
        session=db.session,
    )
    db.session.commit()

    # Student opts in to revision 2
    latest_les, target_prg = opt_in_newer_lesson_revision(
        actor=student_user,
        lesson_id=lesson_v1.id,
        session=db.session,
    )
    assert latest_les.id == staged_v2.id
    assert latest_les.revision_no == 2
    # Completion is carried over (monotonic invariant)!
    assert target_prg.completed_at == progress_v1.completed_at
    assert target_prg.acknowledged_revision_no == 2


def test_instructor_and_student_routes_for_revisions(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    student_user: User,
    published_course: tuple[Course, Lesson],
) -> None:
    """Test REST API routes for working drafts and student opt-in."""
    course, lesson = published_course
    enroll_student(actor=admin_user, student_id=student_user.id, course_id=course.id, session=db.session)
    db.session.commit()

    # 1. Create a rejected change request
    req, _ = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Sửa lại)",
            "markdown_content": "# Nội dung bản nháp",
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "position": lesson.position,
        },
        session=db.session,
    )
    reject_course_change_request(
        actor=admin_user,
        change_request_id=req.id,
        review_reason="Cần chỉnh lại phần mở bài.",
        session=db.session,
    )

    # 2. Instructor calls GET /lessons/<id>
    login_web_user(client, instructor_user)
    resp = client.get(f"/instructor/lessons/{lesson.public_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["working_draft"] is not None
    assert data["working_draft"]["review_reason"] == "Cần chỉnh lại phần mở bài."
    assert "Nội dung bản nháp" in data["working_draft"]["payload"]["markdown_content"]

    # 3. Instructor calls discard draft
    discard_resp = client.post(f"/instructor/lessons/{lesson.public_id}/draft/discard")
    assert discard_resp.status_code == 200
    assert discard_resp.get_json()["discarded"] is True

    # Check that draft is now gone
    resp_after = client.get(f"/instructor/lessons/{lesson.public_id}")
    assert resp_after.get_json()["working_draft"] is None

    # 4. Promote a new revision and test student opt-in route
    req2, staged_v2 = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Revision 2)",
            "markdown_content": "# Bài 1 v2",
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "position": lesson.position,
        },
        session=db.session,
    )
    approve_course_change_request(
        actor=admin_user,
        change_request_id=req2.id,
        review_reason="Đã duyệt v2",
        session=db.session,
    )
    db.session.commit()

    login_web_user(client, student_user)
    optin_resp = client.post(f"/student/lessons/{lesson.public_id}/opt-in")
    assert optin_resp.status_code == 200
    optin_data = optin_resp.get_json()
    assert optin_data["success"] is True
    assert optin_data["lesson"]["revision_no"] == 2
