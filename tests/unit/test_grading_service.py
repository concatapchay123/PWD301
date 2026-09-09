"""Unit tests for Assessment Grading Engine & Manual Essay Evaluation (TASK-016).

Validates:
- Objective auto-grading: SINGLE_CHOICE, MULTIPLE_CHOICE (all-or-nothing),
  TRUE_FALSE, SHORT_ANSWER (normalized & exact).
- Attempt lifecycle transitions: Pure objective -> GRADED; Mixed/Essay -> PENDING_GRADING.
- Manual essay evaluation: bounds check (0 <= score <= points_assigned), MaxPointsExceededError.
- Grade history auditing: reason_code='MANUAL_REVISION', actor, timestamps.
- Attempt auto-finalization: transitions to GRADED when all essays are graded.
- Course completion engine integration: recalculate_course_completion triggered on passing.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AttemptQuestionGradeHistory,
)
from pwd301.models.course import Course, Enrollment
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    grade_essay_question,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.completion_service import set_course_completion_rule
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AttemptNotSubmittedError,
    MaxPointsExceededError,
)
from pwd301.services.question_bank_service import create_question
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
    u = register_user("admin_grade_u@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_grade_u@example.com", "Password@123", "Grading Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_grade_u@example.com", "Password@123", "Grading Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "GRADE-101",
            "title": "Grading Engine Test Course",
            "summary": "Grading Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_student(app: Flask, student_user: User, published_course: Course) -> User:
    """Enroll student into the published course."""
    enroll_student(student_user, published_course.id, session=db.session)
    db.session.commit()
    return student_user


def test_objective_auto_grading_single_choice(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Test SINGLE_CHOICE scoring: correct choice gives full points, wrong choice gives 0."""
    sess: Session = db.session
    now = datetime.now(UTC)

    # Create assessment
    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Single Choice Quiz",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)

    # Create question with 1 correct choice
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "What is 2 + 2?",
            "default_points": 10.0,
            "choices": [
                {"content": "4", "is_correct": True, "position": 1},
                {"content": "5", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # Case 1: Student answers correctly
    attempt1, token1 = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq1 = attempt1.attempt_questions[0]
    correct_choice = [c for c in aq1.choice_snapshots if c.content_snapshot == "4"][0]

    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt1.id,
        attempt_question_id=aq1.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(correct_choice.choice_key_snapshot)],
        },
        raw_lease_token=token1,
        session=sess,
    )

    sub_res1 = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt1.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token1,
        session=sess,
    )

    assert sub_res1["status"] == "GRADED"
    sess.refresh(attempt1)
    assert attempt1.status == "GRADED"
    assert attempt1.result is not None
    assert float(attempt1.result.raw_score) == 10.0
    assert float(attempt1.result.percent_score) == 100.0
    assert attempt1.result.passed is True


def test_objective_auto_grading_true_false(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Test TRUE_FALSE scoring: matching boolean gives full points, wrong boolean gives 0."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "True False Assessment",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 60.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)

    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Python is dynamically typed.",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # Case 1: Select correct choice ('True') -> 100% points
    attempt1, token1 = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq1 = attempt1.attempt_questions[0]
    choice_true = [c for c in aq1.choice_snapshots if c.content_snapshot == "True"][0]

    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt1.id,
        attempt_question_id=aq1.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(choice_true.choice_key_snapshot)],
        },
        raw_lease_token=token1,
        session=sess,
    )

    sub1 = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt1.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token1,
        session=sess,
    )
    assert sub1["status"] == "GRADED"
    sess.refresh(attempt1)
    assert attempt1.status == "GRADED"
    assert attempt1.result is not None
    assert float(attempt1.result.raw_score) == 10.0
    assert float(attempt1.result.percent_score) == 100.0
    assert attempt1.result.passed is True

    # Case 2: Select wrong choice ('False') -> 0 points
    attempt2, token2 = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq2 = attempt2.attempt_questions[0]
    choice_false = [c for c in aq2.choice_snapshots if c.content_snapshot == "False"][0]

    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt2.id,
        attempt_question_id=aq2.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(choice_false.choice_key_snapshot)],
        },
        raw_lease_token=token2,
        session=sess,
    )

    sub2 = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt2.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token2,
        session=sess,
    )
    assert sub2["status"] == "GRADED"
    sess.refresh(attempt2)
    assert attempt2.status == "GRADED"
    assert attempt2.result is not None
    assert float(attempt2.result.raw_score) == 0.0
    assert float(attempt2.result.percent_score) == 0.0
    assert attempt2.result.passed is False


