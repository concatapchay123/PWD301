"""Retention and data lifecycle cleanup service for PWD301.

Implements Algorithm 13 and Database Architecture Retention Matrix 15:
- Skeleton Tombstone attempt detail purge:
  * Purges attempt_answer_events, attempt_answers, attempt_answer_choices.
  * Preserves parent assessment_attempts skeleton and scores.
  * Preserves question_revisions.was_student_exposed invariant.
- 30-day Enrollment detail purge:
  * Targets EnrollmentPeriod in LEFT status where retention_due_at <= now.
  * Purges lesson_progress and calls attempt skeleton purge.
  * Preserves CourseCompletionSummary permanently for prerequisite verification.
  * Marks period.detail_purged_at and status = 'PURGED'.
  * Emits EnrollmentEvent(DETAIL_PURGED).
- 30-day TRASH Pruning (hard-delete vs historical archival tombstone):
  * Targets FileAsset, Assessment, Course, Question in TRASH where restore_until <= now.
  * FileAsset: unlinks physical storage blob when ref_count == 0; deletes asset/revisions.
  * Assessment: hard-deletes if zero attempts; transitions to ARCHIVED if attempts exist.
  * Course: hard-deletes if zero history; transitions to ARCHIVED if history exists.
  * Question: hard-deletes if unreferenced; transitions to RETIRED if referenced.
- AI Chat Inactivity cleanup:
  * Purges raw chat contents (ai_messages.content) after 5 minutes of inactivity.
  * Preserves minimal AIConversation metadata.
- Audit Log Immunity:
  * Absolutely NEVER mutates or deletes rows from audit_events (Append-only Invariant).
"""

from __future__ import annotations

import contextlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.ai_rag import (
    AIConversation,
    AIGeneratedQuestionDraft,
    AIMessage,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeVersion,
)
from pwd301.models.assessment import (
    Assessment,
    AssessmentBlueprint,
    AssessmentBlueprintRule,
    AssessmentQuestionAssignment,
    AssessmentSection,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
)
from pwd301.models.course import (
    Course,
    CourseChangeRequest,
    CourseCompletionRule,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
)
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

    return attempt


def purge_expired_enrollment_details(
    session: Session | scoped_session[Any] | None = None,
    cutoff_date: datetime | None = None,
    batch_size: int = 100,
) -> int:
    """Purge lesson progress and attempt details for enrollments left > 30 days ago.

    Invariants preserved:
    - CourseCompletionSummary is never deleted (used indefinitely for prerequisites).
    - question_revisions.was_student_exposed is never cleared.
    - AssessmentAttempt parent rows remain as skeleton tombstones.
    - EnrollmentEvent(DETAIL_PURGED) is appended.

    Returns:
        Number of enrollment periods purged.
    """
    sess = session if session is not None else db.session
    now = cutoff_date or utc_now()

    # Find candidate periods: status is LEFT, retention_due_at <= now, detail_purged_at is NULL
    periods = (
        sess.query(EnrollmentPeriod)
        .filter(
            EnrollmentPeriod.status == "LEFT",
            EnrollmentPeriod.retention_due_at.is_not(None),
            EnrollmentPeriod.retention_due_at <= now,
            EnrollmentPeriod.detail_purged_at.is_(None),
        )
        .limit(batch_size)
        .all()
    )

    purged_count = 0
    for period in periods:
        enrollment = period.enrollment
        if enrollment is None:
            continue

        # 1. Delete granular lesson progress for this period
        sess.query(LessonProgress).filter(LessonProgress.enrollment_period_id == period.id).delete(
            synchronize_session=False
        )

        # 2. Skeleton-purge completed attempts by this student for this enrollment period
        attempts = (
            sess.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.enrollment_period_id == period.id,
                AssessmentAttempt.is_detail_purged.is_(False),
            )
            .all()
        )
        for att in attempts:
            purge_attempt_details_skeleton_tombstone(att, actor_id=None, session=sess)

        # 3. Update period status and purge timestamp
        period.status = "PURGED"
        period.detail_purged_at = now

        # 4. Append EnrollmentEvent
        event = EnrollmentEvent(
            enrollment_id=enrollment.id,
            period_id=period.id,
            event_type="DETAIL_PURGED",
            reason="30-day enrollment detail retention window elapsed",
            created_at=now,
        )
        sess.add(event)

        # 5. Check if enrollment has any remaining non-purged periods
        active_or_unpurged = (
            sess.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.enrollment_id == enrollment.id,
                EnrollmentPeriod.status != "PURGED",
            )
            .count()
        )
        if active_or_unpurged == 0:
            enrollment.status = "DETAIL_PURGED"

        # 6. Audit event
        audit = AuditEvent(
            actor_user_id=None,
            actor_roles_snapshot="SYSTEM",
            action="ENROLLMENT_DETAILS_PURGED",
            target_type="ENROLLMENT_PERIOD",
            target_id=period.id,
            reason=f"Purged granular learning details for enrollment period #{period.period_no}",
            created_at=now,
        )
        sess.add(audit)
        purged_count += 1

    sess.flush()
    return purged_count


