"""Student Assessment Attempt, Delivery & Server Timer Service for PWD301.

Implements business logic and invariants for:
- Student Assessment Delivery & Precondition Validation (ACTIVE enrollment, window, limits)
- Structural Freeze Invariant (ASSESS-002: first attempt freezes structure and points)
- Presentation Snapshot Invariant (ADR-004: freeze question content, order, choices, points)
- Server-Authoritative Timer & Deadline Engine (Algorithm 06, ADR-006: min(start+limit, close))
- Initial Active Editing Lease Baseline (Algorithm 07, ADR-005: 30s expiry, SHA-256 hash)
- ADR-002 BIGINT Primary Key Masking (public UUIDv4 and deterministic UUIDv5)
- Defensive Zero-Trust Security: own-attempt access only, zero leakage of is_correct/explanation
- Append-Only Audit Logging (ATTEMPT_STARTED)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import unicodedata
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AssessmentResultHistory,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
)
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import (
    Question,
    QuestionRevision,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import _normalize_dt, _resolve_assessment
from pwd301.services.authorization_service import (
    _resolve_attempt,
    require_course_manager,
)
from pwd301.services.completion_service import recalculate_course_completion
from pwd301.services.exceptions import (
    ActiveAttemptExistsError,
    AssessmentClosedError,
    AssessmentNotFoundError,
    AssessmentNotOpenError,
    AttemptAlreadySubmittedError,
    AttemptExpiredError,
    AttemptLeaseConflictError,
    AttemptLeaseExpiredError,
    AttemptLimitExceededError,
    AttemptNotFoundError,
    AttemptNotSubmittedError,
    AttemptValidationError,
    ForbiddenError,
    MaxPointsExceededError,
    ScoreReleasePolicyError,
    StaleAnswerSequenceError,
    StaleLeaseEpochError,
    SubmissionIdempotencyConflictError,
)

# ============================================================================
# AUDIT & LEASE HELPERS
# ============================================================================

# Constant-time dummy digest for side-channel timing attack mitigation
DUMMY_LEASE_HASH = hashlib.sha256(b"pwd301-timing-defense-lease-hash").digest()


def _record_attempt_audit(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    target_id: int,
    reason: str | None = None,
    before_json: str | None = None,
    after_json: str | None = None,
) -> AuditEvent:
    """Helper to record an append-only AuditEvent for assessment attempt actions."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="ATTEMPT",
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


def _generate_lease(lease_seconds: int | None = None) -> tuple[str, bytes, datetime, datetime]:
    """Generate raw cryptographically secure hex lease token, its SHA-256 hash, and timestamps.

    Returns:
        tuple of (raw_lease_token, lease_token_hash, lease_acquired_at, lease_expires_at)
    """
    now = utc_now()
    if lease_seconds is None:
        try:
            lease_seconds = int(current_app.config.get("ATTEMPT_LEASE_SECONDS", 30))
        except RuntimeError:
            lease_seconds = 30
    raw_token = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).digest()
    expires_at = now + timedelta(seconds=lease_seconds)
    return raw_token, token_hash, now, expires_at


# ============================================================================
# SERIALIZERS (ADR-002 Masking)
# ============================================================================


def _serialize_attempt(attempt: AssessmentAttempt) -> dict[str, Any]:
    """Serialize AssessmentAttempt hiding internal BIGINT primary keys (ADR-002)."""
    assessment_pub_id = None
    if attempt.assessment is not None:
        assessment_pub_id = str(attempt.assessment.public_id)

    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": assessment_pub_id,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "deadline_at": attempt.deadline_at.isoformat() if attempt.deadline_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "finalized_at": attempt.finalized_at.isoformat() if attempt.finalized_at else None,
        "graded_at": attempt.graded_at.isoformat() if attempt.graded_at else None,
        "lease_expires_at": (
            attempt.lease_expires_at.isoformat() if attempt.lease_expires_at else None
        ),
        "lease_epoch": attempt.lease_epoch or 1,
        "is_detail_purged": bool(attempt.is_detail_purged),
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
        "updated_at": attempt.updated_at.isoformat() if attempt.updated_at else None,
    }


def _calculate_deadline(
    assessment: Assessment,
    started_at: datetime,
) -> datetime | None:
    """Calculate server-authoritative deadline per Algorithm 06.

    assert published and now >= open_at and now < close_at
    started_at = server_now
    deadline_at = min(started_at + time_limit, close_at)
    """
    norm_start = _normalize_dt(started_at) or started_at
    close_at = _normalize_dt(assessment.close_at)
    time_limit = assessment.time_limit_minutes

    if time_limit is not None and time_limit > 0:
        nominal_deadline = norm_start + timedelta(minutes=time_limit)
        if close_at is not None:
            return min(nominal_deadline, close_at)
        return nominal_deadline
    elif close_at is not None:
        return close_at
    return None


def _check_and_expire_if_needed(
    sess: Session | scoped_session[Any],
    attempt: AssessmentAttempt,
    now: datetime | None = None,
) -> None:
    """Check attempt deadline and status; transition to EXPIRED if past deadline.

    Raises:
        AttemptExpiredError: If attempt deadline has passed or status is EXPIRED.
        AttemptValidationError: If attempt status is not IN_PROGRESS.
    """
    current_time = now if now is not None else utc_now()
    norm_now = _normalize_dt(current_time)

    deadline = _normalize_dt(attempt.deadline_at)
    close_at = (
        _normalize_dt(attempt.assessment.close_at) if attempt.assessment is not None else None
    )

    is_past_deadline = deadline is not None and norm_now is not None and norm_now >= deadline
    is_past_close = close_at is not None and norm_now is not None and norm_now >= close_at

    if attempt.status == "IN_PROGRESS" and (is_past_deadline or is_past_close):
        attempt.status = "EXPIRED"
        attempt.updated_at = current_time
        sess.flush()
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        raise AttemptExpiredError("Assessment attempt deadline has expired.")

    if attempt.status == "EXPIRED":
        raise AttemptExpiredError("Assessment attempt deadline has expired.")

    if attempt.status != "IN_PROGRESS":
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {attempt.status})."
        )


# ============================================================================
# CORE ATTEMPT SERVICE FUNCTIONS
# ============================================================================


