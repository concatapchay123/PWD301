"""Regrading worker engine for PWD301 per Algorithm 11 and Business Domain 10.

Implements background, resumable, and idempotent regrading:
- QuestionCorrection triggers RegradeJob and per-attempt RegradeItems.
- Algorithm 11:
  - ANSWER_ONLY: Re-evaluates objective choices (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE)
    and SHORT_ANSWER (normalized/exact) against destination QuestionRevision.
    Updates AttemptQuestionGrade with grading_rule='ANSWER_CORRECTION',
    grading_status='AUTO_GRADED', and records AttemptQuestionGradeHistory with
    reason_code='AUTO_REGRADE'.
  - CONTENT_OR_CHOICES: Full-credit safety policy for affected attempts.
    Updates AttemptQuestionGrade with grading_rule='CONTENT_FULL_CREDIT',
    grading_status='FULL_CREDIT', and records AttemptQuestionGradeHistory with
    reason_code='FULL_CREDIT'.
- Exclusions / Skip Logic:
  - Purged attempts (is_detail_purged=True) -> SKIPPED with reason 'DETAIL_PURGED'.
  - Cancelled attempts (status='CANCELLED') -> SKIPPED with reason 'CANCELLED'.
  - Unsubmitted attempts (CREATED, IN_PROGRESS) -> naturally ineligible for regrade job.
- Audit Trail:
  - AssessmentResultHistory recorded with reason_code='REGRADE' when attempt raw_score changes.
  - Course completion recalculation triggered when required assessment status changes.
- Resumability & Idempotency:
  - Per-item tracking, retryable failed items up to MAX_RETRIES.
  - Repeating regrade on identical state produces no duplicate history.
- ADR-002:
  - Public UUIDv5 synthetic identifiers for RegradeJob and RegradeItem.
"""

from __future__ import annotations

import unicodedata
import uuid
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AssessmentResultHistory,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    QuestionCorrection,
    RegradeItem,
    RegradeJob,
)
from pwd301.models.identity import User
from pwd301.models.question_bank import (
    QuestionRevision,
)
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_attempt,
    require_course_manager,
)
from pwd301.services.completion_service import recalculate_course_completion
from pwd301.services.exceptions import (
    AttemptNotFoundError,
    ForbiddenError,
    QuestionCorrectionNotFoundError,
    RegradeJobNotFoundError,
)

MAX_RETRIES: int = 3


# ============================================================================
# RESOLUTION & SERIALIZATION HELPERS (ADR-002)
# ============================================================================


_SYNTHETIC_JOB_CACHE: dict[uuid.UUID, int] = {}
_SYNTHETIC_CORRECTION_CACHE: dict[uuid.UUID, int] = {}


