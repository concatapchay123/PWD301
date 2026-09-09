"""Unit tests for Regrading Engine & Score History (TASK-017).

Validates:
- Algorithm 11:
  - ANSWER_ONLY: Single choice, multiple choice, short answer correction against new revision.
  - CONTENT_OR_CHOICES: Full-credit safety policy awarded to all affected students.
- Skip Logic:
  - DETAIL_PURGED -> SKIPPED (DETAIL_PURGED)
  - CANCELLED -> SKIPPED (CANCELLED)
  - Unsubmitted (IN_PROGRESS) -> naturally ineligible for regrade job.
- Score History & Audit Trail:
  - AttemptQuestionGradeHistory with reason_code 'AUTO_REGRADE' or 'FULL_CREDIT'.
  - AssessmentResultHistory with reason_code 'REGRADE' on score change.
  - Course completion recalculation when required assessment outcome changes.
- Concurrency, Resumability & Idempotency:
  - Consecutive runs produce no duplicate history entries.
  - Batching and resumable execution from partial failure.
  - Retry of failed items resets counters and completes successfully.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentResultHistory,
    AttemptChoiceSnapshot,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    RegradeItem,
    RegradeJob,
)
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
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
from pwd301.services.completion_service import set_course_completion_rule
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
)
from pwd301.services.regrade_worker import (
    create_or_get_regrade_job,
    process_regrade_job,
    retry_regrade_job,
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
    u = register_user(f"admin_regrade_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user(
        f"inst_regrade_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Regrade Instructor"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user_1(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student 1 user."""
    u = register_user(
        f"stud1_regrade_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student 1"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_user_2(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student 2 user."""
    u = register_user(
        f"stud2_regrade_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student 2"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"REGRADE-{uuid.uuid4().hex[:4].upper()}",
            "title": "Regrading Test Course",
            "description": "Course for testing Algorithm 11 regrading engine",
            "category": "Testing",
            "difficulty": "INTERMEDIATE",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


def test_regrade_single_choice_answer_only(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    student_user_2: User,
    published_course: Course,
) -> None:
    """Test Algorithm 11 ANSWER_ONLY: Correct answer key is changed from Choice A to Choice B.

    Student 1 selected Choice A (old key).
    Student 2 selected Choice B (new key).
    Initial: Student 1 = 10 pts, Student 2 = 0 pts.
    After regrade: Student 1 = 0 pts, Student 2 = 10 pts.
    """
    sess: Session = db.session

    # 1. Enroll students
    enroll_student(student_user_1, published_course.id)
    enroll_student(student_user_2, published_course.id)

    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is the capital of France?",
            "choices": [
                {"content": "Berlin", "is_correct": True, "position": 1},
                {"content": "Paris", "is_correct": False, "position": 2},
            ],
        },
    )
    c_berlin = [c for c in q.current_revision.choices if c.content == "Berlin"][0]
    c_paris = [c for c in q.current_revision.choices if c.content == "Paris"][0]
    ck_a = c_berlin.choice_key
    ck_b = c_paris.choice_key

    # 3. Create and publish assessment
    asm = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Capital Quiz",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 60,
            "passing_percent": 50.0,
            "score_release_policy": "IMMEDIATE",
        },
    )
    sec = create_section(instructor_user, asm.id, {"title": "Main", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 10.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    # 4. Student 1 starts and answers Choice A (Berlin)
    att1, lease1 = start_assessment_attempt(student_user_1, asm.id)
    aq1 = att1.attempt_questions[0]
    snap1_a = (
        sess.query(AttemptChoiceSnapshot)
        .filter(
            AttemptChoiceSnapshot.attempt_question_id == aq1.id,
            AttemptChoiceSnapshot.choice_key_snapshot == ck_a,
        )
        .first()
    )
    assert snap1_a is not None
    save_attempt_answer(
        student_user_1,
        str(att1.public_id),
        str(aq1.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_a)]},
        raw_lease_token=lease1,
    )
    submit_assessment_attempt(student_user_1, str(att1.public_id), raw_lease_token=lease1)

    # 5. Student 2 starts and answers Choice B (Paris)
    att2, lease2 = start_assessment_attempt(student_user_2, asm.id)
    aq2 = att2.attempt_questions[0]
    save_attempt_answer(
        student_user_2,
        str(att2.public_id),
        str(aq2.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_b)]},
        raw_lease_token=lease2,
    )
    submit_assessment_attempt(student_user_2, str(att2.public_id), raw_lease_token=lease2)

    # Check initial results
    sess.refresh(att1)
    sess.refresh(att2)
    assert att1.result.raw_score == Decimal("10.0000")
    assert att2.result.raw_score == Decimal("0.0000")

    # 6. Instructor fixes the answer key: Paris (ck_b) is correct, Berlin (ck_a) is wrong
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "ANSWER_CHANGE",
            "correction_type": "ANSWER_ONLY",
            "change_reason": "Corrected capital from Berlin to Paris",
            "choices": [
                {"choice_key": str(ck_a), "content": "Berlin", "is_correct": False, "position": 1},
                {"choice_key": str(ck_b), "content": "Paris", "is_correct": True, "position": 2},
            ],
        },
    )
    assert corr is not None
    assert corr.correction_type == "ANSWER_ONLY"

    # 7. Regrade job was automatically created in PENDING status
    job = sess.query(RegradeJob).filter(RegradeJob.question_correction_id == corr.id).first()
    assert job is not None
    assert job.total_items == 2

    # 8. Process regrade job
    res = process_regrade_job(job.id, actor=instructor_user)
    assert res["status"] == "COMPLETED"
    assert res["processed_items"] == 2
    assert res["changed_results"] == 2

    # 9. Verify Student 1 has score 0
    sess.refresh(att1)
    grade1 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq1.id).first()
    assert grade1.awarded_points == Decimal("0.0000")
    assert grade1.grading_status == "AUTO_GRADED"
    assert grade1.grading_rule == "ANSWER_CORRECTION"
    assert grade1.graded_against_revision_id == new_rev.id

    # Check question grade history for Student 1
    hist1 = (
        sess.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=aq1.id)
        .order_by(AttemptQuestionGradeHistory.created_at.desc())
        .first()
    )
    assert hist1.reason_code == "AUTO_REGRADE"
    assert hist1.old_points == Decimal("10.0000")
    assert hist1.new_points == Decimal("0.0000")
    assert hist1.question_correction_id == corr.id

    # Check overall result history for Student 1
    res_hist1 = (
        sess.query(AssessmentResultHistory)
        .filter_by(attempt_id=att1.id)
        .order_by(AssessmentResultHistory.created_at.desc())
        .first()
    )
    assert res_hist1.reason_code == "REGRADE"
    assert res_hist1.old_score == Decimal("10.0000")
    assert res_hist1.new_score == Decimal("0.0000")
    assert res_hist1.regrade_job_id == job.id

    # 10. Verify Student 2 has score 10
    sess.refresh(att2)
    grade2 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq2.id).first()
    assert grade2.awarded_points == Decimal("10.0000")
    assert grade2.grading_status == "AUTO_GRADED"
    assert grade2.grading_rule == "ANSWER_CORRECTION"
    assert grade2.graded_against_revision_id == new_rev.id

    hist2 = (
        sess.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=aq2.id)
        .order_by(AttemptQuestionGradeHistory.created_at.desc())
        .first()
    )
    assert hist2.reason_code == "AUTO_REGRADE"
    assert hist2.old_points == Decimal("0.0000")
    assert hist2.new_points == Decimal("10.0000")

    res_hist2 = (
        sess.query(AssessmentResultHistory)
        .filter_by(attempt_id=att2.id)
        .order_by(AssessmentResultHistory.created_at.desc())
        .first()
    )
    assert res_hist2.reason_code == "REGRADE"
    assert res_hist2.old_score == Decimal("0.0000")
    assert res_hist2.new_score == Decimal("10.0000")


def test_regrade_content_or_choices_full_credit(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    student_user_2: User,
    published_course: Course,
) -> None:
    """Test Algorithm 11 CONTENT_OR_CHOICES: Ambiguous question grants FULL_CREDIT to all."""
    sess: Session = db.session

    enroll_student(student_user_1, published_course.id)
    enroll_student(student_user_2, published_course.id)

    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Defective question content here",
            "choices": [
                {"content": "Option A", "is_correct": True, "position": 1},
                {
                    "content": "Option B",
                    "is_correct": False,
                    "position": 2,
                },
            ],
        },
    )
    c_a = [c for c in q.current_revision.choices if c.content == "Option A"][0]
    c_b = [c for c in q.current_revision.choices if c.content == "Option B"][0]
    ck_a = c_a.choice_key
    ck_b = c_b.choice_key

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {"title": "Exam with Bad Question", "assessment_type": "QUIZ", "passing_percent": 60.0},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 20.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    # Student 1 picks wrong answer (Option B) -> 0 points
    att1, lease1 = start_assessment_attempt(student_user_1, asm.id)
    aq1 = att1.attempt_questions[0]
    save_attempt_answer(
        student_user_1,
        str(att1.public_id),
        str(aq1.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_b)]},
        raw_lease_token=lease1,
    )
    submit_assessment_attempt(student_user_1, str(att1.public_id), raw_lease_token=lease1)

    # Student 2 picks right answer (Option A) -> 20 points
    att2, lease2 = start_assessment_attempt(student_user_2, asm.id)
    aq2 = att2.attempt_questions[0]
    save_attempt_answer(
        student_user_2,
        str(att2.public_id),
        str(aq2.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_a)]},
        raw_lease_token=lease2,
    )
    submit_assessment_attempt(student_user_2, str(att2.public_id), raw_lease_token=lease2)

    # Instructor creates revision marking CONTENT_OR_CHOICES
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Flawed question text confusing students",
            "content": "Fixed clear question text",
        },
    )
    assert corr is not None
    assert corr.correction_type == "CONTENT_OR_CHOICES"

    job = create_or_get_regrade_job(corr.id)
    res = process_regrade_job(job.id, actor=instructor_user)
    assert res["status"] == "COMPLETED"

    # Student 1: was 0 pts, now receives full 20 pts
    sess.refresh(att1)
    grade1 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq1.id).first()
    assert grade1.awarded_points == Decimal("20.0000")
    assert grade1.grading_status == "FULL_CREDIT"
    assert grade1.grading_rule == "CONTENT_FULL_CREDIT"

    hist1 = (
        sess.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=aq1.id)
        .order_by(AttemptQuestionGradeHistory.created_at.desc())
        .first()
    )
    assert hist1.reason_code == "FULL_CREDIT"
    assert hist1.new_points == Decimal("20.0000")

    # Student 2: already had 20 pts, now marked FULL_CREDIT, total score did not change
    sess.refresh(att2)
    grade2 = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq2.id).first()
    assert grade2.awarded_points == Decimal("20.0000")
    assert grade2.grading_status == "FULL_CREDIT"
    assert grade2.grading_rule == "CONTENT_FULL_CREDIT"

    # Only 1 result actually changed score (Student 1)
    assert res["changed_results"] == 1


def test_regrade_short_answer_normalization_and_exact(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    published_course: Course,
) -> None:
    """Test Algorithm 11 on SHORT_ANSWER with normalized NFKC matching."""
    sess: Session = db.session

    enroll_student(student_user_1, published_course.id)

    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "content": "Name the language",
            "accepted_answers": ["Python 3.12"],
            "short_answer_match_mode": "EXACT",
        },
    )

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {"title": "Short Answer Quiz", "assessment_type": "QUIZ"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec 1", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 5.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    # Student submitted with different casing / whitespace
    att, lease = start_assessment_attempt(student_user_1, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_user_1,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "answer_text": "python 3.12"},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_user_1, str(att.public_id), raw_lease_token=lease)

    sess.refresh(att)
    assert att.result.raw_score == Decimal("0.0000")

    # Correction: change mode to NORMALIZED and add accepted answer
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "ANSWER_CHANGE",
            "correction_type": "ANSWER_ONLY",
            "change_reason": "Allow case-insensitive normalized matching",
            "accepted_answers": ["Python 3.12", "python 3"],
            "short_answer_match_mode": "NORMALIZED",
        },
    )

    job = create_or_get_regrade_job(corr.id)
    res = process_regrade_job(job.id, actor=instructor_user)
    assert res["status"] == "COMPLETED"

    sess.refresh(att)
    grade = sess.query(AttemptQuestionGrade).filter_by(attempt_question_id=aq.id).first()
    assert grade.awarded_points == Decimal("5.0000")
    assert grade.grading_status == "AUTO_GRADED"
    assert grade.grading_rule == "ANSWER_CORRECTION"


def test_regrade_skip_logic(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    student_user_2: User,
    published_course: Course,
) -> None:
    """Test skip logic: DETAIL_PURGED and CANCELLED attempts are skipped with proper reasons."""
    sess: Session = db.session

    enroll_student(student_user_1, published_course.id)
    enroll_student(student_user_2, published_course.id)

    ck_a = uuid.uuid4()
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Skip Test Question",
            "choices": [
                {"choice_key": str(ck_a), "content": "A", "is_correct": True, "position": 1},
                {
                    "choice_key": str(uuid.uuid4()),
                    "content": "B",
                    "is_correct": False,
                    "position": 2,
                },
            ],
        },
    )

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {"title": "Skip Test Exam", "assessment_type": "QUIZ"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 10.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    # Attempt 1: submitted then purged
    att1, lease1 = start_assessment_attempt(student_user_1, asm.id)
    submit_assessment_attempt(student_user_1, str(att1.public_id), raw_lease_token=lease1)
    att1.is_detail_purged = True
    sess.flush()

    # Attempt 2: cancelled
    att2, lease2 = start_assessment_attempt(student_user_2, asm.id)
    att2.status = "CANCELLED"
    sess.flush()

    # Revision triggering correction
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Typos in question",
            "content": "Updated content",
        },
    )

    job = create_or_get_regrade_job(corr.id)
    assert job.total_items == 2

    # Check items skip reasons
    items = sess.query(RegradeItem).filter_by(regrade_job_id=job.id).all()
    item_map = {item.attempt_id: item for item in items}

    assert item_map[att1.id].status == "SKIPPED"
    assert item_map[att1.id].skip_reason == "DETAIL_PURGED"

    assert item_map[att2.id].status == "SKIPPED"
    assert item_map[att2.id].skip_reason == "CANCELLED"

    res = process_regrade_job(job.id, actor=instructor_user)
    assert res["status"] == "COMPLETED"
    assert res["processed_items"] == 2
    assert res["changed_results"] == 0


def test_regrade_course_completion_integration(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    published_course: Course,
) -> None:
    """Test Course Completion recalculation when required assessment changes passed status."""
    sess: Session = db.session

    enrollment = enroll_student(student_user_1, published_course.id)
    set_course_completion_rule(
        instructor_user,
        published_course.id,
        {
            "require_all_required_lessons": False,
            "require_required_assessments": True,
            "minimum_progress_percent": 0.0,
        },
    )

    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Completion Gate Question",
            "choices": [
                {"content": "Wrong", "is_correct": False, "position": 1},
                {"content": "Right", "is_correct": True, "position": 2},
            ],
        },
    )
    c_wrong = [c for c in q.current_revision.choices if c.content == "Wrong"][0]
    ck_a = c_wrong.choice_key

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Mandatory Final Exam",
            "assessment_type": "FINAL",
            "is_required_for_completion": True,
            "passing_percent": 100.0,
        },
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 100.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    # Student took exam, picked Wrong -> failed (0%)
    att, lease = start_assessment_attempt(student_user_1, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_user_1,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_a)]},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_user_1, str(att.public_id), raw_lease_token=lease)

    sess.refresh(att)
    sess.refresh(enrollment)
    assert not att.result.passed
    assert enrollment.status != "COMPLETED"

    # Instructor finds question had flawed choices -> gives FULL_CREDIT
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Ambiguous option text",
            "content": "Clarified Question",
        },
    )

    job = create_or_get_regrade_job(corr.id)
    process_regrade_job(job.id, actor=instructor_user)

    sess.refresh(att)
    sess.refresh(enrollment)
    assert att.result.passed
    # Course completion recalculation must have completed the course!
    assert enrollment.status == "COMPLETED"
    assert enrollment.completed_at is not None


def test_regrade_idempotency(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    published_course: Course,
) -> None:
    """Test that running regrade twice with same revision produces no duplicate history."""
    sess: Session = db.session

    enroll_student(student_user_1, published_course.id)

    ck_a = uuid.uuid4()
    ck_b = uuid.uuid4()
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Idempotency Question",
            "choices": [
                {"choice_key": str(ck_a), "content": "A", "is_correct": True, "position": 1},
                {"choice_key": str(ck_b), "content": "B", "is_correct": False, "position": 2},
            ],
        },
    )

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {"title": "Idempotency Exam", "assessment_type": "QUIZ"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 10.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    att, lease = start_assessment_attempt(student_user_1, asm.id)
    aq = att.attempt_questions[0]
    save_attempt_answer(
        student_user_1,
        str(att.public_id),
        str(aq.public_id),
        {"client_sequence": 1, "selected_choice_keys": [str(ck_b)]},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student_user_1, str(att.public_id), raw_lease_token=lease)

    # Correction
    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "ANSWER_CHANGE",
            "correction_type": "ANSWER_ONLY",
            "change_reason": "B is actually correct",
            "choices": [
                {"choice_key": str(ck_a), "content": "A", "is_correct": False, "position": 1},
                {"choice_key": str(ck_b), "content": "B", "is_correct": True, "position": 2},
            ],
        },
    )

    job = create_or_get_regrade_job(corr.id)

    # First run
    process_regrade_job(job.id, actor=instructor_user)

    q_hist_count_1 = (
        sess.query(AttemptQuestionGradeHistory).filter_by(attempt_question_id=aq.id).count()
    )
    res_hist_count_1 = sess.query(AssessmentResultHistory).filter_by(attempt_id=att.id).count()

    # Second run on the same job
    process_regrade_job(job.id, actor=instructor_user)

    q_hist_count_2 = (
        sess.query(AttemptQuestionGradeHistory).filter_by(attempt_question_id=aq.id).count()
    )
    res_hist_count_2 = sess.query(AssessmentResultHistory).filter_by(attempt_id=att.id).count()

    # Counts must NOT have increased!
    assert q_hist_count_1 == q_hist_count_2
    assert res_hist_count_1 == res_hist_count_2


def test_regrade_batching_and_retry(
    app: Flask,
    instructor_user: User,
    student_user_1: User,
    student_user_2: User,
    published_course: Course,
) -> None:
    """Test batch execution, partial failure handling, and retry recovery."""
    sess: Session = db.session

    enroll_student(student_user_1, published_course.id)
    enroll_student(student_user_2, published_course.id)

    ck_a = uuid.uuid4()
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Batch test question",
            "choices": [
                {"choice_key": str(ck_a), "content": "A", "is_correct": True, "position": 1},
                {
                    "choice_key": str(uuid.uuid4()),
                    "content": "B",
                    "is_correct": False,
                    "position": 2,
                },
            ],
        },
    )

    asm = create_assessment(
        instructor_user,
        published_course.id,
        {"title": "Batch Exam", "assessment_type": "QUIZ"},
    )
    sec = create_section(instructor_user, asm.id, {"title": "Sec", "position": 1})
    assign_question(
        instructor_user,
        asm.id,
        {
            "question_id": q.id,
            "section_id": sec.id,
            "position": 1,
            "points_assigned": 10.0,
        },
    )
    publish_assessment(instructor_user, asm.id)

    att1, lease1 = start_assessment_attempt(student_user_1, asm.id)
    submit_assessment_attempt(student_user_1, str(att1.public_id), raw_lease_token=lease1)

    att2, lease2 = start_assessment_attempt(student_user_2, asm.id)
    submit_assessment_attempt(student_user_2, str(att2.public_id), raw_lease_token=lease2)

    new_rev, corr = create_question_revision(
        instructor_user,
        q.id,
        {
            "change_type": "CONTENT_CHANGE",
            "correction_type": "CONTENT_OR_CHOICES",
            "change_reason": "Content flaw",
            "content": "Batch test question fixed",
        },
    )

    job = create_or_get_regrade_job(corr.id)
    assert job.total_items == 2

    # 1. Process batch of 1 item
    batch_res = process_regrade_job(job.id, batch_size=1, actor=instructor_user)
    assert batch_res["processed_items"] == 1
    assert batch_res["status"] == "RUNNING"

    # 2. Simulate transient error on the 2nd item
    from pwd301.services import regrade_worker

    call_count = 0
    original_eval = regrade_worker._evaluate_attempt_item_regrade

    def mock_eval(item, job, correction, session):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated transient database lock error")
        return original_eval(item, job, correction, session)

    with patch.object(regrade_worker, "_evaluate_attempt_item_regrade", side_effect=mock_eval):
        partial_res = process_regrade_job(job.id, actor=instructor_user)
        assert partial_res["status"] == "PARTIAL"

    # Verify 1 item is FAILED
    failed_items = sess.query(RegradeItem).filter_by(regrade_job_id=job.id, status="FAILED").all()
    assert len(failed_items) == 1
    assert failed_items[0].attempt_count == 1
    assert "Simulated transient database lock error" in failed_items[0].last_error

    # 3. Call retry_regrade_job
    retry_res = retry_regrade_job(job.id, actor=instructor_user)
    assert retry_res["status"] == "COMPLETED"
    assert retry_res["processed_items"] == 2