def start_assessment_attempt(
    student_actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[AssessmentAttempt, str]:
    """Validate preconditions, materialize presentation snapshot, and start student attempt.

    Preconditions:
    1. Student account must be active.
    2. Student must have an ACTIVE enrollment in the course containing the assessment.
    3. Assessment must be PUBLISHED.
    4. Current time must be within [open_at, close_at).
    5. No concurrent active IN_PROGRESS attempt (if past deadline, transitions to EXPIRED;
       if still active, raises ActiveAttemptExistsError).
    6. Assessment attempt_limit must not be exceeded within the current enrollment period.

    Side Effects:
    - Sets assessment.first_attempt_started_at on the first attempt (Structural Freeze ASSESS-002).
    - Snapshots all fixed assignments and pool questions into attempt_questions.
    - Shuffles questions if assessment.shuffle_questions is enabled.
    - Snapshots choices with random choice_key_snapshot without is_correct.
    - Shuffles choices if configured, preserving is_fixed_position.
    - Sets was_student_exposed=True on question revision and updates question usage counts.
    - Issues editing lease (Algorithm 07 baseline) with SHA-256 hash.
    - Records append-only AuditEvent.

    Returns:
        tuple of (AssessmentAttempt, raw_lease_token).
    """
    sess = session if session is not None else db.session

    if not student_actor.is_active:
        raise AttemptValidationError("Student account is not active.")

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    # 1. Enforce student ACTIVE enrollment and resolve EnrollmentPeriod
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == student_actor.id,
            Enrollment.course_id == assessment.course_id,
        )
        .first()
    )
    if enrollment is None or enrollment.status != "ACTIVE":
        raise AttemptValidationError("Student does not have an active enrollment in this course.")

    current_period: EnrollmentPeriod | None = None
    if enrollment.current_period_id is not None:
        current_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)
    if current_period is None or current_period.status != "ACTIVE":
        current_period = (
            sess.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.enrollment_id == enrollment.id,
                EnrollmentPeriod.status == "ACTIVE",
            )
            .order_by(EnrollmentPeriod.period_no.desc())
            .first()
        )
    if current_period is None:
        raise AttemptValidationError(
            "No active enrollment period found for this student enrollment."
        )

    # 2. Enforce Assessment PUBLISHED status
    if assessment.status != "PUBLISHED":
        raise AssessmentNotOpenError(f"Assessment is not published (status: {assessment.status}).")

    # 3. Enforce Assessment timing window [open_at, close_at)
    now = utc_now()
    norm_now = _normalize_dt(now)
    open_at = _normalize_dt(assessment.open_at)
    close_at = _normalize_dt(assessment.close_at)

    if open_at is not None and norm_now is not None and norm_now < open_at:
        raise AssessmentNotOpenError("Assessment is not yet open.")
    if close_at is not None and norm_now is not None and norm_now >= close_at:
        raise AssessmentClosedError("Assessment is closed.")

    # 4. Check for concurrent IN_PROGRESS attempt
    in_progress_attempts = (
        sess.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.student_user_id == student_actor.id,
            AssessmentAttempt.status == "IN_PROGRESS",
        )
        .all()
    )
    for existing in in_progress_attempts:
        existing_deadline = _normalize_dt(existing.deadline_at)
        is_past_deadline = (
            existing_deadline is not None and norm_now is not None and norm_now >= existing_deadline
        )
        is_past_close = close_at is not None and norm_now is not None and norm_now >= close_at
        if is_past_deadline or is_past_close:
            existing.status = "EXPIRED"
            existing.updated_at = now
            sess.flush()
        else:
            raise ActiveAttemptExistsError(
                f"An active attempt ({existing.public_id}) is already in progress."
            )

    # 5. Enforce attempt_limit in the current EnrollmentPeriod
    if assessment.attempt_limit is not None and assessment.attempt_limit > 0:
        period_attempts_count = (
            sess.query(func.count(AssessmentAttempt.id))
            .filter(
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.student_user_id == student_actor.id,
                AssessmentAttempt.enrollment_period_id == current_period.id,
                AssessmentAttempt.status != "CANCELLED",
            )
            .scalar()
        ) or 0
        if period_attempts_count >= assessment.attempt_limit:
            raise AttemptLimitExceededError(
                f"Attempt limit ({assessment.attempt_limit}) reached for this enrollment period."
            )

    # 6. Compute server-authoritative deadline per Algorithm 06
    deadline_at = _calculate_deadline(assessment, now)

    # 7. Structural Freeze Trigger (ASSESS-002)
    if assessment.first_attempt_started_at is None:
        assessment.first_attempt_started_at = now
        sess.flush()

    # 8. Determine sequential attempt_number for (assessment_id, student_user_id)
    max_attempt_no = (
        sess.query(func.max(AssessmentAttempt.attempt_number))
        .filter(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.student_user_id == student_actor.id,
        )
        .scalar()
    ) or 0
    attempt_number = max_attempt_no + 1

    # 9. Generate editing lease
    raw_lease_token, lease_token_hash, lease_acquired_at, lease_expires_at = _generate_lease()

    # 10. Persist AssessmentAttempt
    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=current_period.id,
        student_user_id=student_actor.id,
        attempt_number=attempt_number,
        status="IN_PROGRESS",
        started_at=now,
        deadline_at=deadline_at,
        lease_token_hash=lease_token_hash,
        lease_acquired_at=lease_acquired_at,
        lease_expires_at=lease_expires_at,
        lease_epoch=1,
        is_detail_purged=False,
        last_heartbeat_at=lease_acquired_at,
        created_at=now,
        updated_at=now,
    )
    sess.add(attempt)
    try:
        sess.flush()
    except IntegrityError as exc:
        sess.rollback()
        raise ActiveAttemptExistsError(
            "An active attempt is already in progress for this assessment."
        ) from exc

    # 11. Collect candidate questions (fixed assignments + question pool)
    assignments = (
        sess.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == assessment.id)
        .order_by(AssessmentQuestionAssignment.position.asc())
        .all()
    )
    pool_items = (
        sess.query(AssessmentQuestionPool)
        .filter(AssessmentQuestionPool.assessment_id == assessment.id)
        .order_by(AssessmentQuestionPool.position_hint.asc(), AssessmentQuestionPool.id.asc())
        .all()
    )

    candidates: list[dict[str, Any]] = []
    seen_qids: set[int] = set()

    for a in assignments:
        seen_qids.add(a.question_id)
        candidates.append(
            {
                "question_id": a.question_id,
                "section_id": a.section_id,
                "points": a.points,
                "shuffle_choices_override": a.shuffle_choices_override,
                "is_fixed": True,
                "position": a.position,
            }
        )

    for p in pool_items:
        if p.question_id in seen_qids:
            continue
        seen_qids.add(p.question_id)
        candidates.append(
            {
                "question_id": p.question_id,
                "section_id": None,
                "points": p.points,
                "shuffle_choices_override": None,
                "is_fixed": False,
                "position": p.position_hint or 999999,
            }
        )

    if not candidates:
        raise AttemptValidationError("Assessment contains no questions to start an attempt.")

    # Apply question shuffling if configured (Algorithm 04: cryptographically secure random)
    if assessment.shuffle_questions:
        secrets.SystemRandom().shuffle(candidates)

    # 12. Freeze presentation snapshots for questions and choices
    for idx, cand in enumerate(candidates, start=1):
        q = sess.get(Question, cand["question_id"])
        if q is None:
            continue

        rev = q.current_revision
        if rev is None:
            rev = (
                sess.query(QuestionRevision)
                .filter(QuestionRevision.question_id == q.id)
                .order_by(QuestionRevision.revision_no.desc())
                .first()
            )
        if rev is None:
            continue

        attempt_q = AttemptQuestion(
            attempt_id=attempt.id,
            source_question_id=q.id,
            source_question_revision_id=rev.id,
            section_id=cand["section_id"],
            position=idx,
            question_type_snapshot=rev.question_type,
            content_snapshot=rev.content,
            explanation_snapshot=rev.explanation,
            points_assigned=cand["points"],
            choice_shuffle_applied=False,
            created_at=now,
        )
        sess.add(attempt_q)
        sess.flush()

        # Mark question revision exposure and update usage cache
        rev.was_student_exposed = True
        q.usage_count = (q.usage_count or 0) + 1
        q.last_used_at = now
        if q.first_used_at is None:
            q.first_used_at = now

        # Choice presentation snapshot
        choices = sorted(rev.choices, key=lambda c: c.position)
        if choices:
            should_shuffle = assessment.shuffle_choices
            if cand["shuffle_choices_override"] is not None:
                should_shuffle = cand["shuffle_choices_override"]

            if should_shuffle and len(choices) > 1:
                attempt_q.choice_shuffle_applied = True
                # Preserve choices with is_fixed_position=True in their original positions
                non_fixed = [c for c in choices if not c.is_fixed_position]
                secrets.SystemRandom().shuffle(non_fixed)
                ordered_choices: list[QuestionRevisionChoice] = []
                nf_iter = iter(non_fixed)
                for c in choices:
                    if c.is_fixed_position:
                        ordered_choices.append(c)
                    else:
                        ordered_choices.append(next(nf_iter))
            else:
                ordered_choices = list(choices)

            for choice_pos, choice in enumerate(ordered_choices, start=1):
                choice_snap = AttemptChoiceSnapshot(
                    attempt_question_id=attempt_q.id,
                    source_choice_id=choice.id,
                    choice_key_snapshot=choice.choice_key,
                    content_snapshot=choice.content,
                    position=choice_pos,
                    created_at=now,
                )
                sess.add(choice_snap)

    # 13. Record Audit Event
    _record_attempt_audit(
        sess=sess,
        actor=student_actor,
        action="ATTEMPT_STARTED",
        target_id=attempt.id,
        reason=f"Student started attempt #{attempt.attempt_number}",
    )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return attempt, raw_lease_token


def get_attempt_delivery(
    student_actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve the frozen assessment attempt delivery payload for candidate presentation.

    Rules:
    - IDOR defense: Student can only retrieve their own attempt.
    - Admin has platform oversight.
    - Server timer is validated: if past deadline_at, status transitions to EXPIRED.
    - Delivery payload hides all integer PKs (ADR-002), hides is_correct, and hides explanation.

    Returns:
        dict containing timer metadata, countdown, and questions delivery list.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    # Fail-closed IDOR check: own student or admin
    if not student_actor.is_admin and attempt.student_user_id != student_actor.id:
        raise ForbiddenError("You do not have permission to access this assessment attempt.")

    now = utc_now()
    norm_now = _normalize_dt(now)
    deadline = _normalize_dt(attempt.deadline_at)

    # Expiry transition check
    if (
        attempt.status == "IN_PROGRESS"
        and deadline is not None
        and norm_now is not None
        and norm_now >= deadline
    ):
        attempt.status = "EXPIRED"
        attempt.updated_at = now
        sess.flush()

    if attempt.status != "IN_PROGRESS":
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {attempt.status})."
        )

    # Calculate remaining seconds
    remaining_seconds: int | None = None
    if deadline is not None and norm_now is not None:
        diff = (deadline - norm_now).total_seconds()
        remaining_seconds = max(0, int(diff))

    questions_data: list[dict[str, Any]] = []
    total_points = Decimal("0")

    for aq in attempt.attempt_questions:
        total_points += aq.points_assigned
        # ADR-002: Direct public UUID for AttemptQuestion
        aq_public_id = (
            str(aq.public_id)
            if getattr(aq, "public_id", None)
            else str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.attempt_question.{aq.id}"))
        )

        choices_data: list[dict[str, Any]] = []
        for cs in aq.choice_snapshots:
            choices_data.append(
                {
                    "choice_key": str(cs.choice_key_snapshot),
                    "content": cs.content_snapshot,
                    "position": cs.position,
                }
            )

        section_pub_id = None
        if aq.section_id:
            section_pub_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_section.{aq.section_id}")
            )

        questions_data.append(
            {
                "attempt_question_id": aq_public_id,
                "position": aq.position,
                "question_type": aq.question_type_snapshot,
                "content": aq.content_snapshot,
                "points": float(aq.points_assigned),
                "section_id": section_pub_id,
                "choices": choices_data,
            }
        )

    assessment = attempt.assessment
    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": str(assessment.public_id) if assessment else None,
        "assessment_title": assessment.title if assessment else "",
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "deadline_at": attempt.deadline_at.isoformat() if attempt.deadline_at else None,
        "server_time": now.isoformat(),
        "remaining_seconds": remaining_seconds,
        "total_questions": len(questions_data),
        "total_points": float(total_points),
        "lease_epoch": attempt.lease_epoch or 1,
        "questions": questions_data,
    }


def list_student_assessment_attempts(
    student_actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve history of all attempts taken by a student for a specific assessment."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    attempts = (
        sess.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.student_user_id == student_actor.id,
        )
        .order_by(AssessmentAttempt.attempt_number.asc())
        .all()
    )

    now = utc_now()
    norm_now = _normalize_dt(now)
    close_at = _normalize_dt(assessment.close_at)
    mutated = False
    for att in attempts:
        if att.status == "IN_PROGRESS":
            deadline = _normalize_dt(att.deadline_at)
            is_past_deadline = (
                deadline is not None and norm_now is not None and norm_now >= deadline
            )
            is_past_close = close_at is not None and norm_now is not None and norm_now >= close_at
            if is_past_deadline or is_past_close:
                att.status = "EXPIRED"
                att.updated_at = now
                mutated = True

    if mutated:
        sess.flush()
        try:
            sess.commit()
        except Exception:
            sess.rollback()

    return [_serialize_attempt(att) for att in attempts]


# ============================================================================
# ATTEMPT LEASE MANAGEMENT & MULTI-TAB TAKEOVER (TASK-014)
# ============================================================================


