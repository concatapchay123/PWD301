"""Tests for Lesson Video Delivery, Resource Inheritance across Revisions, and History Filtering."""

from __future__ import annotations

import io
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream
from pwd301.services.lesson_service import (
    approve_course_change_request,
    create_learning_unit,
    create_lesson,
    create_lesson_change_request,
    queue_lesson_resource_change,
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
    unique = uuid.uuid4().hex[:6]
    u = register_user(f"inst_{unique}@pwd301.local", "Password123!", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique = uuid.uuid4().hex[:6]
    u = register_user(f"admin_{unique}@pwd301.local", "Password123!", "Admin Test")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique = uuid.uuid4().hex[:6]
    u = register_user(f"student_{unique}@pwd301.local", "Password123!", "Student Test")
    return assign_role_to_user(u.id, "STUDENT")


def test_approved_lesson_revision_inherits_resources(
    app: Flask, instructor_user: User, admin_user: User, student_user: User
) -> None:
    """When a published lesson has video and is updated via change request,

    the new published revision must inherit the video resource so students can view it.
    """
    sess = db.session
    unique = uuid.uuid4().hex[:6]
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"VID_{unique.upper()}",
            "title": f"Video Delivery Test Course {unique}",
            "description": "Testing video delivery across lesson revisions",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Chương 1"}, session=sess)
    lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Bài 1: Khởi động",
            "learning_unit_id": str(unit.public_id),
            "markdown_content": "# Bài 1 ban đầu",
            "status": "PUBLISHED",
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8,
        },
        session=sess,
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course.id, "APPROVED", session=sess)
    change_course_status(admin_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    # Attach video file asset to lesson
    video_asset = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=io.BytesIO(b"fake video mp4 stream"),
        filename="lecture_video.mp4",
        content_type="video/mp4",
        asset_type="RESOURCE",
        title="Video bài giảng",
        session=sess,
    )
    video_asset.status = "ACTIVE"
    for r_rev in video_asset.revisions:
        r_rev.status = "ACTIVE"
    sess.flush()

    res = attach_resource_to_lesson(
        actor=instructor_user,
        lesson_id=lesson.id,
        asset_id=video_asset.id,
        label="Video bài giảng",
        session=sess,
    )
    sess.commit()

    assert len(lesson.resources) == 1

    # Instructor submits lesson edit via CourseChangeRequest
    req, staged_lesson = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1: Khởi động (Bản cập nhật)",
            "summary": "Tóm tắt mới",
            "markdown_content": "# Bài 1 Cập nhật nội dung mới",
            "learning_unit_id": str(unit.public_id),
            "position": lesson.position,
            "target_id": lesson.id,
        },
        session=sess,
    )
    sess.commit()

    # Staged lesson should already inherit the video resource
    assert len(staged_lesson.resources) >= 1

    # Admin approves change request
    approved_req = approve_course_change_request(
        actor=admin_user,
        change_request_id=req.id,
        review_reason="Duyệt bản cập nhật",
        session=sess,
    )
    sess.commit()

    # Verify lesson 1 is now HISTORICAL and staged lesson is PUBLISHED
    sess.refresh(lesson)
    sess.refresh(staged_lesson)
    assert lesson.status == "HISTORICAL"
    assert staged_lesson.status == "PUBLISHED"

    # Crucial assertion: the newly published revision MUST have the video resource!
    assert len(staged_lesson.resources) == 1
    assert staged_lesson.resources[0].file_asset_id == video_asset.id

    # Verify student serialization returns the video url
    from pwd301.blueprints.student.routes import _serialize_student_lesson

    enroll_student(student_user, course.id, session=sess)
    sess.commit()

    serialized = _serialize_student_lesson(staged_lesson, None)
    assert serialized["video_url"] is not None
    assert f"/student/files/{video_asset.public_id}/download" in serialized["video_url"]
    assert len(serialized["video_urls"]) >= 1


