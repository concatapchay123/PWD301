"""Comprehensive security hardening verification tests.

Verifies:
1. REST API endpoints require @jwt_required and appropriate role (@instructor_required /
   @admin_required / @student_required).
2. Attempt essay grading and regrading are restricted to instructors/admins (403 for students).
3. AI question drafting, generation, and knowledge ingestion are restricted to instructors/admins.
4. Web /auth/logout strictly rejects GET with 405 Method Not Allowed (prevents CSRF attacks).
5. CSRF / API boundary: ambient session cookie is rejected on /api/admin/* (401),
   dedicated api_admin_bp requires Bearer JWT.
6. File upload DoS check: Content-Length >= 1 GB rejected with 413 before disk buffering.
7. RFC 6266 filename header: Vietnamese diacritics encoded properly without WSGI Latin-1 error.
8. Database restore concurrency: non-admin requests receive 503 during in-progress restore.
9. ADR-002 Zero Internal PK Leakage in prerequisites API.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import (
    change_course_status,
    create_course,
)
from pwd301.services.email_service import enqueue_email
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
)
from pwd301.services.exceptions import ConflictError, EmailRateLimitExceededError
from pwd301.services.file_service import store_file_stream
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
)
from pwd301.services.operations_service import (
    _restore_lock,
    is_database_restore_in_progress,
    restore_database_snapshot,
)
from pwd301.services.rate_limit_service import reset_all_rate_limits
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture(autouse=True)
def clean_rate_limits() -> None:
    """Ensure in-memory rate limits are clean before and after every test."""
    reset_all_rate_limits()
    yield
    reset_all_rate_limits()


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
    return register_user(f"sec_student_{uid}@example.com", "Password@123", "Sec Student")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an instructor user."""
    uid = uuid.uuid4().hex[:6]
    u = register_user(f"sec_instructor_{uid}@example.com", "Password@123", "Sec Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an admin user."""
    uid = uuid.uuid4().hex[:6]
    u = register_user(f"sec_admin_{uid}@example.com", "Password@123", "Sec Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def published_course_and_lesson(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> tuple[Course, Lesson]:
    """Create and publish a course and lesson."""
    c = create_course(
        instructor_user,
        {"course_code": f"SEC-{uuid.uuid4().hex[:4].upper()}", "title": "Security Course"},
    )
    les = create_lesson(
        instructor_user,
        c.id,
        {
            "title": "Security Lesson",
            "markdown_content": "# Security Lesson Content",
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8000,
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(instructor_user, c.id, "PUBLISHED")
    change_lesson_status(instructor_user, les.id, "PUBLISHED")
    return c, les


@pytest.fixture
def test_course(published_course_and_lesson: tuple[Course, Lesson]) -> Course:
    return published_course_and_lesson[0]


@pytest.fixture
def test_lesson(published_course_and_lesson: tuple[Course, Lesson]) -> Lesson:
    return published_course_and_lesson[1]


# ==============================================================================
# 1. API Authentication & RBAC Hardening
# ==============================================================================


def test_lesson_resources_unauthenticated_rejected(
    client: FlaskClient, test_lesson: Lesson
) -> None:
    """POST and DELETE on lesson resources require JWT authentication."""
    # POST without JWT
    resp = client.post(
        f"/api/lessons/{test_lesson.public_id}/resources",
        json={"file_asset_id": str(uuid.uuid4()), "title": "Resource"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    # DELETE without JWT
    resp_del = client.delete(f"/api/lessons/{test_lesson.public_id}/resources/{uuid.uuid4()}")
    assert resp_del.status_code == 401
    assert resp_del.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_lesson_resources_student_forbidden(
    client: FlaskClient, student_user: User, test_lesson: Lesson
) -> None:
    """Students cannot attach or detach resources on lessons (403 Forbidden)."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/lessons/{test_lesson.public_id}/resources",
        json={"file_asset_id": str(uuid.uuid4()), "title": "Resource"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    resp_del = client.delete(
        f"/api/lessons/{test_lesson.public_id}/resources/{uuid.uuid4()}",
        headers=headers,
    )
    assert resp_del.status_code == 403
    assert resp_del.get_json()["error"]["code"] == "FORBIDDEN"


def test_lesson_detail_unauthenticated_rejected(client: FlaskClient, test_lesson: Lesson) -> None:
    """GET /api/lessons/<id> requires JWT authentication."""
    resp = client.get(f"/api/lessons/{test_lesson.public_id}")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 2. IDOR & Privilege Escalation Hardening
# ==============================================================================


def test_essay_grading_student_forbidden(client: FlaskClient, student_user: User) -> None:
    """Students cannot grade essay questions (POST /api/attempts/<id>/grades/<qid>)."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    fake_attempt_id = str(uuid.uuid4())
    fake_question_id = str(uuid.uuid4())
    resp = client.post(
        f"/api/attempts/{fake_attempt_id}/grades/{fake_question_id}",
        json={"score": 10.0, "feedback": "Self grading"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_regrade_job_student_forbidden(client: FlaskClient, student_user: User) -> None:
    """Students cannot trigger regrade retries or view regrade details."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    fake_job_id = str(uuid.uuid4())
    # Detail
    resp_get = client.get(f"/api/regrade-jobs/{fake_job_id}", headers=headers)
    assert resp_get.status_code == 403
    assert resp_get.get_json()["error"]["code"] == "FORBIDDEN"

    # Retry
    resp_post = client.post(f"/api/regrade-jobs/{fake_job_id}/retry", headers=headers)
    assert resp_post.status_code == 403
    assert resp_post.get_json()["error"]["code"] == "FORBIDDEN"


def test_ai_drafting_and_ingestion_student_forbidden(
    client: FlaskClient, student_user: User, test_course: Course
) -> None:
    """Students cannot use instructor-only AI drafting and course ingestion endpoints."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Draft questions
    resp_draft = client.post(
        "/api/ai/questions/draft",
        json={"topic": "Math", "count": 2},
        headers=headers,
    )
    assert resp_draft.status_code == 403
    assert resp_draft.get_json()["error"]["code"] == "FORBIDDEN"

    # Generate questions
    resp_gen = client.post(
        "/api/ai/questions/generate",
        json={"topic": "Math", "count": 2},
        headers=headers,
    )
    assert resp_gen.status_code == 403
    assert resp_gen.get_json()["error"]["code"] == "FORBIDDEN"

    # Course knowledge ingestion
    resp_ingest = client.post(
        f"/api/ai/courses/{test_course.public_id}/ingest",
        json={"file_asset_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp_ingest.status_code == 403
    assert resp_ingest.get_json()["error"]["code"] == "FORBIDDEN"

    # Sources listing
    resp_src = client.get(
        f"/api/ai/courses/{test_course.public_id}/sources",
        headers=headers,
    )
    assert resp_src.status_code == 403
    assert resp_src.get_json()["error"]["code"] == "FORBIDDEN"


# ==============================================================================
# 3. CSRF Logout Hardening
# ==============================================================================


def test_auth_logout_rejects_get(client: FlaskClient, student_user: User) -> None:
    """GET /auth/logout must return 405 Method Not Allowed (prevents CSRF image/link logout)."""
    client.post("/auth/login", data={"email": student_user.email, "password": "Password@123"})

    resp = client.get("/auth/logout")
    assert resp.status_code == 405
    data = resp.get_json()
    if data:
        assert data.get("error", {}).get("code") == "METHOD_NOT_ALLOWED"


# ==============================================================================
# 4. CSRF / API Boundary & Dedicated api_admin_bp
# ==============================================================================


def test_api_admin_requires_jwt_and_rejects_cookie(client: FlaskClient, admin_user: User) -> None:
    """Ambient cookie sessions cannot access /api/admin/*; Bearer JWT is required."""
    client.post("/auth/login", data={"email": admin_user.email, "password": "Password@123"})

    # Ambient cookie without Authorization header
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    # Bearer JWT succeeds
    tokens = create_token_pair(admin_user)
    resp_jwt = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp_jwt.status_code == 200
    assert "users" in resp_jwt.get_json()


# ==============================================================================
# 5. File Upload DoS & RFC 6266 Headers
# ==============================================================================


def test_file_upload_dos_content_length_rejected(
    client: FlaskClient, instructor_user: User, test_course: Course
) -> None:
    """Upload request with Content-Length >= 1 GB is rejected with 413 immediately."""
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    environ_base = {"CONTENT_LENGTH": "1000000001"}
    resp = client.post(
        f"/api/courses/{test_course.public_id}/files",
        headers=headers,
        environ_base=environ_base,
    )
    assert resp.status_code == 413
    assert resp.get_json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_file_download_vietnamese_rfc6266_header(
    client: FlaskClient, instructor_user: User, test_course: Course
) -> None:
    """Downloading a file with Vietnamese diacritics sets RFC 6266 Content-Disposition header."""
    tokens = create_token_pair(instructor_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    filename = "B\u00e1o c\u00e1o \u0110\u1ed3 \u00e1n Cu\u1ed1i k\u1ef3.pdf"
    upload_resp = client.post(
        f"/api/courses/{test_course.public_id}/files",
        data={"file": (io.BytesIO(b"%PDF-1.4 sample PDF content"), filename)},
        content_type="multipart/form-data",
        headers=headers,
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.get_json()["asset_id"]

    resp = client.get(f"/api/files/{asset_id}/download", headers=headers)
    assert resp.status_code == 200
    cd = resp.headers.get("Content-Disposition", "")
    assert "filename*=UTF-8''" in cd
    # Must be valid Latin-1 encodable without throwing UnicodeEncodeError
    cd.encode("latin-1")


# ==============================================================================
# 6. Null Safety for Progress Percent
# ==============================================================================


def test_progress_percent_null_safety(
    client: FlaskClient, student_user: User, test_course: Course
) -> None:
    """Ensure e.current_progress_percent = None is safely serialized as 0.0 without TypeError."""
    from unittest.mock import MagicMock, patch

    mock_enrollment = MagicMock()
    mock_enrollment.public_id = uuid.uuid4()
    mock_enrollment.course = test_course
    mock_enrollment.student = student_user
    mock_enrollment.status = "ACTIVE"
    mock_enrollment.current_period = None
    mock_enrollment.current_progress_percent = None
    mock_enrollment.enrolled_at = None
    mock_enrollment.left_at = None
    mock_enrollment.detail_retention_due_at = None

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "pwd301.blueprints.api_student.routes.get_student_enrollments",
        return_value=[mock_enrollment],
    ):
        resp = client.get("/api/student/enrollments", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "enrollments" in data
        assert len(data["enrollments"]) == 1
        assert data["enrollments"][0]["current_progress_percent"] == 0.0


# ==============================================================================
# 7. Database Restore Concurrency Isolation
# ==============================================================================


def test_database_restore_blocks_non_admin_with_503(
    client: FlaskClient, student_user: User
) -> None:
    """When a database restore is in progress, non-admin requests receive 503."""
    from pwd301.services import operations_service

    operations_service._is_restore_in_progress = True
    try:
        assert is_database_restore_in_progress() is True

        tokens = create_token_pair(student_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.get("/api/student/profile", headers=headers)
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["error"]["code"] == "MAINTENANCE_MODE_ACTIVE"
        assert "Database restore" in data["error"]["message"]
        assert resp.headers.get("Retry-After") == "300"
    finally:
        operations_service._is_restore_in_progress = False


# ==============================================================================
# 8. ADR-002 Zero Internal PK Leakage in Prerequisites
# ==============================================================================


def test_course_prerequisites_zero_internal_pk_leakage(
    client: FlaskClient, instructor_user: User, test_course: Course
) -> None:
    """Course prerequisites API returns public_id (UUID) and no internal BIGINT pk."""
    c2 = create_course(
        instructor_user,
        {"course_code": f"PREREQ-{uuid.uuid4().hex[:4].upper()}", "title": "Prereq Course"},
    )
    add_course_prerequisite(instructor_user, test_course.id, c2.id)

    client.post("/auth/login", data={"email": instructor_user.email, "password": "Password@123"})
    resp = client.get(f"/instructor/courses/{test_course.public_id}/prerequisites")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "prerequisites" in data
    assert len(data["prerequisites"]) > 0
    for item in data["prerequisites"]:
        assert "course_id" in item
        # Verify valid UUID string
        uuid.UUID(str(item["course_id"]))
        # Verify it matches c2's public_id, NOT c2's internal integer id
        assert item["course_id"] == str(c2.public_id)
        assert item["course_id"] != c2.id


# ==============================================================================
# 9. Admin RBAC Boundary & Non-Admin Rejection (AC-SEC-01)
# ==============================================================================


def test_api_admin_forbidden_for_student_and_instructor(
    client: FlaskClient, student_user: User, instructor_user: User
) -> None:
    """Student and Instructor Bearer tokens are rejected on /api/admin/* with 403 Forbidden."""
    s_tokens = create_token_pair(student_user)
    s_headers = {"Authorization": f"Bearer {s_tokens['access_token']}"}
    resp_s = client.get("/api/admin/users", headers=s_headers)
    assert resp_s.status_code == 403
    assert resp_s.get_json()["error"]["code"] == "FORBIDDEN"

    i_tokens = create_token_pair(instructor_user)
    i_headers = {"Authorization": f"Bearer {i_tokens['access_token']}"}
    resp_i = client.get("/api/admin/users", headers=i_headers)
    assert resp_i.status_code == 403
    assert resp_i.get_json()["error"]["code"] == "FORBIDDEN"


# ==============================================================================
# 10. Security Headers Verification (AC-SEC-06)
# ==============================================================================


def test_security_headers_present_on_all_responses(client: FlaskClient) -> None:
    """All application responses enforce standard HTTP security headers (AC-SEC-06)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in resp.headers
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]


# ==============================================================================
# 11. Fail-Closed File Quarantine & Infection Access Defense (AC-SEC-03)
# ==============================================================================


def test_quarantined_and_infected_file_access_blocked(
    client: FlaskClient,
    student_user: User,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Quarantined and infected files are strictly fail-closed (AC-SEC-03: HTTP 403)."""
    enroll_student(student_user, test_course.id)

    # 1. Quarantined file
    stream_q = io.BytesIO(b"Quarantined test file content")
    asset_q = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=stream_q,
        filename="test_quarantine.pdf",
        content_type="application/pdf",
        session=db.session,
    )
    rev_q = asset_q.current_revision or asset_q.revisions[-1]
    rev_q.status = "QUARANTINED"
    db.session.commit()

    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp_q = client.get(f"/api/files/{asset_q.public_id}/download", headers=headers)
    assert resp_q.status_code == 403
    assert resp_q.get_json()["error"]["code"] == "FILE_QUARANTINED"

    # 2. Infected file
    stream_i = io.BytesIO(b"Infected test file content")
    asset_i = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=stream_i,
        filename="test_infected.pdf",
        content_type="application/pdf",
        session=db.session,
    )
    rev_i = asset_i.current_revision or asset_i.revisions[-1]
    rev_i.status = "REJECTED"
    db.session.commit()

    resp_i = client.get(f"/api/files/{asset_i.public_id}/download", headers=headers)
    assert resp_i.status_code == 403
    assert resp_i.get_json()["error"]["code"] == "FILE_INFECTED"


# ==============================================================================
# 12. Brute-Force & Rate Limiting Verification (AC-SEC-07 & Section 3.4)
# ==============================================================================


def test_login_brute_force_lockout_web_ui(client: FlaskClient, student_user: User) -> None:
    """Web login is locked out after 5 consecutive failed attempts (429 RATE_LIMIT_EXCEEDED)."""
    environ_base = {"REMOTE_ADDR": "192.168.1.50"}
    for _ in range(5):
        resp = client.post(
            "/auth/login",
            json={"email": student_user.email, "password": "WrongPassword!"},
            environ_base=environ_base,
        )
        assert resp.status_code == 401

    resp_locked = client.post(
        "/auth/login",
        json={"email": student_user.email, "password": "WrongPassword!"},
        environ_base=environ_base,
    )
    assert resp_locked.status_code == 429
    data = resp_locked.get_json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp_locked.headers


def test_login_brute_force_lockout_rest_api(client: FlaskClient, student_user: User) -> None:
    """REST API /api/auth/login is locked out after 5 consecutive failed attempts (429)."""
    environ_base = {"REMOTE_ADDR": "192.168.1.51"}
    for _ in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"email": student_user.email, "password": "WrongPassword!"},
            environ_base=environ_base,
        )
        assert resp.status_code == 401

    resp_locked = client.post(
        "/api/auth/login",
        json={"email": student_user.email, "password": "WrongPassword!"},
        environ_base=environ_base,
    )
    assert resp_locked.status_code == 429
    data = resp_locked.get_json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp_locked.headers


def test_login_success_clears_lockout_attempts(client: FlaskClient, student_user: User) -> None:
    """A successful login clears the failed attempt count for that user/IP."""
    environ_base = {"REMOTE_ADDR": "192.168.1.52"}
    for _ in range(3):
        resp = client.post(
            "/api/auth/login",
            json={"email": student_user.email, "password": "WrongPassword!"},
            environ_base=environ_base,
        )
        assert resp.status_code == 401

    resp_ok = client.post(
        "/api/auth/login",
        json={"email": student_user.email, "password": "Password@123"},
        environ_base=environ_base,
    )
    assert resp_ok.status_code == 200

    for _ in range(3):
        resp_after = client.post(
            "/api/auth/login",
            json={"email": student_user.email, "password": "WrongPassword!"},
            environ_base=environ_base,
        )
        assert resp_after.status_code == 401


def test_ai_chat_rate_limiting_enforcement(client: FlaskClient, student_user: User) -> None:
    """AI chat requests exceeding quota limit (20 req/min) are rejected with 429."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    for i in range(20):
        resp = client.post(
            "/api/ai/chat",
            headers=headers,
            json={"message": f"Hello {i}"},
        )
        assert resp.status_code == 200

    resp_blocked = client.post(
        "/api/ai/chat",
        headers=headers,
        json={"message": "Hello overflow"},
    )
    assert resp_blocked.status_code == 429
    assert resp_blocked.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_email_dispatch_rate_limiting_enforcement(app: Flask) -> None:
    """Outbound email enqueue exceeding 30 req/min raises EmailRateLimitExceededError."""
    target_email = "ratelimit_victim@example.com"
    for i in range(30):
        enqueue_email(
            recipient_email=target_email,
            subject=f"Notice {i}",
            body_text=f"Body {i}",
        )

    with pytest.raises(EmailRateLimitExceededError):
        enqueue_email(
            recipient_email=target_email,
            subject="Notice overflow",
            body_text="Body overflow",
        )


def test_database_restore_concurrency_lock(admin_user: User) -> None:
    """Simultaneous database restore attempts are blocked by concurrency lock (AC-SEC-05)."""
    acquired = _restore_lock.acquire(blocking=False)
    assert acquired is True
    try:
        with pytest.raises(
            ConflictError, match="Another database restore operation is already in progress"
        ):
            restore_database_snapshot(
                actor=admin_user,
                backup_id=str(uuid.uuid4()),
                confirmation_phrase="CONFIRM_DATABASE_RESTORE",
                password="Password@123",
            )
    finally:
        _restore_lock.release()