def prune_trash_entities(
    session: Session | scoped_session[Any] | None = None,
    cutoff_date: datetime | None = None,
    batch_size: int = 100,
) -> dict[str, int]:
    """Prune entities in TRASH whose restore_until deadline has passed.

    Invariants preserved:
    - Files: decrements blob reference count; deletes physical disk file when ref_count == 0.
    - Assessments with student attempts are never hard-deleted; transitioned to ARCHIVED.
    - Courses with student history are never hard-deleted; transitioned to ARCHIVED.
    - Questions referenced in attempts are never hard-deleted; transitioned to RETIRED.
    - AuditEvent table is strictly IMMUNE and never deleted.

    Returns:
        Dictionary mapping entity types to count of pruned/archived records.
    """
    from pwd301.services.file_service import get_file_storage_root

    sess = session if session is not None else db.session
    now = cutoff_date or utc_now()
    counts = {
        "file_assets": 0,
        "assessments": 0,
        "courses": 0,
        "questions": 0,
    }

    # -------------------------------------------------------------------------
    # 1. File Assets in TRASH past restore_until
    # -------------------------------------------------------------------------
    expired_files = (
        sess.query(FileAsset)
        .filter(
            FileAsset.status == "TRASH",
            FileAsset.restore_until.is_not(None),
            FileAsset.restore_until <= now,
        )
        .limit(batch_size)
        .all()
    )

    storage_root = None
    with contextlib.suppress(Exception):
        storage_root = get_file_storage_root()

    for asset in expired_files:
        # Delete linked lesson resources
        sess.query(LessonResource).filter(LessonResource.file_asset_id == asset.id).delete(
            synchronize_session=False
        )

        # Inspect revisions and blob references
        revisions = sess.query(FileRevision).filter(FileRevision.file_asset_id == asset.id).all()
        for rev in revisions:
            # Delete scan results
            sess.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).delete(
                synchronize_session=False
            )

            # Decrement blob ref count
            blob = sess.get(FileBlob, rev.blob_id)
            if blob is not None:
                blob.reference_count = max(0, blob.reference_count - 1)
                if blob.reference_count == 0:
                    # Physically remove file from disk
                    if storage_root is not None and blob.storage_key:
                        file_path = storage_root / blob.storage_key
                        if file_path.exists():
                            with contextlib.suppress(OSError):
                                file_path.unlink(missing_ok=True)
                    blob.status = "DELETED"
                    blob.deleted_at = now

            sess.delete(rev)

        sess.delete(asset)
        counts["file_assets"] += 1

    # -------------------------------------------------------------------------
    # 2. Assessments in TRASH past restore_until
    # -------------------------------------------------------------------------
    expired_assessments = (
        sess.query(Assessment)
        .filter(
            Assessment.status == "TRASH",
            Assessment.restore_until.is_not(None),
            Assessment.restore_until <= now,
        )
        .limit(batch_size)
        .all()
    )

    for asm in expired_assessments:
        attempts_count = (
            sess.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == asm.id).count()
        )
        if attempts_count > 0:
            # Has student attempts: transition to ARCHIVED tombstone per Matrix 15
            asm.status = "ARCHIVED"
            asm.restore_until = None
            asm.updated_at = now
        else:
            # Disposable with no attempts: hard delete
            sess.query(AssessmentQuestionAssignment).filter(
                AssessmentQuestionAssignment.assessment_id == asm.id
            ).delete(synchronize_session=False)

            blueprint_subq = sess.query(AssessmentBlueprint.id).filter(
                AssessmentBlueprint.assessment_id == asm.id
            )
            sess.query(AssessmentBlueprintRule).filter(
                AssessmentBlueprintRule.blueprint_id.in_(blueprint_subq)
            ).delete(synchronize_session=False)

            sess.query(AssessmentBlueprint).filter(
                AssessmentBlueprint.assessment_id == asm.id
            ).delete(synchronize_session=False)

            sess.query(AssessmentSection).filter(AssessmentSection.assessment_id == asm.id).delete(
                synchronize_session=False
            )

            sess.delete(asm)
        counts["assessments"] += 1

    # -------------------------------------------------------------------------
    # 3. Courses in TRASH past restore_until
    # -------------------------------------------------------------------------
    expired_courses = (
        sess.query(Course)
        .filter(
            Course.status == "TRASH",
            Course.restore_until.is_not(None),
            Course.restore_until <= now,
        )
        .limit(batch_size)
        .all()
    )

    for crs in expired_courses:
        has_enrollments = sess.query(Enrollment).filter(Enrollment.course_id == crs.id).count() > 0
        has_summaries = (
            sess.query(CourseCompletionSummary)
            .filter(CourseCompletionSummary.course_id == crs.id)
            .count()
            > 0
        )
        if has_enrollments or has_summaries:
            # Preserve minimal Course identity as ARCHIVED historical tombstone
            crs.status = "ARCHIVED"
            crs.restore_until = None
            crs.updated_at = now
        else:
            # Disposable course with zero student history: delete all dependent children
            # in topological order
            # 1. Lesson resources
            lesson_ids = [
                lid[0] for lid in sess.query(Lesson.id).filter(Lesson.course_id == crs.id).all()
            ]
            if lesson_ids:
                sess.query(LessonResource).filter(LessonResource.lesson_id.in_(lesson_ids)).delete(
                    synchronize_session=False
                )

            # 2. RAG Knowledge documents, versions, chunks
            kdoc_ids = [
                kid[0]
                for kid in sess.query(KnowledgeDocument.id)
                .filter(KnowledgeDocument.course_id == crs.id)
                .all()
            ]
            if kdoc_ids:
                kver_ids = [
                    kvid[0]
                    for kvid in sess.query(KnowledgeVersion.id)
                    .filter(KnowledgeVersion.knowledge_document_id.in_(kdoc_ids))
                    .all()
                ]
                if kver_ids:
                    sess.query(KnowledgeChunk).filter(
                        KnowledgeChunk.knowledge_version_id.in_(kver_ids)
                    ).delete(synchronize_session=False)
                    sess.query(KnowledgeVersion).filter(KnowledgeVersion.id.in_(kver_ids)).delete(
                        synchronize_session=False
                    )
                sess.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(kdoc_ids)).delete(
                    synchronize_session=False
                )

            # 3. AI conversation messages & question drafts
            sess.query(AIGeneratedQuestionDraft).filter(
                AIGeneratedQuestionDraft.course_id == crs.id
            ).delete(synchronize_session=False)
            conv_ids = [
                cid[0]
                for cid in sess.query(AIConversation.id)
                .filter(AIConversation.course_id == crs.id)
                .all()
            ]
            if conv_ids:
                sess.query(AIMessage).filter(AIMessage.conversation_id.in_(conv_ids)).delete(
                    synchronize_session=False
                )
                sess.query(AIConversation).filter(AIConversation.id.in_(conv_ids)).delete(
                    synchronize_session=False
                )

            # 4. Assessments without attempts
            asm_ids = [
                aid[0]
                for aid in sess.query(Assessment.id).filter(Assessment.course_id == crs.id).all()
            ]
            if asm_ids:
                sess.query(AssessmentQuestionAssignment).filter(
                    AssessmentQuestionAssignment.assessment_id.in_(asm_ids)
                ).delete(synchronize_session=False)
                bp_ids = [
                    bpid[0]
                    for bpid in sess.query(AssessmentBlueprint.id)
                    .filter(AssessmentBlueprint.assessment_id.in_(asm_ids))
                    .all()
                ]
                if bp_ids:
                    sess.query(AssessmentBlueprintRule).filter(
                        AssessmentBlueprintRule.blueprint_id.in_(bp_ids)
                    ).delete(synchronize_session=False)
                    sess.query(AssessmentBlueprint).filter(
                        AssessmentBlueprint.id.in_(bp_ids)
                    ).delete(synchronize_session=False)
                sess.query(AssessmentSection).filter(
                    AssessmentSection.assessment_id.in_(asm_ids)
                ).delete(synchronize_session=False)
                sess.query(Assessment).filter(Assessment.id.in_(asm_ids)).delete(
                    synchronize_session=False
                )

            # 5. Prerequisites, completion rules, change requests, and lessons
            sess.query(CoursePrerequisite).filter(
                (CoursePrerequisite.course_id == crs.id)
                | (CoursePrerequisite.prerequisite_course_id == crs.id)
            ).delete(synchronize_session=False)

            sess.query(CourseCompletionRule).filter(
                CourseCompletionRule.course_id == crs.id
            ).delete(synchronize_session=False)

            sess.query(CourseChangeRequest).filter(CourseChangeRequest.course_id == crs.id).delete(
                synchronize_session=False
            )

            sess.query(Lesson).filter(Lesson.course_id == crs.id).delete(synchronize_session=False)

            sess.delete(crs)
        counts["courses"] += 1

    # -------------------------------------------------------------------------
    # 4. Questions in TRASH past restore_until
    # -------------------------------------------------------------------------
    expired_questions = (
        sess.query(Question)
        .filter(
            Question.status == "TRASH",
            Question.restore_until.is_not(None),
            Question.restore_until <= now,
        )
        .limit(batch_size)
        .all()
    )

    for q in expired_questions:
        has_attempts = (
            sess.query(AttemptQuestion).filter(AttemptQuestion.source_question_id == q.id).count()
            > 0
        )
        has_assessments = (
            sess.query(AssessmentQuestionAssignment)
            .filter(AssessmentQuestionAssignment.question_id == q.id)
            .count()
            > 0
        )
        if has_attempts or has_assessments:
            # Question was answered or used: preserve minimal identity indefinitely
            q.status = "RETIRED"
            q.restore_until = None
            q.updated_at = now
        else:
            # Disposable unused question: hard delete choices, revisions, and question
            rev_ids = [
                r[0]
                for r in sess.query(QuestionRevision.id)
                .filter(QuestionRevision.question_id == q.id)
                .all()
            ]
            if rev_ids:
                sess.query(QuestionRevisionChoice).filter(
                    QuestionRevisionChoice.question_revision_id.in_(rev_ids)
                ).delete(synchronize_session=False)

                sess.query(QuestionRevisionAcceptedAnswer).filter(
                    QuestionRevisionAcceptedAnswer.question_revision_id.in_(rev_ids)
                ).delete(synchronize_session=False)

                sess.query(QuestionProvenance).filter(
                    QuestionProvenance.question_revision_id.in_(rev_ids)
                ).delete(synchronize_session=False)

                sess.query(QuestionRevision).filter(QuestionRevision.question_id == q.id).delete(
                    synchronize_session=False
                )

            sess.delete(q)
        counts["questions"] += 1

    sess.flush()
    sess.expire_all()
    return counts


