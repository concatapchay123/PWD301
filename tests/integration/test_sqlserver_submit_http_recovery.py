"""Session/JWT submit rollback, retry and legacy recovery through real HTTP."""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
)
from backend.models.identity import User
from backend.models.types import utc_now
from backend.services import attempt_service
from backend.services.enrollment_service import enroll_student
from backend.services.exceptions import AssessmentValidationError
from backend.services.jwt_auth_service import create_token_pair
from backend.services.user_service import register_user
from tests.integration.test_sqlserver_assessment_sync_concurrency import admin_user as admin_user
from tests.integration.test_sqlserver_assessment_sync_concurrency import (
    enrolled_student as enrolled_student,
)
from tests.integration.test_sqlserver_assessment_sync_concurrency import (
    instructor_user as instructor_user,
)
from tests.integration.test_sqlserver_assessment_sync_concurrency import (
    prepared_attempt as prepared_attempt,
)
from tests.integration.test_sqlserver_assessment_sync_concurrency import (
    published_course as published_course,
)
from tests.integration.test_sqlserver_assessment_sync_concurrency import setup_roles as setup_roles
from tests.integration.test_sqlserver_assessment_sync_concurrency import (
    student_user as student_user,
)
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server
from tests.integration.test_sqlserver_password_reset_atomic import SecretString


@pytest.fixture(autouse=True)
def sql_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")


def http_identity(app, user, transport):
    if transport == "api":
        pair = create_token_pair(user)
        return {"Authorization": SecretString("Bearer " + pair["access_token"])}
    app.config["WTF_CSRF_ENABLED"] = True
    email = user.email
    client = app.test_client()
    with app.app_context():
        csrf = client.get("/auth/login").json["csrf_token"]
        assert (
            client.post(
                "/auth/login",
                json={"email": email, "password": "Password@123"},
                headers={"X-CSRFToken": csrf},
            ).status_code
            == 200
        )
        csrf = client.get("/auth/login").json["csrf_token"]
    cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
    return {
        "Cookie": SecretString(f"{cookie.key}={cookie.value}"),
        "X-CSRFToken": SecretString(csrf),
    }


@pytest.mark.parametrize("transport", ["student", "api"])
def test_sync028_http_valid_lease_blocks_takeover_and_only_new_expired_owner_can_submit(
    app, prepared_attempt, http_server, transport
):
    student_id, attempt_id, _, question_public_id, choice_key, lease = prepared_attempt
    student = db.session.get(User, student_id)
    public_id = str(db.session.get(AssessmentAttempt, attempt_id).public_id)
    owner = http_identity(app, student, transport)
    challenger = http_identity(app, student, transport)
    prefix = (
        f"{http_server}/{('api/attempts' if transport == 'api' else 'student/attempt')}/{public_id}"
    )
    engine = db.engine
    db.session.remove()
    with Session(engine) as observer:
        original = observer.get(AssessmentAttempt, attempt_id)
        original_hash, original_epoch = original.lease_token_hash, original.lease_epoch
    denied = http_request(challenger, "POST", f"{prefix}/lease/takeover", {"force": True})
    assert denied.status_code == 409
    missing = http_request(
        challenger, "POST", f"{prefix}/submit", {"submission_idempotency_key": str(uuid.uuid4())}
    )
    assert missing.status_code == 409
    with Session(engine) as observer:
        current = observer.get(AssessmentAttempt, attempt_id)
        assert current.status == "IN_PROGRESS"
        assert (current.lease_token_hash, current.lease_epoch) == (original_hash, original_epoch)
        assert observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).count() == 0
    # Controlled server-side expiry fixture; deadline and Attempt identity are unchanged.
    with Session(engine) as expiry:
        expiry.get(AssessmentAttempt, attempt_id).lease_expires_at = utc_now() - timedelta(
            seconds=1
        )
        expiry.commit()
    acquired = http_request(challenger, "POST", f"{prefix}/lease/takeover", {})
    assert acquired.status_code == 200
    assert acquired.json()["attempt_id"] == public_id
    token = SecretString(acquired.json()["lease_token"])
    assert token != lease
    epoch = acquired.json()["lease_epoch"]
    assert epoch == original_epoch + 1
    stale = http_request(
        {**owner, "X-Attempt-Lease-Token": SecretString(lease)},
        "PUT",
        f"{prefix}/answers/{question_public_id}",
        {
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "lease_epoch": original_epoch,
            "selected_choice_keys": [choice_key],
        },
    )
    assert stale.status_code == 409
    active = {**challenger, "X-Attempt-Lease-Token": token}
    saved = http_request(
        active,
        "PUT",
        f"{prefix}/answers/{question_public_id}",
        {
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "lease_epoch": epoch,
            "selected_choice_keys": [choice_key],
        },
    )
    assert saved.status_code == 200
    submitted = http_request(
        active, "POST", f"{prefix}/submit", {"submission_idempotency_key": str(uuid.uuid4())}
    )
    assert submitted.status_code == 200 and submitted.json()["status"] == "PENDING_GRADING"
    with Session(engine) as observer:
        assert observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).count() == 1
        assert observer.get(AssessmentAttempt, attempt_id).lease_token_hash is None


