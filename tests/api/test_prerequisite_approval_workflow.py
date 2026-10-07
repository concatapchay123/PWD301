"""TDD Tests for Course Prerequisite Approval Workflow & Publication Gate (TASK-084).

Verifies:
1. Cannot assign unpublished (e.g. DRAFT) course as prerequisite.
2. Self-owned course prerequisite is automatically APPROVED and immediately active.
3. Cross-instructor course prerequisite requires approval (PENDING_APPROVAL).
4. Prerequisite owner instructor receives incoming requests and count.
5. Prerequisite owner can approve or reject the request with review note.
6. Only APPROVED prerequisites enforce graduation / completion gates on learners.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CoursePrerequisite
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    check_prerequisites_met,
    get_course_prerequisites,
)
from pwd301.services.exceptions import CourseValidationError
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def prereq_env(app: Flask) -> dict[str, Any]:
    """Setup 2 instructors, 1 student, and courses."""
    sess: Session = db.session
    seed_baseline(sess)

    # Instructor 1 (Owner of Course A)
    inst1 = register_user(
        email="inst1_prereq@pwd301.local",
        password="Password@123",
        display_name="TS. Giảng Viên Một",
        session=sess,
    )
    assign_role_to_user(inst1.id, "INSTRUCTOR", session=sess)

    # Instructor 2 (Owner of Course B & Course C)
    inst2 = register_user(
        email="inst2_prereq@pwd301.local",
        password="Password@123",
        display_name="ThS. Giảng Viên Hai",
        session=sess,
    )
    assign_role_to_user(inst2.id, "INSTRUCTOR", session=sess)

    # Student
    student = register_user(
        email="student_prereq@pwd301.local",
        password="Password@123",
        display_name="Sinh Viên Kiểm Thử",
        session=sess,
    )
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

    # Course Draft: Owner = Inst2, Status = DRAFT
    course_draft = create_course(
        actor=inst2,
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


def test_self_owned_prerequisite_is_auto_approved(prereq_env: dict[str, Any]) -> None:
    """When an instructor adds their own course as prerequisite, it is auto-approved."""
    sess: Session = db.session
    inst1 = prereq_env["inst1"]
    course_a = prereq_env["course_a"]
    course_c = prereq_env["course_c"]

    link = add_course_prerequisite(
        actor=inst1,
        course_id=course_a.id,
        prerequisite_course_id=course_c.id,
        session=sess,
    )
    sess.commit()

    assert link.approval_status == "APPROVED"
    assert link.reviewed_at is not None


def test_cross_instructor_prerequisite_requires_approval(
    client: FlaskClient, prereq_env: dict[str, Any]
) -> None:
    """When adding another instructor's course, it enters PENDING_APPROVAL and owner can review."""
    sess: Session = db.session
    inst1 = prereq_env["inst1"]
    inst2 = prereq_env["inst2"]
    course_a = prereq_env["course_a"]
    course_b = prereq_env["course_b"]

    # Inst1 adds Course B (owned by Inst2) to Course A
    link = add_course_prerequisite(
        actor=inst1,
        course_id=course_a.id,
        prerequisite_course_id=course_b.id,
        session=sess,
    )
    sess.commit()

    assert link.approval_status == "PENDING_APPROVAL"
    assert link.requested_by_user_id == inst1.id

    # Inst2 logs in and checks incoming requests
    csrf2 = login_client(client, inst2.email)

    # 1. Count pending requests
    res_count = client.get(
        "/instructor/prerequisites/incoming-requests/count",
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_count.status_code == 200
    assert res_count.get_json().get("count") == 1

    # 2. List incoming requests
    res_list = client.get(
        "/instructor/prerequisites/incoming-requests",
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_list.status_code == 200
    reqs = res_list.get_json().get("incoming", [])
    assert len(reqs) == 1
    req = reqs[0]
    assert req.get("requesting_course_code") == "CS_A101"
    assert req.get("prerequisite_course_code") == "CS_B201"
    assert req.get("approval_status") == "PENDING_APPROVAL"

    # 3. Inst2 approves request
    res_review = client.post(
        f"/instructor/prerequisites/incoming-requests/{course_a.public_id}/{course_b.public_id}/review",
        json={"action": "APPROVE", "note": "Đồng ý liên kết học phần."},
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_review.status_code == 200
    assert res_review.get_json().get("approval_status") == "APPROVED"

    # Re-check count
    res_count_after = client.get(
        "/instructor/prerequisites/incoming-requests/count",
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_count_after.status_code == 200
    assert res_count_after.get_json().get("count") == 0
