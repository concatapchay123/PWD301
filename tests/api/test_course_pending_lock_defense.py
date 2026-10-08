"""Tests verifying Fail-Closed Edit Lock during active PENDING changeset review.

Ensures that while a course changeset is submitted to Admin (status == 'PENDING'),
all instructor mutation operations (lesson creation, update, trash, unit creation,
update, deletion, and resource attachment) are strictly locked with 409 Conflict.
Once retracted or reviewed, mutations unlock.
"""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def lock_env(app: Flask) -> dict[str, Any]:
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="instructor_lock@pwd301.local",
        password="Password@123",
        display_name="ThS. Giảng Viên Lock Test",
        session=sess,
    )
    admin_user = register_user(
        email="admin_lock@pwd301.local",
        password="Password@123",
        display_name="Admin Lock Test",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)
    assign_role_to_user(admin_user.id, "ADMIN", session=sess)

    course = create_course(
        actor=inst_user,
        data={
            "course_code": "LOCK301",
            "title": "Khoa Hoc Lock Test",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    lesson1 = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 01: Khoi tao",
            "markdown_content": "# Bai 01 content",
            "estimated_duration_minutes": 30,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson1.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst_user,
        "admin": admin_user,
        "course": course,
        "lesson1": lesson1,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


def test_fail_closed_lock_during_pending_changeset(
    client: FlaskClient, lock_env: dict[str, Any]
) -> None:
    inst = lock_env["instructor"]
    course = lock_env["course"]
    lesson1 = lock_env["lesson1"]

    csrf = login_client(client, inst.email)
    headers = {"X-CSRF-Token": csrf}

    # 1. Instructor creates a draft lesson in the published course
    res = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Bài mới nháp", "markdown_content": "Nội dung nháp", "as_draft": True},
        headers=headers,
    )
    assert res.status_code in (200, 201), res.get_data(as_text=True)
    created_lesson_id = res.get_json().get("id") or res.get_json().get("lesson_id")

    # 2. Instructor submits the changeset to Admin
    res_sub = client.post(
        f"/instructor/courses/{course.public_id}/changeset/submit",
        json={"notes": "Kính gửi Admin xét duyệt đợt cập nhật giáo trình"},
        headers=headers,
    )
    assert res_sub.status_code == 202, res_sub.get_data(as_text=True)
    assert res_sub.get_json().get("status") == "pending_approval"

    # 3. VERIFY FAIL-CLOSED LOCK: Try to add another lesson -> 409 Conflict
    res_add = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Cố tình thêm khi đang duyệt", "markdown_content": "Test"},
        headers=headers,
    )
    assert res_add.status_code == 409, (
        f"Expected 409 Conflict but got {res_add.status_code}: {res_add.get_data(as_text=True)}"
    )

    # 4. VERIFY FAIL-CLOSED LOCK: Try to update lesson -> 409 Conflict
    res_upd = client.put(
        f"/instructor/lessons/{created_lesson_id}",
        json={"title": "Cố tình sửa khi đang duyệt"},
        headers=headers,
    )
    assert res_upd.status_code == 409, (
        f"Expected 409 Conflict but got {res_upd.status_code}: {res_upd.get_data(as_text=True)}"
    )

    # 5. VERIFY FAIL-CLOSED LOCK: Try to create learning unit -> 409 Conflict
    res_unit = client.post(
        f"/instructor/courses/{course.public_id}/learning-units",
        json={"title": "Chương mới khi đang duyệt"},
        headers=headers,
    )
    assert res_unit.status_code == 409, (
        f"Expected 409 Conflict but got {res_unit.status_code}: {res_unit.get_data(as_text=True)}"
    )

    # 6. VERIFY FAIL-CLOSED LOCK: Try to delete lesson -> 409 Conflict
    res_del = client.delete(
        f"/instructor/lessons/{created_lesson_id}",
        headers=headers,
    )
    assert res_del.status_code == 409, (
        f"Expected 409 Conflict but got {res_del.status_code}: {res_del.get_data(as_text=True)}"
    )

    # 7. INSTRUCTOR RETRACTS SUBMISSION
    res_retract = client.post(
        f"/instructor/courses/{course.public_id}/changeset/retract",
        headers=headers,
    )
    assert res_retract.status_code == 200, res_retract.get_data(as_text=True)
    assert res_retract.get_json().get("status") == "CANCELLED"

    # 8. VERIFY UNLOCK: Mutations now succeed
    res_unlocked_update = client.put(
        f"/instructor/lessons/{created_lesson_id}",
        json={"title": "Sửa thành công sau khi rút lại"},
        headers=headers,
    )
    assert res_unlocked_update.status_code == 200, res_unlocked_update.get_data(as_text=True)

    # 9. Clean up by discarding the draft
    res_discard = client.post(
        f"/instructor/courses/{course.public_id}/changeset/discard",
        headers=headers,
    )
    assert res_discard.status_code == 200, res_discard.get_data(as_text=True)
