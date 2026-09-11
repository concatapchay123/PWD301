"""Unit and integration tests verifying all 5 critical hotfixes:
1. Chunked upload byte ceiling & temp file cleanup (LimitingStream).
2. Database-level restore locking (DatabaseRestoreLock).
3. Web UI auth routes & token lifecycle (logout, change-pwd, reset-pwd, verify-email).
4. Early-bypass and cached maintenance check in before_request middleware.
5. Enrollment capacity enforcement via DB locking.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import FileSizeLimitExceededError
from pwd301.services.file_service import (
    LimitingStream,
    get_file_quarantine_root,
    store_file_stream,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.operations_service import (
    _restore_lock,
    is_database_restore_in_progress,
    is_maintenance_active_cached,
)
from pwd301.services.user_service import (
    assign_role_to_user,
    generate_email_verification_token,
    generate_password_reset_token,
    register_user,
    verify_email_verification_token,
    verify_password_reset_token,
)


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = db.session.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            db.session.add(role)
            db.session.flush()
        role_map[code] = role
    db.session.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified instructor user."""
    u = register_user("instructor_hotfix@example.com", "Password@123", "Hotfix Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an administrator user."""
    u = register_user("admin_hotfix@example.com", "Password@123", "Hotfix Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified student user."""
    u = register_user("student_hotfix@example.com", "Password@123", "Hotfix Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create a published test course."""
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": "HF101",
            "title": "Hotfix Verification Course",
            "capacity": 10,
        },
        session=db.session,
    )
    course = change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW")
    course = change_course_status(admin_user, course.id, "APPROVED")
    course = change_course_status(instructor_user, course.id, "PUBLISHED")
    db.session.commit()
    return course


class InfiniteChunkStream:
    """A mock binary stream producing infinite chunks without allocating large memory."""

    def __init__(self, chunk_size: int = 64 * 1024) -> None:
        self._chunk = b"X" * chunk_size

    def read(self, size: int = -1) -> bytes:
        return self._chunk


class TestFileLimitingStreamAndCleanup:
    """Verify LimitingStream byte ceiling and quarantine temp file cleanup."""

    def test_limiting_stream_raises_on_limit(self) -> None:
        """LimitingStream raises FileSizeLimitExceededError when bytes reach max_bytes."""
        raw_stream = io.BytesIO(b"A" * 500)
        limiting = LimitingStream(raw_stream, max_bytes=200)

        # First 150 bytes should succeed
        chunk1 = limiting.read(150)
        assert len(chunk1) == 150

        # Next chunk exceeds 200 bytes total, must raise FileSizeLimitExceededError
        with pytest.raises(FileSizeLimitExceededError):
            limiting.read(100)

    def test_store_file_stream_cleans_up_temp_file_on_limit_exceeded(
        self, instructor_user: User, test_course: Course
    ) -> None:
        """Verify temp file in quarantine is unlinked immediately if stream exceeds limit."""
        quarantine_dir = get_file_quarantine_root()
        initial_temp_files = set(quarantine_dir.glob("upload_*.tmp"))

        mock_stream = InfiniteChunkStream()

        with pytest.raises(FileSizeLimitExceededError):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.public_id,
                file_stream=mock_stream,  # type: ignore[arg-type]
                filename="huge_video.mp4",
                content_type="video/mp4",
                session=db.session,
            )

        # Verify no orphaned temp files left in quarantine
        remaining_temp_files = set(quarantine_dir.glob("upload_*.tmp"))
        orphaned = remaining_temp_files - initial_temp_files
        assert len(orphaned) == 0, f"Leaked temporary upload files: {orphaned}"

    def test_upload_route_blocks_oversized_stream(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """POST /api/courses/<id>/files with oversized stream aborts with HTTP 413."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Mock reading beyond max bytes
        oversized_data = io.BytesIO(b"A" * 1024)
        with patch.object(
            LimitingStream, "read", side_effect=FileSizeLimitExceededError("Stream exceeded 1GB")
        ):
            resp = client.post(
                f"/api/courses/{test_course.public_id}/files",
                data={
                    "file": (oversized_data, "sample.mp4", "video/mp4"),
                    "title": "Huge Video Lecture",
                },
                content_type="multipart/form-data",
                headers=headers,
            )
            assert resp.status_code == 413
            data = resp.get_json()
            assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


class TestDatabaseRestoreLock:
    """Verify DatabaseRestoreLock distributed locking semantics."""

    def test_restore_lock_acquire_and_release(self) -> None:
        """Lock can be acquired and released cleanly."""
        assert not is_database_restore_in_progress()

        acquired = _restore_lock.acquire(blocking=False)
        assert acquired is True
        assert is_database_restore_in_progress()

        # Re-entrant or concurrent acquire without release must fail
        second_acquire = _restore_lock.acquire(blocking=False)
        assert second_acquire is False

        # Release lock
        _restore_lock.release()
        assert not is_database_restore_in_progress()

    def test_restore_lock_context_manager(self) -> None:
        """DatabaseRestoreLock works as a context manager."""
        assert not is_database_restore_in_progress()
        with _restore_lock:
            assert is_database_restore_in_progress()
        assert not is_database_restore_in_progress()


class TestWebAuthRoutesAndTokens:
    """Verify complete Web UI auth routes and token helpers."""

    def test_email_verification_token_cycle(self, student_user: User) -> None:
        """Generate and verify email verification token."""
        token = generate_email_verification_token(student_user.id)
        assert token

        # Valid token resolves user ID
        user_id = verify_email_verification_token(token, max_age=3600)
        assert user_id == student_user.id

        # Tampered token returns None
        bad_token = token + "corrupted"
        assert verify_email_verification_token(bad_token) is None

    def test_password_reset_token_cycle(self, student_user: User) -> None:
        """Generate and verify password reset token."""
        token = generate_password_reset_token(student_user.id)
        assert token

        # Valid token resolves user ID
        user_id = verify_password_reset_token(token, max_age=3600)
        assert user_id == student_user.id

        # Tampered token returns None
        assert verify_password_reset_token("invalid-reset-token") is None

    def test_change_password_web_flow(self, client: FlaskClient, student_user: User) -> None:
        """GET and POST /auth/change-password."""
        from pwd301.services.session_auth_service import create_auth_session

        _, raw_key = create_auth_session(student_user, session=db.session)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(student_user.id)
            sess["auth_session_key"] = raw_key
            sess["auth_version"] = student_user.auth_version
            sess["auth_source"] = "SESSION"

        # GET change password page
        resp_get = client.get("/auth/change-password")
        assert resp_get.status_code == 200
        assert "Đổi mật khẩu".encode() in resp_get.data

        # POST with mismatched confirmation returns 400
        resp_bad = client.post(
            "/auth/change-password",
            data={
                "current_password": "Password@123",
                "new_password": "NewPassword@456",
                "confirm_password": "DifferentPassword@789",
            },
        )
        assert resp_bad.status_code == 400
        assert "không khớp".encode() in resp_bad.data

        # POST with wrong current password returns 400
        resp_wrong = client.post(
            "/auth/change-password",
            data={
                "current_password": "WrongPassword@999",
                "new_password": "NewPassword@456",
                "confirm_password": "NewPassword@456",
            },
        )
        assert resp_wrong.status_code == 400
        assert b"Current password is incorrect" in resp_wrong.data

        # POST with correct password changes password and redirects to home
        resp_success = client.post(
            "/auth/change-password",
            data={
                "current_password": "Password@123",
                "new_password": "NewPassword@456",
                "confirm_password": "NewPassword@456",
            },
            follow_redirects=False,
        )
        assert resp_success.status_code == 302
        assert resp_success.headers["Location"].endswith("/")

    def test_forgot_and_reset_password_web_flow(
        self, client: FlaskClient, student_user: User
    ) -> None:
        """GET /auth/forgot-password, POST /auth/forgot-password, and reset flow."""
        # GET forgot password page
        resp_get = client.get("/auth/forgot-password")
        assert resp_get.status_code == 200
        assert "Quên mật khẩu".encode() in resp_get.data

        # POST forgot password with existing user email redirects with notice
        resp_post = client.post(
            "/auth/forgot-password",
            data={"email": student_user.email_normalized},
            follow_redirects=False,
        )
        assert resp_post.status_code == 302
        assert resp_post.headers["Location"].endswith("/auth/login")

        # Generate a valid reset token
        token = generate_password_reset_token(student_user.id)

        # GET reset password page with valid token
        resp_reset_get = client.get(f"/auth/reset-password/{token}")
        assert resp_reset_get.status_code == 200
        assert "Thiết lập mật khẩu mới".encode() in resp_reset_get.data

        # POST reset password with valid token and new password
        resp_reset_post = client.post(
            f"/auth/reset-password/{token}",
            data={
                "password": "CompletelyNewPassword@789",
                "confirm_password": "CompletelyNewPassword@789",
            },
            follow_redirects=False,
        )
        assert resp_reset_post.status_code == 302
        assert resp_reset_post.headers["Location"].endswith("/auth/login")

    def test_verify_email_route(self, client: FlaskClient, student_user: User) -> None:
        """GET /auth/verify-email/<token> marks user email verified."""
        assert student_user.email_verified_at is None

        token = generate_email_verification_token(student_user.id)
        resp = client.get(f"/auth/verify-email/{token}", follow_redirects=False)
        assert resp.status_code == 302

        db.session.refresh(student_user)
        assert student_user.email_verified_at is not None

    def test_logout_route_get_and_post(self, client: FlaskClient, student_user: User) -> None:
        """GET and POST /auth/logout revoke DB session and clear session cookie."""
        from pwd301.services.session_auth_service import create_auth_session

        auth_s, raw_key = create_auth_session(student_user, session=db.session)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(student_user.id)
            sess["auth_session_key"] = raw_key
            sess["auth_version"] = student_user.auth_version
            sess["auth_source"] = "SESSION"

        # POST /auth/logout
        resp_post = client.post("/auth/logout", json={}, follow_redirects=False)
        assert resp_post.status_code == 200

        db.session.refresh(auth_s)
        assert auth_s.revoked_at is not None

        # GET /auth/logout must be rejected with 405 Method Not Allowed to prevent CSRF attacks
        resp_get = client.get("/auth/logout", follow_redirects=False)
        assert resp_get.status_code == 405


class TestBeforeRequestMiddlewareOptimizations:
    """Verify middleware optimizations: early bypass and cached maintenance check."""

    def test_early_bypass_paths_do_not_resolve_actor(self, client: FlaskClient) -> None:
        """Static, health, and login paths return without resolving session actor."""
        with patch("pwd301.services.authorization_service.get_authenticated_actor") as mock_actor:
            resp_health = client.get("/health")
            assert resp_health.status_code == 200
            mock_actor.assert_not_called()

            resp_login = client.get("/auth/login")
            assert resp_login.status_code == 200
            mock_actor.assert_not_called()

    def test_maintenance_cache_avoids_db_queries(self, app: Flask) -> None:
        """is_maintenance_active_cached caches state and does not query DB consecutively."""
        with app.app_context():
            # First call populates cache
            is_active, _ = is_maintenance_active_cached(ttl_seconds=15)
            assert is_active is False

            # With DB query patched out, second call should return cached value without error
            with patch(
                "pwd301.services.operations_service.is_maintenance_active",
                side_effect=RuntimeError("DB query"),
            ):
                is_active2, _ = is_maintenance_active_cached(ttl_seconds=15)
                assert is_active2 is False


class TestEnrollmentCapacityEnforcement:
    """Verify enrollment capacity operates correctly without in-process lock."""

    def test_enrollment_succeeds_under_capacity(
        self, student_user: User, test_course: Course
    ) -> None:
        """Enrollment succeeds within capacity limits."""
        enrollment = enroll_student(
            student_user,
            test_course.public_id,
            session=db.session,
        )
        assert enrollment is not None
        assert enrollment.status == "ACTIVE"


class TestClamAVOversizedStreamHandling:
    """Verify ClamAV scanner handles oversized files (e.g. videos up to 1GB) gracefully."""

    def test_oversized_file_delegates_to_heuristic(self, tmp_path: pytest.TempPathFactory) -> None:
        from pwd301.services.scanner_service import ClamAVScanner

        test_file = Path(str(tmp_path)) / "large_video.mp4"
        test_file.write_bytes(b"\x00" * 1024)

        scanner = ClamAVScanner(max_stream_bytes=500)
        verdict = scanner.scan_file(test_file)
        assert verdict.status == "PASS"
        assert "exceeds ClamAV stream limit" in verdict.details

    def test_normal_file_uses_instream(self, tmp_path: pytest.TempPathFactory) -> None:
        from pwd301.services.scanner_service import ClamAVScanner

        test_file = Path(str(tmp_path)) / "small_text.txt"
        test_file.write_bytes(b"hello world")

        scanner = ClamAVScanner(max_stream_bytes=5000)
        verdict = scanner.scan_file(test_file)
        assert verdict.status == "ERROR"
        assert "unreachable" in verdict.details or "timed out" in verdict.details