@pytest.mark.parametrize("transport", ["student", "api"])
def test_sync036_http_foreign_user_cannot_read_or_replay_terminal_attempt(
    app, prepared_attempt, http_server, transport
):
    student_id, attempt_id, _, _, _, lease = prepared_attempt
    student = db.session.get(User, student_id)
    public_id = str(db.session.get(AssessmentAttempt, attempt_id).public_id)
    owner = http_identity(app, student, transport)
    foreign = register_user(
        f"terminal-foreign-{uuid.uuid4().hex[:8]}@example.invalid",
        "Password@123",
        "Foreign candidate",
    )
    assert foreign.has_role("STUDENT")
    enroll_student(foreign, db.session.get(AssessmentAttempt, attempt_id).assessment.course_id)
    stranger = http_identity(app, foreign, transport)
    prefix = (
        f"{http_server}/{('api/attempts' if transport == 'api' else 'student/attempt')}/{public_id}"
    )
    key = str(uuid.uuid4())
    engine = db.engine
    db.session.remove()
    submitted = http_request(
        {**owner, "X-Attempt-Lease-Token": SecretString(lease)},
        "POST",
        f"{prefix}/submit",
        {"submission_idempotency_key": key},
    )
    assert submitted.status_code == 200
    with Session(engine) as observer:
        result = observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one()
        result_snapshot = (result.attempt_id, result.status, result.raw_score, result.updated_at)
        count = observer.query(AttemptQuestionGradeHistory).count()
    for method, suffix, payload in (
        ("GET", "", None),
        ("POST", "/submit", {"submission_idempotency_key": key}),
    ):
        denied = http_request(stranger, method, prefix + suffix, payload)
        assert denied.status_code == 403
        assert not denied.json().get("questions")
        assert not denied.json().get("result")
    with Session(engine) as observer:
        result = observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one()
        assert (
            result.attempt_id,
            result.status,
            result.raw_score,
            result.updated_at,
        ) == result_snapshot
        assert observer.query(AttemptQuestionGradeHistory).count() == count


