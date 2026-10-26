"""Corrections at concurrent submission use real SQL Server transactions."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy.orm import Query, Session

from backend.extensions import db
from backend.models.attempt_regrade import AssessmentResult, RegradeItem, RegradeJob
from backend.models.identity import User
from backend.services import attempt_service, regrade_worker
from backend.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from backend.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from backend.services.question_bank_service import create_question, create_question_revision
from tests.unit.test_assessment_regrading_traceability import active_course as active_course
from tests.unit.test_assessment_regrading_traceability import admin_user as admin_user
from tests.unit.test_assessment_regrading_traceability import enrolled_students as enrolled_students
from tests.unit.test_assessment_regrading_traceability import instructor_user as instructor_user
from tests.unit.test_assessment_regrading_traceability import setup_roles as setup_roles
from tests.unit.test_assessment_regrading_traceability import student_one as student_one
from tests.unit.test_assessment_regrading_traceability import student_two as student_two


@pytest.mark.parametrize("iteration", range(3))
@pytest.mark.parametrize("corrected,run_worker", [(False, False), (True, False), (True, True)])
def test_concurrent_submissions_preserve_grades_and_correction_job_counters(
    app, instructor_user, active_course, enrolled_students, corrected, run_worker, iteration
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")
    question = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Concurrent correction",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10,
            "choices": [
                {"content": "Old key", "is_correct": True, "position": 1},
                {"content": "Corrected key", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assessment = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Concurrent corrected submissions", "assessment_type": "QUIZ"},
    )
    assign_question(
        instructor_user, assessment.id, {"question_id": str(question.public_id), "points": 10}
    )
    publish_assessment(instructor_user, assessment.id)
    participants = []
    for student in enrolled_students:
        attempt, token = start_assessment_attempt(student, assessment.id)
        snapshot = attempt.attempt_questions[0]
        choice = next(c for c in snapshot.choice_snapshots if c.content_snapshot == "Corrected key")
        save_attempt_answer(
            student,
            attempt.id,
            snapshot.id,
            {
                "selected_choice_keys": [str(choice.choice_key_snapshot)],
                "client_sequence": 1,
                "client_change_id": str(uuid.uuid4()),
                "lease_epoch": attempt.lease_epoch,
            },
            raw_lease_token=token,
        )
        participants.append((student.id, attempt.id, token))
    job_id = None
    if corrected:
        _, correction = create_question_revision(
            instructor_user,
            question.id,
            {
                "content": "Concurrent correction",
                "reason": "Replace incorrect key",
                "correction_type": "ANSWER_ONLY",
                "choices": [
                    {"content": "Old key", "is_correct": False, "position": 1},
                    {"content": "Corrected key", "is_correct": True, "position": 2},
                ],
            },
        )
        job = regrade_worker.create_or_get_regrade_job(correction.id)
        db.session.commit()
        job_id = job.id
    engine = db.engine
    barrier = threading.Barrier(3 if run_worker else 2)

    def submit(participant):
        student_id, attempt_id, token = participant
        with Session(engine) as session:
            actor = session.get(User, student_id)
            barrier.wait(timeout=20)
            return submit_assessment_attempt(
                actor,
                attempt_id,
                idempotency_key=uuid.uuid4(),
                raw_lease_token=token,
                session=session,
            )

    def run_regrade_worker():
        with Session(engine) as session:
            barrier.wait(timeout=20)
            return regrade_worker.process_regrade_job(job_id, session=session)

    db.session.remove()
    with ThreadPoolExecutor(max_workers=3 if run_worker else 2) as executor:
        futures = [executor.submit(submit, participant) for participant in participants]
        if run_worker:
            futures.append(executor.submit(run_regrade_worker))
        outcomes = [future.result(timeout=60) for future in futures]
    assert len(outcomes) == (3 if run_worker else 2)
    with Session(engine) as observer:
        results = observer.query(AssessmentResult).all()
        assert len(results) == 2
        assert all(result.raw_score == Decimal("10" if corrected else "0") for result in results)
        if corrected:
            durable_job = observer.get(RegradeJob, job_id)
            assert durable_job.total_items == 2
            assert durable_job.processed_items == 2
            assert durable_job.changed_results == 2
            assert durable_job.status == "COMPLETED"
            assert (
                observer.query(RegradeItem)
                .filter_by(regrade_job_id=job_id, status="COMPLETED")
                .count()
                == 2
            )


def _completed_attempt_with_two_corrections(instructor_user, active_course, enrolled_students):
    questions = []
    for position in range(2):
        questions.append(
            create_question(
                instructor_user,
                active_course.id,
                {
                    "content": f"Concurrent correction {position}",
                    "question_type": "SINGLE_CHOICE",
                    "difficulty": "REMEMBER",
                    "default_points": 10,
                    "choices": [
                        {"content": "Old key", "is_correct": True, "position": 1},
                        {"content": "Corrected key", "is_correct": False, "position": 2},
                    ],
                    "provenance": {"source_type": "MANUAL"},
                },
            )
        )
    assessment = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Two corrected questions", "assessment_type": "QUIZ"},
    )
    for question in questions:
        assign_question(
            instructor_user,
            assessment.id,
            {"question_id": str(question.public_id), "points": 10},
        )
    publish_assessment(instructor_user, assessment.id)
    student = enrolled_students[0]
    attempt, token = start_assessment_attempt(student, assessment.id)
    for snapshot in attempt.attempt_questions:
        choice = next(c for c in snapshot.choice_snapshots if c.content_snapshot == "Corrected key")
        save_attempt_answer(
            student,
            attempt.id,
            snapshot.id,
            {"selected_choice_keys": [str(choice.choice_key_snapshot)], "client_sequence": 1},
            raw_lease_token=token,
        )
    submit_assessment_attempt(student, attempt.id, raw_lease_token=token)
    attempt_id = attempt.id
    job_ids = []
    for question in questions:
        _, correction = create_question_revision(
            instructor_user,
            question.id,
            {
                "content": question.current_revision.content,
                "reason": "Fix key",
                "correction_type": "ANSWER_ONLY",
                "choices": [
                    {"content": "Old key", "is_correct": False, "position": 1},
                    {"content": "Corrected key", "is_correct": True, "position": 2},
                ],
            },
        )
        job_ids.append(regrade_worker.create_or_get_regrade_job(correction.id).id)
        db.session.commit()
    return attempt_id, job_ids


@pytest.mark.parametrize("iteration", range(3))
def test_different_correction_jobs_on_one_attempt_preserve_combined_result(
    app, instructor_user, active_course, enrolled_students, iteration
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")
    attempt_id, job_ids = _completed_attempt_with_two_corrections(
        instructor_user, active_course, enrolled_students
    )
    engine = db.engine
    barrier = threading.Barrier(2)

    def process(job_id):
        with Session(engine) as session:
            barrier.wait(timeout=20)
            return regrade_worker.process_regrade_job(job_id, session=session)

    db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process, job_id) for job_id in job_ids]
        outcomes = [future.result(timeout=60) for future in futures]
    assert all(outcome["status"] == "COMPLETED" for outcome in outcomes)
    with Session(engine) as observer:
        result = observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one()
        assert result.raw_score == Decimal("20")


@pytest.mark.parametrize("iteration", range(3))
def test_retry_and_worker_use_the_same_correction_before_job_lock_order(
    app, instructor_user, active_course, enrolled_students, monkeypatch, iteration
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")
    _, job_ids = _completed_attempt_with_two_corrections(
        instructor_user, active_course, enrolled_students
    )
    job_id = job_ids[0]
    item = db.session.query(RegradeItem).filter_by(regrade_job_id=job_id).one()
    item.status = "FAILED"
    item.attempt_count = 1
    item.last_error = "Injected retryable fixture failure before any grading"
    db.session.get(RegradeJob, job_id).status = "PARTIAL"
    db.session.commit()
    engine = db.engine
    retry_ready = threading.Event()
    worker_ready = threading.Event()
    worker_has_correction = threading.Event()
    original_process = regrade_worker.process_regrade_job
    original_update = Query.update

    def scheduled_process(*args, **kwargs):
        if kwargs["session"].info.get("race_role") == "retry":
            # Real retry has reached its dispatcher, including its prior flush.
            retry_ready.set()
            # With correct ordering the worker must wait; timeout resumes retry.
            worker_has_correction.wait(timeout=1)
        return original_process(*args, **kwargs)

    def observe_correction_lock(query, *args, **kwargs):
        result = original_update(query, *args, **kwargs)
        if (
            query.session.info.get("race_role") == "worker"
            and query.column_descriptions[0]["entity"].__name__ == "QuestionCorrection"
        ):
            worker_has_correction.set()
        return result

    monkeypatch.setattr(regrade_worker, "process_regrade_job", scheduled_process)
    monkeypatch.setattr(Query, "update", observe_correction_lock)

    def retry():
        assert worker_ready.wait(timeout=20)
        with Session(engine) as session:
            session.info["race_role"] = "retry"
            return regrade_worker.retry_regrade_job(job_id, session=session)

    def process():
        with Session(engine) as session:
            session.info["race_role"] = "worker"
            cached_job = session.get(RegradeJob, job_id)
            worker_ready.set()
            assert retry_ready.wait(timeout=20)
            return original_process(cached_job, session=session)

    db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as executor:
        retry_future = executor.submit(retry)
        worker_future = executor.submit(process)
        outcomes = [future.result(timeout=60) for future in (retry_future, worker_future)]
    assert all(outcome["status"] == "COMPLETED" for outcome in outcomes)
    with Session(engine) as observer:
        job = observer.get(RegradeJob, job_id)
        assert job.processed_items == 1
        assert job.changed_results == 1
        assert (
            observer.query(RegradeItem).filter_by(regrade_job_id=job_id, status="COMPLETED").count()
            == 1
        )


@pytest.mark.parametrize("iteration", range(3))
def test_new_correction_during_old_snapshot_submission_has_no_lock_cycle(
    app, instructor_user, active_course, enrolled_students, monkeypatch, iteration
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")
    payload = {
        "content": "Correction discovery race",
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "default_points": 10,
        "choices": [
            {"content": "Old key", "is_correct": True, "position": 1},
            {"content": "Corrected key", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    question = create_question(instructor_user, active_course.id, payload)
    assessment = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Correction discovery race", "assessment_type": "QUIZ"},
    )
    assign_question(
        instructor_user, assessment.id, {"question_id": str(question.public_id), "points": 10}
    )
    publish_assessment(instructor_user, assessment.id)
    student = enrolled_students[0]
    attempt, token = start_assessment_attempt(student, assessment.id)
    snapshot = attempt.attempt_questions[0]
    choice = next(c for c in snapshot.choice_snapshots if c.content_snapshot == "Corrected key")
    save_attempt_answer(
        student,
        attempt.id,
        snapshot.id,
        {"selected_choice_keys": [str(choice.choice_key_snapshot)], "client_sequence": 1},
        raw_lease_token=token,
    )
    revision_payload = {
        "content": payload["content"],
        "reason": "First key fix",
        "correction_type": "ANSWER_ONLY",
        "choices": [
            {"content": "Old key", "is_correct": False, "position": 1},
            {"content": "Corrected key", "is_correct": True, "position": 2},
        ],
    }
    create_question_revision(instructor_user, question.id, revision_payload)
    db.session.commit()
    student_id, attempt_id, instructor_id, question_id = (
        student.id,
        attempt.id,
        instructor_user.id,
        question.id,
    )
    engine = db.engine
    submitted_grade_ready = threading.Event()
    new_correction_ready = threading.Event()
    original_grade = attempt_service.grade_attempt_objective_questions
    original_job_creation = regrade_worker.create_or_get_regrade_job

    def schedule_after_grade(*args, **kwargs):
        result = original_grade(*args, **kwargs)
        submitted_grade_ready.set()
        # Correct stable-parent locking blocks the creator until submit commits.
        new_correction_ready.wait(timeout=1)
        return result

    def schedule_new_correction(*args, **kwargs):
        if kwargs["session"].info.get("race_role") == "creator":
            new_correction_ready.set()
        return original_job_creation(*args, **kwargs)

    monkeypatch.setattr(attempt_service, "grade_attempt_objective_questions", schedule_after_grade)
    monkeypatch.setattr(regrade_worker, "create_or_get_regrade_job", schedule_new_correction)

    def submit():
        with Session(engine) as session:
            return submit_assessment_attempt(
                session.get(User, student_id), attempt_id, raw_lease_token=token, session=session
            )

    def create_next_correction():
        assert submitted_grade_ready.wait(timeout=20)
        with Session(engine) as session:
            session.info["race_role"] = "creator"
            return create_question_revision(
                session.get(User, instructor_id),
                question_id,
                {**revision_payload, "reason": "Second correction", "choices": payload["choices"]},
                session=session,
            )[1].id

    db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as executor:
        submit_future = executor.submit(submit)
        creator_future = executor.submit(create_next_correction)
        assert submit_future.result(timeout=60)["status"] == "GRADED"
        correction_id = creator_future.result(timeout=60)
    with Session(engine) as observer:
        job = original_job_creation(correction_id, session=observer)
        regrade_worker.process_regrade_job(job, session=observer)
        result = observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one()
        assert result.raw_score == Decimal("0")