def renew_attempt_lease(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    raw_lease_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Renew an active editing lease via heartbeat for an in-progress attempt.

    Preconditions & Invariants (Algorithm 07, ADR-005, ADR-006):
    1. Zero-Trust IDOR: Own-attempt access only (actor.id == attempt.student_user_id).
       Instructors or peer students are rejected with ForbiddenError (403).
    2. Attempt must be IN_PROGRESS and not past server deadline_at or close_at.
       If expired, auto-transitions to EXPIRED and raises AttemptExpiredError (409).
    3. SHA-256 digest of raw_lease_token must match attempt.lease_token_hash.
       If token does not match (taken over or invalid), raises AttemptLeaseConflictError (409).
    4. Current server time must be <= attempt.lease_expires_at.
       If lease expired, raises AttemptLeaseExpiredError (409).
    5. Extends lease_expires_at by ATTEMPT_LEASE_SECONDS (default 30s), clamped to deadline_at.
    6. Updates last_heartbeat_at = now.

    Returns:
        dict with attempt_id, status, lease_expires_at, remaining_seconds, server_time.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    # Zero-Trust IDOR check: only owning student can manage lease
    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to manage this assessment attempt lease.")

    now = utc_now()
    _check_and_expire_if_needed(sess, attempt, now)

    # Validate lease token match
    if not raw_lease_token or not isinstance(raw_lease_token, str):
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    expected_hash = (
        attempt.lease_token_hash if attempt.lease_token_hash is not None else DUMMY_LEASE_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, token_hash)
    if attempt.lease_token_hash is None or not digest_matches:
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    # Validate lease has not expired
    norm_now = _normalize_dt(now)
    lease_exp = _normalize_dt(attempt.lease_expires_at)
    if lease_exp is None or (norm_now is not None and norm_now > lease_exp):
        raise AttemptLeaseExpiredError("Editing lease was lost or taken over by another window.")

    # Compute new lease expiration clamped to deadline_at
    try:
        lease_seconds = int(current_app.config.get("ATTEMPT_LEASE_SECONDS", 30))
    except RuntimeError:
        lease_seconds = 30

    new_expiry = now + timedelta(seconds=lease_seconds)
    deadline = _normalize_dt(attempt.deadline_at)
    if deadline is not None and (_normalize_dt(new_expiry) or new_expiry) > deadline:
        new_expiry = attempt.deadline_at

    attempt.lease_expires_at = new_expiry
    attempt.last_heartbeat_at = now
    attempt.updated_at = now

    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    remaining_seconds: int | None = None
    if deadline is not None and norm_now is not None:
        diff = (deadline - norm_now).total_seconds()
        remaining_seconds = max(0, int(diff))

    return {
        "attempt_id": str(attempt.public_id),
        "status": attempt.status,
        "lease_expires_at": attempt.lease_expires_at.isoformat(),
        "remaining_seconds": remaining_seconds,
        "lease_epoch": attempt.lease_epoch or 1,
        "server_time": now.isoformat(),
    }


def takeover_attempt_lease(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[AssessmentAttempt, str]:
    """Take over the editing lease from another window/device for an in-progress attempt.

    Preconditions & Invariants (Algorithm 07, ADR-005, ADR-006):
    1. Zero-Trust IDOR: Own-attempt access only (actor.id == attempt.student_user_id).
       Instructors or peer students are rejected with ForbiddenError (403).
    2. Attempt must be IN_PROGRESS and not past server deadline_at or close_at.
       If expired, auto-transitions to EXPIRED and raises AttemptExpiredError (409).
    3. Generates new cryptographically secure 32-byte hex token, hashes with SHA-256.
    4. Overwrites lease_token_hash, invalidating the previous tab's lease immediately.
    5. Sets lease_acquired_at = now, last_heartbeat_at = now.
    6. Sets lease_expires_at = min(now + ATTEMPT_LEASE_SECONDS, deadline_at).
    7. Records append-only AuditEvent with action='LEASE_TAKEOVER'.

    Returns:
        tuple of (AssessmentAttempt, raw_lease_token).
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    # Zero-Trust IDOR check: only owning student can takeover lease
    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to manage this assessment attempt lease.")

    now = utc_now()
    _check_and_expire_if_needed(sess, attempt, now)

    # Generate new 32-byte hex lease token and hash
    try:
        lease_seconds = int(current_app.config.get("ATTEMPT_LEASE_SECONDS", 30))
    except RuntimeError:
        lease_seconds = 30

    raw_token, token_hash, acquired_at, expires_at = _generate_lease(lease_seconds=lease_seconds)

    deadline = _normalize_dt(attempt.deadline_at)
    if deadline is not None and (_normalize_dt(expires_at) or expires_at) > deadline:
        expires_at = attempt.deadline_at

    attempt.lease_token_hash = token_hash
    attempt.lease_acquired_at = acquired_at
    attempt.last_heartbeat_at = acquired_at
    attempt.lease_expires_at = expires_at
    attempt.lease_epoch = (attempt.lease_epoch or 1) + 1
    attempt.updated_at = now

    # Record Audit Event
    _record_attempt_audit(
        sess=sess,
        actor=actor,
        action="LEASE_TAKEOVER",
        target_id=attempt.id,
        reason=f"Student took over editing lease for attempt #{attempt.attempt_number}",
    )

    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return attempt, raw_token


def release_attempt_lease(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    raw_lease_token: str,
    session: Session | scoped_session[Any] | None = None,
) -> None:
    """Voluntarily release an editing lease when a tab or window closes.

    Preconditions & Invariants (Algorithm 07, ADR-005):
    1. Zero-Trust IDOR: Own-attempt access only (actor.id == attempt.student_user_id).
       Instructors or peer students are rejected with ForbiddenError (403).
    2. Validates raw_lease_token SHA-256 matches attempt.lease_token_hash.
       If mismatch, raises AttemptLeaseConflictError (409).
    3. Sets lease_token_hash = None, lease_expires_at = now.
    4. Records append-only AuditEvent with action='LEASE_RELEASED'.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    # Zero-Trust IDOR check
    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to manage this assessment attempt lease.")

    if attempt.status != "IN_PROGRESS":
        return

    if not raw_lease_token or not isinstance(raw_lease_token, str):
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    expected_hash = (
        attempt.lease_token_hash if attempt.lease_token_hash is not None else DUMMY_LEASE_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, token_hash)
    if attempt.lease_token_hash is None or not digest_matches:
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    now = utc_now()
    attempt.lease_token_hash = None
    attempt.lease_expires_at = now
    attempt.updated_at = now

    _record_attempt_audit(
        sess=sess,
        actor=actor,
        action="LEASE_RELEASED",
        target_id=attempt.id,
        reason=f"Student released editing lease for attempt #{attempt.attempt_number}",
    )

    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise


def verify_attempt_lease(
    attempt: AssessmentAttempt,
    raw_lease_token: str | None,
) -> bool:
    """Helper to verify lease validity before autosave or submission.

    Returns True if:
    - Attempt status is IN_PROGRESS
    - raw_lease_token is provided and SHA-256 matches attempt.lease_token_hash
    - Server time <= attempt.lease_expires_at
    - Server time < attempt.deadline_at (if deadline configured)
    """
    if attempt.status != "IN_PROGRESS":
        return False

    if not raw_lease_token or not isinstance(raw_lease_token, str):
        return False

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    expected_hash = (
        attempt.lease_token_hash if attempt.lease_token_hash is not None else DUMMY_LEASE_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, token_hash)
    if attempt.lease_token_hash is None or not digest_matches:
        return False

    now = utc_now()
    norm_now = _normalize_dt(now)
    lease_exp = _normalize_dt(attempt.lease_expires_at)
    if lease_exp is None or (norm_now is not None and norm_now > lease_exp):
        return False

    deadline = _normalize_dt(attempt.deadline_at)
    return not (deadline is not None and norm_now is not None and norm_now >= deadline)


def _resolve_attempt_question(
    attempt: AssessmentAttempt,
    attempt_question_id: AttemptQuestion | int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> AttemptQuestion | None:
    """Resolve AttemptQuestion within an attempt by object, internal ID, or public UUID."""
    if isinstance(attempt_question_id, AttemptQuestion):
        return attempt_question_id

    if isinstance(attempt_question_id, int):
        return (
            session.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == attempt.id,
                AttemptQuestion.id == attempt_question_id,
            )
            .first()
        )

    if isinstance(attempt_question_id, str) and attempt_question_id.isdigit():
        aq = (
            session.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == attempt.id,
                AttemptQuestion.id == int(attempt_question_id),
            )
            .first()
        )
        if aq is not None:
            return aq

    try:
        val_uuid = (
            attempt_question_id
            if isinstance(attempt_question_id, uuid.UUID)
            else uuid.UUID(str(attempt_question_id))
        )
        aq = (
            session.query(AttemptQuestion)
            .filter(
                AttemptQuestion.attempt_id == attempt.id,
                AttemptQuestion.public_id == val_uuid,
            )
            .first()
        )
        if aq is not None:
            return aq
    except (ValueError, TypeError):
        pass

    aq_list = session.query(AttemptQuestion).filter(AttemptQuestion.attempt_id == attempt.id).all()
    for aq in aq_list:
        uuid5_val = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.attempt_question.{aq.id}"))
        if uuid5_val == str(attempt_question_id):
            return aq

    return None


def save_attempt_answer(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    attempt_question_id: AttemptQuestion | int | uuid.UUID | str,
    payload: dict[str, Any],
    raw_lease_token: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Save an answer for a question with lease epoch fencing and client sequencing.

    Enforces:
    1. Zero-Trust IDOR check (actor.id == attempt.student_user_id).
    2. Attempt status is IN_PROGRESS and deadline has not expired.
    3. Valid lease token and active lease.
    4. Lease epoch fencing: If payload specifies lease_epoch, must match attempt.lease_epoch.
       If mismatch -> raises StaleLeaseEpochError (409 STALE_LEASE_EPOCH).
    5. Client sequencing: client_sequence must be strictly > last_client_sequence.
       If <= -> records rejected event and raises StaleAnswerSequenceError (409 STALE_ANSWER).
    6. Persists AttemptAnswer, AttemptAnswerChoice, and accepted AttemptAnswerEvent.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to modify this assessment attempt.")

    if attempt.status in ("SUBMITTED", "PENDING_GRADING", "GRADED"):
        raise AttemptAlreadySubmittedError("Assessment attempt has already been submitted.")

    now = utc_now()
    _check_and_expire_if_needed(sess, attempt, now)

    if attempt.status != "IN_PROGRESS":
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {attempt.status})."
        )

    # Validate lease token
    if not raw_lease_token or not isinstance(raw_lease_token, str):
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    if attempt.lease_token_hash is None or attempt.lease_token_hash != token_hash:
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    # Validate lease expiration
    norm_now = _normalize_dt(now)
    lease_exp = _normalize_dt(attempt.lease_expires_at)
    if lease_exp is None or (norm_now is not None and norm_now > lease_exp):
        raise AttemptLeaseExpiredError("Editing lease has expired.")

    # 4. Lease Epoch check
    payload_epoch = payload.get("lease_epoch")
    if payload_epoch is not None and int(payload_epoch) < (attempt.lease_epoch or 1):
        raise StaleLeaseEpochError(
            f"Stale lease epoch ({payload_epoch} < {attempt.lease_epoch or 1})."
        )

    # Resolve AttemptQuestion
    aq = _resolve_attempt_question(attempt, attempt_question_id, session=sess)
    if aq is None:
        raise AttemptValidationError("Attempt question not found in this attempt.")

    # 5. Client Sequence check
    raw_seq = payload.get("client_sequence")
    if raw_seq is None:
        raw_seq = payload.get("client_sequence_no", 0)
    try:
        client_seq = int(raw_seq)
    except (ValueError, TypeError):
        client_seq = 0
    raw_change_id = payload.get("client_change_id") or payload.get("change_id")
    try:
        change_uuid = (
            raw_change_id
            if isinstance(raw_change_id, uuid.UUID)
            else (uuid.UUID(str(raw_change_id)) if raw_change_id else uuid.uuid4())
        )
    except (ValueError, TypeError):
        change_uuid = uuid.uuid4()

    answer_record = (
        sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).first()
    )

    # Check duplicate change_id for idempotency
    existing_event = (
        sess.query(AttemptAnswerEvent)
        .filter(
            AttemptAnswerEvent.attempt_question_id == aq.id,
            AttemptAnswerEvent.change_id == change_uuid,
        )
        .first()
    )
    if existing_event is not None:
        if existing_event.accepted:
            return {
                "attempt_id": str(attempt.public_id),
                "attempt_question_id": (
                    str(aq.public_id)
                    if getattr(aq, "public_id", None)
                    else str(attempt_question_id)
                ),
                "answer_version": (
                    existing_event.server_answer_version
                    or (answer_record.answer_version if answer_record else 1)
                ),
                "last_client_sequence": (
                    answer_record.last_client_sequence if answer_record else client_seq
                ),
                "saved_at": (
                    answer_record.saved_at.isoformat()
                    if answer_record and answer_record.saved_at
                    else now.isoformat()
                ),
                "lease_epoch": attempt.lease_epoch or 1,
            }
        last_seq = answer_record.last_client_sequence if answer_record else 0
        raise StaleAnswerSequenceError(f"Stale answer sequence ({client_seq} <= {last_seq}).")

    if answer_record is not None and client_seq <= answer_record.last_client_sequence:
        # Record rejected event
        event = AttemptAnswerEvent(
            attempt_question_id=aq.id,
            change_id=change_uuid,
            client_sequence=client_seq,
            server_answer_version=answer_record.answer_version,
            payload_json=json.dumps(payload, default=str),
            received_at=now,
            accepted=False,
            rejection_reason="STALE",
        )
        sess.add(event)
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        raise StaleAnswerSequenceError(
            f"Stale answer sequence ({client_seq} <= {answer_record.last_client_sequence})."
        )

    # 6. Apply answer
    raw_answer_text = payload.get("answer_text") or payload.get("answer")
    answer_text = str(raw_answer_text).strip() if raw_answer_text is not None else None

    if answer_record is None:
        answer_record = AttemptAnswer(
            attempt_question_id=aq.id,
            answer_text=answer_text,
            answer_version=1,
            last_client_sequence=client_seq,
            last_change_id=change_uuid,
            saved_at=now,
        )
        sess.add(answer_record)
        sess.flush()
    else:
        if answer_text is not None or "answer_text" in payload or "answer" in payload:
            answer_record.answer_text = answer_text
        answer_record.answer_version = (answer_record.answer_version or 0) + 1
        answer_record.last_client_sequence = client_seq
        answer_record.last_change_id = change_uuid
        answer_record.saved_at = now
        sess.flush()

    q_target = aq.source_question or (
        sess.get(Question, aq.source_question_id) if aq.source_question_id else None
    )
    if q_target and q_target.first_answered_at is None:
        q_target.first_answered_at = now
        sess.flush()

    # Handle choices (for single/multiple choice questions)
    selected_choice_keys = (
        payload.get("selected_choice_keys")
        or payload.get("choice_keys")
        or payload.get("selected_choices")
    )
    if selected_choice_keys is None and "selected_choice_key" in payload:
        val = payload["selected_choice_key"]
        selected_choice_keys = [val] if val is not None else []

    if selected_choice_keys is not None:
        sess.query(AttemptAnswerChoice).filter(
            AttemptAnswerChoice.attempt_answer_id == answer_record.id
        ).delete()

        snapshots = (
            sess.query(AttemptChoiceSnapshot)
            .filter(AttemptChoiceSnapshot.attempt_question_id == aq.id)
            .all()
        )
        snap_map = {str(s.choice_key_snapshot): s for s in snapshots}
        for k in selected_choice_keys:
            snap = snap_map.get(str(k))
            if snap is not None:
                ac = AttemptAnswerChoice(
                    attempt_answer_id=answer_record.id,
                    attempt_choice_snapshot_id=snap.id,
                )
                sess.add(ac)

    # Record accepted AttemptAnswerEvent
    event = AttemptAnswerEvent(
        attempt_question_id=aq.id,
        change_id=change_uuid,
        client_sequence=client_seq,
        server_answer_version=answer_record.answer_version,
        payload_json=json.dumps(payload, default=str),
        received_at=now,
        accepted=True,
        rejection_reason=None,
    )
    sess.add(event)
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "attempt_id": str(attempt.public_id),
        "attempt_question_id": (
            str(aq.public_id) if getattr(aq, "public_id", None) else str(attempt_question_id)
        ),
        "answer_version": answer_record.answer_version,
        "last_client_sequence": answer_record.last_client_sequence,
        "saved_at": (
            answer_record.saved_at.isoformat() if answer_record.saved_at else now.isoformat()
        ),
        "lease_epoch": attempt.lease_epoch or 1,
    }


