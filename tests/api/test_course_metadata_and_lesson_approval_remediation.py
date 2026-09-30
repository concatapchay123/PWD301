"""Comprehensive tests for course metadata review, lesson approval staging,
admin diff payload, and index collision prevention.
"""

from __future__ import annotations

import json
import uuid

from flask import Flask
from flask.testing import FlaskClient
import pytest
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, LearningUnit, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.user_service import assign_role_to_user, register_user
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.lesson_service import (
    approve_course_change_request,
    create_learning_unit,
    create_lesson,
    create_lesson_change_request,
    discard_lesson_working_draft,
)
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
    u = register_user(
        f"remed_inst_{uuid.uuid4().hex[:6]}@example.com",
        "StrongPassword123!",
        "Remediation Instructor",
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user(
        f"remed_admin_{uuid.uuid4().hex[:6]}@example.com",
        "StrongPassword123!",
        "Remediation Admin",
    )
    return assign_role_to_user(u.id, "ADMIN")


def test_published_course_metadata_update_creates_change_request(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Published course metadata edits must return 202 pending_approval and not mutate DB directly."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}",
            "title": "Original Course Title",
            "description": "Original course description.",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    create_lesson(instructor_user, course.id, {"title": "Lesson 1", "learning_unit_id": str(unit.public_id), "markdown_content": "Content"}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp = client.put(
        f"/instructor/courses/{course.public_id}",
        json={"title": "Updated Proposed Title", "description": "Updated proposed description."},
    )

    assert resp.status_code == 202
    body = resp.get_json()
    assert body["status"] == "pending_approval"
    assert "change_request_id" in body

    sess.expire_all()
    reloaded_course = sess.get(Course, course.id)
    assert reloaded_course.title == "Original Course Title"

    req = sess.get(CourseChangeRequest, body["change_request_id"])
    assert req is not None
    assert req.change_type == "COURSE_METADATA"
    assert req.status == "PENDING"
    payload = json.loads(req.proposed_payload_json)
    assert payload["title"] == "Updated Proposed Title"


def test_admin_change_requests_diff_payload_and_original_data(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Admin change requests list provides original_data and proposed_payload for comparison."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}",
            "title": "Course Diff Test",
            "description": "Original description for diff.",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    create_lesson(instructor_user, course.id, {"title": "Lesson 1", "learning_unit_id": str(unit.public_id), "markdown_content": "Content"}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp_edit = client.put(
        f"/instructor/courses/{course.public_id}",
        json={"title": "Proposed New Diff Title"},
    )
    assert resp_edit.status_code == 202

    login_web_user(client, admin_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "ADMIN"

    resp_admin = client.get("/admin/change-requests")
    assert resp_admin.status_code == 200
    items = resp_admin.get_json().get("items", [])
    course_req = next((item for item in items if str(item.get("course_id")) == str(course.public_id)), None)
    assert course_req is not None
    assert course_req["original_data"]["title"] == "Course Diff Test"
    assert course_req["proposed_payload"]["title"] == "Proposed New Diff Title"


def test_admin_approves_course_metadata_change_request(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Approving course metadata change request applies updates to course."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}",
            "title": "Before Approval Title",
            "description": "Before description.",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    create_lesson(instructor_user, course.id, {"title": "Lesson 1", "learning_unit_id": str(unit.public_id), "markdown_content": "Content"}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp_edit = client.put(
        f"/instructor/courses/{course.public_id}",
        json={"title": "After Approval Title", "description": "After description."},
    )
    change_req_id = resp_edit.get_json()["change_request_id"]

    login_web_user(client, admin_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "ADMIN"

    resp_approve = client.post(
        f"/admin/change-requests/{change_req_id}/review",
        json={"decision": "APPROVED", "reason": "Looks great, approved."},
    )
    assert resp_approve.status_code == 200

    sess.expire_all()
    reloaded_course = sess.get(Course, course.id)
    assert reloaded_course.title == "After Approval Title"
    assert reloaded_course.description == "After description."


def test_published_course_create_lesson_approval_and_order_shift(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Creating a lesson in a published course stages request and shifts positions without collisions."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}",
            "title": "Lesson Shift Course",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    l1 = create_lesson(instructor_user, course.id, {"title": "Existing Lesson 1", "learning_unit_id": str(unit.public_id), "markdown_content": "L1", "position": 1}, session=sess)
    l2 = create_lesson(instructor_user, course.id, {"title": "Existing Lesson 2", "learning_unit_id": str(unit.public_id), "markdown_content": "L2", "position": 2}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp_create = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Newly Inserted Lesson at Pos 1",
            "learning_unit_id": str(unit.public_id),
            "markdown_content": "New content",
            "position": 1,
        },
    )
    assert resp_create.status_code == 202
    req_id = resp_create.get_json()["change_request_id"]

    login_web_user(client, admin_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "ADMIN"

    resp_approve = client.post(
        f"/admin/change-requests/{req_id}/review",
        json={"decision": "APPROVED"},
    )
    assert resp_approve.status_code == 200

    sess.expire_all()
    active_lessons = (
        sess.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )
    assert len(active_lessons) == 3
    assert active_lessons[0].title == "Newly Inserted Lesson at Pos 1"
    assert active_lessons[0].position == 1
    assert active_lessons[1].title == "Existing Lesson 1"
    assert active_lessons[1].position == 2
    assert active_lessons[2].title == "Existing Lesson 2"
    assert active_lessons[2].position == 3


def test_published_course_lesson_autosave_deduplication(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Repeated autosaves update the existing pending request without creating duplicates."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {"course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}", "title": "Autosave Course"},
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    l1 = create_lesson(instructor_user, course.id, {"title": "L1", "learning_unit_id": str(unit.public_id), "markdown_content": "Base content"}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    req1, _ = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={"target_id": l1.id, "title": "L1 Autosave 1", "markdown_content": "Content v1"},
        session=sess,
    )
    req2, _ = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={"target_id": l1.id, "title": "L1 Autosave 2", "markdown_content": "Content v2"},
        session=sess,
    )
    sess.commit()

    assert req1.id == req2.id
    total_pending = (
        sess.query(CourseChangeRequest)
        .filter_by(course_id=course.id, status="PENDING")
        .count()
    )
    assert total_pending == 1
    stored_payload = json.loads(req2.proposed_payload_json)
    assert stored_payload["title"] == "L1 Autosave 2"


def test_discard_lesson_working_draft_with_target_id(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Discarding a lesson working draft by lesson_id cancels pending request cleanly."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {"course_code": f"CS-REMED-{uuid.uuid4().hex[:4].upper()}", "title": "Discard Draft Course"},
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    l1 = create_lesson(instructor_user, course.id, {"title": "L1", "learning_unit_id": str(unit.public_id), "markdown_content": "Original Content"}, session=sess)
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    course = change_course_status(admin_user, course.id, "APPROVED", session=sess)
    course = change_course_status(instructor_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    req, _ = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={"target_id": l1.id, "title": "L1 Staged Draft", "markdown_content": "Staged Content"},
        session=sess,
    )
    sess.commit()
    assert req.status == "PENDING"

    discard_lesson_working_draft(instructor_user, l1.id, session=sess)
    sess.commit()

    sess.expire_all()
    reloaded_req = sess.get(CourseChangeRequest, req.id)
    assert reloaded_req.status == "CANCELLED"
    assert "Discarded by instructor" in (reloaded_req.review_reason or "")
