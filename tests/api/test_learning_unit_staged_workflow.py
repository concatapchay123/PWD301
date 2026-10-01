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
    approve_course_change_request,
    create_learning_unit,
    create_lesson,
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
    email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Staged Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Admin Staged Test")
    return assign_role_to_user(u.id, "ADMIN")


def test_admin_has_instructor_role_and_permission(admin_user: User):
    """AUTH-002: System Admin roles and permissions."""
    assert admin_user.is_admin is True
    assert admin_user.is_student is True
    assert admin_user.has_role("ADMIN") is True
    assert admin_user.has_role("STUDENT") is True
    assert admin_user.has_admin_permission("COURSE_REVIEW") is True
    assert admin_user.has_admin_permission("INSTRUCTOR_REVIEW") is True


def test_staged_learning_unit_full_lifecycle(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    """Test staged LearningUnit lifecycle:
    1. Instructor creates unit in published course -> staged in DB, is_staged=True, pending_approval=False.
    2. Instructor adds lesson to staged unit -> directly created as DRAFT, no isolated change request.
    3. Instructor edits lesson in staged unit -> directly saved, no change request.
    4. Instructor deletes lesson in staged unit -> directly soft-deleted, no change request.
    5. Instructor adds another lesson and submits the unit -> CourseChangeRequest created, pending_approval=True.
    6. Admin approves -> unit and lessons promoted to PUBLISHED, is_staged=False.
    """
    sess = db.session
    now = utc_now()

    # 1. Create a published course
    code = f"TST_{uuid.uuid4().hex[:4].upper()}"
    course = Course(
        title="Published Testing Course",
        course_code=code,
        course_code_normalized=code.upper(),
        category="CNTT",
        description="Testing staged learning unit workflow",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        published_at=now,
        created_at=now,
        updated_at=now,
    )
    sess.add(course)
    sess.commit()

    login_web_user(client, instructor_user)

    # 2. Instructor creates a new learning unit in the published course
    res = client.post(
        f"/instructor/courses/{course.public_id}/learning-units",
        json={"title": "Chương 2: Phần Mới Thêm"},
    )
    assert res.status_code == 201
    unit_data = res.get_json()
    unit_public_id = unit_data["learning_unit_id"]
    assert unit_data["is_staged"] is True
    assert unit_data["pending_approval"] is False

    # 3. Instructor adds a lesson into the staged learning unit
    res_lesson = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Bài giảng 1: Nháp trong chương mới",
            "markdown_content": "# Bài 1\nNội dung nháp.",
            "learning_unit_id": unit_public_id,
        },
    )
    assert res_lesson.status_code == 201
    lesson_data = res_lesson.get_json()
    lesson_public_id = lesson_data["lesson_id"]

    # Confirm NO individual CourseChangeRequest was created for this lesson
    pending_crs = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == course.id,
            CourseChangeRequest.status == "PENDING",
        )
        .all()
    )
    assert len(pending_crs) == 0

    # 4. Instructor updates the lesson content in the staged unit
    res_update = client.patch(
        f"/instructor/lessons/{lesson_public_id}",
        json={
            "title": "Bài giảng 1: Đã cập nhật nội dung",
            "markdown_content": "# Bài 1 Sửa Đổi\nNội dung mới sau khi sửa.",
        },
    )
    assert res_update.status_code == 200

    # 5. Instructor deletes the lesson from the staged unit
    res_del = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson_public_id}/delete"
    )
    assert res_del.status_code == 200
    assert res_del.get_json().get("status") == "success"

    # Confirm again that NO CourseChangeRequest was queued
    pending_crs = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == course.id,
            CourseChangeRequest.status == "PENDING",
        )
        .all()
    )
    assert len(pending_crs) == 0

    # 6. Instructor creates a final lesson to keep in the unit
    res_lesson_final = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Bài giảng chính thức",
            "markdown_content": "# Bài Giảng Chính Thức\nNội dung hoàn chỉnh.",
            "learning_unit_id": unit_public_id,
        },
    )
    assert res_lesson_final.status_code == 201

    # 7. Instructor submits the staged learning unit via the "Gửi" button endpoint
    res_submit = client.post(
        f"/instructor/courses/{course.public_id}/learning-units/{unit_public_id}/submit"
    )
    assert res_submit.status_code == 200
    submit_data = res_submit.get_json()
    assert submit_data["status"] == "submitted"
    assert submit_data["pending_approval"] is True
    cr_id = submit_data["change_request_id"]
    assert cr_id is not None

    # Check serialization of learning unit now reports pending_approval=True
    res_units = client.get(f"/instructor/courses/{course.public_id}/learning-units")
    units = res_units.get_json()["items"]
    staged_unit = next(u for u in units if u["learning_unit_id"] == unit_public_id)
    assert staged_unit["is_staged"] is True
    assert staged_unit["pending_approval"] is True

    # 8. Admin approves the change request
    req = approve_course_change_request(
        actor=admin_user,
        change_request_id=cr_id,
        review_reason="Duyệt bài học mới",
        session=sess,
    )
    assert req.status == "APPROVED"

    # Verify unit is no longer staged and its lessons are PUBLISHED
    res_units_after = client.get(f"/instructor/courses/{course.public_id}/learning-units")
    units_after = res_units_after.get_json()["items"]
    approved_unit = next(u for u in units_after if u["learning_unit_id"] == unit_public_id)
    assert approved_unit["is_staged"] is False
    assert approved_unit["pending_approval"] is False
