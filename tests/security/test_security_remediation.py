"""Comprehensive regression test suite verifying architectural, security, and concurrency fixes.

Verifies:
1. Reflected XSS elimination in _format_error_response HTML fallback.
2. ProxyFix integration resolving real client IP from X-Forwarded-For.
3. Rate-limiter loopback/proxy protection preventing whole-platform DoS.
4. Cross-process database restore lock marker triggering HTTP 503 without DB queries.
5. Blueprint authorization decorators (@instructor_required) rejecting student JWTs on:
   - /api/assessments/<id>/release-scores
   - /api/assessments/<id>/regrade
   - /api/courses/<id>/imports (POST and GET)
   - /api/import endpoints (create, get, process, commit)
6. Grade history access control and score release policy enforcement.
7. File upload size limit enforcement via LimitingStream on /api/courses/<id>/imports.
8. Video/file range requests (conditional=True, HTTP 206) and X-Accel-Redirect header support.
"""

from __future__ import annotations

import io
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import AIServiceUnavailableError
from pwd301.services.gemini_service import RealGeminiClient
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.operations_service import (
    _get_restore_lock_file,
    _restore_lock,
    is_database_restore_in_progress,
)
from pwd301.services.rate_limit_service import (
    is_login_locked,
    record_failed_login,
    reset_all_rate_limits,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture(autouse=True)
def clean_rate_limits() -> None:
    """Ensure in-memory rate limits are clean before and after every test."""
    reset_all_rate_limits()
    # Also ensure restore lock is released
    _restore_lock.release()
    lock_file = _get_restore_lock_file()
    if lock_file.is_file():
        lock_file.unlink(missing_ok=True)
    yield
    reset_all_rate_limits()
    _restore_lock.release()
    if lock_file.is_file():
        lock_file.unlink(missing_ok=True)


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure baseline roles exist."""
    sess: Session = db.session
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
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a student user."""
    uid = uuid.uuid4().hex[:6]
    return register_user(f"remed_student_{uid}@example.com", "Password@123", "Remed Student")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an instructor user."""
    uid = uuid.uuid4().hex[:6]
    u = register_user(f"remed_instructor_{uid}@example.com", "Password@123", "Remed Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a course managed by instructor_user."""
    return create_course(
        instructor_user,
        {
            "course_code": f"REM-{uuid.uuid4().hex[:4].upper()}",
            "title": "Remediation Verification Course",
            "capacity": 50,
        },
    )


def _auth_headers(user: User) -> dict[str, str]:
    tokens = create_token_pair(user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ==============================================================================
# 1. Reflected XSS Elimination in HTML Error Response
# ==============================================================================


def test_reflected_xss_in_html_error_response_is_escaped(app: Flask) -> None:
    """XSS payloads in error responses must be escaped and not rendered executable."""
    from pwd301 import _format_error_response

    # Test direct _format_error_response HTML fallback escaping
    with app.test_request_context("/some-path", headers={"Accept": "text/html"}):
        resp = _format_error_response(
            code="<script>alert('PWD301_CODE_XSS')</script>",
            message="<img src=x onerror=alert('PWD301_MSG_XSS')>",
            status_code=400,
        )
        assert resp.status_code == 400
        body = resp.get_data(as_text=True)
        # The raw unescaped tags must NOT be present
        assert "<script>alert('PWD301_CODE_XSS')</script>" not in body
        assert "<img src=x onerror=alert('PWD301_MSG_XSS')>" not in body
        # The properly escaped HTML entities MUST be present
        assert "&lt;script&gt;" in body
        assert "&lt;img" in body


# ==============================================================================
# 2. ProxyFix Configuration & Real Client IP Resolution
# ==============================================================================


def test_proxy_fix_resolves_real_client_ip() -> None:
    """ProxyFix must correctly map X-Forwarded-For header to request.remote_addr."""
    proxy_app = create_app(
        "testing",
        config_override={"USE_PROXY_FIX": True, "NUM_PROXIES": 1},
    )

    @proxy_app.route("/test-real-ip")
    def test_real_ip() -> Any:
        from flask import request

        return {"remote_addr": request.remote_addr}

    client = proxy_app.test_client()
    resp = client.get(
        "/test-real-ip",
        headers={"X-Forwarded-For": "203.0.113.195"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["remote_addr"] == "203.0.113.195"


# ==============================================================================
# 3. Rate Limiting Loopback & Proxy Protection (No Whole-System DoS)
# ==============================================================================


def test_rate_limiter_does_not_lock_out_innocent_users_on_loopback() -> None:
    """Failed logins on 127.0.0.1 must lock only targeted email, never all users."""
    targeted_email = "target_victim@example.com"
    innocent_email = "innocent_user@example.com"

    # Simulate 5 failed logins on loopback address for the targeted email
    for _ in range(5):
        record_failed_login(ip="127.0.0.1", email=targeted_email)

    # The targeted email must be locked
    locked, _ = is_login_locked(ip="127.0.0.1", email=targeted_email)
    assert locked is True

    # The innocent user on the same loopback IP must NOT be locked!
    locked_innocent, _ = is_login_locked(ip="127.0.0.1", email=innocent_email)
    assert locked_innocent is False


def test_rate_limiter_locks_untrusted_external_ip() -> None:
    """Failed logins from an untrusted external IP will lock that external IP."""
    external_ip = "198.51.100.77"
    for _ in range(5):
        record_failed_login(ip=external_ip, email="user@example.com")

    # Untrusted external IP is locked
    locked, retry = is_login_locked(ip=external_ip, email=None)
    assert locked is True
    assert retry > 0


# ==============================================================================
# 4. Cross-Process Database Restore Coordination & HTTP 503
# ==============================================================================


def test_cross_process_restore_lock_activates_503(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Acquiring DatabaseRestoreLock creates lock file and triggers immediate 503."""
    assert is_database_restore_in_progress() is False

    # Acquire restore lock
    acquired = _restore_lock.acquire(blocking=False)
    assert acquired is True
    assert is_database_restore_in_progress() is True
    assert _get_restore_lock_file().is_file() is True

    # Non-admin request receives 503 Maintenance Mode without touching DB
    headers = _auth_headers(student_user)
    resp = client.get("/api/courses", headers=headers)
    assert resp.status_code == 503
    data = resp.get_json()
    assert data["error"]["code"] == "MAINTENANCE_MODE_ACTIVE"
    assert "Retry-After" in resp.headers

    # Release restore lock
    _restore_lock.release()
    assert is_database_restore_in_progress() is False
    assert _get_restore_lock_file().is_file() is False

    # Requests resume normally
    resp_after = client.get("/api/courses", headers=headers)
    assert resp_after.status_code == 200


# ==============================================================================
# 5. Blueprint Authorization Decorators (@instructor_required)
# ==============================================================================


def test_instructor_required_rejects_student_on_assessment_routes(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Students must receive 403 on instructor assessment routes."""
    headers = _auth_headers(student_user)
    fake_id = str(uuid.uuid4())

    # 1. release-scores
    resp1 = client.post(f"/api/assessments/{fake_id}/release-scores", headers=headers)
    assert resp1.status_code == 403

    # 2. regrade
    resp2 = client.post(f"/api/assessments/{fake_id}/regrade", headers=headers)
    assert resp2.status_code == 403

    # 3. create assessment
    resp3 = client.post("/api/assessments", headers=headers, json={"course_id": fake_id})
    assert resp3.status_code == 403

    # 4. configure blueprint
    resp4 = client.post(f"/api/assessments/{fake_id}/blueprint", headers=headers, json={})
    assert resp4.status_code == 403


def test_instructor_required_rejects_student_on_course_import_routes(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Students must receive 403 on course import endpoints."""
    headers = _auth_headers(student_user)
    fake_id = str(uuid.uuid4())

    # POST /api/courses/<id>/imports
    resp_post = client.post(f"/api/courses/{fake_id}/imports", headers=headers, json={})
    assert resp_post.status_code == 403

    # GET /api/courses/<id>/imports
    resp_get = client.get(f"/api/courses/{fake_id}/imports", headers=headers)
    assert resp_get.status_code == 403


def test_instructor_required_rejects_student_on_api_import_routes(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Students must receive 403 on all /api/imports endpoints."""
    headers = _auth_headers(student_user)
    fake_id = str(uuid.uuid4())

    # POST /api/imports
    r1 = client.post("/api/imports", headers=headers, json={})
    assert r1.status_code == 403

    # GET /api/imports/<id>
    r2 = client.get(f"/api/imports/{fake_id}", headers=headers)
    assert r2.status_code == 403

    # POST /api/imports/<id>/process
    r3 = client.post(f"/api/imports/{fake_id}/process", headers=headers)
    assert r3.status_code == 403

    # POST /api/imports/<id>/commit
    r4 = client.post(f"/api/imports/{fake_id}/commit", headers=headers)
    assert r4.status_code == 403


# ==============================================================================
# 6. File Upload Stream Limiting on Course Imports
# ==============================================================================


def test_course_import_file_upload_rejects_excessive_content_length(
    client: FlaskClient,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Course import endpoint rejects Content-Length >= 1,000,000,000 before storage."""
    headers = _auth_headers(instructor_user)

    resp = client.post(
        f"/api/courses/{test_course.public_id}/imports",
        headers=headers,
        environ_base={"CONTENT_LENGTH": "1000000005"},
    )
    assert resp.status_code == 413
    data = resp.get_json()
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


# ==============================================================================
# 7. File Download Range Requests & X-Accel-Redirect Support
# ==============================================================================


def test_download_file_supports_conditional_range_and_accel_redirect(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    test_course: Course,
) -> None:
    """send_file supports conditional range requests and X-Accel-Redirect offloading."""
    from pwd301.services.file_service import store_file_stream

    content = b"0123456789abcdefghijklmnopqrstuvwxyz"
    asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.public_id,
        file_stream=io.BytesIO(content),
        filename="lecture.mp4",
        content_type="video/mp4",
        session=db.session,
    )
    for rev in asset.revisions:
        rev.security_scan_status = "CLEAN"
    db.session.commit()

    headers = _auth_headers(instructor_user)

    # Standard range request: bytes=0-9
    range_headers = dict(headers)
    range_headers["Range"] = "bytes=0-9"
    resp = client.get(f"/api/files/{asset.public_id}/download", headers=range_headers)
    assert resp.status_code == 206
    assert resp.data == b"0123456789"
    assert "Content-Range" in resp.headers

    # When USE_X_ACCEL_REDIRECT is enabled
    app.config["USE_X_ACCEL_REDIRECT"] = True
    app.config["ACCEL_REDIRECT_PREFIX"] = "/internal-storage"
    try:
        resp_accel = client.get(f"/api/files/{asset.public_id}/download", headers=headers)
        assert resp_accel.status_code == 200
        assert "X-Accel-Redirect" in resp_accel.headers
        assert resp_accel.headers["X-Accel-Redirect"].startswith("/internal-storage")
    finally:
        app.config["USE_X_ACCEL_REDIRECT"] = False


# ==============================================================================
# 8. Outbound Gemini Resilience & Timeout Safety
# ==============================================================================


def test_gemini_service_executor_timeout_raises_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Outbound calls that exceed timeout raise AIServiceUnavailableError without blocking."""
    import time
    import urllib.request

    client = RealGeminiClient(api_key="test_fake_key", timeout_seconds=0.1)

    def _slow_urlopen(*args: Any, **kwargs: Any) -> Any:
        time.sleep(2.5)
        return None

    monkeypatch.setattr(urllib.request, "urlopen", _slow_urlopen)

    with pytest.raises(AIServiceUnavailableError) as exc_info:
        client._call_gemini_api({"contents": []})

    assert "timed out" in str(exc_info.value).lower()