def sync_offline_answers(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    answers_batch: list[dict[str, Any]],
    raw_lease_token: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Synchronize a batch of offline answers accumulated while disconnected.

    Enforces:
    1. Zero-Trust IDOR check (actor.id == attempt.student_user_id).
    2. Attempt status is IN_PROGRESS and deadline has not expired.
    3. Valid lease token and active lease.
    4. Lease epoch fencing on batch items.
    5. Sorts items by client_sequence ascending and reconciles each change idempotently.
    6. Returns summary of synced and skipped questions.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to modify this assessment attempt.")

    if attempt.status in ("SUBMITTED", "PENDING_GRADING", "GRADED"):
        raise AttemptAlreadySubmittedError("Assessment attempt has already been submitted.")

    now = utc_now()
    _check_and_expire_if_needed(sess, attempt, now)

    if attempt.status != "IN_PROGRESS":
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {attempt.status})."
        )

    # Validate lease token
    if not raw_lease_token or not isinstance(raw_lease_token, str):
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    expected_hash = (
        attempt.lease_token_hash if attempt.lease_token_hash is not None else DUMMY_LEASE_HASH
    )
    digest_matches = hmac.compare_digest(expected_hash, token_hash)
    if attempt.lease_token_hash is None or not digest_matches:
        raise AttemptLeaseConflictError("Editing lease was lost or taken over by another window.")

    # Validate lease expiration
    norm_now = _normalize_dt(now)
    lease_exp = _normalize_dt(attempt.lease_expires_at)
    if lease_exp is None or (norm_now is not None and norm_now > lease_exp):
        raise AttemptLeaseExpiredError("Editing lease has expired.")

    # Validate lease epoch on batch items
    current_epoch = attempt.lease_epoch or 1
    for item in answers_batch:
        item_epoch = item.get("lease_epoch")
        if item_epoch is not None and int(item_epoch) < current_epoch:
            raise StaleLeaseEpochError(f"Stale lease epoch ({item_epoch} < {current_epoch}).")

    # Sort batch by client_sequence ascending
    sorted_items = sorted(answers_batch, key=lambda x: int(x.get("client_sequence", 0)))

    synced: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for item in sorted_items:
        q_ref = item.get("attempt_question_id") or item.get("question_id")
        if not q_ref:
            continue
        aq = _resolve_attempt_question(attempt, q_ref, session=sess)
        if aq is None:
            skipped.append(
                {
                    "attempt_question_id": str(q_ref),
                    "reason": "QUESTION_NOT_FOUND",
                }
            )
            continue

        client_seq = int(item.get("client_sequence", 0))
        raw_change_id = item.get("client_change_id") or item.get("change_id")
        try:
            change_uuid = (
                raw_change_id
                if isinstance(raw_change_id, uuid.UUID)
                else (uuid.UUID(str(raw_change_id)) if raw_change_id else uuid.uuid4())
            )
        except (ValueError, TypeError):
            change_uuid = uuid.uuid4()

        # Check existing event
        existing_event = (
            sess.query(AttemptAnswerEvent)
            .filter(
                AttemptAnswerEvent.attempt_question_id == aq.id,
                AttemptAnswerEvent.change_id == change_uuid,
            )
            .first()
        )
        if existing_event is not None:
            if existing_event.accepted:
                synced.append(
                    {
                        "attempt_question_id": str(aq.public_id),
                        "client_sequence": client_seq,
                        "answer_version": existing_event.server_answer_version,
                        "idempotent_replay": True,
                    }
                )
            else:
                skipped.append(
                    {
                        "attempt_question_id": str(aq.public_id),
                        "client_sequence": client_seq,
                        "reason": existing_event.rejection_reason or "STALE",
                    }
                )
            continue

        answer_record = (
            sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).first()
        )

        if answer_record is not None and client_seq <= answer_record.last_client_sequence:
            event = AttemptAnswerEvent(
                attempt_question_id=aq.id,
                change_id=change_uuid,
                client_sequence=client_seq,
                server_answer_version=answer_record.answer_version,
                payload_json=json.dumps(item, default=str),
                received_at=now,
                accepted=False,
                rejection_reason="STALE",
            )
            sess.add(event)
            sess.flush()
            skipped.append(
                {
                    "attempt_question_id": str(aq.public_id),
                    "client_sequence": client_seq,
                    "reason": "STALE",
                }
            )
            continue

        raw_answer_text = item.get("answer_text") or item.get("answer")
        answer_text = str(raw_answer_text).strip() if raw_answer_text is not None else None

        if answer_record is None:
            answer_record = AttemptAnswer(
                attempt_question_id=aq.id,
                answer_text=answer_text,
                answer_version=1,
                last_client_sequence=client_seq,
                last_change_id=change_uuid,
                saved_at=now,
            )
            sess.add(answer_record)
            sess.flush()
        else:
            if answer_text is not None or "answer_text" in item or "answer" in item:
                answer_record.answer_text = answer_text
            answer_record.answer_version = (answer_record.answer_version or 0) + 1
            answer_record.last_client_sequence = client_seq
            answer_record.last_change_id = change_uuid
            answer_record.saved_at = now
            sess.flush()

        q_target = aq.source_question or (
            sess.get(Question, aq.source_question_id) if aq.source_question_id else None
        )
        if q_target and q_target.first_answered_at is None:
            q_target.first_answered_at = now
            sess.flush()

        # Choices
        selected_choice_keys = (
            item.get("selected_choice_keys")
            or item.get("choice_keys")
            or item.get("selected_choices")
        )
        if selected_choice_keys is None and "selected_choice_key" in item:
            val = item["selected_choice_key"]
            selected_choice_keys = [val] if val is not None else []

        if selected_choice_keys is not None:
            sess.query(AttemptAnswerChoice).filter(
                AttemptAnswerChoice.attempt_answer_id == answer_record.id
            ).delete()

            snapshots = (
                sess.query(AttemptChoiceSnapshot)
                .filter(AttemptChoiceSnapshot.attempt_question_id == aq.id)
                .all()
            )
            snap_map = {str(s.choice_key_snapshot): s for s in snapshots}
            for k in selected_choice_keys:
                snap = snap_map.get(str(k))
                if snap is not None:
                    ac = AttemptAnswerChoice(
                        attempt_answer_id=answer_record.id,
                        attempt_choice_snapshot_id=snap.id,
                    )
                    sess.add(ac)

        event = AttemptAnswerEvent(
            attempt_question_id=aq.id,
            change_id=change_uuid,
            client_sequence=client_seq,
            server_answer_version=answer_record.answer_version,
            payload_json=json.dumps(item, default=str),
            received_at=now,
            accepted=True,
            rejection_reason=None,
        )
        sess.add(event)
        sess.flush()

        synced.append(
            {
                "attempt_question_id": str(aq.public_id),
                "client_sequence": client_seq,
                "answer_version": answer_record.answer_version,
            }
        )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "attempt_id": str(attempt.public_id),
        "synced_count": len(synced),
        "skipped_count": len(skipped),
        "synced": synced,
        "skipped": skipped,
        "lease_epoch": attempt.lease_epoch or 1,
    }


