"""Prerequisite publication gate and unified course administrator approval."""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.models.types import utc_now
from backend.extensions import db
from backend.models.course import CourseChangeRequest, CoursePrerequisite
from backend.seeds.baseline import seed_baseline
from backend.services.course_service import create_course
from backend.services.enrollment_service import (
    add_course_prerequisite,
)
from backend.services.exceptions import CourseValidationError
from backend.services.lesson_service import approve_course_change_request, submit_course_changeset
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def prereq_env(app: Flask) -> dict[str, Any]:
    """Setup 2 instructors, 1 student, and courses."""
    sess: Session = db.session
    seed_baseline(sess)

    now = utc_now()
    # Instructor 1 (Owner of Course A)
    inst1 = register_user(
        email="inst1_prereq@backend.local",
        password="Password@123",
        display_name="TS. Giảng Viên Một",
        session=sess,
    )
    inst1.email_verified_at = now
    assign_role_to_user(inst1.id, "INSTRUCTOR", session=sess)

    # Instructor 2 (Owner of Course B & Course C)
    inst2 = register_user(
        email="inst2_prereq@backend.local",
        password="Password@123",
        display_name="ThS. Giảng Viên Hai",
        session=sess,
    )
    inst2.email_verified_at = now
    assign_role_to_user(inst2.id, "INSTRUCTOR", session=sess)

    admin = register_user(
        "prereq_review@backend.local", "Password@123", "Prerequisite Admin", session=sess
    )
    admin.email_verified_at = now
    assign_role_to_user(admin.id, "ADMIN", session=sess)

    # Student
    student = register_user(
        email="student_prereq@backend.local",
        password="Password@123",
        display_name="Sinh Viên Kiểm Thử",
        session=sess,
    )
    student.email_verified_at = now
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # Course A: Owner = Inst1, Status = PUBLISHED
    course_a = create_course(
        actor=inst1,
        data={
            "course_code": "CS_A101",
            "title": "Nhập Môn Lập Trình A",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course_a.status = "PUBLISHED"

    # Course B: Owner = Inst2, Status = PUBLISHED
    course_b = create_course(
        actor=inst2,
        data={
            "course_code": "CS_B201",
            "title": "Cấu Trúc Dữ Liệu B",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course_b.status = "PUBLISHED"

    # Course C: Owner = Inst1 (same owner as A), Status = PUBLISHED
    course_c = create_course(
        actor=inst1,
        data={
            "course_code": "CS_C102",
            "title": "Toán Rời Rạc C",
            "category": "Mathematics",
            "capacity": 50,
        },
        session=sess,
    )
    course_c.status = "PUBLISHED"

    # Course Draft: Owner = Inst1, Status = DRAFT
    course_draft = create_course(
        actor=inst1,
        data={
            "course_code": "CS_DRAFT",
            "title": "Khóa Học Bản Nháp",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course_draft.status = "DRAFT"

    sess.commit()

    return {
        "admin": admin,
        "inst1": inst1,
        "inst2": inst2,
        "student": student,
        "course_a": course_a,
        "course_b": course_b,
        "course_c": course_c,
        "course_draft": course_draft,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


def test_cannot_add_unpublished_course_as_prerequisite(prereq_env: dict[str, Any]) -> None:
    """Invariant: Course must be PUBLISHED to be selected as a prerequisite."""
    sess: Session = db.session
    inst1 = prereq_env["inst1"]
    course_a = prereq_env["course_a"]
    course_draft = prereq_env["course_draft"]

    with pytest.raises(CourseValidationError) as exc_info:
        add_course_prerequisite(
            actor=inst1,
            course_id=course_a.id,
            prerequisite_course_id=course_draft.id,
            session=sess,
        )
    assert "chưa được xuất bản" in str(exc_info.value) or "PUBLISHED" in str(exc_info.value)


def test_review_incoming_prerequisite_request_persists_to_db(
    client: FlaskClient, prereq_env: dict[str, Any]
) -> None:
    """Invariant: Instructor reviewing incoming prerequisite request commits changes to database."""
    sess: Session = db.session
    inst1 = prereq_env["inst1"]
    inst2 = prereq_env["inst2"]
    course_draft = prereq_env["course_draft"]
    course_b = prereq_env["course_b"]

    # Inst1 adds published course B (owned by Inst2) to draft course_draft
    link = add_course_prerequisite(
        actor=inst1,
        course_id=course_draft.id,
        prerequisite_course_id=course_b.id,
        session=sess,
    )
    sess.commit()

    assert link.approval_status == "PENDING_APPROVAL"

    # Login as Inst2
    csrf2 = login_client(client, inst2.email)

    # Check incoming requests count
    res_count = client.get(
        "/instructor/prerequisites/incoming-requests/count", headers={"X-CSRF-Token": csrf2}
    )
    assert res_count.status_code == 200
    assert res_count.get_json()["count"] >= 1

    # Inst2 approves the incoming prerequisite request
    res_review = client.post(
        f"/instructor/prerequisites/incoming-requests/{course_draft.public_id}/{course_b.public_id}/review",
        json={"action": "APPROVE", "note": "Đồng ý liên kết môn tiên quyết."},
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_review.status_code == 200
    assert res_review.get_json()["success"] is True
    assert res_review.get_json()["approval_status"] == "APPROVED"

    # Ensure database session reflects committed status
    sess.expire_all()
    persisted = (
        sess.query(CoursePrerequisite)
        .filter_by(course_id=course_draft.id, prerequisite_course_id=course_b.id)
        .one()
    )
    assert persisted.approval_status == "APPROVED"
    assert persisted.reviewed_by_user_id == inst2.id
    assert persisted.review_note == "Đồng ý liên kết môn tiên quyết."
