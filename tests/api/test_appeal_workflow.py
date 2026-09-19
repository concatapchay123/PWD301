"""Integration tests for student appeal workflow and instructor appeal review."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AssessmentResultHistory,
)
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import create_assessment, publish_assessment
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user


def test_student_appeal_submission_and_retrieval(app: Flask, client: FlaskClient):
    """Verify student can submit appeal and retrieve its status, and instructor can review."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Instructor & Student
    instructor = register_user(
        email="appeal_inst@pwd301.local",
        password="Password@123",
        display_name="TS. Tran Giang Vien",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    student = register_user(
        email="appeal_student@pwd301.local",
        password="Password@123",
        display_name="Le Van Sinh Vien",
        session=sess,
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # 2. Course & Assessment
    course = create_course(
        actor=instructor,
        data={
            "course_code": "APP301",
            "title": "Kiem thu hoc phan",
            "category": "Computer Science",
            "capacity": 30,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    enr = Enrollment(
        student_user_id=student.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enr)
    sess.flush()

    period = EnrollmentPeriod(
        enrollment_id=enr.id,
        period_no=1,
        started_at=utc_now(),
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()

    assess = create_assessment(
        actor=instructor,
        course_id=str(course.public_id),
        payload={
            "title": "Thi cuoi ky",
            "assessment_type": "FINAL",
            "time_limit_minutes": 60,
            "passing_score": 5.0,
        },
        session=sess,
    )
    assess.status = "PUBLISHED"
    sess.flush()

    # 3. Create completed attempt for student
    attempt = AssessmentAttempt(
        assessment_id=assess.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=1,
        status="GRADED",
        started_at=utc_now(),
        submitted_at=utc_now(),
        graded_at=utc_now(),
    )
    sess.add(attempt)
    sess.flush()

    result = AssessmentResult(
        attempt_id=attempt.id,
        raw_score=Decimal("6.0"),
        max_score=Decimal("10.0"),
        percent_score=Decimal("60.0"),
        passed=True,
        status="RELEASED",
    )
    sess.add(result)
    sess.commit()

    attempt_public_id = str(attempt.public_id)

    def login_user(email: str, password: str = "Password@123") -> str:
        res = client.get("/auth/login")
        data = res.get_json() or {}
        csrf_token = data.get("csrf_token", "")
        login_res = client.post(
            "/auth/login",
            json={"email": email, "password": password},
            headers={"X-CSRFToken": csrf_token},
        )
        assert login_res.status_code == 200
        return csrf_token

    # 4. Login as student and submit appeal
    csrf = login_user("appeal_student@pwd301.local")

    res = client.get(f"/student/attempts/{attempt_public_id}/appeal")
    assert res.status_code == 200
    assert res.json.get("appeal") is None

    # Submit appeal
    appeal_payload = {
        "reason": "Chấm sai đáp án câu hỏi trắc nghiệm",
        "note": "Xin xem xét lại câu 3, tài liệu tham khảo chương 2 mục 4 ghi nhận đáp án B là chính xác.",
    }
    res_post = client.post(
        f"/student/attempts/{attempt_public_id}/appeal",
        json=appeal_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res_post.status_code == 201
    assert res_post.json.get("appeal", {}).get("status") == "PENDING"
    assert res_post.json.get("appeal", {}).get("reason") == appeal_payload["reason"]

    # Retrieve appeal as student
    res_get = client.get(f"/student/attempts/{attempt_public_id}/appeal")
    assert res_get.status_code == 200
    appeal_data = res_get.json.get("appeal")
    assert appeal_data is not None
    assert appeal_data["status"] == "PENDING"
    assert appeal_data["note"] == appeal_payload["note"]

    # 5. Login as instructor and review appeal
    csrf_inst = login_user("appeal_inst@pwd301.local")

    review_payload = {
        "decision": "APPROVED",
        "score_delta": 1.5,
        "reviewer_note": "Chấp thuận khiếu nại câu 3. Cộng 1.5 điểm vào kết quả bài thi.",
    }
    res_review = client.post(
        f"/instructor/attempts/{attempt_public_id}/appeal/review",
        json=review_payload,
        headers={"X-CSRFToken": csrf_inst},
    )
    assert res_review.status_code == 200
    assert res_review.json.get("status") == "APPROVED"

    # Verify score updated in AssessmentResult
    sess.refresh(result)
    assert result.raw_score == Decimal("7.5")
    assert result.percent_score == Decimal("75.0")

    # Verify history entry created
    history = (
        sess.query(AssessmentResultHistory)
        .filter(AssessmentResultHistory.attempt_id == attempt.id)
        .order_by(AssessmentResultHistory.id.desc())
        .first()
    )
    assert history is not None
    assert history.old_score == Decimal("6.0")
    assert history.new_score == Decimal("7.5")
    assert "Chấp thuận khiếu nại câu 3" in history.reason