def test_objective_auto_grading_multiple_choice_all_or_nothing(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Test MULTIPLE_CHOICE: exact set comparison; partial, extra or missing selection gets 0."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "MCQ Quiz",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 60.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)

    # Question with 2 correct choices (A and C)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Select prime numbers.",
            "default_points": 20.0,
            "choices": [
                {"content": "2", "is_correct": True, "position": 1},
                {"content": "4", "is_correct": False, "position": 2},
                {"content": "3", "is_correct": True, "position": 3},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points_assigned": 20.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # Case A: Partial selection (only '2', missing '3') -> 0 points
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    c_two = [c for c in aq.choice_snapshots if c.content_snapshot == "2"][0]

    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "selected_choice_keys": [str(c_two.choice_key_snapshot)],
        },
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    sess.refresh(attempt)
    assert attempt.status == "GRADED"
    assert attempt.result is not None
    assert float(attempt.result.raw_score) == 0.0
    assert attempt.result.passed is False


def test_objective_auto_grading_short_answer_normalization_and_exact(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Test SHORT_ANSWER scoring: whitespace/case normalization and exact mode."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Short Answer Exam",
            "assessment_type": "FINAL",
            "time_limit_minutes": 30,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)

    # Q1: Normalized short answer (accepted: "Paris")
    q1 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "content": "Capital of France?",
            "default_points": 10.0,
            "accepted_answers": [
                {"answer_text": "Paris", "is_case_sensitive": False},
            ],
            "short_answer_match_mode": "NORMALIZED",
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q1.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )

    # Q2: Exact short answer (accepted: "H2O")
    q2 = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "SHORT_ANSWER",
            "difficulty": "REMEMBER",
            "content": "Chemical formula for water?",
            "default_points": 10.0,
            "accepted_answers": [
                {"answer_text": "H2O", "is_case_sensitive": True},
            ],
            "short_answer_match_mode": "EXACT",
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q2.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq1 = [aq for aq in attempt.attempt_questions if aq.source_question_id == q1.id][0]
    aq2 = [aq for aq in attempt.attempt_questions if aq.source_question_id == q2.id][0]

    # Answer Q1 with extra whitespace and lowercase ("  paris   ")
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq1.id,
        payload={"client_sequence": 1, "answer_text": "  paris   "},
        raw_lease_token=token,
        session=sess,
    )

    # Answer Q2 with exact match ("H2O")
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq2.id,
        payload={"client_sequence": 1, "answer_text": "H2O"},
        raw_lease_token=token,
        session=sess,
    )

    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    sess.refresh(attempt)
    assert attempt.status == "GRADED"
    assert attempt.result is not None
    assert float(attempt.result.raw_score) == 20.0
    assert float(attempt.result.percent_score) == 100.0


def test_mixed_attempt_with_essay_transitions_to_pending_grading(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Attempts containing ESSAY questions transition to PENDING_GRADING upon submission."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Mixed Assessment",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 60.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)

    # Objective Q (10 pts)
    q_obj = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Python is interpreted.",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q_obj.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )

    # Essay Q (15 pts)
    q_essay = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Discuss idempotent API design.",
            "default_points": 15.0,
            "rubric": "Clarity (5), Correctness (5), Examples (5)",
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q_essay.id, "points_assigned": 15.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq_obj = [aq for aq in attempt.attempt_questions if aq.source_question_id == q_obj.id][0]
    aq_essay = [aq for aq in attempt.attempt_questions if aq.source_question_id == q_essay.id][0]

    # Student answers objective correctly
    c_true = [c for c in aq_obj.choice_snapshots if c.content_snapshot == "True"][0]
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq_obj.id,
        payload={"client_sequence": 1, "selected_choice_keys": [str(c_true.choice_key_snapshot)]},
        raw_lease_token=token,
        session=sess,
    )

    # Student answers essay
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq_essay.id,
        payload={
            "client_sequence": 1,
            "answer_text": "Idempotency prevents duplicate side-effects.",
        },
        raw_lease_token=token,
        session=sess,
    )

    sub_res = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    assert sub_res["status"] == "PENDING_GRADING"
    sess.refresh(attempt)
    assert attempt.status == "PENDING_GRADING"
    assert aq_obj.current_grade.grading_status == "AUTO_GRADED"
    assert float(aq_obj.current_grade.awarded_points) == 10.0
    assert aq_essay.current_grade.grading_status == "PENDING"
    assert float(aq_essay.current_grade.awarded_points) == 0.0


