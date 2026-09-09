"""Retention and data purging service for PWD301.

Implements Skeleton Tombstone purge invariant (Defect 4):
- Never delete the parent assessment_attempts row (preserves educational audit trail).
- Purges raw child detail tables:
  * attempt_answer_events
  * attempt_answers
  * attempt_answer_choices
  * attempt_choice_snapshots
- Sets is_detail_purged = 1, detail_purged_at = SYSUTCDATETIME()
- Preserves high-level attempt metadata (scores, timestamps, completion status).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
)
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import _resolve_attempt
from pwd301.services.exceptions import AttemptNotFoundError


def purge_attempt_details_skeleton_tombstone(
    attempt_id: AssessmentAttempt | int | uuid.UUID | str,
    actor_id: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentAttempt:
    """Purge granular attempt details while preserving the parent AssessmentAttempt skeleton.

    Args:
        attempt_id: AssessmentAttempt instance, integer PK, public UUID, or string.
        actor_id: Optional ID of user performing the purge (for audit).
        session: Optional SQLAlchemy session.

    Returns:
        Updated AssessmentAttempt with is_detail_purged=True.
    """
    sess = session if session is not None else db.session

    attempt = _resolve_attempt(attempt_id, session=sess)
    if attempt is None:
        raise AttemptNotFoundError("Assessment attempt not found.")

    if attempt.is_detail_purged:
        return attempt

    now = utc_now()

    # Get attempt_question IDs
    aq_ids = [
        row[0]
        for row in sess.query(AttemptQuestion.id)
        .filter(AttemptQuestion.attempt_id == attempt.id)
        .all()
    ]

    if aq_ids:
        # 1. Truncate attempt_answer_events
        sess.query(AttemptAnswerEvent).filter(
            AttemptAnswerEvent.attempt_question_id.in_(aq_ids)
        ).delete(synchronize_session=False)

        # 2. Find and delete attempt_answer_choices and attempt_answers
        ans_ids = [
            row[0]
            for row in sess.query(AttemptAnswer.id)
            .filter(AttemptAnswer.attempt_question_id.in_(aq_ids))
            .all()
        ]
        if ans_ids:
            sess.query(AttemptAnswerChoice).filter(
                AttemptAnswerChoice.attempt_answer_id.in_(ans_ids)
            ).delete(synchronize_session=False)

            sess.query(AttemptAnswer).filter(AttemptAnswer.id.in_(ans_ids)).delete(
                synchronize_session=False
            )

        # 3. Truncate attempt_choice_snapshots
        sess.query(AttemptChoiceSnapshot).filter(
            AttemptChoiceSnapshot.attempt_question_id.in_(aq_ids)
        ).delete(synchronize_session=False)

    # 4. Mark skeleton tombstone
    attempt.is_detail_purged = True
    attempt.detail_purged_at = now
    attempt.updated_at = now

    # 5. Record Audit Event
    audit = AuditEvent(
        actor_user_id=actor_id,
        actor_roles_snapshot="SYSTEM",
        action="ATTEMPT_SKELETON_PURGED",
        target_type="ATTEMPT",
        target_id=attempt.id,
        reason=f"Skeleton tombstone purge executed for attempt #{attempt.attempt_number}",
        created_at=now,
    )
    sess.add(audit)
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return attempt
