"""Quick Add durability and duplicate suppression on independent SQL sessions."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.question_bank import Question, QuestionProvenance, QuestionRevision
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import create_assessment
from tests.api.test_instructor_backend_remediation import login_session
from tests.api.test_instructor_backend_remediation import remediation_env as remediation_env
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server


@pytest.fixture
def quick_add(app, remediation_env):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    actor = remediation_env["instructor"]
    assessment = create_assessment(
        actor,
        remediation_env["course"].id,
        {"title": "Quick Add SQL gate", "assessment_type": "QUIZ"},
    )
    clients = []
    for _ in range(2):
        client = app.test_client()
        csrf = login_session(client, actor.email)
        cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
        clients.append({"Cookie": f"{cookie.key}={cookie.value}", "X-CSRFToken": csrf})
    result = (assessment.id, str(assessment.public_id), clients)
    db.session.remove()
    return result


def counts(engine, assessment_id):
    with Session(engine) as observer:
        assignments = (
            observer.query(AssessmentQuestionAssignment)
            .filter_by(assessment_id=assessment_id)
            .all()
        )
        return (
            observer.query(Question).count(),
            observer.query(QuestionRevision).count(),
            observer.query(QuestionProvenance).count(),
            len(assignments),
        )


def payload():
    return {
        "client_question_id": str(uuid.uuid4()),
        "question_type": "ESSAY",
        "content": "Explain atomic persistence",
        "points": 5,
    }


def test_sql_quick_add_frozen_new_creation_is_rejected_without_orphans(app, quick_add, http_server):
    engine = db.engine
    assessment_id, public_id, clients = quick_add
    with Session(engine) as freezer:
        freezer.get(Assessment, assessment_id).first_attempt_started_at = utc_now()
        freezer.commit()
    response = http_request(
        clients[0],
        "POST",
        f"{http_server}/instructor/assessments/{public_id}/questions/create",
        payload(),
    )
    assert response.status_code == 409, response.text
    assert counts(engine, assessment_id) == (0, 0, 0, 0)


def test_sql_quick_add_assignment_freeze_failure_rolls_back_created_question(
    app, quick_add, http_server, monkeypatch
):
    from pwd301.blueprints.instructor import routes

    engine = db.engine
    assessment_id, public_id, clients = quick_add
    real_assign = routes.assign_question
    reached_assignment = []

    def freeze_before_assignment(*args, **kwargs):
        session = kwargs["session"]
        assert session.query(Question).count() == 1
        reached_assignment.append(True)
        session.get(Assessment, assessment_id).first_attempt_started_at = utc_now()
        session.flush()
        return real_assign(*args, **kwargs)

    monkeypatch.setattr(routes, "assign_question", freeze_before_assignment)
    response = http_request(
        clients[0],
        "POST",
        f"{http_server}/instructor/assessments/{public_id}/questions/create",
        payload(),
    )
    assert response.status_code == 409, response.text
    assert reached_assignment == [True]
    assert counts(engine, assessment_id) == (0, 0, 0, 0)
    with Session(engine) as observer:
        assert observer.get(Assessment, assessment_id).first_attempt_started_at is None


@pytest.mark.parametrize("points", [1.234567, 1.23445])
def test_sql_quick_add_precision_preserves_retry(app, quick_add, http_server, points):
    engine = db.engine
    assessment_id, public_id, clients = quick_add
    endpoint = f"{http_server}/instructor/assessments/{public_id}/questions/create"
    request_payload = {**payload(), "points": points}
    first = http_request(clients[0], "POST", endpoint, request_payload)
    assert first.status_code == 201, first.text
    repeated = http_request(clients[0], "POST", endpoint, request_payload)
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["question"]["question_id"] == request_payload["client_question_id"]
    assert counts(engine, assessment_id) == (1, 1, 1, 1)


def test_sql_quick_add_concurrent_stable_key_and_frozen_ack_replay(app, quick_add, http_server):
    engine = db.engine
    assessment_id, public_id, clients = quick_add
    endpoint = f"{http_server}/instructor/assessments/{public_id}/questions/create"
    request_payload = payload()
    barrier = threading.Barrier(2)
    seen_threads = set()
    spids = set()
    guard = threading.Lock()

    def gate(connection, cursor, statement, parameters, context, executemany):
        if "FROM assessments WITH (UPDLOCK, HOLDLOCK)" not in statement:
            return
        thread_id = threading.get_ident()
        with guard:
            if thread_id in seen_threads:
                return
            seen_threads.add(thread_id)
            spids.add(connection.exec_driver_sql("SELECT @@SPID").scalar())
        barrier.wait(timeout=15)

    sa.event.listen(engine, "before_cursor_execute", gate)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(http_request, headers, "POST", endpoint, request_payload)
                for headers in clients
            ]
            responses = [future.result(timeout=35) for future in futures]
    finally:
        sa.event.remove(engine, "before_cursor_execute", gate)
    assert len(spids) == 2
    assert sorted(response.status_code for response in responses) == [200, 201]
    assert {response.json()["question"]["question_id"] for response in responses} == {
        request_payload["client_question_id"]
    }
    assert counts(engine, assessment_id) == (1, 1, 1, 1)
    with Session(engine) as freezer:
        freezer.get(Assessment, assessment_id).first_attempt_started_at = utc_now()
        freezer.commit()
    repeated = http_request(clients[0], "POST", endpoint, request_payload)
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["question"]["question_id"] == request_payload["client_question_id"]
    different = http_request(
        clients[0], "POST", endpoint, {**request_payload, "content": "Changed intent"}
    )
    assert different.status_code == 409
    assert counts(engine, assessment_id) == (1, 1, 1, 1)
