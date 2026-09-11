"""End-to-End Scenario 4: Data Lifecycle & Retention Pruning Engine (TASK-028).

Validates Algorithm 13 and Database Architecture Retention Matrix 15:
1. 30-day Enrollment Detail Purge:
   - Student enrolls, completes lessons, takes assessment, achieves course completion.
   - CourseCompletionSummary is generated and stored.
   - Student withdraws (LEFT) and 30-day retention window elapses.
   - Granular lesson progress and attempt answers/events are purged (skeleton tombstone).
   - CourseCompletionSummary is strictly PRESERVED indefinitely for prerequisite validation.
   - Enrollment status transitions to DETAIL_PURGED with append-only EnrollmentEvent.
2. 30-day TRASH Pruning (Hard Delete vs Historical Archival):
   - Expired FileAsset (>30 days): physical bytes unlinked from storage when ref_count==0.
   - Unexpired FileAsset (<30 days): preserved on disk and restorable to ACTIVE.
   - Assessments: unused hard-deleted; attempted transitioned to ARCHIVED.
   - Courses: unused hard-deleted; with student history transitioned to ARCHIVED.
   - Questions: unused hard-deleted; answered/assigned transitioned to RETIRED.
3. AI Chat Inactivity 5-Minute Inactivity Purge:
   - Conversations inactive > 5 minutes have raw AIMessage content wiped completely.
   - Minimal AIConversation metadata preserved with status EXPIRED.
   - Active conversations remain intact.
4. Audit Log Absolute Immunity:
   - Guarantee audit_events table is strictly IMMUNE and never deleted or mutated.
"""

from __future__ import annotations