def submit_assessment_attempt(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    idempotency_key: uuid.UUID | str | None = None,
    raw_lease_token: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Submit an assessment attempt with idempotent replay and lease revocation.

    Enforces:
    1. Zero-Trust IDOR check (actor.id == attempt.student_user_id).
    2. Server-Authoritative Timer: auto-expires if now >= deadline_at or now >= close_at.
    3. Idempotency Check:
       - If attempt.status == 'SUBMITTED' and key matches -> returns original result (200).
       - If attempt.status == 'SUBMITTED' and key differs ->
         raises SubmissionIdempotencyConflictError (409).
    4. Precondition: attempt.status must be 'IN_PROGRESS'.
    5. Atomically transitions to 'SUBMITTED', sets timestamps, saves submission_idempotency_key.
    6. Revokes editing lease (lease_token_hash, lease_expires_at, editor_session_id cleared).
    7. Records append-only AuditEvent (ATTEMPT_SUBMITTED).
    8. Handles concurrent races safely.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to submit this assessment attempt.")

    # Parse and validate idempotency key
    if idempotency_key is None:
        key_uuid = uuid.uuid4()
    elif isinstance(idempotency_key, uuid.UUID):
        key_uuid = idempotency_key
    else:
        try:
            key_uuid = uuid.UUID(str(idempotency_key).strip())
        except (ValueError, TypeError) as err:
            raise AttemptValidationError(
                "Invalid submission idempotency key format; must be a valid UUID."
            ) from err

    # Idempotent replay check if already SUBMITTED / PENDING_GRADING / GRADED
    if attempt.status in ("SUBMITTED", "PENDING_GRADING", "GRADED"):
        if attempt.submission_idempotency_key is not None and str(
            attempt.submission_idempotency_key
        ) == str(key_uuid):
            return {
                "attempt_id": str(attempt.public_id),
                "status": attempt.status,
                "attempt_number": attempt.attempt_number,
                "submitted_at": (
                    attempt.submitted_at.isoformat() if attempt.submitted_at else None
                ),
                "finalized_at": (
                    attempt.finalized_at.isoformat() if attempt.finalized_at else None
                ),
                "submission_idempotency_key": str(attempt.submission_idempotency_key),
                "is_idempotent_replay": True,
                "message": "Assessment attempt already submitted (idempotent replay).",
            }
        else:
            raise SubmissionIdempotencyConflictError(
                "Attempt has already been submitted with a different idempotency key."
            )

    now = utc_now()
    _check_and_expire_if_needed(sess, attempt, now)

    if attempt.status != "IN_PROGRESS":
        if attempt.status == "EXPIRED":
            raise AttemptExpiredError("Assessment attempt deadline has expired.")
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {attempt.status})."
        )

    # Validate lease token if provided
    if raw_lease_token is not None and isinstance(raw_lease_token, str):
        token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
        expected_hash = (
            attempt.lease_token_hash if attempt.lease_token_hash is not None else DUMMY_LEASE_HASH
        )
        digest_matches = hmac.compare_digest(expected_hash, token_hash)
        if attempt.lease_token_hash is not None and not digest_matches:
            raise AttemptLeaseConflictError(
                "Editing lease was lost or taken over by another window."
            )

    # Atomically update attempt if and only if status is still 'IN_PROGRESS'
    try:
        updated_rows = (
            sess.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.id == attempt.id,
                AssessmentAttempt.status == "IN_PROGRESS",
            )
            .update(
                {
                    "status": "SUBMITTED",
                    "submitted_at": now,
                    "finalized_at": now,
                    "submission_idempotency_key": key_uuid,
                    "lease_token_hash": None,
                    "lease_expires_at": None,
                    "editor_session_id": None,
                    "updated_at": now,
                },
                synchronize_session=False,
            )
        )
    except (OperationalError, DBAPIError):
        # Database lock contention / serialization conflict under concurrent requests
        sess.rollback()
        updated_rows = 0

    if updated_rows == 0:
        # Another concurrent request transitioned or submitted this attempt
        reloaded: AssessmentAttempt | None = None
        for _ in range(10):
            sess.expire_all()
            reloaded = (
                sess.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt.id).first()
            )
            if reloaded is not None and reloaded.status in (
                "SUBMITTED",
                "PENDING_GRADING",
                "GRADED",
            ):
                break
            time.sleep(0.05)

        if reloaded is not None and reloaded.status in ("SUBMITTED", "PENDING_GRADING", "GRADED"):
            if reloaded.submission_idempotency_key is not None and str(
                reloaded.submission_idempotency_key
            ) == str(key_uuid):
                return {
                    "attempt_id": str(reloaded.public_id),
                    "status": reloaded.status,
                    "attempt_number": reloaded.attempt_number,
                    "submitted_at": (
                        reloaded.submitted_at.isoformat() if reloaded.submitted_at else None
                    ),
                    "finalized_at": (
                        reloaded.finalized_at.isoformat() if reloaded.finalized_at else None
                    ),
                    "submission_idempotency_key": str(reloaded.submission_idempotency_key),
                    "is_idempotent_replay": True,
                    "message": "Assessment attempt already submitted (idempotent replay).",
                }
            raise SubmissionIdempotencyConflictError(
                "Attempt has already been submitted with a different idempotency key."
            )
        status_str = reloaded.status if reloaded else "UNKNOWN"
        raise AttemptValidationError(
            f"Assessment attempt is not in progress (status: {status_str})."
        )

    # Transition succeeded
    attempt.status = "SUBMITTED"
    attempt.submitted_at = now
    attempt.finalized_at = now
    attempt.submission_idempotency_key = key_uuid
    attempt.lease_token_hash = None
    attempt.lease_expires_at = None
    attempt.editor_session_id = None

    # Record append-only audit event
    _record_attempt_audit(
        sess=sess,
        actor=actor,
        action="ATTEMPT_SUBMITTED",
        target_id=attempt.id,
        reason=f"Student submitted attempt #{attempt.attempt_number}",
    )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    # Trigger objective auto-grading engine (Algorithm 10)
    grade_attempt_objective_questions(attempt, session=sess)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "attempt_id": str(attempt.public_id),
        "status": attempt.status,
        "attempt_number": attempt.attempt_number,
        "submitted_at": attempt.submitted_at.isoformat(),
        "finalized_at": attempt.finalized_at.isoformat(),
        "submission_idempotency_key": str(attempt.submission_idempotency_key),
        "is_idempotent_replay": False,
        "message": "Assessment attempt submitted successfully.",
    }


# ============================================================================
# GRADING ENGINE & RESULT AGGREGATION (Algorithm 10)
# ============================================================================


def _serialize_attempt_grade(grade: AttemptQuestionGrade, aq: AttemptQuestion) -> dict[str, Any]:
    """Serialize AttemptQuestionGrade without leaking internal BIGINT PKs (ADR-002)."""
    return {
        "attempt_question_id": str(aq.public_id),
        "position": aq.position,
        "question_type": aq.question_type_snapshot,
        "points_assigned": float(aq.points_assigned),
        "awarded_points": float(grade.awarded_points),
        "grading_status": grade.grading_status,
        "grading_rule": grade.grading_rule,
        "graded_at": grade.graded_at.isoformat() if grade.graded_at else None,
        "manual_reason": grade.manual_reason,
    }