def purge_expired_ai_messages(
    session: Session | scoped_session[Any] | None = None,
    cutoff_date: datetime | None = None,
    batch_size: int = 100,
) -> int:
    """Purge raw AI chat content after 5 minutes of inactivity (Matrix row 51).

    Invariants preserved:
    - Raw messages in ai_messages table are completely deleted.
    - AIConversation parent record is retained with status = 'EXPIRED'.
    - AIRequest telemetry remains intact (raw prompts not stored).

    Returns:
        Number of expired conversations purged.
    """
    sess = session if session is not None else db.session
    now = cutoff_date or utc_now()
    inactivity_cutoff = now - timedelta(seconds=300)

    # Find conversations where expires_at <= now, status is EXPIRED,
    # or last_activity_at <= inactivity_cutoff (5 minutes)
    expired_convs = (
        sess.query(AIConversation)
        .filter(
            (AIConversation.expires_at <= now)
            | (AIConversation.status == "EXPIRED")
            | (AIConversation.last_activity_at <= inactivity_cutoff)
        )
        .limit(batch_size)
        .all()
    )

    purged_count = 0
    for conv in expired_convs:
        # Delete child AIMessage rows to wipe raw chat content completely
        msg_count = (
            sess.query(AIMessage)
            .filter(AIMessage.conversation_id == conv.id)
            .delete(synchronize_session=False)
        )
        if conv.status != "EXPIRED":
            conv.status = "EXPIRED"

        if msg_count > 0:
            purged_count += 1

    sess.flush()
    return purged_count