import io
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import AIConversation, AIMessage
from pwd301.models.assessment import (
    Assessment,
)
from pwd301.models.attempt_regrade import (
    AttemptAnswer,
    AttemptAnswerEvent,
    AttemptQuestion,
)
from pwd301.models.course import (
    Course,
    CourseCompletionSummary,
    EnrollmentEvent,
    LessonProgress,
)
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.completion_service import (
    set_course_completion_rule,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
    leave_course,
)
from pwd301.services.file_service import (
    get_file_storage_root,
    restore_file_asset,
    store_file_stream,
    trash_file_asset,
)
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    record_lesson_progress,
)
from pwd301.services.question_bank_service import create_question
from pwd301.services.retention_service import (
    prune_trash_entities,
    purge_expired_ai_messages,
    purge_expired_enrollment_details,
    run_full_retention_cycle,
)
from pwd301.services.user_service import assign_role_to_user, register_user


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
    """Create administrator user."""
    u = register_user(
        f"ret_admin_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Retention Admin",
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user(
        f"ret_inst_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Retention Instructor",
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    return register_user(
        f"ret_student_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Retention Student",
    )


def _publish_course(instructor: User, admin: User, course: Course, session: Session) -> Course:
    """Promote course from DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED."""
    change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW", session=session)
    change_course_status(admin, course.id, "APPROVED", session=session)
    return change_course_status(admin, course.id, "PUBLISHED", session=session)


def test_enrollment_detail_purge_preserves_course_completion_summary(
    app: Flask,
    admin_user: User,
    instructor_user: User,
    student_user: User,
) -> None:
    """E2E Retention 1: Purge details of former student while permanently retaining
    prerequisite proof.
    """
    sess: Session = db.session

    # 1. Instructor creates Course A and downstream Course B
    course_a = create_course(
        actor=instructor_user,
        data={
            "course_code": f"RET-A-{uuid.uuid4().hex[:4].upper()}",
            "title": "Foundation of Operating Systems",
            "difficulty": "BEGINNER",
        },
        session=sess,
    )
    course_b = create_course(
        actor=instructor_user,
        data={
            "course_code": f"RET-B-{uuid.uuid4().hex[:4].upper()}",
            "title": "Distributed Systems Engineering",
            "difficulty": "ADVANCED",
        },
        session=sess,
    )
    _publish_course(instructor_user, admin_user, course_a, session=sess)
    _publish_course(instructor_user, admin_user, course_b, session=sess)

    # Course B requires Course A
    add_course_prerequisite(
        actor=instructor_user,
        course_id=course_b.id,
        prerequisite_course_id=course_a.id,
        session=sess,
    )

    # Lessons and Completion Rule for Course A (2 required lessons)
    lesson = create_lesson(
        actor=instructor_user,
        course_id=course_a.id,
        data={
            "title": "Intro to Concurrency",
            "markdown_content": "# Intro to Concurrency\nMutexes and locks.",
        },
        session=sess,
    )
    change_lesson_status(instructor_user, lesson.id, "PUBLISHED", session=sess)

    lesson2 = create_lesson(
        actor=instructor_user,
        course_id=course_a.id,
        data={
            "title": "Advanced Concurrency",
            "markdown_content": "# Advanced Concurrency\nSemaphores and barriers.",
        },
        session=sess,
    )
    change_lesson_status(instructor_user, lesson2.id, "PUBLISHED", session=sess)

    set_course_completion_rule(
        actor=instructor_user,
        course_id=course_a.id,
        payload={
            "require_all_required_lessons": True,
            "require_required_assessments": True,
            "minimum_progress_percent": 100.0,
        },
        session=sess,
    )

    # Assessment for Course A
    q = create_question(
        actor=instructor_user,
        course_id=course_a.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is a mutex?",
            "default_points": 10.0,
            "choices": [
                {
                    "choice_key": "A",
                    "content": "Mutual exclusion lock",
                    "is_correct": True,
                    "position": 1,
                },
                {
                    "choice_key": "B",
                    "content": "Multiple execution thread",
                    "is_correct": False,
                    "position": 2,
                },
            ],
        },
        session=sess,
    )
    asm = create_assessment(
        instructor_user,
        course_a.id,
        {
            "title": "OS Final Quiz",
            "assessment_type": "QUIZ",
            "is_required_for_completion": True,
            "max_attempts": 3,
            "passing_score": 10.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, asm.id, {"title": "Section 1"}, session=sess)
    assign_question(
        instructor_user,
        asm.id,
        {"question_id": q.id, "section_id": sec.id, "assigned_points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm.id, session=sess)

    # 2. Student enrolls in Course A, completes lesson, takes quiz
    enrollment = enroll_student(student_user, course_a.id, session=sess)
    period = enrollment.current_period
    assert period is not None

    record_lesson_progress(
        actor=student_user,
        lesson_id=lesson.id,
        seconds_increment=30,
        view_fraction=1.0,
        session=sess,
    )
    sess.commit()

    attempt, raw_lease_token = start_assessment_attempt(student_user, asm.id, session=sess)
    aq = sess.query(AttemptQuestion).filter(AttemptQuestion.attempt_id == attempt.id).first()
    assert aq is not None

    choice_a = next(c for c in aq.choice_snapshots if "Mutual exclusion" in c.content_snapshot)
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "choice_keys": [str(choice_a.choice_key_snapshot)],
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=raw_lease_token,
        session=sess,
    )
    sess.commit()
    submit_assessment_attempt(
        actor=student_user,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=raw_lease_token,
        session=sess,
    )
    sess.commit()

    # 3. Student leaves course while ACTIVE -> period status becomes 'LEFT'
    enrollment = leave_course(
        student_user, course_a.id, reason="Withdrawn from course", session=sess
    )
    sess.commit()
    assert enrollment.status == "LEFT"

    # Compact CourseCompletionSummary represents prior permanent completion/prerequisite proof
    summary = CourseCompletionSummary(
        student_user_id=student_user.id,
        course_id=course_a.id,
        ever_completed=True,
        prerequisite_eligible=True,
        first_completed_at=utc_now() - timedelta(days=35),
        latest_completed_at=utc_now() - timedelta(days=35),
        final_aggregate_score=Decimal("100.0000"),
    )
    sess.add(summary)
    sess.commit()

    # Fast-forward retention cutoff date to simulate > 30 days after leaving
    sess.refresh(period)
    assert period.status == "LEFT"
    period.retention_due_at = utc_now() - timedelta(days=31)
    sess.commit()

    # Verify rows exist before purge
    lp_count_before = (
        sess.query(LessonProgress).filter(LessonProgress.enrollment_period_id == period.id).count()
    )
    assert lp_count_before > 0

    ans_count_before = (
        sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).count()
    )
    assert ans_count_before > 0

    # 5. Run enrollment details retention purge
    purged_count = purge_expired_enrollment_details(session=sess)
    sess.commit()
    assert purged_count >= 1

    # 6. Verify granular data was purged
    lp_count_after = (
        sess.query(LessonProgress).filter(LessonProgress.enrollment_period_id == period.id).count()
    )
    assert lp_count_after == 0

    ans_count_after = (
        sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).count()
    )
    assert ans_count_after == 0

    evt_count_after = (
        sess.query(AttemptAnswerEvent)
        .filter(AttemptAnswerEvent.attempt_question_id == aq.id)
        .count()
    )
    assert evt_count_after == 0

    # Parent attempt skeleton and scores preserved
    sess.refresh(attempt)
    assert attempt.is_detail_purged is True
    assert attempt.detail_purged_at is not None
    assert attempt.result is not None
    assert attempt.result.passed is True

    # Period status is PURGED
    sess.refresh(period)
    assert period.status == "PURGED"
    assert period.detail_purged_at is not None

    # EnrollmentEvent was recorded
    ee = (
        sess.query(EnrollmentEvent)
        .filter(
            EnrollmentEvent.enrollment_id == enrollment.id,
            EnrollmentEvent.event_type == "DETAIL_PURGED",
        )
        .first()
    )
    assert ee is not None

    # 7. CRITICAL INVARIANT: CourseCompletionSummary MUST BE PERMANENTLY PRESERVED!
    retained_summary = (
        sess.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == student_user.id,
            CourseCompletionSummary.course_id == course_a.id,
        )
        .first()
    )
    assert retained_summary is not None
    assert retained_summary.ever_completed is True
    assert retained_summary.prerequisite_eligible is True

    # Student can still enroll in Course B using retained prerequisite summary!
    enroll_b = enroll_student(student_user, course_b.id, session=sess)
    sess.commit()
    assert enroll_b.status == "ACTIVE"