def _resolve_regrade_job(
    job_id: RegradeJob | int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> RegradeJob | None:
    """Resolve a RegradeJob instance from entity, integer PK, or synthetic UUID (ADR-002)."""
    if isinstance(job_id, RegradeJob):
        return job_id
    if isinstance(job_id, int):
        return session.get(RegradeJob, job_id)

    raw = str(job_id).strip()
    if raw.isdigit():
        return session.get(RegradeJob, int(raw))

    try:
        val_uuid = uuid.UUID(raw)
    except ValueError:
        return None

    if val_uuid in _SYNTHETIC_JOB_CACHE:
        return session.get(RegradeJob, _SYNTHETIC_JOB_CACHE[val_uuid])

    # Scan job IDs (lightweight column query) to match synthetic UUIDv5 without full ORM loading
    for (jid,) in session.query(RegradeJob.id).all():
        syn = uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.regrade_job.{jid}")
        _SYNTHETIC_JOB_CACHE[syn] = jid
        if syn == val_uuid:
            return session.get(RegradeJob, jid)

    return None


def _resolve_question_correction(
    correction_id: QuestionCorrection | int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> QuestionCorrection | None:
    """Resolve a QuestionCorrection entity from PK or synthetic UUID (ADR-002)."""
    if isinstance(correction_id, QuestionCorrection):
        return correction_id
    if isinstance(correction_id, int):
        return session.get(QuestionCorrection, correction_id)

    raw = str(correction_id).strip()
    if raw.isdigit():
        return session.get(QuestionCorrection, int(raw))

    try:
        val_uuid = uuid.UUID(raw)
    except ValueError:
        return None

    if val_uuid in _SYNTHETIC_CORRECTION_CACHE:
        return session.get(QuestionCorrection, _SYNTHETIC_CORRECTION_CACHE[val_uuid])

    # Scan correction IDs (lightweight column query) to match synthetic UUIDv5
    # without full ORM loading
    for (qcid,) in session.query(QuestionCorrection.id).all():
        syn = uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.question_correction.{qcid}")
        _SYNTHETIC_CORRECTION_CACHE[syn] = qcid
        if syn == val_uuid:
            return session.get(QuestionCorrection, qcid)

    return None


def _serialize_regrade_item(item: RegradeItem) -> dict[str, Any]:
    """Serialize RegradeItem masking BIGINT PKs per ADR-002."""
    synthetic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.regrade_item.{item.id}"))
    job_synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.regrade_job.{item.regrade_job_id}")
    )
    attempt_public_id = str(item.attempt.public_id) if item.attempt else None

    return {
        "item_id": synthetic_id,
        "job_id": job_synthetic_id,
        "attempt_id": attempt_public_id,
        "status": item.status,
        "old_score": float(item.old_score) if item.old_score is not None else None,
        "new_score": float(item.new_score) if item.new_score is not None else None,
        "skip_reason": item.skip_reason,
        "attempt_count": item.attempt_count,
        "processed_at": item.processed_at.isoformat() if item.processed_at else None,
        "last_error": item.last_error,
    }


def _serialize_regrade_job(job: RegradeJob, include_items: bool = False) -> dict[str, Any]:
    """Serialize RegradeJob masking BIGINT PKs per ADR-002."""
    synthetic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.regrade_job.{job.id}"))
    corr_synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.question_correction.{job.question_correction_id}")
    )

    data: dict[str, Any] = {
        "job_id": synthetic_id,
        "question_correction_id": corr_synthetic_id,
        "status": job.status,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "changed_results": job.changed_results,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "last_error": job.last_error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
    if include_items:
        data["items"] = [_serialize_regrade_item(item) for item in job.items]
    return data


# ============================================================================
# REGRADE JOB CREATION & SCHEDULING
# ============================================================================


def create_or_get_regrade_job(
    question_correction_id: QuestionCorrection | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> RegradeJob:
    """Create or retrieve a RegradeJob and populate affected RegradeItems.

    Invariants enforced:
    - Scans AssessmentAttempt instances containing AttemptQuestion for this question.
    - Excludes unsubmitted attempts ('CREATED', 'IN_PROGRESS') so they submit naturally.
    - Details purged (is_detail_purged=True) -> SKIPPED (DETAIL_PURGED).
    - Cancelled attempts (status='CANCELLED') -> SKIPPED (CANCELLED).
    - Other attempts (SUBMITTED, PENDING_GRADING, GRADED, EXPIRED) -> PENDING.
    - Idempotent: does not duplicate items if job already exists.
    """
    sess = session if session is not None else db.session

    correction = _resolve_question_correction(question_correction_id, sess)
    if correction is None:
        raise QuestionCorrectionNotFoundError("Question correction not found.")

    # Find existing job or create new one
    job = sess.query(RegradeJob).filter(RegradeJob.question_correction_id == correction.id).first()

    now = utc_now()
    if job is None:
        job = RegradeJob(
            question_correction_id=correction.id,
            status="QUEUED",
            total_items=0,
            processed_items=0,
            changed_results=0,
            created_at=now,
        )
        sess.add(job)
        sess.flush()

    # Query all attempts referencing the corrected question
    attempts = (
        sess.query(AssessmentAttempt)
        .join(AttemptQuestion, AttemptQuestion.attempt_id == AssessmentAttempt.id)
        .filter(AttemptQuestion.source_question_id == correction.question_id)
        .distinct()
        .all()
    )

    existing_attempt_ids = {
        item.attempt_id
        for item in sess.query(RegradeItem.attempt_id)
        .filter(RegradeItem.regrade_job_id == job.id)
        .all()
    }

    for attempt in attempts:
        # Rule: In-progress or created attempts are not regraded via job;
        # they will be submitted naturally against active snapshot/revision.
        if attempt.status in ("CREATED", "IN_PROGRESS"):
            continue

        if attempt.id in existing_attempt_ids:
            continue

        if attempt.is_detail_purged:
            status = "SKIPPED"
            skip_reason = "DETAIL_PURGED"
            processed_at = now
        elif attempt.status == "CANCELLED":
            status = "SKIPPED"
            skip_reason = "CANCELLED"
            processed_at = now
        else:
            status = "PENDING"
            skip_reason = None
            processed_at = None

        item = RegradeItem(
            regrade_job_id=job.id,
            attempt_id=attempt.id,
            status=status,
            skip_reason=skip_reason,
            attempt_count=0,
            processed_at=processed_at,
        )
        sess.add(item)

    sess.flush()

    # Recalculate totals
    job.total_items = sess.query(RegradeItem).filter(RegradeItem.regrade_job_id == job.id).count()
    job.processed_items = (
        sess.query(RegradeItem)
        .filter(
            RegradeItem.regrade_job_id == job.id,
            RegradeItem.status.in_(["COMPLETED", "SKIPPED"]),
        )
        .count()
    )
    sess.flush()
    return job


# ============================================================================
# ALGORITHM 11: REGRADING EXECUTION ENGINE
# ============================================================================


def _evaluate_attempt_item_regrade(
    item: RegradeItem,
    job: RegradeJob,
    correction: QuestionCorrection,
    session: Session | scoped_session[Any],
) -> None:
    """Execute Algorithm 11 regrading logic for a single RegradeItem."""
    sess = session
    now = utc_now()
    attempt = item.attempt

    # 1. Skip checks
    if attempt.is_detail_purged:
        item.status = "SKIPPED"
        item.skip_reason = "DETAIL_PURGED"
        item.processed_at = now
        sess.flush()
        return

    if attempt.status == "CANCELLED":
        item.status = "SKIPPED"
        item.skip_reason = "CANCELLED"
        item.processed_at = now
        sess.flush()
        return

    if attempt.status in ("CREATED", "IN_PROGRESS"):
        item.status = "SKIPPED"
        item.skip_reason = "NOT_AFFECTED"
        item.processed_at = now
        sess.flush()
        return

    target_rev = correction.to_revision
    corr_type = correction.correction_type

    # 2. Find affected questions in attempt
    affected_aqs = (
        sess.query(AttemptQuestion)
        .filter(
            AttemptQuestion.attempt_id == attempt.id,
            AttemptQuestion.source_question_id == correction.question_id,
        )
        .all()
    )

    if not affected_aqs:
        item.status = "SKIPPED"
        item.skip_reason = "NOT_AFFECTED"
        item.processed_at = now
        sess.flush()
        return

    for aq in affected_aqs:
        grade = (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        old_points = grade.awarded_points if grade else Decimal("0.0000")

        if corr_type == "CONTENT_OR_CHOICES":
            # Rule: Content or choice defect awards full points
            awarded_pts = aq.points_assigned
            grading_status = "FULL_CREDIT"
            grading_rule = "CONTENT_FULL_CREDIT"
            reason_code = "FULL_CREDIT"
            reason_text = f"Full credit awarded for question correction: {correction.reason}"
        else:  # ANSWER_ONLY
            q_type = target_rev.question_type if target_rev else aq.question_type_snapshot
            if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                target_choices = target_rev.choices if target_rev else []
                ans = (
                    sess.query(AttemptAnswer)
                    .filter(AttemptAnswer.attempt_question_id == aq.id)
                    .first()
                )
                selected_snaps = []
                if ans:
                    selected_snaps = (
                        sess.query(AttemptChoiceSnapshot)
                        .join(
                            AttemptAnswerChoice,
                            AttemptAnswerChoice.attempt_choice_snapshot_id
                            == AttemptChoiceSnapshot.id,
                        )
                        .filter(AttemptAnswerChoice.attempt_answer_id == ans.id)
                        .all()
                    )

                selected_target_choices = []
                for ac in selected_snaps:
                    matched_c = None
                    for c in target_choices:
                        if str(c.choice_key).lower() == str(ac.choice_key_snapshot).lower():
                            matched_c = c
                            break
                    if matched_c is None:
                        for c in target_choices:
                            if c.position == ac.position:
                                matched_c = c
                                break
                    if matched_c is None:
                        for c in target_choices:
                            if c.content.strip().lower() == ac.content_snapshot.strip().lower():
                                matched_c = c
                                break
                    if matched_c is not None:
                        selected_target_choices.append(matched_c)

                if q_type in ("SINGLE_CHOICE", "TRUE_FALSE"):
                    correct_target_choices = [c for c in target_choices if c.is_correct]
                    is_correct = (
                        len(selected_target_choices) == 1
                        and len(correct_target_choices) == 1
                        and selected_target_choices[0].id == correct_target_choices[0].id
                    )
                else:  # MULTIPLE_CHOICE
                    correct_ids = {c.id for c in target_choices if c.is_correct}
                    selected_ids = {c.id for c in selected_target_choices}
                    is_correct = (selected_ids == correct_ids) and len(correct_ids) > 0

                awarded_pts = aq.points_assigned if is_correct else Decimal("0.0000")
            elif q_type == "SHORT_ANSWER":
                ans = (
                    sess.query(AttemptAnswer)
                    .filter(AttemptAnswer.attempt_question_id == aq.id)
                    .first()
                )
                student_text = (ans.answer_text or "").strip() if ans else ""
                accepted = target_rev.accepted_answers if target_rev else []
                match_mode = (
                    target_rev.short_answer_match_mode if target_rev else None
                ) or "NORMALIZED"

                if match_mode == "EXACT":
                    is_correct = any(student_text == aa.answer_text.strip() for aa in accepted)
                else:
                    norm_student = unicodedata.normalize("NFKC", student_text.lower())
                    is_correct = any(
                        norm_student
                        == unicodedata.normalize(
                            "NFKC", (aa.answer_normalized or aa.answer_text).strip().lower()
                        )
                        for aa in accepted
                    )
                awarded_pts = aq.points_assigned if is_correct else Decimal("0.0000")
            elif q_type == "ESSAY":
                # Essays preserve manual evaluation or remain pending
                awarded_pts = old_points
            else:
                awarded_pts = Decimal("0.0000")

            grading_status = "AUTO_GRADED"
            grading_rule = "ANSWER_CORRECTION"
            reason_code = "AUTO_REGRADE"
            reason_text = (
                f"Auto regrade against revision {target_rev.revision_no}: {correction.reason}"
            )

        # Idempotency check: if grade already matches target revision and score,
        # avoid redundant history records
        is_already_identical = (
            grade is not None
            and grade.awarded_points == awarded_pts
            and grade.graded_against_revision_id == target_rev.id
            and grade.grading_rule == grading_rule
        )

        if grade is None:
            grade = AttemptQuestionGrade(
                attempt_question_id=aq.id,
                awarded_points=awarded_pts,
                grading_status=grading_status,
                grading_rule=grading_rule,
                graded_against_revision_id=target_rev.id,
                graded_by_user_id=correction.actor_user_id,
                graded_at=now,
            )
            sess.add(grade)
            sess.flush()

            hist = AttemptQuestionGradeHistory(
                attempt_question_id=aq.id,
                old_points=None,
                new_points=awarded_pts,
                reason_code=reason_code,
                reason=reason_text,
                actor_user_id=correction.actor_user_id,
                question_correction_id=correction.id,
                created_at=now,
            )
            sess.add(hist)
        elif not is_already_identical:
            grade.awarded_points = awarded_pts
            grade.grading_status = grading_status
            grade.grading_rule = grading_rule
            grade.graded_against_revision_id = target_rev.id
            grade.graded_by_user_id = correction.actor_user_id
            grade.graded_at = now
            sess.flush()

            hist = AttemptQuestionGradeHistory(
                attempt_question_id=aq.id,
                old_points=old_points,
                new_points=awarded_pts,
                reason_code=reason_code,
                reason=reason_text,
                actor_user_id=correction.actor_user_id,
                question_correction_id=correction.id,
                created_at=now,
            )
            sess.add(hist)

    sess.flush()

    # Check if attempt has any pending questions left
    pending_count = (
        sess.query(AttemptQuestionGrade)
        .join(AttemptQuestion, AttemptQuestion.id == AttemptQuestionGrade.attempt_question_id)
        .filter(
            AttemptQuestion.attempt_id == attempt.id,
            AttemptQuestionGrade.grading_status == "PENDING",
        )
        .count()
    )
    if pending_count == 0 and attempt.status in ("PENDING_GRADING", "SUBMITTED"):
        attempt.status = "GRADED"
        attempt.graded_at = now

    # 3. Recalculate AssessmentResult
    all_qs = (
        sess.query(AttemptQuestion)
        .filter(AttemptQuestion.attempt_id == attempt.id)
        .order_by(AttemptQuestion.position)
        .all()
    )
    max_score = sum((q.points_assigned for q in all_qs), Decimal("0.0000"))

    total_raw = Decimal("0.0000")
    for q in all_qs:
        g = (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == q.id)
            .first()
        )
        if g and g.awarded_points:
            total_raw += g.awarded_points

    percent_score: Decimal | None = None
    if max_score > 0:
        percent_score = (total_raw / max_score) * Decimal("100.0000")

    passed: bool | None = None
    if (
        attempt.assessment
        and attempt.assessment.passing_percent is not None
        and percent_score is not None
    ):
        passed = percent_score >= attempt.assessment.passing_percent

    res = sess.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()
    old_raw_score = res.raw_score if res else None
    old_percent = res.percent_score if res else None
    old_passed = res.passed if res else None

    # Determine result status
    res_status = "FINAL"
    if attempt.status != "GRADED":
        res_status = "PENDING"
    elif attempt.assessment and attempt.assessment.score_release_policy == "IMMEDIATE":
        res_status = "RELEASED"

    if res is None:
        res = AssessmentResult(
            attempt_id=attempt.id,
            raw_score=total_raw,
            max_score=max_score,
            percent_score=percent_score,
            passed=passed,
            status=res_status,
            graded_at=now if attempt.status == "GRADED" else None,
            released_at=now if res_status == "RELEASED" else None,
            updated_at=now,
        )
        sess.add(res)
        sess.flush()
    else:
        res.raw_score = total_raw
        res.max_score = max_score
        res.percent_score = percent_score
        res.passed = passed
        if attempt.status == "GRADED" and res.status == "PENDING":
            res.status = res_status
            if res_status == "RELEASED":
                res.released_at = now
            res.graded_at = now
        res.updated_at = now
        sess.flush()

    # 4. Audit history on score modification
    if old_raw_score != total_raw:
        res_hist = AssessmentResultHistory(
            attempt_id=attempt.id,
            old_score=old_raw_score,
            new_score=total_raw,
            old_percent=old_percent,
            new_percent=percent_score,
            reason_code="REGRADE",
            reason=f"Regrade: {correction.reason}",
            actor_user_id=correction.actor_user_id,
            regrade_job_id=job.id,
            created_at=now,
        )
        sess.add(res_hist)
        job.changed_results += 1

        # Check Course Completion recalculation if required
        if (
            attempt.assessment
            and attempt.assessment.is_required_for_completion
            and passed != old_passed
        ):
            recalculate_course_completion(
                student_user_id=attempt.student_user_id,
                course_id=attempt.assessment.course_id,
                session=sess,
            )

    # 5. Mark item completed
    item.status = "COMPLETED"
    item.old_score = old_raw_score
    item.new_score = total_raw
    item.processed_at = now
    item.last_error = None
    sess.flush()


def process_regrade_job(
    job_id: RegradeJob | int | uuid.UUID | str,
    batch_size: int | None = None,
    actor: User | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Execute batch or complete synchronous processing for a RegradeJob.

    Invariants enforced:
    - State transitions: QUEUED -> RUNNING -> COMPLETED / PARTIAL / FAILED.
    - Idempotent and resumable: processes pending items or retries failed items.
    - Updates QuestionCorrection status to 'APPLIED' upon full completion.
    """
    sess = session if session is not None else db.session

    job = _resolve_regrade_job(job_id, sess)
    if job is None:
        raise RegradeJobNotFoundError("Regrade job not found.")

    if job.status == "COMPLETED":
        return _serialize_regrade_job(job)

    now = utc_now()
    job.status = "RUNNING"
    if job.started_at is None:
        job.started_at = now
    sess.flush()

    correction = job.question_correction
    if correction and correction.status == "PENDING":
        correction.status = "RUNNING"
        sess.flush()

    # Query items to process
    items_query = (
        sess.query(RegradeItem)
        .filter(RegradeItem.regrade_job_id == job.id)
        .filter(
            sa.or_(
                RegradeItem.status == "PENDING",
                # Recover items stalled from worker crash/restart:
                RegradeItem.status == "PROCESSING",
                sa.and_(
                    RegradeItem.status == "FAILED",
                    RegradeItem.attempt_count < MAX_RETRIES,
                ),
            )
        )
        .order_by(RegradeItem.id.asc())
    )

    if batch_size is not None and batch_size > 0:
        items = items_query.limit(batch_size).all()
    else:
        items = items_query.all()

    for item in items:
        item.status = "PROCESSING"
        item.attempt_count += 1
        sess.flush()

        try:
            _evaluate_attempt_item_regrade(item, job, correction, session=sess)
        except Exception as exc:
            item.status = "FAILED"
            item.last_error = str(exc)[:2000]
            item.processed_at = utc_now()
            sess.flush()

    # Update processed count
    job.processed_items = (
        sess.query(RegradeItem)
        .filter(
            RegradeItem.regrade_job_id == job.id,
            RegradeItem.status.in_(["COMPLETED", "SKIPPED"]),
        )
        .count()
    )

    # Evaluate final job state
    pending_count = (
        sess.query(RegradeItem)
        .filter(
            RegradeItem.regrade_job_id == job.id,
            RegradeItem.status.in_(["PENDING", "PROCESSING"]),
        )
        .count()
    )
    failed_count = (
        sess.query(RegradeItem)
        .filter(
            RegradeItem.regrade_job_id == job.id,
            RegradeItem.status == "FAILED",
        )
        .count()
    )

    if pending_count == 0 and failed_count == 0:
        job.status = "COMPLETED"
        job.completed_at = utc_now()
        if correction:
            correction.status = "APPLIED"
    elif failed_count > 0:
        job.status = "PARTIAL"
    else:
        job.status = "RUNNING"

    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return _serialize_regrade_job(job)


def retry_regrade_job(
    job_id: RegradeJob | int | uuid.UUID | str,
    actor: User | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retry all failed items in a RegradeJob."""
    sess = session if session is not None else db.session

    job = _resolve_regrade_job(job_id, sess)
    if job is None:
        raise RegradeJobNotFoundError("Regrade job not found.")

    if actor is not None:
        if not (
            actor.is_admin
            or (
                job.question_correction
                and job.question_correction.question
                and actor.has_role("INSTRUCTOR")
            )
        ):
            raise ForbiddenError("You do not have permission to retry this regrade job.")
        if job.question_correction and job.question_correction.question:
            require_course_manager(actor, job.question_correction.question.course_id, session=sess)

    failed_items = (
        sess.query(RegradeItem)
        .filter(
            RegradeItem.regrade_job_id == job.id,
            RegradeItem.status == "FAILED",
        )
        .all()
    )

    for item in failed_items:
        item.status = "PENDING"
        item.last_error = None
        item.attempt_count = 0

    job.status = "QUEUED"
    job.last_error = None
    sess.flush()

    return process_regrade_job(job, actor=actor, session=sess)


def get_regrade_job_detail(
    actor: User,
    job_id: RegradeJob | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve detailed regrade job progress, enforcing object-level authorization."""
    sess = session if session is not None else db.session

    job = _resolve_regrade_job(job_id, sess)
    if job is None:
        raise RegradeJobNotFoundError("Regrade job not found.")

    if not (
        actor.is_admin
        or (
            job.question_correction
            and job.question_correction.question
            and actor.has_role("INSTRUCTOR")
        )
    ):
        raise ForbiddenError("You do not have permission to view this regrade job.")

    if job.question_correction and job.question_correction.question:
        require_course_manager(actor, job.question_correction.question.course_id, session=sess)

    return _serialize_regrade_job(job, include_items=True)


# ============================================================================
# SINGLE ATTEMPT REGRADE (BACKWARD COMPATIBILITY)
# ============================================================================


def regrade_attempt(
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    question_correction_id: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Regrade an individual assessment attempt against active question revisions or correction."""
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.is_detail_purged:
        return {
            "attempt_id": str(attempt.public_id),
            "skipped": True,
            "reason": "SKELETON_TOMBSTONE_PURGED",
        }

    if attempt.status == "CANCELLED":
        return {
            "attempt_id": str(attempt.public_id),
            "skipped": True,
            "reason": "CANCELLED",
        }

    now = utc_now()
    changed_count = 0

    correction: QuestionCorrection | None = None
    if question_correction_id is not None:
        correction = sess.get(QuestionCorrection, question_correction_id)

    for aq in attempt.attempt_questions:
        if correction is not None and aq.source_question_id != correction.question_id:
            continue

        active_rev: QuestionRevision | None = None
        if correction is not None:
            active_rev = correction.to_revision
        else:
            active_rev = (
                sess.query(QuestionRevision)
                .filter(
                    QuestionRevision.question_id == aq.source_question_id,
                    QuestionRevision.is_current == True,
                )
                .first()
            )
            if active_rev is None:
                active_rev = (
                    sess.query(QuestionRevision)
                    .filter(QuestionRevision.question_id == aq.source_question_id)
                    .order_by(QuestionRevision.revision_no.desc())
                    .first()
                )

        if active_rev is None:
            continue

        if correction is not None and correction.correction_type == "CONTENT_OR_CHOICES":
            awarded = aq.points_assigned
            grading_status = "FULL_CREDIT"
            grading_rule = "CONTENT_FULL_CREDIT"
            reason_code = "FULL_CREDIT"
        else:
            q_type = active_rev.question_type
            if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                correct_choice_keys = {
                    str(c.choice_key) for c in active_rev.choices if c.is_correct
                }
                student_choice_keys: set[str] = set()
                if aq.current_answer:
                    for ac in aq.current_answer.selected_choices:
                        student_choice_keys.add(str(ac.choice_key_snapshot))

                if q_type in ("SINGLE_CHOICE", "TRUE_FALSE"):
                    is_correct = (
                        len(student_choice_keys) == 1
                        and student_choice_keys == correct_choice_keys
                        and len(correct_choice_keys) == 1
                    )
                else:
                    is_correct = (student_choice_keys == correct_choice_keys) and len(
                        correct_choice_keys
                    ) > 0

                awarded = aq.points_assigned if is_correct else Decimal("0.0000")
            elif q_type == "SHORT_ANSWER":
                student_text = (
                    aq.current_answer.answer_text.strip()
                    if aq.current_answer and aq.current_answer.answer_text
                    else ""
                )
                accepted = active_rev.accepted_answers
                match_mode = active_rev.short_answer_match_mode or "NORMALIZED"
                if match_mode == "EXACT":
                    is_correct = any(student_text == aa.answer_text.strip() for aa in accepted)
                else:
                    norm_student = unicodedata.normalize("NFKC", student_text.lower())
                    is_correct = any(
                        norm_student
                        == unicodedata.normalize(
                            "NFKC", (aa.answer_normalized or aa.answer_text).strip().lower()
                        )
                        for aa in accepted
                    )
                awarded = aq.points_assigned if is_correct else Decimal("0.0000")
            else:
                grade = aq.current_grade
                awarded = grade.awarded_points if grade else Decimal("0.0000")

            grading_status = "AUTO_GRADED"
            grading_rule = "ANSWER_CORRECTION" if question_correction_id else "ORIGINAL"
            reason_code = "AUTO_REGRADE" if question_correction_id else "INITIAL"

        grade = (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == aq.id)
            .first()
        )
        old_pts = grade.awarded_points if grade else Decimal("0.0000")

        if grade is None:
            grade = AttemptQuestionGrade(
                attempt_question_id=aq.id,
                awarded_points=awarded,
                grading_status=grading_status,
                grading_rule=grading_rule,
                graded_against_revision_id=active_rev.id,
                graded_at=now,
            )
            sess.add(grade)
            changed_count += 1
        else:
            if grade.awarded_points != awarded or grade.graded_against_revision_id != active_rev.id:
                changed_count += 1
            grade.awarded_points = awarded
            grade.grading_status = grading_status
            grade.grading_rule = grading_rule
            grade.graded_against_revision_id = active_rev.id
            grade.graded_at = now

        hist = AttemptQuestionGradeHistory(
            attempt_question_id=aq.id,
            old_points=old_pts,
            new_points=awarded,
            reason_code=reason_code,
            reason=f"Regrade against revision {active_rev.revision_no}",
            question_correction_id=question_correction_id,
            created_at=now,
        )
        sess.add(hist)

    # Recalculate result
    all_qs = attempt.attempt_questions
    max_score = sum((q.points_assigned for q in all_qs), Decimal("0.0000"))
    total_raw = Decimal("0.0000")
    for q in all_qs:
        g = (
            sess.query(AttemptQuestionGrade)
            .filter(AttemptQuestionGrade.attempt_question_id == q.id)
            .first()
        )
        if g is not None and g.awarded_points is not None:
            total_raw += g.awarded_points
    percent_score = (
        (total_raw / max_score) * Decimal("100.0000") if max_score > 0 else Decimal("0.0000")
    )
    passed = (
        percent_score >= attempt.assessment.passing_percent
        if attempt.assessment and attempt.assessment.passing_percent is not None
        else None
    )

    res = (
        attempt.result
        or sess.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()
    )
    old_raw = res.raw_score if res else None
    old_percent = res.percent_score if res else None

    if res is None:
        res = AssessmentResult(
            attempt_id=attempt.id,
            raw_score=total_raw,
            max_score=max_score,
            percent_score=percent_score,
            passed=passed,
            status="FINAL",
            graded_at=now,
            updated_at=now,
        )
        sess.add(res)
    else:
        res.raw_score = total_raw
        res.max_score = max_score
        res.percent_score = percent_score
        res.passed = passed
        res.updated_at = now

    if old_raw != total_raw:
        res_hist = AssessmentResultHistory(
            attempt_id=attempt.id,
            old_score=old_raw,
            new_score=total_raw,
            old_percent=old_percent,
            new_percent=percent_score,
            reason_code="REGRADE" if question_correction_id else "INITIAL",
            reason="Regrade execution",
            created_at=now,
        )
        sess.add(res_hist)

    attempt.updated_at = now
    sess.flush()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "attempt_id": str(attempt.public_id),
        "skipped": False,
        "total_score": float(total_raw),
        "total_possible": float(max_score),
        "changed_questions": changed_count,
    }