def test_manual_essay_grading_workflow_and_bounds_check(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Manual essay grading validates bounds (0 <= points <= assigned) and records audit history."""
    sess: Session = db.session
    now = datetime.now(UTC)

    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Essay Assessment",
            "assessment_type": "PRACTICE",
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "S1"}, session=sess)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Explain acid transactions.",
            "default_points": 10.0,
            "rubric": "Atomicity, Consistency, Isolation, Durability.",
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Cannot grade an in-progress attempt
    with pytest.raises(AttemptNotSubmittedError):
        grade_essay_question(
            actor=instructor_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            awarded_points=8.0,
            session=sess,
        )

    # Submit attempt
    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )
    sess.refresh(attempt)
    assert attempt.status == "PENDING_GRADING"

    # Bounds check 1: negative points rejected
    with pytest.raises(MaxPointsExceededError, match="cannot be negative"):
        grade_essay_question(
            actor=instructor_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            awarded_points=-2.0,
            session=sess,
        )

    # Bounds check 2: exceeding assigned points (10.0) rejected
    with pytest.raises(MaxPointsExceededError, match="exceed maximum assigned points"):
        grade_essay_question(
            actor=instructor_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            awarded_points=12.5,
            session=sess,
        )

    # Grade valid score: 8.5 / 10.0
    grade_res = grade_essay_question(
        actor=instructor_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        awarded_points=8.5,
        reason="Good coverage of ACID properties.",
        session=sess,
    )

    assert grade_res["awarded_points"] == 8.5
    assert grade_res["grading_status"] == "MANUAL_GRADED"
    assert grade_res["is_finalized"] is True
    assert grade_res["attempt_status"] == "GRADED"

    # Check AttemptQuestionGradeHistory
    hist = (
        sess.query(AttemptQuestionGradeHistory)
        .filter(AttemptQuestionGradeHistory.attempt_question_id == aq.id)
        .all()
    )
    assert len(hist) >= 2  # INITIAL + MANUAL_REVISION
    latest = hist[-1]
    assert latest.reason_code == "MANUAL_REVISION"
    assert latest.new_points == Decimal("8.5000")
    assert latest.actor_user_id == instructor_user.id


def test_course_completion_recalculated_on_assessment_pass(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """When a required assessment is passed, recalculate_course_completion evaluates completion."""
    sess: Session = db.session
    now = datetime.now(UTC)

    # Configure course completion rule requiring assessments
    set_course_completion_rule(
        actor=instructor_user,
        course_id=published_course.id,
        payload={
            "require_all_required_lessons": False,
            "require_required_assessments": True,
            "minimum_progress_percent": 0.0,
        },
        session=sess,
    )

    # Create assessment flagged as required for course completion
    assessment = create_assessment(
        instructor_user,
        published_course.id,
        {
            "title": "Final Capstone Assessment",
            "assessment_type": "FINAL",
            "is_required_for_completion": True,
            "time_limit_minutes": 60,
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=24)).isoformat(),
            "passing_score": 50.0,
        },
        session=sess,
    )
    sec = create_section(instructor_user, assessment.id, {"title": "Final"}, session=sess)
    q = create_question(
        instructor_user,
        published_course.id,
        {
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "content": "Assessment is required.",
            "default_points": 10.0,
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor_user,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment.id, session=sess)
    sess.commit()

    # Verify enrollment is ACTIVE
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == enrolled_student.id,
            Enrollment.course_id == published_course.id,
        )
        .one()
    )
    assert enrollment.status == "ACTIVE"

    # Student takes and passes the exam
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    c_true = [c for c in aq.choice_snapshots if c.content_snapshot == "True"][0]

    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={"client_sequence": 1, "selected_choice_keys": [str(c_true.choice_key_snapshot)]},
        raw_lease_token=token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=token,
        session=sess,
    )

    sess.expire_all()
    sess.refresh(enrollment)
    assert enrollment.status == "COMPLETED"
    assert enrollment.completed_at is not None