def test_trash_pruning_file_assets_lifecycle(
    app: Flask,
    admin_user: User,
    instructor_user: User,
) -> None:
    """E2E Retention 2: TRASH pruning unlinks physical disk files when >30 days,
    preserves restorable files.
    """
    sess: Session = db.session
    storage_root = get_file_storage_root()

    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"TRASH-FILE-{uuid.uuid4().hex[:4].upper()}",
            "title": "Storage Lifecycle Lab",
        },
        session=sess,
    )
    _publish_course(instructor_user, admin_user, course, session=sess)

    # 1. Upload File 1 (will expire in TRASH)
    file1_content = b"PDF-1.4 Dummy Syllabus Content for File 1"
    asset1 = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=io.BytesIO(file1_content),
        filename="syllabus_expired.pdf",
        content_type="application/pdf",
        session=sess,
    )
    sess.commit()
    blob1 = asset1.current_revision.blob
    file1_disk_path = storage_root / blob1.storage_key
    assert file1_disk_path.exists()

    # 2. Upload File 2 (will NOT expire, restorable)
    file2_content = b"PDF-1.4 Dummy Syllabus Content for File 2"
    asset2 = store_file_stream(
        actor=instructor_user,
        course_id=course.id,
        file_stream=io.BytesIO(file2_content),
        filename="syllabus_keep.pdf",
        content_type="application/pdf",
        session=sess,
    )
    sess.commit()
    blob2 = asset2.current_revision.blob
    file2_disk_path = storage_root / blob2.storage_key
    assert file2_disk_path.exists()

    # 3. Move both to TRASH
    trash_file_asset(instructor_user, asset1.id, session=sess)
    trash_file_asset(instructor_user, asset2.id, session=sess)
    sess.commit()

    # Asset 1 restore window expired (set in past)
    asset1.restore_until = utc_now() - timedelta(days=5)
    # Asset 2 restore window still active (in future)
    asset2.restore_until = utc_now() + timedelta(days=20)
    sess.commit()

    # 4. Run trash pruning
    prune_res = prune_trash_entities(session=sess)
    sess.commit()
    assert prune_res["file_assets"] >= 1

    # 5. Asset 1 is deleted from DB and unlinked from disk
    assert sess.get(FileAsset, asset1.id) is None
    assert not file1_disk_path.exists()

    # 6. Asset 2 is preserved in DB and still on disk
    assert sess.get(FileAsset, asset2.id) is not None
    assert file2_disk_path.exists()

    # 7. Asset 2 can be restored back to ACTIVE
    restored2 = restore_file_asset(instructor_user, asset2.id, session=sess)
    assert restored2.status == "ACTIVE"
    assert restored2.restore_until is None

    # Cleanup File 2
    file2_disk_path.unlink(missing_ok=True)


