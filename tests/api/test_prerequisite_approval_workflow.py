"""Prerequisite publication gate and unified course administrator approval."""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest, CoursePrerequisite
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
)
from pwd301.services.exceptions import CourseValidationError
from pwd301.services.lesson_service import approve_course_change_request, submit_course_changeset
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

    admin = register_user(
        "prereq_review@pwd301.local", "Password@123", "Prerequisite Admin", session=sess
    )
    assign_role_to_user(admin.id, "ADMIN", session=sess)
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


def test_self_owned_prerequisite_waits_for_complete_course_approval(
    prereq_env: dict[str, Any],
) -> None:
    """A published target stages all prerequisite changes, including self-owned courses."""
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

    assert link.approval_status == "PENDING_APPROVAL"
    assert sess.query(CoursePrerequisite).filter_by(course_id=course_a.id).count() == 0
    request = submit_course_changeset(inst1, course_a.id, {}, session=sess)
    approve_course_change_request(prereq_env["admin"], request.id, session=sess)
    sess.commit()
    assert (
        sess.query(CoursePrerequisite).filter_by(course_id=course_a.id).one().approval_status
        == "APPROVED"
    )


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
    request = sess.query(CourseChangeRequest).filter_by(course_id=course_a.id, status="DRAFT").one()
    assert request.change_type == "COURSE_VERSION_CHANGESET"
    assert sess.query(CoursePrerequisite).filter_by(course_id=course_a.id).count() == 0
    csrf2 = login_client(client, inst2.email)
    res_count = client.get(
        "/instructor/prerequisites/incoming-requests/count", headers={"X-CSRF-Token": csrf2}
    )
    assert res_count.status_code == 200 and res_count.get_json()["count"] == 0
    forbidden_alias = client.post(
        f"/instructor/prerequisites/incoming-requests/{course_a.public_id}/{course_b.public_id}/review",
        json={"action": "APPROVE"},
        headers={"X-CSRF-Token": csrf2},
    )
    assert forbidden_alias.status_code == 409
    submitted = submit_course_changeset(inst1, course_a.id, {}, session=sess)
    approve_course_change_request(prereq_env["admin"], submitted.id, session=sess)
    sess.commit()
    link = sess.query(CoursePrerequisite).filter_by(course_id=course_a.id).one()
    assert link.prerequisite_course_id == course_b.id and link.approval_status == "APPROVED"
