import uuid
from datetime import datetime, timezone, timedelta
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
import pytest

from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptQuestion,
    AttemptChoiceSnapshot,
    AttemptAnswer,
    AttemptAnswerChoice,
)
from pwd301.services.attempt_service import submit_assessment_attempt
from pwd301.services.session_auth_service import create_auth_session


def test_assessment_attempt_has_user_id_property(app: Flask) -> None:
    """Ensure AssessmentAttempt model has user_id property aliasing student_user_id."""
    att = AssessmentAttempt(student_user_id=12345)
    assert hasattr(att, "user_id")
    assert att.user_id == 12345


def test_submit_assessment_attempt_does_not_raise_attribute_error_user_id(
    app: Flask,
) -> None:
    """Ensure submit_assessment_attempt safely handles user_id/student_user_id without AttributeError."""
    sess: Session = db.session

    now_utc = datetime.now(timezone.utc)
    # Create test user
    student = User(
        email=f"sub_student_{uuid.uuid4().hex[:8]}@example.com",
        display_name="Submission Student",
        status="ACTIVE",
        password_hash="fake-hash",
    )
    sess.add(student)
    sess.flush()

    course = Course(
        course_code=f"SUB_{uuid.uuid4().hex[:6].upper()}",
        title="Direct Submission Course",
        status="PUBLISHED",
        owner_instructor_id=student.id,
    )
    sess.add(course)
    sess.flush()

    enrollment = Enrollment(
        student_user_id=student.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.flush()

    period = EnrollmentPeriod(
        enrollment_id=enrollment.id,
        period_no=1,
        status="ACTIVE",
        started_at=now_utc - timedelta(days=1),
    )
    sess.add(period)
    sess.flush()
    enrollment.current_period_id = period.id

    assessment = Assessment(
        course_id=course.id,
        title="Submission Test Assessment",
        assessment_type="QUIZ",
        status="PUBLISHED",
        passing_percent=50.0,
        score_release_policy="IMMEDIATE",
        open_at=now_utc - timedelta(hours=1),
        close_at=now_utc + timedelta(days=1),
    )
    sess.add(assessment)
    sess.flush()

    import hashlib
    raw_lease = "test-lease-token-unit-test-12345"
    att = AssessmentAttempt(
        assessment_id=assessment.id,
        enrollment_period_id=period.id,
        student_user_id=student.id,
        attempt_number=1,
        status="IN_PROGRESS",
        started_at=now_utc - timedelta(minutes=10),
        deadline_at=now_utc + timedelta(hours=1),
        lease_token_hash=hashlib.sha256(raw_lease.encode("utf-8")).digest(),
        lease_expires_at=now_utc + timedelta(minutes=15),
        lease_epoch=1,
    )
    sess.add(att)
    sess.flush()

    # Create Question and Revision
    q = Question(
        course_id=course.id,
        creator_user_id=student.id,
        difficulty="REMEMBER",
        status="ACTIVE",
    )
    sess.add(q)
    sess.flush()

    rev = QuestionRevision(
        question_id=q.id,
        revision_no=1,
        question_type="SINGLE_CHOICE",
        content="Sample Question 1",
        is_current=True,
    )
    sess.add(rev)
    sess.flush()
    q.current_revision_id = rev.id

    rev_choice = QuestionRevisionChoice(
        question_revision_id=rev.id,
        choice_key=uuid.uuid4(),
        content="Option A",
        is_correct=True,
        position=1,
    )
    sess.add(rev_choice)
    sess.flush()

    # Add 1 question and choice snapshot
    aq = AttemptQuestion(
        attempt_id=att.id,
        source_question_id=q.id,
        source_question_revision_id=rev.id,
        position=1,
        points_assigned=10.0,
        question_type_snapshot="SINGLE_CHOICE",
        content_snapshot="Sample Question 1",
    )
    sess.add(aq)
    sess.flush()

    cs1 = AttemptChoiceSnapshot(
        attempt_question_id=aq.id,
        source_choice_id=rev_choice.id,
        choice_key_snapshot=rev_choice.choice_key,
        content_snapshot="Option A",
        position=1,
    )
    sess.add(cs1)
    sess.flush()

    ans = AttemptAnswer(
        attempt_question_id=aq.id,
        saved_at=now_utc,
    )
    sess.add(ans)
    sess.flush()

    ans_choice = AttemptAnswerChoice(
        attempt_answer_id=ans.id,
        attempt_choice_snapshot_id=cs1.id,
    )
    sess.add(ans_choice)
    sess.flush()
    sess.commit()

    try:
        result = submit_assessment_attempt(
            actor=student,
            attempt_id=att.id,
            raw_lease_token=raw_lease,
            session=sess,
        )
        assert result is not None
        assert result["status"] in ("SUBMITTED", "PENDING_GRADING", "GRADED")
        assert "attempt_id" in result
    finally:
        sess.rollback()
