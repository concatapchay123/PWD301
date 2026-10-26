"""Real SQL Server transaction races for acknowledged authoring publication."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
)
from backend.models.identity import User
from backend.models.notification_audit import AuditEvent
from backend.services.assessment_service import (
    assessment_authoring_token,
    configure_blueprint,
    create_assessment,
    materialize_blueprint_pool,
    publish_assessment,
    update_assessment,
)
from backend.services.attempt_service import start_assessment_attempt
from backend.services.enrollment_service import enroll_student
from backend.services.exceptions import AssessmentLockedError, ConflictError
from backend.services.question_bank_service import create_question, update_question
from tests.api.test_instructor_backend_remediation import login_session
from tests.api.test_instructor_backend_remediation import remediation_env as remediation_env


@pytest.fixture(autouse=True)
def sqlserver_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires an isolated migrated SQL Server database")


@pytest.fixture
def authored(client, remediation_env):
    actor = remediation_env["instructor"]
    assessment = create_assessment(
        actor, remediation_env["course"].id, {"title": "CAS submitted", "assessment_type": "QUIZ"}
    )
    csrf = login_session(client, actor.email)
    response = client.post(
        f"/instructor/assessments/{assessment.public_id}/authoring",
        json={
            "assessment": {},
            "questions": [
                {
                    "client_question_id": str(uuid.uuid4()),
                    "question_type": "ESSAY",
                    "content": "CAS initial content",
                    "difficulty": "REMEMBER",
                    "points": 5,
                }
            ],
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200
    question_id = (
        db.session.query(AssessmentQuestionAssignment.question_id)
        .filter_by(assessment_id=assessment.id)
        .scalar()
    )
    identifiers = (
        actor.id,
        assessment.id,
        question_id,
        response.get_json()["data"]["authoring_token"],
    )
    db.session.remove()
    return identifiers


@pytest.mark.parametrize("change", ["assessment", "question"])
def test_stale_publish_waits_for_concurrent_edit_then_rejects(app, authored, change):
    actor_id, assessment_id, question_id, token = authored
    engine = db.engine
    cached = threading.Event()
    edited = threading.Event()
    publish_sql = threading.Event()

    def before_sql(connection, cursor, statement, parameters, context, executemany):
        if not threading.current_thread().name.startswith("cas-publish"):
            return
        if (
            change == "assessment"
            and (
                statement.startswith("UPDATE assessments")
                or "FROM assessments" in statement
                and "UPDLOCK" in statement
            )
            or change == "question"
            and "FROM questions" in statement
            and "UPDLOCK" in statement
        ):
            publish_sql.set()

    def publish():
        with app.app_context(), Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 10000"))
            assessment = session.get(Assessment, assessment_id)
            actor = session.get(User, actor_id)
            assert assessment.status == "DRAFT"
            cached.set()
            assert edited.wait(10)
            try:
                publish_assessment(
                    actor, assessment, session=session, expected_authoring_token=token
                )
            except ConflictError:
                session.rollback()
                return "conflict"
            return "published"

    def edit():
        assert cached.wait(10)
        with app.app_context(), Session(engine) as session:
            actor = session.get(User, actor_id)
            if change == "assessment":
                update_assessment(
                    actor,
                    assessment_id,
                    {"title": "Concurrent editor"},
                    session=session,
                    commit=False,
                )
            else:
                update_question(
                    actor,
                    question_id,
                    {"content": "Concurrent question edit", "change_reason": "CAS race"},
                    session=session,
                    commit=False,
                )
            session.flush()
            edited.set()
            assert publish_sql.wait(10)
            session.commit()

    sa.event.listen(engine, "before_cursor_execute", before_sql)
    try:
        with (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="cas-publish") as publisher,
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="cas-edit") as editor,
        ):
            publishing = publisher.submit(publish)
            editing = editor.submit(edit)
            editing.result(timeout=30)
            assert publishing.result(timeout=30) == "conflict"
    finally:
        sa.event.remove(engine, "before_cursor_execute", before_sql)
    with Session(engine) as observer:
        assert observer.get(Assessment, assessment_id).status == "DRAFT"
        assert (
            observer.query(AuditEvent)
            .filter_by(action="ASSESSMENT_PUBLISHED", target_id=assessment_id)
            .count()
            == 0
        )


def test_concurrent_matching_publish_records_one_transition(app, authored):
    actor_id, assessment_id, _, token = authored
    engine = db.engine
    barrier = threading.Barrier(2)

    def publish():
        with app.app_context(), Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 10000"))
            actor = session.get(User, actor_id)
            assessment = session.get(Assessment, assessment_id)
            barrier.wait(timeout=10)
            result = publish_assessment(
                actor, assessment, session=session, expected_authoring_token=token
            )
            return result.status

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: publish(), range(2)))
    assert results == ["PUBLISHED", "PUBLISHED"]
    with Session(engine) as observer:
        assert (
            observer.query(AuditEvent)
            .filter_by(action="ASSESSMENT_PUBLISHED", target_id=assessment_id)
            .count()
            == 1
        )


@pytest.fixture
def blueprint_authored(authored):
    actor_id, assessment_id, _, _ = authored
    actor = db.session.get(User, actor_id)
    assessment = db.session.get(Assessment, assessment_id)
    candidate = create_question(
        actor,
        assessment.course_id,
        {
            "question_type": "ESSAY",
            "content": "Dynamic eligible question",
            "difficulty": "REMEMBER",
        },
    )
    candidate.status = "ACTIVE"
    db.session.commit()
    configure_blueprint(
        actor,
        assessment_id,
        {
            "name": "Conditional dynamic blueprint",
            "rules": [
                {
                    "question_type": "ESSAY",
                    "difficulty": "REMEMBER",
                    "question_count": 1,
                    "points_each": 3,
                }
            ],
        },
    )
    token = assessment_authoring_token(assessment)
    db.session.remove()
    return actor_id, assessment_id, token


def test_blueprint_publish_and_lost_ack_replay_keep_authoring_token(blueprint_authored):
    actor_id, assessment_id, token = blueprint_authored
    engine = db.engine
    for _ in range(2):
        with Session(engine) as session:
            result = publish_assessment(
                session.get(User, actor_id),
                assessment_id,
                session=session,
                expected_authoring_token=token,
            )
            assert result.status == "PUBLISHED"
            assert assessment_authoring_token(result, session) == token
    with Session(engine) as observer:
        assert (
            observer.query(AssessmentQuestionPool).filter_by(assessment_id=assessment_id).count()
            == 1
        )
        assert (
            observer.query(AuditEvent)
            .filter_by(action="ASSESSMENT_PUBLISHED", target_id=assessment_id)
            .count()
            == 1
        )


@pytest.mark.parametrize("preexisting_pool", [False, True])
def test_blueprint_pool_and_publish_roll_back_together_on_audit_failure(
    blueprint_authored, monkeypatch, preexisting_pool
):
    import backend.services.assessment_service as service

    actor_id, assessment_id, _ = blueprint_authored
    engine = db.engine
    with Session(engine) as session:
        actor = session.get(User, actor_id)
        if preexisting_pool:
            materialize_blueprint_pool(actor, assessment_id, session=session)
        old_pool = [
            row.id
            for row in session.query(AssessmentQuestionPool)
            .filter_by(assessment_id=assessment_id)
            .all()
        ]
        token = assessment_authoring_token(session.get(Assessment, assessment_id), session)
        session.rollback()
    original = service._record_assessment_audit

    def fail_publish_audit(*args, **kwargs):
        if kwargs.get("action") == "ASSESSMENT_PUBLISHED":
            raise RuntimeError("Injected mandatory audit failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "_record_assessment_audit", fail_publish_audit)
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="audit failure"):
            publish_assessment(
                session.get(User, actor_id),
                assessment_id,
                session=session,
                expected_authoring_token=token,
            )
        session.rollback()
    with Session(engine) as observer:
        assert observer.get(Assessment, assessment_id).status == "DRAFT"
        assert [
            row.id
            for row in observer.query(AssessmentQuestionPool)
            .filter_by(assessment_id=assessment_id)
            .all()
        ] == old_pool


def test_blueprint_rematerialization_preserves_fixed_pool_and_fingerprints_its_revision(
    blueprint_authored,
):
    actor_id, assessment_id, _ = blueprint_authored
    actor = db.session.get(User, actor_id)
    assessment = db.session.get(Assessment, assessment_id)
    fixed_question = create_question(
        actor,
        assessment.course_id,
        {"question_type": "ESSAY", "content": "Fixed pool question", "difficulty": "REMEMBER"},
    )
    fixed_question.status = "ACTIVE"
    fixed = AssessmentQuestionPool(
        assessment_id=assessment_id,
        question_id=fixed_question.id,
        points=2,
        is_fixed=True,
        selection_source="MANUAL_POOL",
        position_hint=99,
    )
    db.session.add(fixed)
    db.session.commit()
    fixed_id = fixed.id
    token = assessment_authoring_token(assessment)
    publish_assessment(actor, assessment, expected_authoring_token=token)
    assert db.session.get(AssessmentQuestionPool, fixed_id) is not None
    assert (
        db.session.query(AssessmentQuestionPool).filter_by(assessment_id=assessment_id).count() == 2
    )
    assert assessment_authoring_token(assessment) == token
    update_question(
        actor,
        fixed_question.id,
        {"content": "Corrected fixed content", "change_reason": "Fixed pool correction"},
    )
    assert assessment_authoring_token(assessment) != token


@pytest.mark.parametrize("commit", [False, True])
def test_cached_materializer_cannot_change_pool_after_first_attempt_commits(
    blueprint_authored, commit
):
    actor_id, assessment_id, token = blueprint_authored
    engine = db.engine
    assessment = db.session.get(Assessment, assessment_id)
    student = db.session.query(User).filter_by(email="student_remed@backend.local").one()
    student_id = student.id
    enroll_student(student, assessment.course_id, session=db.session)
    db.session.commit()
    publish_assessment(db.session.get(User, actor_id), assessment, expected_authoring_token=token)
    db.session.remove()
    with Session(engine) as cached_session:
        cached = cached_session.get(Assessment, assessment_id)
        actor = cached_session.get(User, actor_id)
        assert cached.first_attempt_started_at is None
        old_pool = [
            row.id
            for row in cached_session.query(AssessmentQuestionPool)
            .filter_by(assessment_id=assessment_id)
            .all()
        ]
        with Session(engine) as starter:
            attempt, _ = start_assessment_attempt(
                starter.get(User, student_id), assessment_id, session=starter
            )
            assert attempt.status == "IN_PROGRESS"
            assert starter.get(Assessment, assessment_id).first_attempt_started_at is not None
        assert cached.first_attempt_started_at is None
        with pytest.raises(AssessmentLockedError):
            materialize_blueprint_pool(actor, cached, session=cached_session, commit=commit)
            if not commit:
                cached_session.commit()
        cached_session.rollback()
    with Session(engine) as observer:
        assert [
            row.id
            for row in observer.query(AssessmentQuestionPool)
            .filter_by(assessment_id=assessment_id)
            .all()
        ] == old_pool


@pytest.mark.parametrize(
    "operation",
    [
        "create_section",
        "delete_section",
        "assign_question",
        "remove_question_assignment",
        "update_question_assignment",
        "reorder_assessment_questions",
        "configure_blueprint",
        "update_assessment",
    ],
)
def test_legacy_structure_writer_refreshes_committed_first_attempt(blueprint_authored, operation):
    from backend.services import assessment_service as service

    actor_id, assessment_id, _ = blueprint_authored
    engine = db.engine
    assessment = db.session.get(Assessment, assessment_id)
    actor = db.session.get(User, actor_id)
    section_id = service.create_section(actor, assessment, {"title": "Original section"}).id
    question_id = (
        db.session.query(AssessmentQuestionAssignment.question_id)
        .filter_by(assessment_id=assessment_id)
        .first()[0]
    )
    candidate_id = (
        db.session.query(service.Question.id)
        .filter_by(course_id=assessment.course_id, status="ACTIVE")
        .first()[0]
    )
    student = db.session.query(User).filter_by(email="student_remed@backend.local").one()
    student_id = student.id
    enroll_student(student, assessment.course_id, session=db.session)
    publish_assessment(actor, assessment)
    db.session.remove()
    with Session(engine) as cached_session:
        cached = cached_session.get(Assessment, assessment_id)
        cached_actor = cached_session.get(User, actor_id)
        assert cached.first_attempt_started_at is None
        with Session(engine) as starter:
            start_assessment_attempt(starter.get(User, student_id), assessment_id, session=starter)
        with Session(engine) as observer:
            before = assessment_authoring_token(observer.get(Assessment, assessment_id), observer)
        assert cached.first_attempt_started_at is None
        arguments = {
            "create_section": ({"title": "Late section"},),
            "delete_section": (section_id,),
            "assign_question": ({"question_id": candidate_id, "points": 2},),
            "remove_question_assignment": (question_id,),
            "update_question_assignment": (question_id, {"points": 7}),
            "reorder_assessment_questions": ([question_id],),
            "configure_blueprint": ({"name": "Late blueprint", "rules": []},),
            "update_assessment": ({"random_question_count": 2},),
        }
        with pytest.raises(AssessmentLockedError):
            getattr(service, operation)(
                cached_actor, cached, *arguments[operation], session=cached_session
            )
        cached_session.rollback()
    with Session(engine) as observer:
        assert (
            assessment_authoring_token(observer.get(Assessment, assessment_id), observer) == before
        )


@pytest.mark.parametrize("iteration", range(3))
def test_conditional_publish_replay_and_legacy_grading_repair_do_not_deadlock(
    authored, monkeypatch, iteration
):
    from backend.models.attempt_regrade import AssessmentResult
    from backend.models.types import utc_now
    from backend.services import attempt_service

    actor_id, assessment_id, _, token = authored
    engine = db.engine
    student = db.session.query(User).filter_by(email="student_remed@backend.local").one()
    student_id = student.id
    assessment = db.session.get(Assessment, assessment_id)
    enroll_student(student, assessment.course_id, session=db.session)
    publish_assessment(db.session.get(User, actor_id), assessment, expected_authoring_token=token)
    attempt, _ = start_assessment_attempt(student, assessment, session=db.session)
    attempt_id = attempt.id
    key = uuid.uuid4()
    # Historical committed-SUBMITTED rows require grading repair on replay.
    attempt.status = "SUBMITTED"
    attempt.submission_idempotency_key = key
    attempt.submitted_at = utc_now()
    attempt.finalized_at = attempt.submitted_at
    attempt.lease_token_hash = None
    attempt.lease_expires_at = None
    db.session.commit()
    db.session.remove()
    grading_ready = threading.Event()
    publication_locked = threading.Event()
    original = attempt_service.calculate_attempt_result

    def pause_before_result(*args, **kwargs):
        grading_ready.set()
        assert publication_locked.wait(10)
        return original(*args, **kwargs)

    def parent_locked(connection, cursor, statement, parameters, context, executemany):
        if threading.current_thread().name.startswith("repair-publish") and (
            statement.startswith("UPDATE assessments")
            or "FROM assessments" in statement
            and "UPDLOCK" in statement
        ):
            publication_locked.set()

    monkeypatch.setattr(attempt_service, "calculate_attempt_result", pause_before_result)
    sa.event.listen(engine, "after_cursor_execute", parent_locked)

    def repair():
        with Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 15000"))
            return attempt_service.submit_assessment_attempt(
                session.get(User, student_id), attempt_id, idempotency_key=key, session=session
            )

    def replay():
        assert grading_ready.wait(10)
        with Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 15000"))
            result = publish_assessment(
                session.get(User, actor_id),
                assessment_id,
                session=session,
                expected_authoring_token=token,
            )
            assert result.status == "PUBLISHED"

    try:
        with (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="repair-grade") as graders,
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="repair-publish") as publishers,
        ):
            repair_future = graders.submit(repair)
            replay_future = publishers.submit(replay)
            repaired = repair_future.result(timeout=25)
            replay_future.result(timeout=25)
        assert repaired["is_idempotent_replay"]
        with Session(engine) as observer:
            assert observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).count() == 1
    finally:
        sa.event.remove(engine, "after_cursor_execute", parent_locked)
