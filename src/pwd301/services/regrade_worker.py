"""Regrading worker engine for PWD301.

Implements background regrading invariants (Defect 2 & Defect 4):
- Regrade Choice Key Invariant:
  Matches student selected choice_key_snapshot against active QuestionRevision choice_key set.
  Preserves scoring accuracy across revision authoring updates.
- Skeleton Tombstone Invariant:
  Skips all attempts where is_detail_purged = True (retained skeleton records).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswerChoice,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    QuestionCorrection,
    RegradeItem,
    RegradeJob,
)
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import _resolve_attempt
from pwd301.services.exceptions import AttemptNotFoundError


def regrade_attempt(
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    question_correction_id: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Regrade an assessment attempt against current question revisions.

    Args:
        attempt_id: AssessmentAttempt instance, PK, or UUID.
        question_correction_id: Optional QuestionCorrection ID that triggered regrading.
        session: Optional SQLAlchemy session.

    Returns:
        Summary dict containing attempt_id, skipped status, old_score, new_score.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    # Invariant: Skeleton tombstone attempts must NEVER be regraded
    if attempt.is_detail_purged:
        return {
            "attempt_id": str(attempt.public_id),
            "skipped": True,
            "reason": "SKELETON_TOMBSTONE_PURGED",
        }

    now = utc_now()
    total_score = Decimal("0")
    total_possible = Decimal("0")
    changed_count = 0

    for aq in attempt.attempt_questions:
        total_possible += aq.points_assigned

        # Find active question revision
        active_rev = (
            sess.query(QuestionRevision)
            .filter(
                QuestionRevision.question_id == aq.source_question_id,
                QuestionRevision.is_current.is_(True),
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

        q_type = active_rev.question_type

        # Grade choice-based questions by choice_key matching
        if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
            correct_choice_keys = {
                str(c.choice_key) for c in active_rev.choices if c.is_correct
            }

            student_choice_keys: set[str] = set()
            if aq.current_answer:
                # Find choice snapshots selected by student
                for ac in aq.current_answer.selected_choices:
                    student_choice_keys.add(str(ac.choice_key_snapshot))

            is_correct = (student_choice_keys == correct_choice_keys) and len(correct_choice_keys) > 0
            awarded = aq.points_assigned if is_correct else Decimal("0")

            grade = aq.current_grade
            old_pts = grade.awarded_points if grade else Decimal("0")

            if grade is None:
                grade = AttemptQuestionGrade(
                    attempt_question_id=aq.id,
                    awarded_points=awarded,
                    grading_status="AUTO_GRADED",
                    grading_rule="ANSWER_CORRECTION" if question_correction_id else "ORIGINAL",
                    graded_against_revision_id=active_rev.id,
                    graded_at=now,
                )
                sess.add(grade)
                changed_count += 1
            else:
                if grade.awarded_points != awarded:
                    changed_count += 1
                grade.awarded_points = awarded
                grade.grading_status = "AUTO_GRADED"
                grade.grading_rule = "ANSWER_CORRECTION" if question_correction_id else grade.grading_rule
                grade.graded_against_revision_id = active_rev.id
                grade.graded_at = now

            # Record history
            hist = AttemptQuestionGradeHistory(
                attempt_question_id=aq.id,
                old_points=old_pts,
                new_points=awarded,
                reason_code="AUTO_REGRADE" if question_correction_id else "INITIAL",
                reason="Automatic regrade choice_key evaluation",
                question_correction_id=question_correction_id,
                created_at=now,
            )
            sess.add(hist)
            total_score += awarded
        else:
            # Non-choice questions keep existing grade if present
            if aq.current_grade:
                total_score += aq.current_grade.awarded_points

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
        "total_score": float(total_score),
        "total_possible": float(total_possible),
        "changed_questions": changed_count,
    }