def _serialize_assessment_result(
    result: AssessmentResult, attempt: AssessmentAttempt
) -> dict[str, Any]:
    """Serialize AssessmentResult without leaking internal BIGINT PKs (ADR-002)."""
    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": str(attempt.assessment.public_id) if attempt.assessment else None,
        "attempt_number": attempt.attempt_number,
        "raw_score": float(result.raw_score),
        "max_score": float(result.max_score),
        "percent_score": float(result.percent_score) if result.percent_score is not None else None,
        "passed": result.passed,
        "status": result.status,
        "released_at": result.released_at.isoformat() if result.released_at else None,
        "graded_at": result.graded_at.isoformat() if result.graded_at else None,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
    }


def calculate_attempt_result(
    attempt: AssessmentAttempt,
    actor: User | None = None,
    reason: str = "Initial automated grading",
    reason_code: str = "INITIAL",
    regrade_job_id: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentResult:
    """Aggregate question grades into AssessmentResult and append history.

    Calculations:
    - raw_score = sum(awarded_points)
    - max_score = sum(points_assigned)
    - percent_score = (raw_score / max_score) * 100
    - passed = percent_score >= passing_percent (if configured, else True)
    - Status evaluation: PENDING if any question has grading_status == 'PENDING',
      otherwise FINAL or RELEASED based on score_release_policy.
    """
    sess = session if session is not None else db.session
    now = utc_now()
    assessment = attempt.assessment

    raw_score = Decimal("0.0000")
    max_score = Decimal("0.0000")
    has_pending = False

    for aq in attempt.attempt_questions:
        max_score += Decimal(str(aq.points_assigned))
        grade = aq.current_grade or (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        if grade is not None:
            raw_score += Decimal(str(grade.awarded_points))
            if grade.grading_status == "PENDING":
                has_pending = True
        else:
            has_pending = True

    if max_score <= Decimal("0"):
        max_score = Decimal("1.0000")

    percent_score: Decimal | None = None
    passed: bool | None = None
    status: str = "PENDING"
    released_at: datetime | None = None
    graded_at: datetime | None = None

    if not has_pending:
        pct = (raw_score / max_score) * Decimal("100.0")
        percent_score = Decimal(str(round(float(pct), 4)))
        graded_at = now

        if assessment and assessment.passing_percent is not None:
            passed = bool(percent_score >= Decimal(str(assessment.passing_percent)))
        else:
            passed = True

        policy = assessment.score_release_policy if assessment else "IMMEDIATE"
        if policy == "IMMEDIATE":
            status = "RELEASED"
            released_at = now
        elif policy == "AFTER_CLOSE":
            close_at = _normalize_dt(assessment.close_at) if assessment else None
            curr_now = _normalize_dt(now)
            if close_at and curr_now and curr_now >= close_at:
                status = "RELEASED"
                released_at = now
            else:
                status = "FINAL"
                released_at = None
        else:  # INSTRUCTOR_RELEASE
            if attempt.result and attempt.result.status == "RELEASED":
                status = "RELEASED"
                released_at = attempt.result.released_at or now
            else:
                status = "FINAL"
                released_at = None
    else:
        status = "PENDING"
        percent_score = None
        passed = None

    result = attempt.result or (
        sess.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()
    )
    old_score = result.raw_score if result else None
    old_percent = result.percent_score if result else None

    if result is None:
        result = AssessmentResult(
            attempt_id=attempt.id,
            raw_score=raw_score,
            max_score=max_score,
            percent_score=percent_score,
            passed=passed,
            status=status,
            released_at=released_at,
            graded_at=graded_at,
            updated_at=now,
        )
        attempt.result = result
        sess.add(result)
        sess.flush()
    else:
        result.raw_score = raw_score
        result.max_score = max_score
        result.percent_score = percent_score
        result.passed = passed
        result.status = status
        if released_at is not None:
            result.released_at = released_at
        if graded_at is not None:
            result.graded_at = graded_at
        result.updated_at = now
        sess.flush()

    valid_reason_code = (
        reason_code if reason_code in ("INITIAL", "REGRADE", "MANUAL", "CORRECTION") else "MANUAL"
    )
    history_entry = AssessmentResultHistory(
        attempt_id=attempt.id,
        old_score=old_score,
        new_score=raw_score,
        old_percent=old_percent,
        new_percent=percent_score,
        reason_code=valid_reason_code,
        reason=reason,
        actor_user_id=actor.id if actor else None,
        regrade_job_id=regrade_job_id,
        created_at=now,
    )
    sess.add(history_entry)
    sess.flush()

    return result


def grade_attempt_objective_questions(
    attempt: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Automatically grade all objective questions for an assessment attempt.

    Evaluates:
    - SINGLE_CHOICE: Exactly 1 selected choice with is_correct = True -> 100% points, else 0.
    - TRUE_FALSE: Exactly 1 selected choice with is_correct = True -> 100% points, else 0.
    - MULTIPLE_CHOICE: Exact set match with all correct choices -> 100% points, else 0.
    - SHORT_ANSWER: Normalized text match against accepted answers -> 100% points, else 0.
    - ESSAY: Sets status to PENDING with 0 points and MANUAL rule.

    Transition:
    - If no ESSAY questions: attempt.status -> 'GRADED', graded_at = utc_now().
    - If has ESSAY question: attempt.status -> 'PENDING_GRADING'.
    """
    sess = session if session is not None else db.session
    resolved_attempt = _resolve_attempt(attempt, session=sess)
    if resolved_attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    now = utc_now()
    has_essay = False

    for aq in resolved_attempt.attempt_questions:
        q_type = aq.question_type_snapshot
        assigned_pts = Decimal(str(aq.points_assigned))
        awarded_pts = Decimal("0.0000")
        grading_status = "AUTO_GRADED"
        grading_rule = "ORIGINAL"
        is_essay = False

        ans = aq.current_answer or (
            sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).first()
        )
        selected_snaps = (
            (
                sess.query(AttemptChoiceSnapshot)
                .join(
                    AttemptAnswerChoice,
                    AttemptAnswerChoice.attempt_choice_snapshot_id == AttemptChoiceSnapshot.id,
                )
                .filter(AttemptAnswerChoice.attempt_answer_id == ans.id)
                .all()
            )
            if ans
            else []
        )

        if q_type in ("SINGLE_CHOICE", "TRUE_FALSE"):
            if len(selected_snaps) == 1:
                sel = selected_snaps[0]
                is_correct = False
                if sel.source_choice_id is not None:
                    c = sess.get(QuestionRevisionChoice, sel.source_choice_id)
                    if c is not None:
                        is_correct = bool(c.is_correct)
                if not is_correct:
                    rev = aq.source_question_revision or (
                        sess.get(QuestionRevision, aq.source_question_revision_id)
                        if aq.source_question_revision_id
                        else None
                    )
                    if rev:
                        for c in rev.choices:
                            if str(c.choice_key).lower() == str(sel.choice_key_snapshot).lower():
                                is_correct = bool(c.is_correct)
                                break
                if is_correct:
                    awarded_pts = assigned_pts
        elif q_type == "MULTIPLE_CHOICE":
            rev = aq.source_question_revision or (
                sess.get(QuestionRevision, aq.source_question_revision_id)
                if aq.source_question_revision_id
                else None
            )
            correct_keys = (
                {str(c.choice_key).lower() for c in rev.choices if c.is_correct} if rev else set()
            )
            selected_keys = {str(sel.choice_key_snapshot).lower() for sel in selected_snaps}
            if len(correct_keys) > 0 and selected_keys == correct_keys:
                awarded_pts = assigned_pts
        elif q_type == "SHORT_ANSWER":
            if ans and ans.answer_text:
                student_text = ans.answer_text.strip()
                rev = aq.source_question_revision or (
                    sess.get(QuestionRevision, aq.source_question_revision_id)
                    if aq.source_question_revision_id
                    else None
                )
                accepted = rev.accepted_answers if rev else []
                match_mode = (rev.short_answer_match_mode if rev else None) or "NORMALIZED"

                if match_mode == "EXACT":
                    for aa in accepted:
                        if student_text == aa.answer_text.strip():
                            awarded_pts = assigned_pts
                            break
                else:
                    norm_student = unicodedata.normalize("NFKC", student_text.lower())
                    for aa in accepted:
                        cand = aa.answer_normalized or aa.answer_text
                        cand_norm = unicodedata.normalize("NFKC", cand.strip().lower())
                        if norm_student == cand_norm:
                            awarded_pts = assigned_pts
                            break
        elif q_type == "ESSAY":
            has_essay = True
            is_essay = True
            awarded_pts = Decimal("0.0000")
            grading_status = "PENDING"
            grading_rule = "MANUAL"
        else:
            awarded_pts = Decimal("0.0000")

        grade = aq.current_grade or (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        old_points = grade.awarded_points if grade else None
        if grade is None:
            grade = AttemptQuestionGrade(
                attempt_question_id=aq.id,
                awarded_points=awarded_pts,
                grading_status=grading_status,
                grading_rule=grading_rule,
                graded_against_revision_id=aq.source_question_revision_id,
                graded_at=None if is_essay else now,
            )
            aq.current_grade = grade
            sess.add(grade)
        else:
            grade.awarded_points = awarded_pts
            grade.grading_status = grading_status
            grade.grading_rule = grading_rule
            grade.graded_against_revision_id = aq.source_question_revision_id
            grade.graded_at = None if is_essay else now

        rev_target = aq.source_question_revision or (
            sess.get(QuestionRevision, aq.source_question_revision_id)
            if aq.source_question_revision_id
            else None
        )
        if rev_target is not None:
            rev_target.was_used_for_grading = True

        sess.flush()

        grade_hist = AttemptQuestionGradeHistory(
            attempt_question_id=aq.id,
            old_points=old_points,
            new_points=awarded_pts,
            reason_code="INITIAL",
            reason="Initial pending essay evaluation" if is_essay else "Initial automated grading",
            actor_user_id=None,
            created_at=now,
        )
        sess.add(grade_hist)

    sess.flush()

    if not has_essay:
        resolved_attempt.status = "GRADED"
        resolved_attempt.graded_at = now
        res = calculate_attempt_result(
            attempt=resolved_attempt,
            actor=None,
            reason="Initial automated grading",
            reason_code="INITIAL",
            session=sess,
        )
        if (
            res.passed
            and resolved_attempt.assessment
            and resolved_attempt.assessment.is_required_for_completion
        ):
            recalculate_course_completion(
                student_user_id=resolved_attempt.student_user_id,
                course_id=resolved_attempt.assessment.course_id,
                session=sess,
            )
    else:
        resolved_attempt.status = "PENDING_GRADING"
        res = calculate_attempt_result(
            attempt=resolved_attempt,
            actor=None,
            reason="Initial pending essay evaluation",
            reason_code="INITIAL",
            session=sess,
        )

    resolved_attempt.updated_at = now
    sess.flush()

    return {
        "attempt_id": str(resolved_attempt.public_id),
        "status": resolved_attempt.status,
        "has_essay": has_essay,
        "result": _serialize_assessment_result(res, resolved_attempt),
    }


def grade_essay_question(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    attempt_question_id: AttemptQuestion | int | uuid.UUID | str,
    awarded_points: float | Decimal | int | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Grade or update manual score for an essay question.

    Invariants:
    - Actor must be managing instructor or system administrator.
    - Attempt must be in terminal or pending grading state (cannot be IN_PROGRESS).
    - 0 <= awarded_points <= points_assigned (raises MaxPointsExceededError).
    - Appends history to AttemptQuestionGradeHistory (reason_code='MANUAL_REVISION').
    - If all questions are now graded, attempt transitions to 'GRADED'.
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.status == "IN_PROGRESS":
        raise AttemptNotSubmittedError("Cannot grade an attempt that is still in progress.")

    if attempt.assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")
    require_course_manager(actor, attempt.assessment.course_id, session=sess)

    aq: AttemptQuestion | None = None
    if isinstance(attempt_question_id, AttemptQuestion):
        aq = attempt_question_id
    elif isinstance(attempt_question_id, int):
        aq = sess.get(AttemptQuestion, attempt_question_id)
    elif isinstance(attempt_question_id, uuid.UUID):
        aq = (
            sess.query(AttemptQuestion)
            .filter(AttemptQuestion.public_id == attempt_question_id)
            .first()
        )
    elif isinstance(attempt_question_id, str):
        try:
            val_uuid = uuid.UUID(attempt_question_id.strip())
            aq = sess.query(AttemptQuestion).filter(AttemptQuestion.public_id == val_uuid).first()
        except ValueError:
            if attempt_question_id.isdigit():
                aq = sess.get(AttemptQuestion, int(attempt_question_id))

    if aq is None or aq.attempt_id != attempt.id:
        raise AttemptValidationError("Attempt question not found for this attempt.")

    try:
        dec_points = Decimal(str(awarded_points))
    except (ValueError, TypeError) as err:
        raise AttemptValidationError("Invalid awarded_points value; must be numeric.") from err

    if dec_points < Decimal("0"):
        raise MaxPointsExceededError("Awarded points cannot be negative.")
    if dec_points > aq.points_assigned:
        raise MaxPointsExceededError(
            f"Awarded points ({dec_points}) exceed maximum assigned points ({aq.points_assigned})."
        )

    now = utc_now()
    grade = aq.current_grade or (
        sess.query(AttemptQuestionGrade)
        .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
        .first()
    )
    old_points = grade.awarded_points if grade else None

    if grade is None:
        grade = AttemptQuestionGrade(
            attempt_question_id=aq.id,
            awarded_points=dec_points,
            grading_status="MANUAL_GRADED",
            grading_rule="MANUAL",
            graded_against_revision_id=aq.source_question_revision_id,
            graded_by_user_id=actor.id,
            graded_at=now,
            manual_reason=reason,
        )
        sess.add(grade)
    else:
        grade.awarded_points = dec_points
        grade.grading_status = "MANUAL_GRADED"
        grade.grading_rule = "MANUAL"
        grade.graded_by_user_id = actor.id
        grade.graded_at = now
        grade.manual_reason = reason

    rev_target = aq.source_question_revision or (
        sess.get(QuestionRevision, aq.source_question_revision_id)
        if aq.source_question_revision_id
        else None
    )
    if rev_target is not None:
        rev_target.was_used_for_grading = True

    sess.flush()

    grade_hist = AttemptQuestionGradeHistory(
        attempt_question_id=aq.id,
        old_points=old_points,
        new_points=dec_points,
        reason_code="MANUAL_REVISION",
        reason=reason or "Manual essay grade by instructor",
        actor_user_id=actor.id,
        created_at=now,
    )
    sess.add(grade_hist)
    sess.flush()

    pending_count = (
        sess.query(AttemptQuestionGrade)
        .join(AttemptQuestion, AttemptQuestion.id == AttemptQuestionGrade.attempt_question_id)
        .filter(
            AttemptQuestion.attempt_id == attempt.id,
            AttemptQuestionGrade.grading_status == "PENDING",
        )
        .count()
    )

    if pending_count == 0:
        attempt.status = "GRADED"
        attempt.graded_at = now
        attempt.updated_at = now
        sess.flush()
        res = calculate_attempt_result(
            attempt=attempt,
            actor=actor,
            reason=reason or "Manual grading finalized",
            reason_code="MANUAL",
            session=sess,
        )
        if res.passed and attempt.assessment and attempt.assessment.is_required_for_completion:
            recalculate_course_completion(
                student_user_id=attempt.student_user_id,
                course_id=attempt.assessment.course_id,
                session=sess,
            )
    else:
        res = calculate_attempt_result(
            attempt=attempt,
            actor=actor,
            reason=reason or "Manual grade updated",
            reason_code="MANUAL",
            session=sess,
        )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "attempt_id": str(attempt.public_id),
        "attempt_question_id": str(aq.public_id),
        "awarded_points": float(dec_points),
        "grading_status": grade.grading_status,
        "attempt_status": attempt.status,
        "is_finalized": (pending_count == 0),
        "result": _serialize_assessment_result(res, attempt),
    }


def get_attempt_result_for_student(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve attempt result for student respecting score and answer release policies.

    Invariants:
    - Student can only view their own attempt; managing instructor or admin can view all.
    - score_release_policy ('IMMEDIATE', 'AFTER_CLOSE', 'INSTRUCTOR_RELEASE'):
      If not yet released, returns score_status='SCORE_HIDDEN' with masked scores.
    - answer_visibility_policy ('IMMEDIATE', 'AFTER_CLOSE', 'AFTER_ALL_ATTEMPTS', 'NEVER'):
      Controls visibility of explanations and question-level breakdowns.
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    is_owner = attempt.student_user_id == actor.id
    is_admin = actor.is_admin
    is_manager = False
    if attempt.assessment and actor.has_role("INSTRUCTOR"):
        is_manager = attempt.assessment.course.owner_instructor_id == actor.id

    if not (is_owner or is_admin or is_manager):
        raise ForbiddenError("You do not have permission to view this attempt result.")

    assessment = attempt.assessment
    result = attempt.result
    now = utc_now()

    is_score_released = False
    if is_admin or is_manager:
        is_score_released = True
    elif attempt.status in ("IN_PROGRESS", "PENDING_GRADING"):
        is_score_released = False
    elif assessment is None:
        is_score_released = True
    else:
        policy = assessment.score_release_policy
        if policy == "IMMEDIATE":
            is_score_released = (
                attempt.status == "GRADED"
                and result is not None
                and result.status in ("FINAL", "RELEASED")
            )
        elif policy == "AFTER_CLOSE":
            close_at = _normalize_dt(assessment.close_at)
            curr_now = _normalize_dt(now)
            is_score_released = bool(
                close_at and curr_now and curr_now >= close_at and attempt.status == "GRADED"
            )
        elif policy == "INSTRUCTOR_RELEASE":
            is_score_released = bool(result and result.status == "RELEASED")

    if not is_score_released:
        return {
            "attempt_id": str(attempt.public_id),
            "assessment_id": str(assessment.public_id) if assessment else None,
            "attempt_number": attempt.attempt_number,
            "status": attempt.status,
            "score_status": "SCORE_HIDDEN",
            "score_release_policy": assessment.score_release_policy if assessment else "IMMEDIATE",
            "message": "Scores have not been released yet.",
            "raw_score": None,
            "max_score": None,
            "percent_score": None,
            "passed": None,
            "questions": None,
        }

    ans_policy = assessment.answer_visibility_policy if assessment else "AFTER_CLOSE"
    show_answers = False
    if is_admin or is_manager or ans_policy == "IMMEDIATE":
        show_answers = True
    elif ans_policy == "AFTER_CLOSE":
        close_at = _normalize_dt(assessment.close_at) if assessment else None
        curr_now = _normalize_dt(now)
        show_answers = bool(close_at and curr_now and curr_now >= close_at)
    elif ans_policy == "AFTER_ALL_ATTEMPTS":
        if (
            assessment
            and assessment.attempt_limit
            and attempt.attempt_number >= assessment.attempt_limit
        ):
            show_answers = True
        else:
            close_at = _normalize_dt(assessment.close_at) if assessment else None
            curr_now = _normalize_dt(now)
            show_answers = bool(close_at and curr_now and curr_now >= close_at)
    elif ans_policy == "NEVER":
        show_answers = False

    question_grades = []
    for aq in attempt.attempt_questions:
        grade = aq.current_grade or (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        ans = aq.current_answer or (
            sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).first()
        )
        q_info: dict[str, Any] = {
            "attempt_question_id": str(aq.public_id),
            "position": aq.position,
            "question_type": aq.question_type_snapshot,
            "points_assigned": float(aq.points_assigned),
            "awarded_points": float(grade.awarded_points) if grade else 0.0,
            "grading_status": grade.grading_status if grade else "PENDING",
        }
        if show_answers:
            q_info["explanation"] = aq.explanation_snapshot
            if ans:
                q_info["student_answer_text"] = ans.answer_text
                selected_snaps = (
                    sess.query(AttemptChoiceSnapshot)
                    .join(
                        AttemptAnswerChoice,
                        AttemptAnswerChoice.attempt_choice_snapshot_id == AttemptChoiceSnapshot.id,
                    )
                    .filter(AttemptAnswerChoice.attempt_answer_id == ans.id)
                    .all()
                )
                q_info["selected_choice_keys"] = [
                    str(c.choice_key_snapshot) for c in selected_snaps
                ]
            if grade and grade.manual_reason:
                q_info["feedback"] = grade.manual_reason
        question_grades.append(q_info)

    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": str(assessment.public_id) if assessment else None,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "score_status": "RELEASED",
        "score_release_policy": assessment.score_release_policy if assessment else "IMMEDIATE",
        "answer_visibility_policy": ans_policy,
        "raw_score": float(result.raw_score) if result else 0.0,
        "max_score": float(result.max_score) if result else 0.0,
        "percent_score": (
            float(result.percent_score) if result and result.percent_score is not None else None
        ),
        "passed": result.passed if result else None,
        "released_at": result.released_at.isoformat() if result and result.released_at else None,
        "graded_at": result.graded_at.isoformat() if result and result.graded_at else None,
        "questions": question_grades,
    }


def list_pending_grading_attempts(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """List attempts for an assessment that are pending manual grading.

    Enforces course manager authorization (or admin).
    Returns list of attempt summaries with student display names and pending essay counts.
    """
    sess = session if session is not None else db.session
    assessment = _resolve_assessment(assessment_id, session=sess)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    attempts = (
        sess.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.status == "PENDING_GRADING",
        )
        .order_by(AssessmentAttempt.submitted_at.asc())
        .all()
    )

    results: list[dict[str, Any]] = []
    for att in attempts:
        pending_count = (
            sess.query(AttemptQuestionGrade)
            .join(AttemptQuestion, AttemptQuestion.id == AttemptQuestionGrade.attempt_question_id)
            .filter(
                AttemptQuestion.attempt_id == att.id,
                AttemptQuestionGrade.grading_status == "PENDING",
            )
            .count()
        )
        results.append(
            {
                "attempt_id": str(att.public_id),
                "assessment_id": str(assessment.public_id),
                "attempt_number": att.attempt_number,
                "student_id": str(att.student.public_id) if att.student else None,
                "student_name": att.student.display_name if att.student else None,
                "status": att.status,
                "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
                "total_questions": len(att.attempt_questions),
                "pending_essay_count": pending_count,
            }
        )
    return results


def get_attempt_grading_detail(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve detailed attempt question and answer information for instructor grading.

    Enforces course manager authorization (or admin).
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, attempt.assessment.course_id, session=sess)

    questions_data: list[dict[str, Any]] = []
    for aq in sorted(attempt.attempt_questions, key=lambda q: q.position):
        grade = aq.current_grade or (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        ans = aq.current_answer or (
            sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).first()
        )
        rev = aq.source_question_revision or (
            sess.get(QuestionRevision, aq.source_question_revision_id)
            if aq.source_question_revision_id
            else None
        )

        correct_info: dict[str, Any] = {}
        if rev:
            if aq.question_type_snapshot in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                correct_info["correct_choice_keys"] = [
                    str(c.choice_key) for c in rev.choices if c.is_correct
                ]
            elif aq.question_type_snapshot == "SHORT_ANSWER":
                correct_info["accepted_answers"] = [
                    {"answer_text": a.answer_text, "answer_normalized": a.answer_normalized}
                    for a in rev.accepted_answers
                ]
            elif aq.question_type_snapshot == "ESSAY":
                correct_info["rubric"] = getattr(rev, "rubric", None) or aq.explanation_snapshot

        selected_keys: list[str] = []
        if ans:
            selected_snaps = (
                sess.query(AttemptChoiceSnapshot)
                .join(
                    AttemptAnswerChoice,
                    AttemptAnswerChoice.attempt_choice_snapshot_id == AttemptChoiceSnapshot.id,
                )
                .filter(AttemptAnswerChoice.attempt_answer_id == ans.id)
                .all()
            )
            selected_keys = [str(c.choice_key_snapshot) for c in selected_snaps]

        choices_data: list[dict[str, Any]] = []
        for cs in sorted(aq.choice_snapshots, key=lambda c: c.position):
            choices_data.append(
                {
                    "choice_key": str(cs.choice_key_snapshot),
                    "content": cs.content_snapshot,
                    "position": cs.position,
                }
            )

        questions_data.append(
            {
                "attempt_question_id": str(aq.public_id),
                "position": aq.position,
                "question_type": aq.question_type_snapshot,
                "content": aq.content_snapshot,
                "explanation": aq.explanation_snapshot,
                "points_assigned": float(aq.points_assigned),
                "awarded_points": float(grade.awarded_points) if grade else 0.0,
                "grading_status": grade.grading_status if grade else "PENDING",
                "manual_reason": grade.manual_reason if grade else None,
                "student_answer_text": ans.answer_text if ans else None,
                "selected_choice_keys": selected_keys,
                "choices": choices_data,
                "correct_info": correct_info,
            }
        )

    res = attempt.result
    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": str(attempt.assessment.public_id),
        "assessment_title": attempt.assessment.title,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "student_id": str(attempt.student.public_id) if attempt.student else None,
        "student_name": attempt.student.display_name if attempt.student else None,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "graded_at": attempt.graded_at.isoformat() if attempt.graded_at else None,
        "raw_score": float(res.raw_score) if res else None,
        "max_score": float(res.max_score) if res else None,
        "percent_score": (
            float(res.percent_score) if res and res.percent_score is not None else None
        ),
        "passed": res.passed if res else None,
        "questions": questions_data,
    }


def get_attempt_grade_history(
    actor: User,
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve full audit history of score evaluations for an attempt per ADR-002.

    Invariants:
    - Actor authorization: student can view own attempt only; instructor must manage course;
      admin can view all.
    - If student: check score_release_policy. If not released, raises ScoreReleasePolicyError (403).
    - Discloses zero internal database integer PKs/FKs; uses UUIDv4/v5 public identifiers.
    """
    sess = session if session is not None else db.session
    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    is_owner = attempt.student_user_id == actor.id
    is_admin = actor.is_admin
    is_manager = False
    if attempt.assessment and actor.has_role("INSTRUCTOR"):
        from pwd301.services.authorization_service import can_manage_course

        is_manager = can_manage_course(actor, attempt.assessment.course)

    if not (is_owner or is_admin or is_manager):
        raise ForbiddenError("You do not have permission to view this attempt grade history.")

    # If student, enforce score release policy
    if is_owner and not (is_admin or is_manager):
        assessment = attempt.assessment
        result = attempt.result
        now = utc_now()
        is_score_released = False
        if assessment is None:
            is_score_released = True
        elif attempt.status in ("IN_PROGRESS", "PENDING_GRADING"):
            is_score_released = False
        else:
            policy = assessment.score_release_policy
            if policy == "IMMEDIATE":
                is_score_released = (
                    attempt.status == "GRADED"
                    and result is not None
                    and result.status in ("FINAL", "RELEASED")
                )
            elif policy == "AFTER_CLOSE":
                close_at = _normalize_dt(assessment.close_at)
                curr_now = _normalize_dt(now)
                is_score_released = bool(
                    close_at and curr_now and curr_now >= close_at and attempt.status == "GRADED"
                )
            elif policy == "INSTRUCTOR_RELEASE":
                is_score_released = bool(result and result.status == "RELEASED")

        if not is_score_released:
            raise ScoreReleasePolicyError(
                "Grade history is not accessible until assessment scores are released."
            )

    # Fetch result history
    result_history = (
        sess.query(AssessmentResultHistory)
        .filter(AssessmentResultHistory.attempt_id == attempt.id)
        .order_by(AssessmentResultHistory.created_at.asc(), AssessmentResultHistory.id.asc())
        .all()
    )

    overall_data = [
        {
            "history_id": str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_result_history.{h.id}")
            ),
            "attempt_id": str(attempt.public_id),
            "old_score": float(h.old_score) if h.old_score is not None else None,
            "new_score": float(h.new_score),
            "old_percent": float(h.old_percent) if h.old_percent is not None else None,
            "new_percent": float(h.new_percent) if h.new_percent is not None else None,
            "reason_code": h.reason_code,
            "reason": h.reason,
            "actor_id": str(h.actor.public_id) if h.actor else None,
            "regrade_job_id": (
                str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.regrade_job.{h.regrade_job_id}"))
                if h.regrade_job_id
                else None
            ),
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in result_history
    ]

    # Fetch question grade history
    q_map = {q.id: q for q in attempt.attempt_questions}
    question_ids = list(q_map.keys())
    q_histories: list[AttemptQuestionGradeHistory] = []
    if question_ids:
        q_histories = (
            sess.query(AttemptQuestionGradeHistory)
            .filter(AttemptQuestionGradeHistory.attempt_question_id.in_(question_ids))
            .order_by(
                AttemptQuestionGradeHistory.created_at.asc(),
                AttemptQuestionGradeHistory.id.asc(),
            )
            .all()
        )

    question_data = [
        {
            "history_id": str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.attempt_question_grade_history.{qh.id}")
            ),
            "attempt_question_id": (
                str(q_map[qh.attempt_question_id].public_id)
                if qh.attempt_question_id in q_map
                else None
            ),
            "old_points": float(qh.old_points) if qh.old_points is not None else None,
            "new_points": float(qh.new_points),
            "reason_code": qh.reason_code,
            "reason": qh.reason,
            "actor_id": str(qh.actor.public_id) if qh.actor else None,
            "question_correction_id": (
                str(
                    uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"pwd301.question_correction.{qh.question_correction_id}",
                    )
                )
                if qh.question_correction_id
                else None
            ),
            "created_at": qh.created_at.isoformat() if qh.created_at else None,
        }
        for qh in q_histories
    ]

    return {
        "attempt_id": str(attempt.public_id),
        "assessment_id": str(attempt.assessment.public_id) if attempt.assessment else None,
        "overall_history": overall_data,
        "question_history": question_data,
    }
