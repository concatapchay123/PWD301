"""Assessment synchronization with real independent SQL Server transactions."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptQuestionGrade,
)
from pwd301.models.identity import User
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.exceptions import AttemptAlreadySubmittedError, AttemptLeaseConflictError
from tests.api.test_instructor_backend_remediation import login_session
from tests.unit.test_attempt_autosave_service import _make_assessment_with_questions
from tests.unit.test_attempt_autosave_service import admin_user as admin_user
from tests.unit.test_attempt_autosave_service import enrolled_student as enrolled_student
from tests.unit.test_attempt_autosave_service import instructor_user as instructor_user
from tests.unit.test_attempt_autosave_service import published_course as published_course
from tests.unit.test_attempt_autosave_service import setup_roles as setup_roles
from tests.unit.test_attempt_autosave_service import student_user as student_user


@pytest.fixture(autouse=True)
def sqlserver_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")


@pytest.fixture
def prepared_attempt(app, instructor_user, enrolled_student, published_course):
    assessment = _make_assessment_with_questions(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id)
    question = next(
        question
        for question in attempt.attempt_questions
        if question.question_type_snapshot == "SINGLE_CHOICE"
    )
    correct = min(question.choice_snapshots, key=lambda choice: choice.position)
    return (
        enrolled_student.id,
        attempt.id,
        question.id,
        question.public_id,
        str(correct.choice_key_snapshot),
        token,
    )


def answer_payload(sequence, keys):
    return {
        "client_sequence": sequence,
        "client_change_id": str(uuid.uuid4()),
        "selected_choice_keys": keys,
        "lease_epoch": 1,
    }


def test_empty_selection_commits_clear_across_connections(prepared_attempt):
    student_id, attempt_id, question_id, question_public_id, choice_key, token = prepared_attempt
    with Session(db.engine) as first:
        save_attempt_answer(
            first.get(User, student_id),
            attempt_id,
            question_public_id,
            answer_payload(1, [choice_key]),
            raw_lease_token=token,
            session=first,
        )
    with Session(db.engine) as second:
        answer = second.query(AttemptAnswer).filter_by(attempt_question_id=question_id).one()
        assert second.query(AttemptAnswerChoice).filter_by(attempt_answer_id=answer.id).count() == 1
        save_attempt_answer(
            second.get(User, student_id),
            attempt_id,
            question_public_id,
            answer_payload(2, []),
            raw_lease_token=token,
            session=second,
        )
    with Session(db.engine) as observer:
        answer = observer.query(AttemptAnswer).filter_by(attempt_question_id=question_id).one()
        assert answer.last_client_sequence == 2
        assert (
            observer.query(AttemptAnswerChoice).filter_by(attempt_answer_id=answer.id).count() == 0
        )
        submit_assessment_attempt(
            observer.get(User, student_id), attempt_id, raw_lease_token=token, session=observer
        )
        grade = (
            observer.query(AttemptQuestionGrade).filter_by(attempt_question_id=question_id).one()
        )
        assert grade.awarded_points == 0


def test_cached_in_progress_session_cannot_save_after_submit(prepared_attempt):
    student_id, attempt_id, question_id, question_public_id, choice_key, token = prepared_attempt
    with Session(db.engine) as stale, Session(db.engine) as submitter:
        cached = stale.get(AssessmentAttempt, attempt_id)
        actor = stale.get(User, student_id)
        assert cached.status == "IN_PROGRESS"
        submit_assessment_attempt(
            submitter.get(User, student_id), attempt_id, raw_lease_token=token, session=submitter
        )
        assert cached.status == "IN_PROGRESS"
        with pytest.raises((AttemptAlreadySubmittedError, AttemptLeaseConflictError)):
            save_attempt_answer(
                actor,
                attempt_id,
                question_public_id,
                answer_payload(1, [choice_key]),
                raw_lease_token=token,
                session=stale,
            )
        stale.rollback()
    with Session(db.engine) as observer:
        assert observer.get(AssessmentAttempt, attempt_id).status == "PENDING_GRADING"
        assert (
            observer.query(AttemptAnswerEvent)
            .filter_by(attempt_question_id=question_id, accepted=True)
            .count()
            == 0
        )
        grade = (
            observer.query(AttemptQuestionGrade).filter_by(attempt_question_id=question_id).one()
        )
        assert grade.awarded_points == 0


@pytest.mark.parametrize("iteration", range(3))
def test_simultaneous_save_and_submit_preserves_grade_answer_consistency(
    prepared_attempt, iteration
):
    student_id, attempt_id, question_id, question_public_id, choice_key, token = prepared_attempt
    engine = db.engine
    barrier = threading.Barrier(2)

    def save():
        with Session(engine) as session:
            actor = session.get(User, student_id)
            session.get(AssessmentAttempt, attempt_id)
            barrier.wait(timeout=15)
            try:
                save_attempt_answer(
                    actor,
                    attempt_id,
                    question_public_id,
                    answer_payload(1, [choice_key]),
                    raw_lease_token=token,
                    session=session,
                )
                return "saved"
            except (AttemptAlreadySubmittedError, AttemptLeaseConflictError):
                session.rollback()
                return "rejected"

    def submit():
        with Session(engine) as session:
            actor = session.get(User, student_id)
            session.get(AssessmentAttempt, attempt_id)
            barrier.wait(timeout=15)
            result = submit_assessment_attempt(
                actor, attempt_id, raw_lease_token=token, session=session
            )
            return result["status"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        save_future = pool.submit(save)
        submit_future = pool.submit(submit)
        outcome = save_future.result(timeout=30)
        assert submit_future.result(timeout=30) == "PENDING_GRADING"
    with Session(engine) as observer:
        attempt = observer.get(AssessmentAttempt, attempt_id)
        grade = (
            observer.query(AttemptQuestionGrade).filter_by(attempt_question_id=question_id).one()
        )
        accepted = (
            observer.query(AttemptAnswerEvent)
            .filter_by(attempt_question_id=question_id, accepted=True)
            .count()
        )
        assert attempt.lease_token_hash is None
        assert accepted == (1 if outcome == "saved" else 0)
        assert grade.awarded_points == (5 if outcome == "saved" else 0)


def test_authoring_loaded_before_first_attempt_rechecks_freeze_after_lock(
    app, instructor_user, enrolled_student, published_course
):
    assessment = _make_assessment_with_questions(instructor_user, published_course)
    assessment_id = assessment.id
    student_id = enrolled_student.id
    original_title = assessment.title
    endpoint = f"/instructor/assessments/{assessment.public_id}/authoring"
    client = app.test_client()
    csrf = login_session(client, instructor_user.email)
    engine = db.engine
    authoring_loaded = threading.Event()
    student_committed = threading.Event()

    def gate_authoring_lock(connection, cursor, statement, parameters, context, executemany):
        if (
            threading.current_thread().name.startswith("authoring-freeze")
            and "UPDATE assessments SET updated_at=assessments.updated_at" in statement
        ):
            authoring_loaded.set()
            assert student_committed.wait(timeout=20), "Student did not finish the first attempt"

    def author():
        return client.post(
            endpoint,
            json={"assessment": {"title": "Concurrent title"}, "questions": []},
            headers={"X-CSRFToken": csrf},
        )

    sa.event.listen(engine, "before_cursor_execute", gate_authoring_lock)
    try:
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="authoring-freeze") as pool:
            future = pool.submit(author)
            assert authoring_loaded.wait(timeout=20), "Authoring did not reach the lock gate"
            try:
                with Session(engine) as student_session:
                    attempt, _ = start_assessment_attempt(
                        student_session.get(User, student_id),
                        assessment_id,
                        session=student_session,
                    )
                    assert len(attempt.attempt_questions) == 2
            finally:
                student_committed.set()
            response = future.result(timeout=30)
            assert response.status_code == 409, response.get_data(as_text=True)
    finally:
        student_committed.set()
        sa.event.remove(engine, "before_cursor_execute", gate_authoring_lock)
    with Session(engine) as observer:
        current = observer.get(Assessment, assessment_id)
        assert current.first_attempt_started_at is not None
        assert current.title == original_title
        assert (
            observer.query(AssessmentQuestionAssignment)
            .filter_by(assessment_id=assessment_id)
            .count()
            == 2
        )