def test_resource_change_request_attaches_to_active_published_lesson_when_target_historical(
    client: FlaskClient, app: Flask, instructor_user: User, admin_user: User
) -> None:
    """If an instructor uploaded a video to a lesson that was subsequently updated to a newer

    PUBLISHED revision before the video change request was reviewed, approving the video request
    must attach the video to the active PUBLISHED revision.
    """
    sess = db.session
    unique = uuid.uuid4().hex[:6]
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"RCE_{unique.upper()}",
            "title": f"Resource Race Condition Test {unique}",
            "description": "Testing race condition between edit and resource attach",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Chương 1"}, session=sess)
    lesson1 = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Bài 1",
            "learning_unit_id": str(unit.public_id),
            "markdown_content": "# Bài 1",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course.id, "APPROVED", session=sess)
    change_course_status(admin_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    # Upload video asset and queue resource change on lesson1
    video_asset = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=io.BytesIO(b"fake video mp4 stream"),
        filename="demo.mp4",
        content_type="video/mp4",
        asset_type="RESOURCE",
        title="Video demo",
        session=sess,
    )
    video_asset.status = "ACTIVE"
    for r_rev in video_asset.revisions:
        r_rev.status = "ACTIVE"
    sess.flush()

    res_req = queue_lesson_resource_change(
        instructor_user, course, lesson1, "ATTACH", asset=video_asset, label="Video demo", session=sess
    )
    sess.commit()

    # Now an edit is created and approved BEFORE res_req is approved
    edit_req, lesson2 = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1 (Cập nhật)",
            "markdown_content": "# Bài 1 Cập nhật",
            "learning_unit_id": str(unit.public_id),
            "position": lesson1.position,
            "target_id": lesson1.id,
        },
        session=sess,
    )
    sess.commit()
    approve_course_change_request(admin_user, edit_req.id, session=sess)
    sess.commit()

    sess.refresh(lesson1)
    sess.refresh(lesson2)
    assert lesson1.status == "HISTORICAL"
    assert lesson2.status == "PUBLISHED"

    # Now Admin approves res_req via API endpoint
    login_web_user(client, admin_user)
    resp = client.post(
        f"/admin/change-requests/{res_req.id}/review",
        json={"action": "approve", "reason": "Duyệt video"},
    )
    assert resp.status_code == 200

    # Verify that the active PUBLISHED lesson2 received the attached video!
    sess.refresh(lesson2)
    assert any(r.file_asset_id == video_asset.id for r in lesson2.resources)


def test_instructor_curriculum_serialization_filters_historical_lessons(
    app: Flask, instructor_user: User, admin_user: User
) -> None:
    """Instructor curriculum serializations (_serialize_learning_unit & _serialize_course)

    must not return superseded HISTORICAL lessons.
    """
    from pwd301.blueprints.instructor.routes import _serialize_course, _serialize_learning_unit

    sess = db.session
    unique = uuid.uuid4().hex[:6]
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"FLT_{unique.upper()}",
            "title": f"Filter Test {unique}",
        },
        session=sess,
    )
    unit = create_learning_unit(instructor_user, course.id, {"title": "Chương 1"}, session=sess)
    lesson1 = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Bài 1 Bản Cũ",
            "learning_unit_id": str(unit.public_id),
            "markdown_content": "# Bản cũ",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course.id, "APPROVED", session=sess)
    change_course_status(admin_user, course.id, "PUBLISHED", session=sess)
    sess.commit()

    # Create new revision and approve it
    edit_req, lesson2 = create_lesson_change_request(
        actor=instructor_user,
        course_id=course.id,
        payload={
            "title": "Bài 1 Bản Mới",
            "markdown_content": "# Bản mới",
            "learning_unit_id": str(unit.public_id),
            "position": lesson1.position,
            "target_id": lesson1.id,
        },
        session=sess,
    )
    sess.commit()
    approve_course_change_request(admin_user, edit_req.id, session=sess)
    sess.commit()

    sess.refresh(lesson1)
    sess.refresh(lesson2)
    assert lesson1.status == "HISTORICAL"
    assert lesson2.status == "PUBLISHED"

    # Serializing unit must contain ONLY 1 lesson (the published one)
    ser_unit = _serialize_learning_unit(unit)
    assert ser_unit["lesson_count"] == 1
    assert len(ser_unit["lessons"]) == 1
    assert ser_unit["lessons"][0]["lesson_id"] == str(lesson2.public_id)

    # Serializing course must contain ONLY 1 lesson (the published one)
    ser_course = _serialize_course(course)
    assert len(ser_course["lessons"]) == 1
    assert ser_course["lessons"][0]["lesson_id"] == str(lesson2.public_id)