def run_full_retention_cycle(
    session: Session | scoped_session[Any] | None = None,
    cutoff_date: datetime | None = None,
) -> dict[str, Any]:
    """Execute complete Algorithm 13 data retention and cleanup cycle.

    Idempotent operation coordinating:
    1. Enrollment detail purging (after 30 days of leaving).
    2. Trash entity pruning (files, assessments, courses, questions > 30 days).
    3. AI chat raw content purging (after 5 minutes of inactivity).

    Guarantees:
    - AuditEvent table is append-only and never modified or deleted.
    - Emits high-level system audit log of retention cycle execution.
    """
    sess = session if session is not None else db.session
    now = cutoff_date or utc_now()

    # 1. Purge expired enrollment details
    purged_enrollments = purge_expired_enrollment_details(session=sess, cutoff_date=now)

    # 2. Prune trash entities
    pruned_trash = prune_trash_entities(session=sess, cutoff_date=now)

    # 3. Purge expired AI messages
    purged_ai = purge_expired_ai_messages(session=sess, cutoff_date=now)

    # 4. Append audit event
    audit = AuditEvent(
        actor_user_id=None,
        actor_roles_snapshot="SYSTEM",
        action="RETENTION_CYCLE_EXECUTED",
        target_type="SYSTEM",
        target_id=0,
        reason=(
            f"Retention cycle completed: enrollments={purged_enrollments}, "
            f"files={pruned_trash['file_assets']}, assessments={pruned_trash['assessments']}, "
            f"courses={pruned_trash['courses']}, questions={pruned_trash['questions']}, "
            f"ai_conversations={purged_ai}"
        ),
        created_at=now,
    )
    sess.add(audit)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return {
        "status": "COMPLETED",
        "purged_enrollment_periods": purged_enrollments,
        "pruned_file_assets": pruned_trash["file_assets"],
        "pruned_assessments": pruned_trash["assessments"],
        "pruned_courses": pruned_trash["courses"],
        "pruned_questions": pruned_trash["questions"],
        "purged_ai_conversations": purged_ai,
        "executed_at": now.isoformat(),
    }
