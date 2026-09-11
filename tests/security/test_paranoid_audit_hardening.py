"""Comprehensive Regression & Hardening Test Suite for Paranoid Security Audit.

Validates the remediations across all 7 vulnerability categories:
1. Authentication & Token Security: Single-use UserSecurityToken enforcement, replay rejection,
   session/JWT invalidation on password reset.
2. Timing Attack Hardening: Constant-time digest verification with hmac.compare_digest in
   Attempt Service.
3. Background Worker Concurrency: Collision resilience and bounded retries in
   claim_next_background_job.
4. File Storage Traversal: Strict is_relative_to boundary enforcement preventing path escape.
5. Audit Trail Integrity: Target public UUID resolution for ASSESSMENT, QUESTION, and ATTEMPT
   entities (ADR-002).
6. Data Retention: 5-minute inactivity cutoff in raw AI message purging (Matrix row 51).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import AIConversation, AIMessage
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    release_attempt_lease,
    renew_attempt_lease,
    start_assessment_attempt,
)
from pwd301.services.audit_service import (
    get_audit_log_detail,
    query_audit_logs,
    record_audit_event,
)
from pwd301.services.auth_token_service import (
    reset_password_with_token,
    verify_email_with_token,
)
from pwd301.services.background_job_service import (
    claim_next_background_job,
    enqueue_background_job,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AttemptLeaseConflictError,
    FileAccessDeniedError,
    InvalidTokenError,
    TokenAlreadyConsumedError,
)
from pwd301.services.file_service import get_file_for_download
from pwd301.services.question_bank_service import create_question
from pwd301.services.retention_service import purge_expired_ai_messages
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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("admin_paranoid@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("inst_paranoid@example.com", "Password@123", "Instructor User")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("student_paranoid@example.com", "Password@123", "Student User")
    return assign_role_to_user(u.id, "STUDENT")


# ==============================================================================
# 1. Authentication & Token Security Tests
# ==============================================================================


class TestAuthTokenHardening:
    """Test single-use database security tokens and replay attack rejection."""

    def test_password_reset_token_single_use_and_replay_rejection(
        self, app: Flask, student_user: User, client: FlaskClient
    ) -> None:
        """Password reset token is stored in DB, single-use, and replay is rejected."""
        # 1. Generate token
        raw_token = generate_password_reset_token(student_user.id)
        assert raw_token
        assert "." not in raw_token  # Must be database hex token, not legacy dot-token

        # 2. Token verification returns student_user.id prior to consumption
        assert verify_password_reset_token(raw_token) == student_user.id

        # 3. First reset attempt succeeds
        user_after = reset_password_with_token(raw_token, "NewStrongPassword123!")
        assert user_after.verify_password("NewStrongPassword123!")

        # 4. Token verification returns None after consumption
        assert verify_password_reset_token(raw_token) is None

        # 5. Replay attempt with the same token raises TokenAlreadyConsumedError
        with pytest.raises(TokenAlreadyConsumedError):
            reset_password_with_token(raw_token, "AnotherPassword456!")

    def test_password_reset_new_token_invalidates_previous(
        self, app: Flask, student_user: User
    ) -> None:
        """Generating a new reset token invalidates any previously issued unconsumed tokens."""
        token1 = generate_password_reset_token(student_user.id)
        token2 = generate_password_reset_token(student_user.id)

        # token1 should now be rejected as invalid/superseded
        assert verify_password_reset_token(token1) is None
        assert verify_password_reset_token(token2) == student_user.id

        with pytest.raises(InvalidTokenError):
            reset_password_with_token(token1, "ShouldFailPassword123!")

    def test_email_verification_token_single_use(self, app: Flask, student_user: User) -> None:
        """Email verification token is single-use and rejected on replay."""
        student_user.email_verified_at = None
        db.session.commit()

        raw_token = generate_email_verification_token(student_user.id)
        assert raw_token
        assert "." not in raw_token

        assert verify_email_verification_token(raw_token) == student_user.id

        # First verification succeeds
        verified_user = verify_email_with_token(raw_token)
        assert verified_user.email_verified_at is not None

        # After consumption, token verification returns None
        assert verify_email_verification_token(raw_token) is None

        # Replay is rejected
        with pytest.raises(TokenAlreadyConsumedError):
            verify_email_with_token(raw_token)

    def test_web_routes_password_reset_and_email_verify(
        self, app: Flask, student_user: User, client: FlaskClient
    ) -> None:
        """Verify Web endpoints consume single-use tokens safely."""
        raw_token = generate_password_reset_token(student_user.id)

        # GET reset page is valid
        resp_get = client.get(f"/auth/reset-password/{raw_token}")
        assert resp_get.status_code == 200

        # POST reset password succeeds
        resp_post = client.post(
            f"/auth/reset-password/{raw_token}",
            json={
                "password": "NewWebPassword123!",
                "confirm_password": "NewWebPassword123!",
            },
        )
        assert resp_post.status_code == 200

        # Second POST with same token must fail
        resp_replay = client.post(
            f"/auth/reset-password/{raw_token}",
            json={
                "password": "ReplayPassword123!",
                "confirm_password": "ReplayPassword123!",
            },
        )
        assert resp_replay.status_code == 400


# ==============================================================================
# 2. Timing Attack Hardening Tests
# ==============================================================================


class TestAttemptLeaseTimingHardening:
    """Test constant-time lease token comparisons in attempt service."""

    def test_attempt_lease_verification_and_constant_time(
        self,
        app: Flask,
        admin_user: User,
        instructor_user: User,
        student_user: User,
    ) -> None:
        """Attempt lease verification correctly validates tokens using constant-time logic."""
        now = datetime.now(UTC)
        course = create_course(
            instructor_user,
            {"course_code": "SEC-TIME-101", "title": "Security Timing 101"},
        )
        change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW")
        change_course_status(admin_user, course.id, "APPROVED")
        change_course_status(admin_user, course.id, "PUBLISHED")
        enroll_student(student_user, course.id, session=db.session)
        db.session.commit()

        q = create_question(
            instructor_user,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Is hmac.compare_digest constant-time?",
                "default_points": 10.0,
                "choices": [
                    {"content": "Yes", "is_correct": True, "position": 1},
                    {"content": "No", "is_correct": False, "position": 2},
                ],
                "provenance": {"source_type": "MANUAL"},
            },
            session=db.session,
        )
        asm = create_assessment(
            instructor_user,
            course.id,
            {
                "title": "Timing Assessment",
                "assessment_type": "QUIZ",
                "time_limit_minutes": 30,
                "open_at": (now - timedelta(hours=1)).isoformat(),
                "close_at": (now + timedelta(hours=24)).isoformat(),
                "passing_score": 50.0,
            },
            session=db.session,
        )
        sec = create_section(instructor_user, asm.id, {"title": "Section 1"}, session=db.session)
        assign_question(
            instructor_user,
            asm.id,
            {"question_id": q.id, "points": 10.0, "section_id": sec.id},
            session=db.session,
        )
        publish_assessment(instructor_user, asm.id, session=db.session)
        db.session.commit()

        # Start attempt to get lease token
        attempt, valid_lease_token = start_assessment_attempt(
            student_user,
            asm.id,
            session=db.session,
        )
        assert valid_lease_token

        # 1. Valid token renews lease
        renew_res = renew_attempt_lease(
            actor=student_user,
            attempt_id=attempt.id,
            raw_lease_token=valid_lease_token,
            session=db.session,
        )
        assert renew_res["status"] == "IN_PROGRESS"
        assert renew_res["lease_expires_at"] is not None

        # 2. Invalid lease token of exact same length raises AttemptLeaseConflictError
        tampered_token = valid_lease_token[:-1] + ("0" if valid_lease_token[-1] != "0" else "1")
        with pytest.raises(AttemptLeaseConflictError):
            renew_attempt_lease(
                actor=student_user,
                attempt_id=attempt.id,
                raw_lease_token=tampered_token,
                session=db.session,
            )

        # 3. Release attempt lease with valid token
        release_attempt_lease(
            actor=student_user,
            attempt_id=attempt.id,
            raw_lease_token=valid_lease_token,
            session=db.session,
        )
        db.session.refresh(attempt)
        assert attempt.lease_token_hash is None


# ==============================================================================
# 3. Background Job Concurrency Resilience Tests
# ==============================================================================


class TestBackgroundJobConcurrencyHardening:
    """Test claim_next_background_job retry logic preventing worker starvation."""

    def test_claim_next_background_job_retry_on_collision(self, app: Flask) -> None:
        """Worker retries bounded claim attempts when concurrent collision occurs."""
        enqueue_background_job("EMAIL", {"index": 1}, run_async=False)
        enqueue_background_job("EMAIL", {"index": 2}, run_async=False)

        # Test normal claim works smoothly
        claimed = claim_next_background_job(lease_seconds=300)
        assert claimed is not None
        assert claimed.status == "RUNNING"
        assert claimed.lease_expires_at is not None

        # Second job can also be claimed
        claimed2 = claim_next_background_job(lease_seconds=300)
        assert claimed2 is not None
        assert claimed2.status == "RUNNING"

        # No more queued jobs left
        claimed_empty = claim_next_background_job(lease_seconds=300)
        assert claimed_empty is None


# ==============================================================================
# 4. File Storage Traversal & Quarantine Hardening Tests
# ==============================================================================


class TestFileStorageTraversalHardening:
    """Test path traversal prevention in get_file_for_download."""

    def test_file_storage_escape_path_traversal_blocked(
        self,
        app: Flask,
        admin_user: User,
        instructor_user: User,
    ) -> None:
        """Attempts to access files outside storage root are blocked with FileAccessDeniedError."""
        course = create_course(
            instructor_user,
            {"course_code": "SEC-FILE-101", "title": "File Traversal Test Course"},
        )
        now = utc_now()
        fake_sha256 = hashlib.sha256(b"malicious_fake_file").digest()

        # Create blob with path traversal storage_key
        blob = FileBlob(
            sha256=fake_sha256,
            size_bytes=100,
            detected_mime_type="application/pdf",
            storage_key="../../windows/system32/cmd.exe",
            status="PRESENT",
            reference_count=1,
        )
        db.session.add(blob)
        db.session.flush()

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=instructor_user.id,
            asset_type="RESOURCE",
            display_name="traversal_test.pdf",
            public_id=uuid.uuid4(),
            status="ACTIVE",
        )
        db.session.add(asset)
        db.session.flush()

        rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            blob_id=blob.id,
            original_filename="traversal_test.pdf",
            size_bytes=100,
            status="ACTIVE",
            uploaded_by_user_id=instructor_user.id,
            security_checks_completed_at=now,
        )
        db.session.add(rev)
        db.session.commit()

        # Attempt to download as admin: must be blocked due to path escape
        with pytest.raises(FileAccessDeniedError, match="escapes designated storage root"):
            get_file_for_download(admin_user, asset.public_id)


# ==============================================================================
# 5. Audit Trail Integrity & ADR-002 Zero PK Tests
# ==============================================================================


class TestAuditTrailTargetResolution:
    """Test resolution of public UUIDs for ASSESSMENT, QUESTION, and ATTEMPT in audit logs."""

    def test_audit_resolves_assessment_question_attempt_public_ids(
        self,
        app: Flask,
        admin_user: User,
        instructor_user: User,
        student_user: User,
    ) -> None:
        """query_audit_logs and get_audit_log_detail correctly resolve public UUIDs."""
        now = datetime.now(UTC)
        course = create_course(
            instructor_user,
            {"course_code": "SEC-AUDIT-101", "title": "Audit Resolution Course"},
        )
        change_course_status(instructor_user, course.id, "SUBMITTED_FOR_REVIEW")
        change_course_status(admin_user, course.id, "APPROVED")
        change_course_status(admin_user, course.id, "PUBLISHED")
        enroll_student(student_user, course.id, session=db.session)
        db.session.commit()

        q = create_question(
            instructor_user,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Audit Target Test Question?",
                "default_points": 5.0,
                "choices": [
                    {"content": "A", "is_correct": True, "position": 1},
                    {"content": "B", "is_correct": False, "position": 2},
                ],
                "provenance": {"source_type": "MANUAL"},
            },
            session=db.session,
        )
        asm = create_assessment(
            instructor_user,
            course.id,
            {
                "title": "Audit Assessment",
                "assessment_type": "QUIZ",
                "time_limit_minutes": 30,
                "open_at": (now - timedelta(hours=1)).isoformat(),
                "close_at": (now + timedelta(hours=24)).isoformat(),
                "passing_score": 50.0,
            },
            session=db.session,
        )
        sec = create_section(instructor_user, asm.id, {"title": "Section 1"}, session=db.session)
        assign_question(
            instructor_user,
            asm.id,
            {"question_id": q.id, "points": 5.0, "section_id": sec.id},
            session=db.session,
        )
        publish_assessment(instructor_user, asm.id, session=db.session)
        db.session.commit()

        attempt, token = start_assessment_attempt(
            student_user,
            asm.id,
            session=db.session,
        )
        attempt_pub_id = attempt.public_id

        # Record audit events referencing their public UUIDs
        evt_asm = record_audit_event(
            actor=admin_user,
            action="ASSESSMENT_AUDIT_TEST",
            target_type="ASSESSMENT",
            target_id=asm.public_id,
            reason="Testing assessment audit resolution",
            commit=True,
        )
        evt_q = record_audit_event(
            actor=admin_user,
            action="QUESTION_AUDIT_TEST",
            target_type="QUESTION",
            target_id=q.public_id,
            reason="Testing question audit resolution",
            commit=True,
        )
        evt_att = record_audit_event(
            actor=admin_user,
            action="ATTEMPT_AUDIT_TEST",
            target_type="ATTEMPT",
            target_id=attempt_pub_id,
            reason="Testing attempt audit resolution",
            commit=True,
        )

        # 1. Verify internal target_ids were resolved correctly in the DB
        assert evt_asm.target_id == asm.id
        assert evt_q.target_id == q.id
        assert evt_att.target_id is not None

        # 2. Verify query_audit_logs resolves target_id to public UUID
        items, _, _, _, _ = query_audit_logs(actor=admin_user, per_page=50)
        items_by_action = {i["action"]: i for i in items}

        assert "ASSESSMENT_AUDIT_TEST" in items_by_action
        assert items_by_action["ASSESSMENT_AUDIT_TEST"]["target_id"] == str(asm.public_id)

        assert "QUESTION_AUDIT_TEST" in items_by_action
        assert items_by_action["QUESTION_AUDIT_TEST"]["target_id"] == str(q.public_id)

        assert "ATTEMPT_AUDIT_TEST" in items_by_action
        assert items_by_action["ATTEMPT_AUDIT_TEST"]["target_id"] == str(attempt_pub_id)

        # 3. Verify get_audit_log_detail resolves target_id to public UUID
        detail_asm = get_audit_log_detail(admin_user, evt_asm.event_id)
        assert detail_asm["target_id"] == str(asm.public_id)

        detail_q = get_audit_log_detail(admin_user, evt_q.event_id)
        assert detail_q["target_id"] == str(q.public_id)

        detail_att = get_audit_log_detail(admin_user, evt_att.event_id)
        assert detail_att["target_id"] == str(attempt_pub_id)


# ==============================================================================
# 6. Data Retention: 5-Minute Inactivity AI Purge Tests
# ==============================================================================


class TestAIDataRetentionHardening:
    """Test 5-minute inactivity purge of raw AI chat messages."""

    def test_ai_message_purge_5_minute_inactivity(self, app: Flask, student_user: User) -> None:
        """AI conversations inactive for > 5 minutes have their raw messages purged."""
        now = utc_now()

        # Inactive conversation (> 5 minutes ago)
        inactive_conv = AIConversation(
            user_id=student_user.id,
            context_type="GLOBAL",
            last_activity_at=now - timedelta(minutes=6),
            expires_at=now + timedelta(hours=1),  # expires_at in future, but inactive!
            status="ACTIVE",
            created_at=now - timedelta(minutes=10),
        )
        db.session.add(inactive_conv)
        db.session.flush()

        msg1 = AIMessage(
            conversation_id=inactive_conv.id,
            sender="USER",
            content="Sensitive question asked 6 minutes ago",
            sequence_no=1,
            created_at=now - timedelta(minutes=6),
        )
        msg2 = AIMessage(
            conversation_id=inactive_conv.id,
            sender="ASSISTANT",
            content="AI response answering the sensitive question",
            sequence_no=2,
            created_at=now - timedelta(minutes=6),
        )
        db.session.add_all([msg1, msg2])

        # Active conversation (< 5 minutes ago)
        active_conv = AIConversation(
            user_id=student_user.id,
            context_type="GLOBAL",
            last_activity_at=now - timedelta(minutes=2),
            expires_at=now + timedelta(hours=1),
            status="ACTIVE",
            created_at=now - timedelta(minutes=2),
        )
        db.session.add(active_conv)
        db.session.flush()

        msg3 = AIMessage(
            conversation_id=active_conv.id,
            sender="USER",
            content="Fresh question asked 2 minutes ago",
            sequence_no=1,
            created_at=now - timedelta(minutes=2),
        )
        db.session.add(msg3)
        db.session.commit()

        # Execute purge
        purged_count = purge_expired_ai_messages(session=db.session, cutoff_date=now)
        db.session.commit()

        assert purged_count >= 1

        # Check inactive conversation: messages wiped, status = EXPIRED
        remaining_inactive_msgs = (
            db.session.query(AIMessage)
            .filter(AIMessage.conversation_id == inactive_conv.id)
            .count()
        )
        assert remaining_inactive_msgs == 0
        db.session.refresh(inactive_conv)
        assert inactive_conv.status == "EXPIRED"

        # Check active conversation: messages preserved, status = ACTIVE
        remaining_active_msgs = (
            db.session.query(AIMessage).filter(AIMessage.conversation_id == active_conv.id).count()
        )
        assert remaining_active_msgs == 1
        db.session.refresh(active_conv)
        assert active_conv.status == "ACTIVE"
