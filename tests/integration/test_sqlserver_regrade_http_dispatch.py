"""Object-authorized regrade HTTP and durable dispatcher execution on real SQL."""

import uuid

import pytest
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.attempt_regrade import (
    AssessmentResult,
    AttemptQuestionGradeHistory,
    RegradeItem,
    RegradeJob,
)
from backend.models.operations import BackgroundJob
from backend.services.assessment_service import create_assessment
from backend.services.attempt_service import submit_assessment_attempt
from backend.services.background_job_service import claim_next_background_job, execute_background_job
from backend.services.course_service import create_course
from backend.services.jwt_auth_service import create_token_pair
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server
from tests.integration.test_sqlserver_password_reset_atomic import SecretString
from tests.unit.test_regrade_service import _sync_correction_fixture, _sync_create_correction
from tests.unit.test_regrade_service import admin_user as admin_user
from tests.unit.test_regrade_service import instructor_user as instructor_user
from tests.unit.test_regrade_service import published_course as published_course
from tests.unit.test_regrade_service import setup_roles as setup_roles
from tests.unit.test_regrade_service import student_user_1 as student_user_1


@pytest.mark.parametrize("transport", ["session", "jwt"])
def test_wrong_course_http_regrade_cannot_consume_dispatch_then_worker_applies_once(
    app, instructor_user, published_course, student_user_1, http_server, transport
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    app.config["WTF_CSRF_ENABLED"] = True
    question, assessment, attempt, lease, keys = _sync_correction_fixture(
        instructor_user, published_course, student_user_1
    )
    submit_assessment_attempt(student_user_1, attempt.id, raw_lease_token=lease)
    correction = _sync_create_correction(instructor_user, question, keys)
    job = db.session.query(RegradeJob).filter_by(question_correction_id=correction.id).one()
    background = (
        db.session.query(BackgroundJob)
        .filter_by(job_type="REGRADE", dedupe_key=f"regrade:{job.id}")
        .one()
    )
    assert background.status == "QUEUED"
    other_course = create_course(
        instructor_user,
        {"course_code": "HTTP-RG-" + uuid.uuid4().hex[:6], "title": "Different owned course"},
    )
    other_assessment = create_assessment(
        instructor_user,
        other_course.id,
        {"title": "Unrelated assessment", "assessment_type": "QUIZ"},
    )
    attempt_id, job_id, background_id = attempt.id, job.id, background.id
    public_id, other_id = str(assessment.public_id), str(other_assessment.public_id)
    correction_id = correction.id
    if transport == "jwt":
        pair = create_token_pair(instructor_user)
        headers = {"Authorization": SecretString("Bearer " + pair["access_token"])}
        prefix = "api/assessments"
    else:
        client = app.test_client()
        csrf = client.get("/auth/login").get_json()["csrf_token"]
        assert (
            client.post(
                "/auth/login",
                json={"email": instructor_user.email, "password": "Password@123"},
                headers={"X-CSRFToken": csrf},
            ).status_code
            == 200
        )
        csrf = client.get("/auth/login").get_json()["csrf_token"]
        cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
        headers = {"Cookie": SecretString(f"{cookie.key}={cookie.value}"), "X-CSRFToken": csrf}
        prefix = "instructor/assessments"
    engine = db.engine
    db.session.remove()
    with Session(engine) as observer:
        baseline_history = observer.query(AttemptQuestionGradeHistory).count()
        assert (
            observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one().raw_score == 0
        )
    denied = http_request(
        headers,
        "POST",
        f"{http_server}/{prefix}/{other_id}/regrade",
        {"correction_id": correction_id},
    )
    assert denied.status_code == 403
    with Session(engine) as observer:
        assert observer.get(BackgroundJob, background_id).status == "QUEUED"
        assert observer.query(RegradeJob).count() == 1
        assert (
            observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one().raw_score == 0
        )
        assert observer.query(AttemptQuestionGradeHistory).count() == baseline_history
    claimed = claim_next_background_job()
    assert claimed.id == background_id
    assert execute_background_job(claimed) is True
    with Session(engine) as observer:
        assert observer.get(BackgroundJob, background_id).status == "SUCCEEDED"
        job = observer.get(RegradeJob, job_id)
        assert job.status == "COMPLETED"
        assert (job.total_items, job.processed_items, job.changed_results) == (1, 1, 1)
        assert (
            observer.query(RegradeItem).filter_by(regrade_job_id=job_id, status="COMPLETED").count()
            == 1
        )
        assert (
            observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one().raw_score == 10
        )
        completed_history = observer.query(AttemptQuestionGradeHistory).count()
        assert completed_history == baseline_history + 1
    assert execute_background_job(claimed) is False
    replay = http_request(
        headers,
        "POST",
        f"{http_server}/{prefix}/{public_id}/regrade",
        {"correction_id": correction_id},
    )
    assert replay.status_code == 200
    with Session(engine) as observer:
        assert (
            observer.query(BackgroundJob)
            .filter_by(job_type="REGRADE", dedupe_key=f"regrade:{job_id}")
            .count()
            == 1
        )
        assert observer.query(AttemptQuestionGradeHistory).count() == completed_history
        assert (
            observer.query(AssessmentResult).filter_by(attempt_id=attempt_id).one().raw_score == 10
        )
