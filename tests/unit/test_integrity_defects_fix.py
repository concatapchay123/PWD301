"""Dedicated unit & regression test suite for the 6 critical database architecture fixes.

Verifies:
1. Circular Foreign Keys broken: current_revision_id/current_version_id removed, is_current with filtered unique index.
2. Regrade Choice Key: choice_key preserved across revisions, regrade matches student snapshot against active revision.
3. Autosave Sequence & Lease Epoch Collision: StaleLeaseEpochError (409) and StaleAnswerSequenceError (409) rejected.
4. Skeleton Tombstone Purge: parent attempt retained with is_detail_purged=True, child details purged, regrade skips gracefully.
5. Duration vs Window Timing: Assessment open_at/time_limit locked after publish, close_at can only extend forward with audit.
6. Relational Staging for Lessons: staged lesson in PENDING_APPROVAL shares position without unique constraint violation,
   approval atomically promotes staged lesson to PUBLISHED and sets old lesson to HISTORICAL.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
)
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.models.file_import import FileAsset, FileRevision
from pwd301.models.identity import Role, User
from pwd301.models.ai_rag import KnowledgeDocument, KnowledgeVersion
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
    update_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    takeover_attempt_lease,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AssessmentLockedError,
    StaleAnswerSequenceError,
    StaleLeaseEpochError,
)
from pwd301.services.lesson_service import (
    approve_course_change_request,
    create_lesson,
    create_lesson_change_request,
)
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
)
from pwd301.services.regrade_worker import regrade_attempt
from pwd301.services.retention_service import purge_attempt_details_skeleton_tombstone
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
    u = register_user("admin_integrity@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("inst_integrity@example.com", "Password@123", "Instructor User")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("student_integrity@example.com", "Password@123", "Student User")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-INTEGRITY",
            "title": "Database Systems Integrity",
            "summary": "Core Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_student(app: Flask, student_user: User, published_course: Course) -> User:
    enroll_student(student_user, published_course.id, session=db.session)
    db.session.commit()
    return student_user


def test_defect_1_circular_foreign_keys_and_is_current_filtered_unique(
    app: Flask, instructor_user: User, published_course: Course
):
    """Defect 1: Circular FKs dropped, is_current with filtered unique index prevents dual active revisions."""
    sess: Session = db.session

    # 1. Check Question / QuestionRevision
    assert not hasattr(Question, "current_revision_id")
    q = Question(
        course_id=published_course.id,
        difficulty="REMEMBER",
        status="ACTIVE",
        creator_user_id=instructor_user.id,
    )
    sess.add(q)
    sess.flush()

    rev1 = QuestionRevision(
        question_id=q.id,
        revision_no=1,
        question_type="SINGLE_CHOICE",
        content="Question content 1",
        is_current=True,
    )
    sess.add(rev1)
    sess.commit()

    # Verify relationship resolves to current revision
    sess.refresh(q)
    assert q.current_revision is not None
    assert q.current_revision.id == rev1.id

    # Inserting a second revision with is_current=True must violate filtered unique index
    rev2 = QuestionRevision(
        question_id=q.id,
        revision_no=2,
        question_type="SINGLE_CHOICE",
        content="Question content 2",
        is_current=True,
    )
    sess.add(rev2)
    with pytest.raises(IntegrityError):
        sess.commit()
    sess.rollback()

    # Inserting second revision with is_current=False succeeds
    rev2_inactive = QuestionRevision(
        question_id=q.id,
        revision_no=2,
        question_type="SINGLE_CHOICE",
        content="Question content 2",
        is_current=False,
    )
    sess.add(rev2_inactive)
    sess.commit()
    assert q.current_revision.id == rev1.id

    # 2. Check FileAsset / FileRevision
    assert not hasattr(FileAsset, "current_revision_id")
    fa = FileAsset(
        course_id=published_course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Diagram.png",
        status="ACTIVE",
    )
    sess.add(fa)
    sess.flush()

    frev1 = FileRevision(
        file_asset_id=fa.id,
        revision_no=1,
        original_filename="Diagram.png",
        size_bytes=1024,
        uploaded_by_user_id=instructor_user.id,
        is_current=True,
    )
    sess.add(frev1)
    sess.commit()

    sess.refresh(fa)
    assert fa.current_revision is not None
    assert fa.current_revision.id == frev1.id

    frev2 = FileRevision(
        file_asset_id=fa.id,
        revision_no=2,
        original_filename="Diagram_v2.png",
        size_bytes=2048,
        uploaded_by_user_id=instructor_user.id,
        is_current=True,
    )
    sess.add(frev2)
    with pytest.raises(IntegrityError):
        sess.commit()
    sess.rollback()

    # 3. Check KnowledgeDocument / KnowledgeVersion
    assert not hasattr(KnowledgeDocument, "current_version_id")
    kd = KnowledgeDocument(
        course_id=published_course.id,
        source_type="FAQ",
        source_entity_id=999,
        status="ACTIVE",
    )
    sess.add(kd)
    sess.flush()

    kver1 = KnowledgeVersion(
        knowledge_document_id=kd.id,
        version_no=1,
        content_hash=b"h" * 32,
        is_current=True,
    )
    sess.add(kver1)
    sess.commit()

    sess.refresh(kd)
    assert kd.current_version is not None
    assert kd.current_version.id == kver1.id

    kver2 = KnowledgeVersion(
        knowledge_document_id=kd.id,
        version_no=2,
        content_hash=b"g" * 32,
        is_current=True,
    )
    sess.add(kver2)
    with pytest.raises(IntegrityError):
        sess.commit()
    sess.rollback()


def test_defect_2_regrade_choice_key_invariant(
    app: Flask, instructor_user: User, student_user: User, published_course: Course, enrolled_student: User
):
    """Defect 2: choice_key is preserved across revisions and correctly evaluated by regrade_attempt."""
    sess: Session = db.session

    # 1. Create MCQ question with Choice Alpha (correct) and Choice Beta (incorrect)
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Which protocol is connection-oriented?",
        "default_points": 10.0,
        "choices": [
            {"content": "TCP", "is_correct": True, "position": 1},
            {"content": "UDP", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL", "notes": "Networking test"},
    }
    q = create_question(instructor_user, published_course.id, payload, session=sess)
    sess.commit()

    tcp_choice = next(c for c in q.current_revision.choices if c.content == "TCP")
    udp_choice = next(c for c in q.current_revision.choices if c.content == "UDP")
    key_alpha = tcp_choice.choice_key
    key_beta = udp_choice.choice_key

    # 2. Publish assessment with this question
    now = datetime.now(UTC)
    assess_payload = {
        "title": "Networking Quiz",
        "assessment_type": "QUIZ",
        "scoring_policy": "HIGHEST",
        "score_release_policy": "IMMEDIATE",
        "time_limit_minutes": 30,
        "attempt_limit": 1,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(days=1)).isoformat(),
    }
    assessment = create_assessment(instructor_user, published_course.id, assess_payload, session=sess)
    sec = create_section(instructor_user, assessment.public_id, {"title": "Section 1", "position": 1}, session=sess)
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0, "position": 1},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.public_id, session=sess)
    sess.commit()

    # 3. Student takes attempt, answering Choice Alpha (TCP)
    attempt, raw_lease_token = start_assessment_attempt(student_user, assessment.public_id, session=sess)
    aq = attempt.attempt_questions[0]

    # Save answer selecting key_alpha
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"choice_keys": [str(key_alpha)], "client_sequence": 1, "lease_epoch": 1},
        raw_lease_token=raw_lease_token,
        session=sess,
    )
    sess.commit()

    # Initial regrade / grading: student selected key_alpha, which is correct -> 10 points
    result1 = regrade_attempt(attempt.id, session=sess)
    sess.commit()
    assert result1["attempt_id"] == str(attempt.public_id)
    assert not result1.get("skipped")
    assert aq.current_grade.awarded_points == Decimal("10.0")

    # 4. Instructor updates question to make UDP (key_beta) the correct answer instead
    # The revisions must preserve the choice_key values
    rev_payload = {
        "change_type": "ANSWER_CHANGE",
        "reason": "Official syllabus changed correct answer to UDP",
        "choices": [
            {"choice_key": str(key_alpha), "content": "TCP", "is_correct": False, "position": 1},
            {"choice_key": str(key_beta), "content": "UDP", "is_correct": True, "position": 2},
        ],
    }
    new_rev, _ = create_question_revision(instructor_user, q.id, rev_payload, session=sess)
    sess.commit()

    # Confirm choice_keys preserved
    alpha_in_rev2 = next(c for c in new_rev.choices if c.content == "TCP")
    beta_in_rev2 = next(c for c in new_rev.choices if c.content == "UDP")
    assert alpha_in_rev2.choice_key == key_alpha
    assert beta_in_rev2.choice_key == key_beta
    assert new_rev.is_current is True

    # 5. Regrade attempt against active revision:
    # Student selected key_alpha, but now key_beta is correct. Regrade worker must award 0 points!
    result2 = regrade_attempt(attempt.id, session=sess)
    sess.commit()
    assert aq.current_grade.awarded_points == Decimal("0.0")

    # 6. Revert correct answer back to TCP (key_alpha)
    rev_payload_revert = {
        "change_type": "ANSWER_CHANGE",
        "reason": "Reverting correct answer to TCP",
        "choices": [
            {"choice_key": str(key_alpha), "content": "TCP", "is_correct": True, "position": 1},
            {"choice_key": str(key_beta), "content": "UDP", "is_correct": False, "position": 2},
        ],
    }
    rev3, _ = create_question_revision(instructor_user, q.id, rev_payload_revert, session=sess)
    sess.commit()
    assert rev3.is_current is True

    # Regrade again: student's key_alpha is correct again -> 10 points restored
    result3 = regrade_attempt(attempt.id, session=sess)
    sess.commit()
    assert aq.current_grade.awarded_points == Decimal("10.0")


def test_defect_3_autosave_lease_epoch_fencing_and_sequence_collision(
    app: Flask, instructor_user: User, student_user: User, published_course: Course, enrolled_student: User
):
    """Defect 3: Reject stale lease_epoch with 409 and stale client sequence with 409."""
    sess: Session = db.session

    payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "UNDERSTAND",
        "content": "Define idempotency in HTTP.",
        "default_points": 5.0,
        "accepted_answers": [{"answer_text": "same result", "match_mode": "NORMALIZED"}],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor_user, published_course.id, payload, session=sess)

    now = datetime.now(UTC)
    assess_payload = {
        "title": "HTTP Protocol Exam",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 30,
        "attempt_limit": 1,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(days=1)).isoformat(),
    }
    assessment = create_assessment(instructor_user, published_course.id, assess_payload, session=sess)
    sec = create_section(instructor_user, assessment.public_id, {"title": "Section 1", "position": 1}, session=sess)
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 5.0, "position": 1},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.public_id, session=sess)
    sess.commit()

    attempt, token1 = start_assessment_attempt(student_user, assessment.public_id, session=sess)
    aq = attempt.attempt_questions[0]

    # Initial lease_epoch must be 1
    assert attempt.lease_epoch == 1

    # 1. Valid autosave: sequence 1, lease_epoch 1
    save_res1 = save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"text_answer": "same result after repeated calls", "client_sequence": 1, "lease_epoch": 1},
        raw_lease_token=token1,
        session=sess,
    )
    sess.commit()
    assert save_res1["last_client_sequence"] == 1
    assert save_res1["lease_epoch"] == 1

    # 2. Duplicate or stale sequence collision: sequence 1 again -> raises StaleAnswerSequenceError (409)
    with pytest.raises(StaleAnswerSequenceError):
        save_attempt_answer(
            actor=student_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={"text_answer": "outdated edit", "client_sequence": 1, "lease_epoch": 1},
            raw_lease_token=token1,
            session=sess,
        )

    # 3. Decreasing sequence collision: sequence 0 -> raises StaleAnswerSequenceError (409)
    with pytest.raises(StaleAnswerSequenceError):
        save_attempt_answer(
            actor=student_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={"text_answer": "outdated edit 0", "client_sequence": 0, "lease_epoch": 1},
            raw_lease_token=token1,
            session=sess,
        )

    # 4. Another device/tab takes over the lease
    attempt, token2 = takeover_attempt_lease(student_user, attempt.id, session=sess)
    sess.commit()
    assert attempt.lease_epoch == 2

    # 5. Old device/tab submits with stale lease_epoch = 1 -> raises StaleLeaseEpochError (409)
    with pytest.raises(StaleLeaseEpochError):
        save_attempt_answer(
            actor=student_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={"text_answer": "late write from tab 1", "client_sequence": 2, "lease_epoch": 1},
            raw_lease_token=token2,
            session=sess,
        )

    # 6. New device/tab submits with current lease_epoch = 2 and sequence 2 -> succeeds!
    save_res2 = save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"text_answer": "clean write from tab 2", "client_sequence": 2, "lease_epoch": 2},
        raw_lease_token=token2,
        session=sess,
    )
    sess.commit()
    assert save_res2["last_client_sequence"] == 2
    assert save_res2["lease_epoch"] == 2


def test_defect_4_skeleton_tombstone_purge_and_regrade_skip(
    app: Flask, instructor_user: User, student_user: User, admin_user: User, published_course: Course, enrolled_student: User
):
    """Defect 4: Skeleton tombstone purge deletes detail rows, retains parent attempt with is_detail_purged=True, regrade skips it."""
    sess: Session = db.session

    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "True or False?",
        "default_points": 10.0,
        "choices": [
            {"content": "True", "is_correct": True, "position": 1},
            {"content": "False", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor_user, published_course.id, payload, session=sess)

    now = datetime.now(UTC)
    assess_payload = {
        "title": "Retention Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 30,
        "attempt_limit": 1,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(days=1)).isoformat(),
    }
    assessment = create_assessment(instructor_user, published_course.id, assess_payload, session=sess)
    sec = create_section(instructor_user, assessment.public_id, {"title": "Section 1", "position": 1}, session=sess)
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0, "position": 1},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.public_id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(student_user, assessment.public_id, session=sess)
    aq = attempt.attempt_questions[0]

    choice_alpha = aq.choice_snapshots[0].choice_key_snapshot
    save_attempt_answer(
        actor=student_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"choice_keys": [str(choice_alpha)], "client_sequence": 1, "lease_epoch": 1},
        raw_lease_token=token,
        session=sess,
    )
    sess.commit()

    # Verify child details exist
    assert sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).count() > 0
    assert sess.query(AttemptChoiceSnapshot).filter(AttemptChoiceSnapshot.attempt_question_id == aq.id).count() > 0
    assert sess.query(AttemptAnswerEvent).filter(AttemptAnswerEvent.attempt_question_id == aq.id).count() > 0

    # Execute Skeleton Tombstone Purge
    purged_attempt = purge_attempt_details_skeleton_tombstone(attempt.id, actor_id=admin_user.id, session=sess)
    sess.commit()

    # Invariants:
    # 1. Parent attempt MUST still exist in database
    retrieved_attempt = sess.get(AssessmentAttempt, attempt.id)
    assert retrieved_attempt is not None
    assert retrieved_attempt.is_detail_purged is True
    assert retrieved_attempt.detail_purged_at is not None

    # 2. Child detail tables MUST be truncated/purged
    assert sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == aq.id).count() == 0
    assert sess.query(AttemptChoiceSnapshot).filter(AttemptChoiceSnapshot.attempt_question_id == aq.id).count() == 0
    assert sess.query(AttemptAnswerEvent).filter(AttemptAnswerEvent.attempt_question_id == aq.id).count() == 0

    # 3. Audit event is recorded
    audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "ATTEMPT_SKELETON_PURGED",
            AuditEvent.target_id == attempt.id,
        )
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == admin_user.id

    # 4. Regrade worker gracefully skips purged attempt without error
    regrade_res = regrade_attempt(attempt.id, session=sess)
    assert regrade_res["skipped"] is True
    assert regrade_res["reason"] == "SKELETON_TOMBSTONE_PURGED"


def test_defect_5_assessment_duration_vs_window_timing_freeze(
    app: Flask, instructor_user: User, published_course: Course
):
    """Defect 5: Assessment open_at/time_limit locked after publish, close_at can only extend forward."""
    sess: Session = db.session

    # Question required to satisfy publish gate
    q_payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "REMEMBER",
        "content": "Sample question for timing test?",
        "default_points": 5.0,
        "accepted_answers": [{"answer_text": "sample", "match_mode": "EXACT"}],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor_user, published_course.id, q_payload, session=sess)

    now = datetime.now(UTC)
    orig_open = now - timedelta(hours=2)
    orig_close = now + timedelta(days=2)

    assess_payload = {
        "title": "Timing Freeze Test",
        "assessment_type": "FINAL",
        "time_limit_minutes": 90,
        "attempt_limit": 1,
        "open_at": orig_open.isoformat(),
        "close_at": orig_close.isoformat(),
    }
    assessment = create_assessment(instructor_user, published_course.id, assess_payload, session=sess)
    sec = create_section(instructor_user, assessment.public_id, {"title": "Section 1", "position": 1}, session=sess)
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 5.0, "position": 1},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.public_id, session=sess)
    sess.commit()

    # 1. Modifying open_at on published assessment is forbidden
    with pytest.raises(AssessmentLockedError, match="open_at"):
        update_assessment(
            instructor_user,
            assessment.id,
            {"open_at": (now - timedelta(hours=3)).isoformat()},
            session=sess,
        )

    # 2. Modifying time_limit_minutes on published assessment is forbidden
    with pytest.raises(AssessmentLockedError, match="time_limit_minutes"):
        update_assessment(
            instructor_user,
            assessment.id,
            {"time_limit_minutes": 120},
            session=sess,
        )

    # 3. Modifying attempt_limit on published assessment is forbidden
    with pytest.raises(AssessmentLockedError, match="attempt_limit"):
        update_assessment(
            instructor_user,
            assessment.id,
            {"attempt_limit": 2},
            session=sess,
        )

    # 4. Shortening close_at is forbidden
    shorter_close = orig_close - timedelta(hours=6)
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended forward"):
        update_assessment(
            instructor_user,
            assessment.id,
            {"close_at": shorter_close.isoformat()},
            session=sess,
        )

    # 5. Extending close_at forward is permitted and creates audit event
    extended_close = orig_close + timedelta(days=3)
    updated = update_assessment(
        instructor_user,
        assessment.id,
        {"close_at": extended_close.isoformat(), "reason": "Severe weather extension"},
        session=sess,
    )
    sess.commit()

    assert updated.close_at.replace(tzinfo=UTC) == extended_close.replace(tzinfo=UTC)

    # Check audit event
    audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "ASSESSMENT_CLOSE_AT_EXTENDED",
            AuditEvent.target_id == assessment.id,
        )
        .first()
    )
    assert audit is not None
    assert audit.reason == "Severe weather extension"


def test_defect_6_relational_staging_lesson_change_request_and_approval(
    app: Flask, instructor_user: User, published_course: Course
):
    """Defect 6: Staged lesson at position 1 does not collide with active lesson at position 1, approval promotes atomically."""
    sess: Session = db.session

    # 1. Create and publish initial lesson at position 1
    lesson1 = create_lesson(
        instructor_user,
        published_course.id,
        {
            "title": "Lesson 1: Introduction",
            "markdown_content": "# Intro to DB",
            "position": 1,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    sess.commit()
    assert lesson1.status == "PUBLISHED"
    assert lesson1.position == 1

    # 2. Create staged lesson change request targeting position 1
    change_payload = {
        "title": "Lesson 1: Advanced Introduction (Staged)",
        "markdown_content": "# Intro to Modern DB Engines",
        "position": 1,
        "reason": "Comprehensive curriculum modernization",
    }
    req, staged_lesson = create_lesson_change_request(
        actor=instructor_user,
        course_id=published_course.id,
        payload=change_payload,
        session=sess,
    )
    sess.commit()

    # Invariants:
    # - Staged lesson created in PENDING_APPROVAL status
    # - Staged lesson shares position 1 with published lesson WITHOUT unique constraint collision
    # - Filtered unique index allows this because staged_lesson.status == 'PENDING_APPROVAL'
    assert staged_lesson.status == "PENDING_APPROVAL"
    assert staged_lesson.position == 1
    assert staged_lesson.change_request_id == req.id
    assert req.status == "PENDING"

    # Both lessons co-exist at position 1 in database
    lessons_at_pos_1 = sess.query(Lesson).filter(Lesson.course_id == published_course.id, Lesson.position == 1).all()
    assert len(lessons_at_pos_1) == 2

    # 3. Approve change request
    approved_req = approve_course_change_request(
        actor=instructor_user,
        change_request_id=req.id,
        review_reason="Approved after syllabus review",
        session=sess,
    )
    sess.commit()

    # Invariants after approval:
    # - Old lesson status becomes 'HISTORICAL'
    # - Staged lesson status becomes 'PUBLISHED'
    # - Change request status becomes 'APPROVED' and applied_at is set
    # - Filtered unique index continues to be satisfied because only ONE lesson is PUBLISHED at position 1
    sess.refresh(lesson1)
    sess.refresh(staged_lesson)

    assert lesson1.status == "HISTORICAL"
    assert staged_lesson.status == "PUBLISHED"
    assert approved_req.status == "APPROVED"
    assert approved_req.applied_at is not None

    # Verifying active uniqueness: exactly 1 active/published lesson at position 1
    active_at_pos_1 = (
        sess.query(Lesson)
        .filter(
            Lesson.course_id == published_course.id,
            Lesson.position == 1,
            Lesson.status.in_(["ACTIVE", "PUBLISHED"]),
        )
        .all()
    )
    assert len(active_at_pos_1) == 1
    assert active_at_pos_1[0].id == staged_lesson.id
