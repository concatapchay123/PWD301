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
import json
import random
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
)
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import _normalize_dt, _resolve_assessment
from pwd301.services.authorization_service import _resolve_attempt
from pwd301.services.exceptions import (
    ActiveAttemptExistsError,
    AssessmentClosedError,
    AssessmentNotFoundError,
    AssessmentNotOpenError,
    AttemptExpiredError,
    AttemptLeaseConflictError,
    AttemptLeaseExpiredError,
    AttemptLimitExceededError,
    AttemptNotFoundError,
    AttemptValidationError,
    ForbiddenError,
    StaleAnswerSequenceError,
    StaleLeaseEpochError,
)

# ============================================================================
# AUDIT & LEASE HELPERS
# ============================================================================


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

    # Apply question shuffling if configured
    if assessment.shuffle_questions:
        random.shuffle(candidates)

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
                random.shuffle(non_fixed)
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
    if attempt.lease_token_hash is None or attempt.lease_token_hash != token_hash:
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
    if attempt.lease_token_hash is None or attempt.lease_token_hash != token_hash:
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

    if attempt.lease_token_hash is None:
        return False

    token_hash = hashlib.sha256(raw_lease_token.strip().encode("utf-8")).digest()
    if attempt.lease_token_hash != token_hash:
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
    """Resolve AttemptQuestion within an attempt by object, internal integer ID, public UUID, or uuid5."""
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

    aq_list = (
        session.query(AttemptQuestion)
        .filter(AttemptQuestion.attempt_id == attempt.id)
        .all()
    )
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
    """Save an answer for a specific question in an attempt with lease epoch fencing and client sequencing.

    Enforces:
    1. Zero-Trust IDOR check (actor.id == attempt.student_user_id).
    2. Attempt status is IN_PROGRESS and deadline has not expired.
    3. Valid lease token and active lease.
    4. Lease epoch fencing: If payload specifies lease_epoch, must match attempt.lease_epoch.
       If mismatch -> raises StaleLeaseEpochError (409 STALE_LEASE_EPOCH).
    5. Client sequencing: client_sequence must be strictly > last_client_sequence.
       If <= -> records rejected event and raises StaleAnswerSequenceError (409 STALE_ANSWER).
    6. Persists AttemptAnswer, AttemptAnswerChoice (if choices provided), and accepted AttemptAnswerEvent.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.student_user_id != actor.id:
        raise ForbiddenError("You do not have permission to modify this assessment attempt.")

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
    if payload_epoch is not None and int(payload_epoch) != (attempt.lease_epoch or 1):
        raise StaleLeaseEpochError(
            f"Stale lease epoch ({payload_epoch} != {attempt.lease_epoch or 1})."
        )

    # Resolve AttemptQuestion
    aq = _resolve_attempt_question(attempt, attempt_question_id, session=sess)
    if aq is None:
        raise AttemptValidationError("Attempt question not found in this attempt.")

    # 5. Client Sequence check
    client_seq = int(payload.get("client_sequence", 0))
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
        sess.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_question_id == aq.id)
        .first()
    )

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
        sess.commit()
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

    # Handle choices (for single/multiple choice questions)
    selected_choice_keys = payload.get("selected_choice_keys") or payload.get("choice_keys")
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
        "attempt_question_id": str(aq.public_id) if getattr(aq, "public_id", None) else str(attempt_question_id),
        "answer_version": answer_record.answer_version,
        "last_client_sequence": answer_record.last_client_sequence,
        "saved_at": answer_record.saved_at.isoformat() if answer_record.saved_at else now.isoformat(),
        "lease_epoch": attempt.lease_epoch or 1,
    }

