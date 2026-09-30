import json
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, LearningUnit, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.lesson_service import (
    create_learning_unit,
    create_lesson,
    trash_lesson,
    validate_lesson_media_limits,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"inst_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Admin Test")
    return assign_role_to_user(u.id, "ADMIN")


def test_admin_approve_learning_unit_creation_on_published_course(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    """BE-01: Admin approving CREATE_LEARNING_UNIT must actually create the unit in DB."""
    sess = db.session
    course = Course(
        course_code=f"BE01_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE01_{uuid.uuid4().hex[:4]}",
        title="Published Course BE-01",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    # Instructor submits learning unit creation request
    login_web_user(client, instructor_user)
    res = client.post(
        f"/instructor/courses/{course.id}/learning-units",
        json={"title": "Chương mới qua duyệt"},
    )
    assert res.status_code == 202
    data = res.get_json()
    assert data["pending_approval"] is True
    req_id = data["change_request_id"]

    # Admin reviews and approves
    login_web_user(client, admin_user)
    review_res = client.post(
        f"/admin/change-requests/{req_id}/review",
        json={"status": "APPROVED", "reason": "Duyệt tạo chương"},
    )
    assert review_res.status_code == 200

    # Verify unit actually created in DB
    sess.expire_all()
    created_unit = (
        sess.query(LearningUnit)
        .filter(LearningUnit.course_id == course.id, LearningUnit.title == "Chương mới qua duyệt")
        .first()
    )
    assert created_unit is not None, "LearningUnit was NOT created in DB! (Shadowed branch bug BE-01)"


def test_admin_approve_learning_unit_reordering_on_published_course(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    """BE-01: Admin approving REORDER_LEARNING_UNITS must reorder units."""
    sess = db.session
    course = Course(
        course_code=f"BE01B_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE01B_{uuid.uuid4().hex[:4]}",
        title="Draft Course BE-01B",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    u1 = create_learning_unit(instructor_user, course.id, {"title": "Unit 1"}, session=sess)
    u2 = create_learning_unit(instructor_user, course.id, {"title": "Unit 2"}, session=sess)
    course.status = "PUBLISHED"
    sess.commit()

    login_web_user(client, instructor_user)
    res = client.post(
        f"/instructor/courses/{course.id}/learning-units/reorder",
        json={"unit_ids": [str(u2.public_id), str(u1.public_id)]},
    )
    assert res.status_code == 202
    req_id = res.get_json()["change_request_id"]

    login_web_user(client, admin_user)
    review_res = client.post(
        f"/admin/change-requests/{req_id}/review",
        json={"status": "APPROVED", "reason": "Duyệt sắp xếp"},
    )
    assert review_res.status_code == 200

    sess.expire_all()
    refreshed_u1 = sess.query(LearningUnit).filter_by(id=u1.id).one()
    refreshed_u2 = sess.query(LearningUnit).filter_by(id=u2.id).one()
    assert refreshed_u2.position == 1
    assert refreshed_u1.position == 2


def test_create_lesson_ignores_historical_lessons_for_unit_limit(
    app: Flask, instructor_user: User
):
    """BE-02: 10 lessons per unit limit must NOT count HISTORICAL lessons."""
    sess = db.session
    course = Course(
        course_code=f"BE02_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE02_{uuid.uuid4().hex[:4]}",
        title="Course BE-02",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit With Revisions"}, session=sess)
    sess.commit()

    # Create 1 active lesson
    lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={"title": "Active Lesson", "markdown_content": "# Active", "learning_unit_id": str(unit.public_id)},
        session=sess,
    )
    sess.commit()

    # Simulate 10 historical revisions belonging to this same unit
    for i in range(10):
        hist = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title=f"Old Revision {i}",
            markdown_content=f"Old content {i}",
            status="HISTORICAL",
            position=100 + i,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        sess.add(hist)
    sess.commit()

    # Even though there are 1 active + 10 historical = 11 records in this unit,
    # create_lesson should succeed because active count is only 1!
    new_lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={"title": "Second Active Lesson", "markdown_content": "# Active 2", "learning_unit_id": str(unit.public_id)},
        session=sess,
    )
    assert new_lesson is not None
    assert new_lesson.title == "Second Active Lesson"


def test_validate_media_limits_ignores_historical_videos(
    app: Flask, instructor_user: User
):
    """BE-03: 7 videos per unit limit must NOT count videos in HISTORICAL lessons."""
    sess = db.session
    course = Course(
        course_code=f"BE03_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE03_{uuid.uuid4().hex[:4]}",
        title="Course BE-03",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit Videos"}, session=sess)
    sess.commit()

    # Add 4 historical lessons each with 2 videos (total 8 historical videos)
    for i in range(4):
        hist = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title=f"Old Video Lesson {i}",
            markdown_content='<!-- video_urls: ["https://v1.com", "https://v2.com"] -->\nContent',
            status="HISTORICAL",
            position=200 + i,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        sess.add(hist)
    sess.commit()

    # Now validate limits for a new active lesson with 2 videos:
    # It should PASS because the 8 historical videos are excluded!
    validate_lesson_media_limits(
        unit=unit,
        lesson=None,
        markdown_content='<!-- video_urls: ["https://new1.com", "https://new2.com"] -->\nNew content',
    )


def test_create_lesson_max_position_ignores_historical_and_trash(
    app: Flask, instructor_user: User
):
    """BE-04: max_position should only count active lessons, not HISTORICAL or TRASH."""
    sess = db.session
    course = Course(
        course_code=f"BE04_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE04_{uuid.uuid4().hex[:4]}",
        title="Course BE-04",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit BE04"}, session=sess)
    sess.commit()

    l1 = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={"title": "Lesson 1", "markdown_content": "# L1", "learning_unit_id": str(unit.public_id)},
        session=sess,
    )
    sess.commit()

    # Add a historical lesson
    hist = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Hist Lesson",
        markdown_content="hist",
        status="HISTORICAL",
        position=50,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(hist)
    sess.commit()

    # Next created lesson should have position 2, NOT position 3!
    l2 = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={"title": "Lesson 2", "markdown_content": "# L2", "learning_unit_id": str(unit.public_id)},
        session=sess,
    )
    assert l2.position == 2


def test_trash_lesson_recompact_preserves_historical_records(
    app: Flask, instructor_user: User
):
    """BE-05: trash_lesson recompact must not alter position of HISTORICAL lessons."""
    sess = db.session
    course = Course(
        course_code=f"BE05_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE05_{uuid.uuid4().hex[:4]}",
        title="Course BE-05",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit BE05"}, session=sess)
    sess.commit()

    l1 = create_lesson(actor=instructor_user, course_id=course.id, data={"title": "L1", "markdown_content": "# L1", "learning_unit_id": str(unit.public_id)}, session=sess)
    l2 = create_lesson(actor=instructor_user, course_id=course.id, data={"title": "L2", "markdown_content": "# L2", "learning_unit_id": str(unit.public_id)}, session=sess)
    l3 = create_lesson(actor=instructor_user, course_id=course.id, data={"title": "L3", "markdown_content": "# L3", "learning_unit_id": str(unit.public_id)}, session=sess)

    hist = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Hist BE05",
        markdown_content="hist",
        status="HISTORICAL",
        position=999,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(hist)
    sess.commit()

    # Trash lesson 2
    trash_lesson(instructor_user, l2.id, session=sess)
    sess.commit()

    sess.expire_all()
    refreshed_hist = sess.query(Lesson).filter_by(id=hist.id).one()
    refreshed_l1 = sess.query(Lesson).filter_by(id=l1.id).one()
    refreshed_l3 = sess.query(Lesson).filter_by(id=l3.id).one()

    assert refreshed_l1.position == 1
    assert refreshed_l3.position == 2
    assert refreshed_hist.position == 999, "HISTORICAL lesson position was altered during recompact! (BE-05)"


def test_create_lesson_title_fallback_in_route(
    client: FlaskClient, instructor_user: User
):
    """BE-08: create_lesson route should supply fallback title if title is missing."""
    sess = db.session
    course = Course(
        course_code=f"BE08_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE08_{uuid.uuid4().hex[:4]}",
        title="Course BE-08",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    unit = create_learning_unit(instructor_user, course.id, {"title": "Unit BE08"}, session=sess)
    sess.commit()

    login_web_user(client, instructor_user)
    res = client.post(
        f"/instructor/courses/{course.id}/lessons",
        json={"learning_unit_id": str(unit.public_id), "markdown_content": "# Blank Title Test"},
    )
    assert res.status_code == 201, f"Expected 201 with fallback title, got {res.status_code}: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert data["title"] == "Bài giảng mới"


def test_create_lesson_handles_blank_or_undefined_unit_id(
    app: Flask, instructor_user: User
):
    """BE-07: create_lesson should gracefully handle undefined or blank learning_unit_id."""
    sess = db.session
    course = Course(
        course_code=f"BE07_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"BE07_{uuid.uuid4().hex[:4]}",
        title="Course BE-07",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    # Pass "undefined" string
    l1 = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={"title": "Test Undefined Unit", "markdown_content": "# Undefined Unit", "learning_unit_id": "undefined"},
        session=sess,
    )
    assert l1 is not None
    assert l1.learning_unit_id is not None
