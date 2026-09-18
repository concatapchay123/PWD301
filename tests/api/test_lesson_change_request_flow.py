import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.lesson_service import create_lesson
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
    u = register_user(email, "Password@123", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Admin Test")
    return assign_role_to_user(u.id, "ADMIN")


def test_update_and_delete_lesson_in_published_course_requires_admin_approval(
    client: FlaskClient, instructor_user: User, admin_user: User
):
    """When a course is published, lesson edits and deletes must create a change request
    for admin review."""
    sess = db.session

    # 1. Create published course and lesson
    course = Course(
        course_code=f"PUB_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"PUB_{uuid.uuid4().hex[:4]}",
        title="Published Course",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(course)
    sess.commit()

    lesson = create_lesson(
        actor=instructor_user,
        course_id=course.id,
        data={
            "title": "Initial Lesson Title",
            "markdown_content": "# Initial Content",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)

    # 2. Instructor attempts to edit lesson -> should return 202 pending_approval
    res_edit = client.put(
        f"/instructor/lessons/{lesson.id}",
        json={"title": "Updated Title That Needs Admin Approval"},
    )
    assert res_edit.status_code == 202
    edit_data = res_edit.get_json()
    assert edit_data["pending_approval"] is True
    edit_req_id = edit_data["change_request_id"]

    # Lesson title in DB remains unchanged until approved
    sess.expire_all()
    lesson_check = sess.get(Lesson, lesson.id)
    assert lesson_check.title == "Initial Lesson Title"

    # 3. Instructor attempts to delete lesson -> should return 202 pending_approval
    res_del = client.post(
        f"/instructor/courses/{course.id}/lessons/{lesson.id}/delete",
        json={"reason": "Request to remove obsolete chapter"},
    )
    assert res_del.status_code == 202
    del_data = res_del.get_json()
    assert del_data["pending_approval"] is True
    del_req_id = del_data["change_request_id"]

    # Lesson is NOT trashed yet
    sess.expire_all()
    assert lesson_check.deleted_at is None

    # 4. Admin logs in and checks change requests
    login_web_user(client, admin_user)

    list_res = client.get("/admin/change-requests")
    assert list_res.status_code == 200
    list_json = list_res.get_json()
    assert list_json["pending_count"] >= 2

    # 5. Admin approves the edit request
    approve_edit_res = client.post(
        f"/admin/change-requests/{edit_req_id}/review",
        json={"action": "approve", "reason": "Syllabus revision accepted"},
    )
    assert approve_edit_res.status_code == 200
    assert approve_edit_res.get_json()["status"] == "APPROVED"

    # Lesson title is now updated
    sess.expire_all()
    lesson_updated = sess.get(Lesson, lesson.id)
    assert lesson_updated.title == "Updated Title That Needs Admin Approval"

    # 6. Admin approves the delete request
    approve_del_res = client.post(
        f"/admin/change-requests/{del_req_id}/review",
        json={"action": "approve", "reason": "Removal approved"},
    )
    assert approve_del_res.status_code == 200
    assert approve_del_res.get_json()["status"] == "APPROVED"

    # Lesson is now trashed (soft-deleted)
    sess.expire_all()
    lesson_trashed = sess.get(Lesson, lesson.id)
    assert lesson_trashed.deleted_at is not None
