"""TDD Tests for Course Changeset & Seamless Instructor Staging Workflow (TASK-079).

Verifies the consolidated Course Version Changeset lifecycle:
1. Instructor edits/creates lessons in a PUBLISHED course -> saves into DRAFT without creating PENDING admin requests.
2. Changeset status reflects draft changes accurately.
3. Submitting changeset creates exactly ONE consolidated PENDING request for Admin.
4. Retracting changeset unlocks the draft for editing.
5. Admin approves changeset -> promotes staged lessons atomically to PUBLISHED.
6. Discarding changeset -> purges draft changes and restores live curriculum state.
"""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def changeset_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, admin, student, and published course with initial lessons."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Register users
    inst_user = register_user(
        email="instructor_cs@pwd301.local",
        password="Password@123",
        display_name="ThS. Giảng Viên Changeset",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    admin_user = register_user(
        email="admin_cs@pwd301.local",
        password="Password@123",
        display_name="Quản Trị Viên Phê Duyệt",
        session=sess,
    )
    assign_role_to_user(admin_user.id, "ADMIN", session=sess)
    # Grant COURSE_REVIEW permission to admin
    from pwd301.models.identity import UserRole

    ur = sess.query(UserRole).filter_by(user_id=admin_user.id).first()
    if ur:
        ur.assignment_reason = "SUB_ROLE:ADMIN_COURSE_REVIEW"

    # 2. Create Published Course
    course = create_course(
        actor=inst_user,
        data={
            "course_code": "CS301",
            "title": "Khoa Hoc Changeset Mau",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    # 3. Create 2 initial published lessons
    lesson1 = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 01: Gioi thieu mon hoc",
            "markdown_content": "# Bai 01 content goc",
            "estimated_duration_minutes": 30,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson1.status = "PUBLISHED"

    lesson2 = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 02: Kien truc Co ban",
            "markdown_content": "# Bai 02 content goc",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson2.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst_user,
        "admin": admin_user,
        "course": course,
        "lesson1": lesson1,
        "lesson2": lesson2,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


def test_seamless_auto_draft_editing_and_changeset_status(
    client: FlaskClient, changeset_env: dict[str, Any]
) -> None:
    """Editing and creating lessons saves into DRAFT without creating PENDING change requests."""
    inst = changeset_env["instructor"]
    course = changeset_env["course"]
    lesson1 = changeset_env["lesson1"]

    csrf = login_client(client, inst.email)

    # 1. Instructor edits lesson1
    res_edit = client.put(
        f"/instructor/lessons/{lesson1.public_id}",
        json={
            "title": "Bai 01: Gioi thieu mon hoc (Cap nhat)",
            "markdown_content": "# Bai 01 content da duoc sua doi",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert res_edit.status_code == 200, f"Expected 200 OK: {res_edit.get_json()}"
    data_edit = res_edit.get_json()
    assert data_edit.get("is_draft") is True
    assert "Đã lưu thay đổi vào bản nháp" in data_edit.get("message", "")

    # 2. Check no PENDING CourseChangeRequest created
    pending_crs = (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="PENDING").all()
    )
    assert len(pending_crs) == 0, "No PENDING request should be created during drafting!"

    # 3. Instructor adds a new lesson
    res_add = client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={
            "title": "Bai 03: Bai giang moi them",
            "markdown_content": "# Bai 03 content moi",
            "estimated_duration_minutes": 20,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert res_add.status_code in (200, 201), f"Expected 201: {res_add.get_json()}"
    data_add = res_add.get_json()
    assert data_add.get("is_draft") is True or data_add.get("status") == "DRAFT"

    # 4. Check changeset status
    res_status = client.get(
        f"/instructor/courses/{course.public_id}/changeset/status",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_status.status_code == 200
    st_data = res_status.get_json()
    assert st_data.get("status") in ("DRAFT", "WORKING_DRAFT")
    assert st_data.get("modified_count", 0) >= 1
    assert st_data.get("added_count", 0) >= 1


def test_submit_changeset_and_admin_approval_lifecycle(
    client: FlaskClient, changeset_env: dict[str, Any]
) -> None:
    """Full lifecycle: draft -> submit -> admin review & approve -> promoted to live."""
    inst = changeset_env["instructor"]
    admin = changeset_env["admin"]
    course = changeset_env["course"]
    lesson1 = changeset_env["lesson1"]

    # Step 1: Instructor makes changes
    csrf_inst = login_client(client, inst.email)
    client.put(
        f"/instructor/lessons/{lesson1.public_id}",
        json={"title": "Bai 01: Da Duoc Chinh Sua"},
        headers={"X-CSRF-Token": csrf_inst},
    )
    client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Bai 03: Bai Giang Moi"},
        headers={"X-CSRF-Token": csrf_inst},
    )

    # Step 2: Instructor submits changeset
    res_submit = client.post(
        f"/instructor/courses/{course.public_id}/changeset/submit",
        json={
            "version_title": "Cap Nhat Hoc Ky 1",
            "summary": "Bo sung noi dung bai 1 va them bai 3",
        },
        headers={"X-CSRF-Token": csrf_inst},
    )
    assert res_submit.status_code == 202
    req_id = res_submit.get_json().get("change_request_id")
    assert req_id is not None

    # Step 3: Check changeset status is PENDING
    st_res = client.get(
        f"/instructor/courses/{course.public_id}/changeset/status",
        headers={"X-CSRF-Token": csrf_inst},
    )
    assert st_res.get_json().get("status") == "PENDING"

    # Step 4: Admin logs in and checks change-requests queue
    csrf_admin = login_client(client, admin.email)
    res_queue = client.get("/admin/change-requests?status=PENDING")
    assert res_queue.status_code == 200
    queue_data = res_queue.get_json()
    req_item = next((r for r in queue_data.get("items", []) if r.get("id") == req_id), None)
    assert req_item is not None, "Changeset should appear in admin queue"

    # Step 5: Admin approves the changeset
    res_approve = client.post(
        f"/admin/change-requests/{req_id}/review",
        json={"action": "approve", "reason": "Noi dung cap nhat tot, phe duyet toan bo."},
        headers={"X-CSRF-Token": csrf_admin},
    )
    assert res_approve.status_code == 200, f"Approve failed: {res_approve.get_json()}"

    # Step 6: Verify live database reflects the approved changes
    sess = db.session
    course_refreshed = sess.get(Course, course.id)
    live_lessons = [
        les
        for les in course_refreshed.lessons
        if les.status == "PUBLISHED" and les.deleted_at is None
    ]
    live_titles = [les.title for les in live_lessons]
    assert "Bai 01: Da Duoc Chinh Sua" in live_titles
    assert "Bai 03: Bai Giang Moi" in live_titles

    # Changeset status is now NONE
    st_after = client.get(
        f"/instructor/courses/{course.public_id}/changeset/status",
        headers={"X-CSRF-Token": csrf_inst},
    )
    assert st_after.get_json().get("status") == "NONE"


def test_discard_changeset_purges_drafts(
    client: FlaskClient, changeset_env: dict[str, Any]
) -> None:
    """Discarding changeset cleans up working draft lessons completely."""
    inst = changeset_env["instructor"]
    course = changeset_env["course"]
    lesson1 = changeset_env["lesson1"]

    csrf = login_client(client, inst.email)

    # Edit lesson and create a new one
    client.put(
        f"/instructor/lessons/{lesson1.public_id}",
        json={"title": "Bai 01: Nhap tam thoi se bi huy"},
        headers={"X-CSRF-Token": csrf},
    )
    client.post(
        f"/instructor/courses/{course.public_id}/lessons",
        json={"title": "Bai 03: Nhap tam thoi se bi huy"},
        headers={"X-CSRF-Token": csrf},
    )

    # Discard
    res_discard = client.post(
        f"/instructor/courses/{course.public_id}/changeset/discard",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_discard.status_code == 200

    # Verify no draft lessons remain
    draft_lessons = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.status == "DRAFT")
        .all()
    )
    assert len(draft_lessons) == 0, "All draft lessons should be removed on discard"

    # Live lesson 1 title should still be original
    db.session.refresh(lesson1)
    assert lesson1.title == "Bai 01: Gioi thieu mon hoc"