def test_trash_pruning_assessments_courses_questions_differentiation(
    app: Flask,
    admin_user: User,
    instructor_user: User,
    student_user: User,
) -> None:
    """E2E Retention 3: Pruning disposable unused entities vs historically referenced
    archival tombstones.
    """
    sess: Session = db.session

    # 1. COURSES:
    # Course with history vs Unused Course
    course_used = create_course(
        actor=instructor_user,
        data={"course_code": f"CRS-USED-{uuid.uuid4().hex[:4].upper()}", "title": "Used Course"},
        session=sess,
    )
    _publish_course(instructor_user, admin_user, course_used, session=sess)
    enroll_student(student_user, course_used.id, session=sess)

    course_unused = create_course(
        actor=instructor_user,
        data={
            "course_code": f"CRS-UNUSED-{uuid.uuid4().hex[:4].upper()}",
            "title": "Unused Course",
        },
        session=sess,
    )

    # Both moved to TRASH with past deadline
    course_used.status = "TRASH"
    course_used.restore_until = utc_now() - timedelta(days=2)
    course_unused.status = "TRASH"
    course_unused.restore_until = utc_now() - timedelta(days=2)

    # 2. QUESTIONS:
    q_used = create_question(
        actor=instructor_user,
        course_id=course_used.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Referenced question?",
            "default_points": 10.0,
            "choices": [
                {"choice_key": "A", "content": "Yes", "is_correct": True, "position": 1},
                {"choice_key": "B", "content": "No", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    q_unused = create_question(
        actor=instructor_user,
        course_id=course_used.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Unreferenced question?",
            "default_points": 10.0,
            "choices": [
                {"choice_key": "A", "content": "Alpha", "is_correct": True, "position": 1},
                {"choice_key": "B", "content": "Beta", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )

    # 3. ASSESSMENTS:
    asm_used = create_assessment(
        instructor_user,
        course_used.id,
        {"title": "Used Assessment", "assessment_type": "FINAL", "max_attempts": 2},
        session=sess,
    )
    sec = create_section(instructor_user, asm_used.id, {"title": "Section A"}, session=sess)
    assign_question(
        instructor_user,
        asm_used.id,
        {"question_id": q_used.id, "section_id": sec.id, "assigned_points": 10.0},
        session=sess,
    )
    publish_assessment(instructor_user, asm_used.id, session=sess)

    # Student starts attempt -> freezes attempt and establishes historical reference
    attempt = start_assessment_attempt(student_user, asm_used.id, session=sess)
    assert attempt is not None

    asm_unused = create_assessment(
        instructor_user,
        course_used.id,
        {"title": "Unused Assessment", "assessment_type": "QUIZ", "max_attempts": 1},
        session=sess,
    )

    # Set questions and assessments into TRASH with expired deadlines
    q_used.status = "TRASH"
    q_used.restore_until = utc_now() - timedelta(days=2)
    q_unused.status = "TRASH"
    q_unused.restore_until = utc_now() - timedelta(days=2)

    asm_used.status = "TRASH"
    asm_used.restore_until = utc_now() - timedelta(days=2)
    asm_unused.status = "TRASH"
    asm_unused.restore_until = utc_now() - timedelta(days=2)
    sess.commit()

    # 4. Run TRASH Pruning
    prune_trash_entities(session=sess)
    sess.commit()

    # 5. Verify Courses:
    # Unused course is completely deleted
    assert sess.get(Course, course_unused.id) is None
    # Used course transitioned to ARCHIVED historical tombstone
    refreshed_used_course = sess.get(Course, course_used.id)
    assert refreshed_used_course is not None
    assert refreshed_used_course.status == "ARCHIVED"

    # 6. Verify Assessments:
    # Unused assessment is completely deleted
    assert sess.get(Assessment, asm_unused.id) is None
    # Used assessment transitioned to ARCHIVED historical tombstone
    refreshed_used_asm = sess.get(Assessment, asm_used.id)
    assert refreshed_used_asm is not None
    assert refreshed_used_asm.status == "ARCHIVED"

    # 7. Verify Questions:
    # Unused question is completely deleted
    assert sess.get(Question, q_unused.id) is None
    # Used question transitioned to RETIRED historical tombstone
    refreshed_used_q = sess.get(Question, q_used.id)
    assert refreshed_used_q is not None
    assert refreshed_used_q.status == "RETIRED"


def test_ai_chat_inactivity_five_minute_purge(
    app: Flask,
    student_user: User,
) -> None:
    """E2E Retention 4: Wipe raw AIMessage content after 5-minute inactivity
    while keeping metadata.
    """
    sess: Session = db.session
    now = utc_now()

    # 1. Expired conversation (> 5 minutes inactive)
    conv_expired = AIConversation(
        user_id=student_user.id,
        context_type="GLOBAL",
        course_id=None,
        status="ACTIVE",
        created_at=now - timedelta(minutes=20),
        last_activity_at=now - timedelta(minutes=15),
        expires_at=now - timedelta(minutes=10),
    )
    sess.add(conv_expired)
    sess.flush()

    msg1 = AIMessage(
        conversation_id=conv_expired.id,
        sender="USER",
        content="What is virtual memory and paging?",
        sequence_no=1,
        created_at=now - timedelta(minutes=18),
    )
    msg2 = AIMessage(
        conversation_id=conv_expired.id,
        sender="ASSISTANT",
        content="Virtual memory allows executing processes that may not be completely in memory...",
        sequence_no=2,
        created_at=now - timedelta(minutes=17),
    )
    sess.add_all([msg1, msg2])

    # 2. Active conversation (< 5 minutes inactive)
    conv_active = AIConversation(
        user_id=student_user.id,
        context_type="GLOBAL",
        course_id=None,
        status="ACTIVE",
        created_at=now - timedelta(minutes=2),
        last_activity_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=10),
    )
    sess.add(conv_active)
    sess.flush()

    msg_active = AIMessage(
        conversation_id=conv_active.id,
        sender="USER",
        content="Explain page replacement algorithms",
        sequence_no=1,
        created_at=now - timedelta(minutes=1),
    )
    sess.add(msg_active)
    sess.commit()

    # 3. Execute AI chat inactivity purge
    purged_convs = purge_expired_ai_messages(session=sess, cutoff_date=now)
    sess.commit()
    assert purged_convs >= 1

    # 4. Check expired conversation: messages deleted, metadata retained with EXPIRED status
    sess.refresh(conv_expired)
    assert conv_expired.status == "EXPIRED"
    expired_msgs_count = (
        sess.query(AIMessage).filter(AIMessage.conversation_id == conv_expired.id).count()
    )
    assert expired_msgs_count == 0

    # 5. Check active conversation: messages untouched, status ACTIVE
    sess.refresh(conv_active)
    assert conv_active.status == "ACTIVE"
    active_msgs_count = (
        sess.query(AIMessage).filter(AIMessage.conversation_id == conv_active.id).count()
    )
    assert active_msgs_count == 1


def test_audit_logs_absolute_immunity_under_retention_cycle(
    app: Flask,
    admin_user: User,
) -> None:
    """E2E Retention 5: Guarantee AuditEvent table is strictly IMMUNE from deletion
    (Append-only).
    """
    sess: Session = db.session

    # Record baseline audit events
    audit_pre1 = AuditEvent(
        actor_user_id=admin_user.id,
        actor_roles_snapshot="ADMIN",
        action="SYSTEM_PARAMETER_UPDATED",
        target_type="SYSTEM",
        target_id=0,
        reason="Pre-retention parameter configuration",
        created_at=utc_now() - timedelta(days=90),
    )
    audit_pre2 = AuditEvent(
        actor_user_id=admin_user.id,
        actor_roles_snapshot="ADMIN",
        action="SECURITY_KEY_ROTATED",
        target_type="SECURITY",
        target_id=0,
        reason="Scheduled encryption key rotation",
        created_at=utc_now() - timedelta(days=45),
    )
    sess.add_all([audit_pre1, audit_pre2])
    sess.commit()

    pre_count = sess.query(AuditEvent).count()
    assert pre_count >= 2

    # Execute complete retention cycle
    summary = run_full_retention_cycle(session=sess)
    assert summary["status"] == "COMPLETED"

    post_count = sess.query(AuditEvent).count()
    # Audit log must strictly grow or remain equal (appended cycle audit event)
    assert post_count > pre_count

    # The historical audit events are intact and never mutated
    sess.refresh(audit_pre1)
    sess.refresh(audit_pre2)
    assert audit_pre1.action == "SYSTEM_PARAMETER_UPDATED"
    assert audit_pre2.action == "SECURITY_KEY_ROTATED"
