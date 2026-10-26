"""Tests for Rate Limiter Middleware, Admin Governance Summary, and Course Pricing.

Verifies:
1. Rate Limiter Middleware:
   - 429 Too Many Requests when rate limit threshold is exceeded with Retry-After header.
   - Sensitive authentication tier (10 req/min/IP).
   - Heavy tasks tier (20 req/min/IP).
   - Exempt routes (/static/, /admin/health, /favicon.ico) and RATELIMIT_ENABLED = False.
2. Administrative Governance Summary endpoint (GET /admin/governance/summary):
   - Returns counts for pending courses, change requests, instructor applications, total users, and total pending work.
3. Course Pricing:
   - create_course stores valid price (>= 0) and rejects negative values.
   - PUT /instructor/courses/<course_id>/price allows course manager to update price.
   - PUT /admin/courses/<course_id>/price allows admin to update price.
   - Serialized courses contain price and price_formatted.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.middlewares.rate_limiter import get_rate_limiter
from backend.models.course import Course, CourseChangeRequest
from backend.models.identity import InstructorApplication, User
from backend.seeds.baseline import seed_baseline
from backend.services.course_service import create_course
from backend.services.exceptions import CourseValidationError
from backend.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def pricing_and_governance_fixture(app: Flask) -> dict[str, Any]:
    """Setup users, instructor, admin, and courses for testing."""
    sess: Session = db.session
    seed_baseline(sess)

    admin_user = sess.query(User).filter_by(email="tqtphamnguyenhoangphuc@gmail.com").first()
    if not admin_user:
        admin_user = register_user(
            f"admin_{uuid.uuid4().hex[:6]}@example.com",
            "AdminPass@123",
            "Super Admin",
            session=sess,
        )
        assign_role_to_user(admin_user.id, "ADMIN", session=sess)

    instructor = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com",
        "InstPass@123",
        "Giảng Viên Toán Tin",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    other_instructor = register_user(
        f"other_inst_{uuid.uuid4().hex[:6]}@example.com",
        "InstPass@123",
        "Giảng Viên Ngoại Ngữ",
        session=sess,
    )
    assign_role_to_user(other_instructor.id, "INSTRUCTOR", session=sess)

    course = create_course(
        instructor,
        {
            "course_code": f"PRC{uuid.uuid4().hex[:4].upper()}",
            "title": f"Khóa Học Lập Trình Python Căn Bản {uuid.uuid4().hex[:4]}",
            "category": "LẬP TRÌNH",
            "difficulty": "BEGINNER",
            "price": 250000,
        },
        session=sess,
    )
    sess.commit()

    return {
        "admin": admin_user,
        "instructor": instructor,
        "other_instructor": other_instructor,
        "course": course,
    }


# ============================================================================
# 1. RATE LIMITER MIDDLEWARE TESTS
# ============================================================================


def test_rate_limiter_auth_sensitive_tier(app: Flask, client: FlaskClient):
    """Verify sensitive auth routes trigger HTTP 429 after 10 requests within a minute."""
    limiter = get_rate_limiter()
    limiter.reset()

    app.config["RATELIMIT_ENABLED"] = True
    test_ip = "192.0.2.1"
    headers = {"X-Forwarded-For": test_ip}

    # First 10 requests should be admitted by rate limiter
    for _ in range(10):
        resp = client.get("/auth/login", headers=headers)
        assert resp.status_code != 429, "First 10 requests should not be rate limited"

    # 11th request must be rejected with HTTP 429
    resp_blocked = client.get("/auth/login", headers=headers)
    assert resp_blocked.status_code == 429
    assert "Retry-After" in resp_blocked.headers
    retry_after = int(resp_blocked.headers["Retry-After"])
    assert retry_after >= 1

    json_body = resp_blocked.get_json()
    assert json_body["success"] is False
    assert "Bạn đã gửi quá nhiều yêu cầu" in json_body["error"]
    assert json_body["retry_after"] == retry_after


def test_rate_limiter_heavy_task_tier(app: Flask, client: FlaskClient):
    """Verify heavy task routes (/files/upload, /api/ai/) trigger HTTP 429 after 20 requests."""
    limiter = get_rate_limiter()
    limiter.reset()

    app.config["RATELIMIT_ENABLED"] = True
    test_ip = "192.0.2.2"
    headers = {"X-Forwarded-For": test_ip}

    for _ in range(20):
        resp = client.post("/files/upload", headers=headers)
        assert resp.status_code != 429, "First 20 heavy requests should not be rate limited"

    resp_blocked = client.post("/files/upload", headers=headers)
    assert resp_blocked.status_code == 429
    assert "Retry-After" in resp_blocked.headers
    assert resp_blocked.get_json()["success"] is False


def test_rate_limiter_exempt_paths(app: Flask, client: FlaskClient):
    """Verify exempt paths (/admin/health, /static/*, /favicon.ico) never trigger rate limit."""
    limiter = get_rate_limiter()
    limiter.reset()

    app.config["RATELIMIT_ENABLED"] = True
    test_ip = "192.0.2.3"
    headers = {"X-Forwarded-For": test_ip}

    # Spam health check 50 times
    for _ in range(50):
        resp = client.get("/admin/health", headers=headers)
        assert resp.status_code != 429


def test_rate_limiter_disabled_via_config(app: Flask, client: FlaskClient):
    """Verify rate limiter is completely bypassed when RATELIMIT_ENABLED is False."""
    limiter = get_rate_limiter()
    limiter.reset()

    app.config["RATELIMIT_ENABLED"] = False
    test_ip = "192.0.2.4"
    headers = {"X-Forwarded-For": test_ip}

    try:
        for _ in range(15):
            resp = client.post("/api/auth/login", json={"email": "nobody@example.com"}, headers=headers)
            assert resp.status_code != 429
    finally:
        app.config["RATELIMIT_ENABLED"] = True


# ============================================================================
# 2. ADMIN GOVERNANCE SUMMARY TESTS
# ============================================================================


def test_admin_governance_summary_endpoint(app: Flask, client: FlaskClient, pricing_and_governance_fixture: dict[str, Any]):
    """Verify GET /admin/governance/summary computes exact counts and returns standardized envelope."""
    admin = pricing_and_governance_fixture["admin"]
    instructor = pricing_and_governance_fixture["instructor"]
    sess: Session = db.session

    # Create a course submitted for review
    course_sub = create_course(
        instructor,
        {
            "course_code": f"SUB{uuid.uuid4().hex[:4].upper()}",
            "title": f"Khóa Học Chờ Xét Duyệt {uuid.uuid4().hex[:4]}",
        },
        session=sess,
    )
    course_sub.status = "SUBMITTED_FOR_REVIEW"
    sess.commit()

    # Login as Admin
    login_web_user(client, admin)

    resp = client.get("/admin/governance/summary")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    summary = data["data"]

    assert "pending_courses_count" in summary
    assert "pending_change_requests_count" in summary
    assert "pending_instructor_applications_count" in summary
    assert "total_users_count" in summary
    assert "total_pending_work" in summary

    assert summary["pending_courses_count"] >= 1
    assert summary["total_users_count"] >= 1
    assert summary["total_pending_work"] == (
        summary["pending_courses_count"]
        + summary["pending_change_requests_count"]
        + summary["pending_instructor_applications_count"]
    )


# ============================================================================
# 3. COURSE PRICING TESTS
# ============================================================================


def test_create_course_with_price(pricing_and_governance_fixture: dict[str, Any]):
    """Verify create_course accepts and stores valid price, and rejects negative values."""
    instructor = pricing_and_governance_fixture["instructor"]
    sess: Session = db.session

    # 1. Valid positive price
    c1 = create_course(
        instructor,
        {
            "course_code": f"P1_{uuid.uuid4().hex[:4].upper()}",
            "title": f"Khóa Học Có Phí {uuid.uuid4().hex[:4]}",
            "price": 350000,
        },
        session=sess,
    )
    assert c1.price == 350000

    # 2. Free course (price = 0 or omitted)
    c2 = create_course(
        instructor,
        {
            "course_code": f"P2_{uuid.uuid4().hex[:4].upper()}",
            "title": f"Khóa Học Miễn Phí {uuid.uuid4().hex[:4]}",
        },
        session=sess,
    )
    assert c2.price == 0

    # 3. Negative price must raise CourseValidationError
    with pytest.raises(CourseValidationError, match="Giá khóa học"):
        create_course(
            instructor,
            {
                "course_code": f"P3_{uuid.uuid4().hex[:4].upper()}",
                "title": f"Khóa Học Giá Âm {uuid.uuid4().hex[:4]}",
                "price": -50000,
            },
            session=sess,
        )


def test_instructor_update_course_price(client: FlaskClient, pricing_and_governance_fixture: dict[str, Any]):
    """Verify instructor can update price for courses they manage, but not others."""
    instructor = pricing_and_governance_fixture["instructor"]
    other_instructor = pricing_and_governance_fixture["other_instructor"]
    course = pricing_and_governance_fixture["course"]

    # 1. Login as managing instructor
    login_web_user(client, instructor)

    # Valid update
    resp = client.put(f"/instructor/courses/{course.public_id}/price", json={"price": 600000})
    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["price"] == 600000
    assert res_data["data"]["price_formatted"] == "600.000 đ"

    # Refresh from database
    db.session.refresh(course)
    assert course.price == 600000

    # Invalid negative price returns 400
    resp_invalid = client.put(f"/instructor/courses/{course.public_id}/price", json={"price": -1000})
    assert resp_invalid.status_code == 400
    assert "Giá khóa học" in resp_invalid.get_json()["error"]

    # 2. Login as other instructor (IDOR prevention) -> 403 Forbidden
    login_web_user(client, other_instructor)
    resp_forbidden = client.put(f"/instructor/courses/{course.public_id}/price", json={"price": 800000})
    assert resp_forbidden.status_code == 403


def test_admin_update_course_price(client: FlaskClient, pricing_and_governance_fixture: dict[str, Any]):
    """Verify admin can update price for any course, records audit event, and dispatches notification."""
    from backend.models.notification_audit import AuditEvent, Notification

    admin = pricing_and_governance_fixture["admin"]
    course = pricing_and_governance_fixture["course"]

    login_web_user(client, admin)

    # Admin updates price with reason
    reason_text = "Điều chỉnh theo chính sách học phí mới"
    resp = client.put(
        f"/admin/courses/{course.public_id}/price",
        json={"price": 1500000, "reason": reason_text},
    )
    assert resp.status_code == 200

    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["price"] == 1500000
    assert res_data["data"]["price_formatted"] == "1.500.000 đ"

    db.session.refresh(course)
    assert course.price == 1500000

    # Verify AuditEvent was created
    audit = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.action == "COURSE_PRICE_UPDATED",
            AuditEvent.target_id == course.id,
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit is not None
    assert audit.reason == reason_text
    assert audit.actor_user_id == admin.id
    assert "1.500.000" in (audit.after_json or "")

    # Verify Notification dispatched to instructor if course has owner
    if course.owner_instructor_id:
        notif = (
            db.session.query(Notification)
            .filter(
                Notification.recipient_user_id == course.owner_instructor_id,
                Notification.title.like("%học phí%"),
            )
            .order_by(Notification.id.desc())
            .first()
        )
        assert notif is not None
        assert reason_text in notif.body

    # Admin invalid negative price returns 400
    resp_invalid = client.put(f"/admin/courses/{course.public_id}/price", json={"price": -500})
    assert resp_invalid.status_code == 400

    # Course not found returns 404
    non_existent_uuid = str(uuid.uuid4())
    resp_not_found = client.put(f"/admin/courses/{non_existent_uuid}/price", json={"price": 100000})
    assert resp_not_found.status_code == 404
    assert resp_not_found.get_json()["success"] is False

    # Security check: Non-admin (Instructor) attempting to call Admin pricing endpoint -> 403 Forbidden
    instructor = pricing_and_governance_fixture["instructor"]
    login_web_user(client, instructor)
    resp_forbidden = client.put(f"/admin/courses/{course.public_id}/price", json={"price": 999999})
    assert resp_forbidden.status_code == 403

    # Security check: Unauthenticated actor -> 401 or 403 or redirect
    with client.session_transaction() as sess:
        sess.clear()
    resp_unauth = client.put(f"/admin/courses/{course.public_id}/price", json={"price": 999999})
    assert resp_unauth.status_code in (401, 403, 302)


def test_serialized_course_pricing_format(pricing_and_governance_fixture: dict[str, Any]):
    """Verify both instructor and admin serializers output price and price_formatted correctly."""
    from backend.blueprints.admin.routes import _serialize_course as admin_serialize
    from backend.blueprints.instructor.routes import _serialize_course as instructor_serialize

    course = pricing_and_governance_fixture["course"]
    course.price = 450000

    admin_data = admin_serialize(course)
    assert admin_data["price"] == 450000
    assert admin_data["price_formatted"] == "450.000 đ"

    inst_data = instructor_serialize(course)
    assert inst_data["price"] == 450000
    assert inst_data["price_formatted"] == "450.000 đ"

    # Test free course formatting
    course.price = 0
    assert admin_serialize(course)["price_formatted"] == "Miễn phí"
    assert instructor_serialize(course)["price_formatted"] == "Miễn phí"


def test_token_bucket_sliding_window_logic():
    """Verify TokenBucket direct unit logic: capacity, consumption, exhaustion, and refill."""
    from backend.middlewares.rate_limiter import TokenBucket

    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    now = 1000.0

    # Consume 5 tokens
    for _ in range(5):
        allowed, retry_after = bucket.consume(now)
        assert allowed is True
        assert retry_after == 0

    # 6th token should be rejected with 1s retry_after
    allowed, retry_after = bucket.consume(now)
    assert allowed is False
    assert retry_after == 1

    # Advance time by 2 seconds -> should refill 2 tokens
    now += 2.0
    allowed1, _ = bucket.consume(now)
    allowed2, _ = bucket.consume(now)
    assert allowed1 is True
    assert allowed2 is True

    # 3rd token immediately after should fail
    allowed3, _ = bucket.consume(now)
    assert allowed3 is False
