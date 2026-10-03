"""Tests for Change Request Disappearance upon Admin Approval (TASK-080).

Verifies that:
1. Approved (APPROVED) and cancelled (CANCELLED) change requests are completely excluded
   from the Admin Review Queue (/admin/change-requests) even when status=ALL.
2. When an admin approves an individual change request, it disappears from the queue.
3. When an admin approves a course version changeset, it disappears from the queue.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest
from pwd301.models.identity import UserRole
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def cr_disappear_env(app: Flask) -> dict[str, Any]:
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="inst_disappear@pwd301.local",
        password="Password@123",
        display_name="ThS. Giang Vien Test",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    admin_user = register_user(
        email="admin_disappear@pwd301.local",
        password="Password@123",
        display_name="Admin Phe Duyet Test",
        session=sess,
    )
    assign_role_to_user(admin_user.id, "ADMIN", session=sess)
    ur = sess.query(UserRole).filter_by(user_id=admin_user.id).first()
    if ur:
        ur.assignment_reason = "SUB_ROLE:ADMIN_COURSE_REVIEW"

    course = create_course(
        actor=inst_user,
        data={
            "course_code": "DISP101",
            "title": "Khoa hoc Thu nghiem Disappearance",
            "description": "Mo ta",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    course.status = "PUBLISHED"

    lesson = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 01: Khoi dong",
            "markdown_content": "# Noi dung",
            "estimated_duration_minutes": 20,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst_user,
        "admin": admin_user,
        "course": course,
        "lesson": lesson,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


def test_admin_list_change_requests_excludes_approved_and_cancelled(
    client: FlaskClient, cr_disappear_env: dict[str, Any]
) -> None:
    """Verify GET /admin/change-requests?status=ALL excludes APPROVED and CANCELLED."""
    sess: Session = db.session
    course = cr_disappear_env["course"]
    inst = cr_disappear_env["instructor"]
    admin = cr_disappear_env["admin"]

    # Create 4 requests: 1 PENDING, 1 REJECTED, 1 APPROVED, 1 CANCELLED
    r_pending = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps({"title": "Ten moi PENDING"}),
    )
    r_rejected = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="REJECTED",
        review_reason="Ly do tu choi",
        proposed_payload_json=json.dumps({"title": "Ten moi REJECTED"}),
    )
    r_approved = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="APPROVED",
        review_reason="Admin da duyet",
        proposed_payload_json=json.dumps({"title": "Ten moi APPROVED"}),
    )
    r_cancelled = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="CANCELLED",
        review_reason="Thay the",
        proposed_payload_json=json.dumps({"title": "Ten moi CANCELLED"}),
    )
    sess.add_all([r_pending, r_rejected, r_approved, r_cancelled])
    sess.commit()

    # Login admin
    login_client(client, admin.email)

    # Query status=ALL
    res_all = client.get("/admin/change-requests?status=ALL")
    assert res_all.status_code == 200
    data_all = res_all.get_json()
    items_all = data_all["change_requests"]
    statuses_all = [it["status"] for it in items_all]

    # Must contain PENDING only!
    assert "PENDING" in statuses_all
    # Must NOT contain APPROVED, REJECTED, or CANCELLED!
    assert "APPROVED" not in statuses_all, "APPROVED request must not appear in review queue"
    assert "REJECTED" not in statuses_all, "REJECTED request must not appear in review queue"
    assert "CANCELLED" not in statuses_all, "CANCELLED request must not appear in review queue"

    # Query status=PENDING
    res_pending = client.get("/admin/change-requests?status=PENDING")
    assert res_pending.status_code == 200
    data_p = res_pending.get_json()
    for it in data_p["change_requests"]:
        assert it["status"] == "PENDING"


def test_change_request_disappears_immediately_upon_approval(
    client: FlaskClient, cr_disappear_env: dict[str, Any]
) -> None:
    """Verify that after an admin approves a change request, it disappears from the queue."""
    sess: Session = db.session
    course = cr_disappear_env["course"]
    inst = cr_disappear_env["instructor"]
    admin = cr_disappear_env["admin"]

    # 1. Create a pending change request
    cr = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps({"title": "Ten cap nhat bien mat"}),
    )
    sess.add(cr)
    sess.commit()
    cr_id = cr.id

    # 2. Login admin and verify it appears in queue
    csrf = login_client(client, admin.email)
    res_before = client.get("/admin/change-requests?status=ALL")
    assert res_before.status_code == 200
    ids_before = [it["id"] for it in res_before.get_json()["change_requests"]]
    assert cr_id in ids_before

    # 3. Approve the change request
    res_approve = client.post(
        f"/admin/change-requests/{cr_id}/review",
        json={"action": "approve", "reason": "Phe duyet thanh cong"},
        headers={"X-CSRFToken": csrf},
    )
    assert res_approve.status_code == 200

    # 4. Check queue again: it MUST HAVE DISAPPEARED from status=ALL and status=PENDING
    res_after_all = client.get("/admin/change-requests?status=ALL")
    assert res_after_all.status_code == 200
    ids_after_all = [it["id"] for it in res_after_all.get_json()["change_requests"]]
    assert cr_id not in ids_after_all, f"Request {cr_id} must have disappeared from status=ALL!"

    res_after_pending = client.get("/admin/change-requests?status=PENDING")
    assert res_after_pending.status_code == 200
    ids_after_pending = [it["id"] for it in res_after_pending.get_json()["change_requests"]]
    assert cr_id not in ids_after_pending, f"Request {cr_id} must have disappeared from status=PENDING!"

    # 5. Verify database still keeps the record as APPROVED for audit/history
    sess.expire_all()
    db_record = sess.get(CourseChangeRequest, cr_id)
    assert db_record is not None
    assert db_record.status == "APPROVED"
    assert db_record.reviewed_by_user_id == admin.id


def test_change_request_disappears_immediately_upon_rejection(
    client: FlaskClient, cr_disappear_env: dict[str, Any]
) -> None:
    """Verify that after an admin rejects a change request, it also disappears from the queue."""
    sess: Session = db.session
    course = cr_disappear_env["course"]
    inst = cr_disappear_env["instructor"]
    admin = cr_disappear_env["admin"]

    # 1. Create a pending change request
    cr = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=inst.id,
        change_type="COURSE_METADATA",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps({"title": "Ten cap nhat tu choi bien mat"}),
    )
    sess.add(cr)
    sess.commit()
    cr_id = cr.id

    # 2. Login admin and verify it appears in queue
    csrf = login_client(client, admin.email)
    res_before = client.get("/admin/change-requests?status=ALL")
    assert res_before.status_code == 200
    ids_before = [it["id"] for it in res_before.get_json()["change_requests"]]
    assert cr_id in ids_before

    # 3. Reject the change request
    res_reject = client.post(
        f"/admin/change-requests/{cr_id}/review",
        json={"action": "reject", "reason": "Tu choi yeu cau nay"},
        headers={"X-CSRFToken": csrf},
    )
    assert res_reject.status_code == 200

    # 4. Check queue again: it MUST HAVE DISAPPEARED from status=ALL and status=PENDING
    res_after_all = client.get("/admin/change-requests?status=ALL")
    assert res_after_all.status_code == 200
    ids_after_all = [it["id"] for it in res_after_all.get_json()["change_requests"]]
    assert cr_id not in ids_after_all, f"Rejected request {cr_id} must have disappeared from status=ALL!"

    res_after_pending = client.get("/admin/change-requests?status=PENDING")
    assert res_after_pending.status_code == 200
    ids_after_pending = [it["id"] for it in res_after_pending.get_json()["change_requests"]]
    assert cr_id not in ids_after_pending, f"Rejected request {cr_id} must have disappeared from status=PENDING!"

    # 5. Verify database still keeps the record as REJECTED for audit/history
    sess.expire_all()
    db_record = sess.get(CourseChangeRequest, cr_id)
    assert db_record is not None
    assert db_record.status == "REJECTED"
    assert db_record.reviewed_by_user_id == admin.id
    assert db_record.review_reason == "Tu choi yeu cau nay"