@pytest.mark.parametrize("transport", ["student", "api"])
@pytest.mark.parametrize("mode", ["grading_failure", "legacy_terminal"])
def test_http_submit_fault_or_legacy_repair_then_idempotent_retry(
    app, prepared_attempt, http_server, monkeypatch, transport, mode
):
    student_id, attempt_id, question_id, question_public_id, choice_key, lease = prepared_attempt
    app.config["WTF_CSRF_ENABLED"] = True
    student = db.session.get(User, student_id)
    attempt = db.session.get(AssessmentAttempt, attempt_id)
    public_id = str(attempt.public_id)
    expected_points = next(
        question.points_assigned
        for question in attempt.attempt_questions
        if question.id == question_id
    )
    if transport == "api":
        pair = create_token_pair(student)
        headers = {"Authorization": SecretString("Bearer " + pair["access_token"])}
        prefix = f"{http_server}/api/attempts/{public_id}"
    else:
        client = app.test_client()
        csrf = client.get("/auth/login").get_json()["csrf_token"]
        assert (
            client.post(
                "/auth/login",
                json={"email": student.email, "password": "Password@123"},
                headers={"X-CSRFToken": csrf},
            ).status_code
            == 200
        )
        csrf = client.get("/auth/login").get_json()["csrf_token"]
        cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
        headers = {"Cookie": SecretString(f"{cookie.key}={cookie.value}"), "X-CSRFToken": csrf}
        prefix = f"{http_server}/student/attempt/{public_id}"
    headers["X-Attempt-Lease-Token"] = SecretString(lease)
    engine = db.engine
    db.session.remove()
    saved = http_request(
        headers,
        "PUT",
        f"{prefix}/answers/{question_public_id}",
        {
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "lease_epoch": 1,
            "selected_choice_keys": [choice_key],
        },
    )
    assert saved.status_code == 200
    key = str(uuid.uuid4())
    body = {"submission_idempotency_key": key}
    if mode == "grading_failure":

        def fail(*args, **kwargs):
            raise AssessmentValidationError("Injected grading fault")

        with monkeypatch.context() as fault:
            fault.setattr(attempt_service, "grade_attempt_objective_questions", fail)
            rejected = http_request(headers, "POST", f"{prefix}/submit", body)
            assert rejected.status_code == 400
        with Session(engine) as observer:
            persisted = observer.get(AssessmentAttempt, attempt_id)
            assert persisted.status == "IN_PROGRESS"
            assert persisted.submission_idempotency_key is None
            assert persisted.lease_token_hash is not None
            assert observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).count() == 0
            assert observer.query(AttemptQuestionGrade).count() == 0
    else:
        # Explicit pre-fix crash fixture: terminal Attempt without its durable result.
        with Session(engine) as legacy:
            attempt = legacy.get(AssessmentAttempt, attempt_id)
            attempt.status = "SUBMITTED"
            attempt.submitted_at = utc_now()
            attempt.submission_idempotency_key = uuid.UUID(key)
            attempt.lease_token_hash = None
            attempt.editor_session_id = None
            attempt.lease_expires_at = None
            legacy.commit()
    completed = http_request(headers, "POST", f"{prefix}/submit", body)
    assert completed.status_code == 200
    assert completed.json()["status"] == "PENDING_GRADING"
    assert completed.json()["is_idempotent_replay"] == (mode == "legacy_terminal")
    with Session(engine) as observer:
        # The shared fixture includes an essay, so objective grading stays pending.
        assert observer.get(AssessmentAttempt, attempt_id).status == "PENDING_GRADING"
        result = observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one()
        assert result.raw_score == expected_points
        grade_count = observer.query(AttemptQuestionGrade).count()
        history_count = observer.query(AttemptQuestionGradeHistory).count()
    repeated = http_request(headers, "POST", f"{prefix}/submit", body)
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "PENDING_GRADING"
    assert repeated.json()["is_idempotent_replay"] is True
    assert (
        http_request(
            headers, "POST", f"{prefix}/submit", {"submission_idempotency_key": str(uuid.uuid4())}
        ).status_code
        == 409
    )
    with Session(engine) as observer:
        assert observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).count() == 1
        assert observer.query(AttemptQuestionGrade).count() == grade_count
        assert observer.query(AttemptQuestionGradeHistory).count() == history_count
        assert observer.get(AssessmentAttempt, attempt_id).lease_token_hash is None
