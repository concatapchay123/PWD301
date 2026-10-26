"""Import promotion HTTP rollback/retry and independent SQL session serialization."""

import json
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from werkzeug.serving import make_server

from backend.extensions import db
from backend.models.assessment import AssessmentQuestionAssignment
from backend.models.file_import import DocumentImportJob, ImportQuestion
from backend.models.identity import User
from backend.models.question_bank import Question, QuestionProvenance, QuestionRevision
from backend.services import import_service
from backend.services.assessment_service import create_assessment
from backend.services.exceptions import DocumentImportStateViolationError
from backend.services.jwt_auth_service import create_token_pair
from tests.api.test_import_api import clean_docx_file_asset as clean_docx_file_asset
from tests.api.test_import_api import foreign_instructor as foreign_instructor
from tests.api.test_import_api import instructor_user as instructor_user
from tests.api.test_import_api import setup_roles as setup_roles
from tests.api.test_import_api import test_course as test_course
from tests.conftest import login_web_user


@pytest.fixture
def promotion(app, instructor_user, test_course, clean_docx_file_asset):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    assessment = create_assessment(
        instructor_user,
        test_course.id,
        {"title": "Atomic import target", "assessment_type": "QUIZ"},
    )
    job = import_service.create_import_job(
        instructor_user, test_course.id, clean_docx_file_asset.id, assessment.id
    )
    job.status = "REVIEW_REQUIRED"
    for ordinal in (1, 2):
        db.session.add(
            ImportQuestion(
                import_job_id=job.id,
                ordinal=ordinal,
                detected_type="ESSAY",
                content_text=f"Imported essay {ordinal}",
                confidence_score=1,
                review_state="ACCEPTED",
            )
        )
    db.session.commit()
    return job.id, str(job.public_id), test_course.id, assessment.id


@pytest.fixture
def http_server(app):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def authenticated_http(app, actor, transport):
    headers = {}
    if transport == "api":
        pair = create_token_pair(actor)
        headers["Authorization"] = f"Bearer {pair['access_token']}"
    else:
        bootstrap = app.test_client()
        login_web_user(bootstrap, actor)
        cookie = bootstrap.get_cookie(app.config["SESSION_COOKIE_NAME"])
        headers["Cookie"] = f"{cookie.key}={cookie.value}"
    return headers


def http_request(headers, method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url, data=data, headers={**headers, "Content-Type": "application/json"}, method=method
    )
    try:
        response = urllib.request.urlopen(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read().decode()
        return SimpleNamespace(
            status_code=response.status, text=body, json=lambda: json.loads(body)
        )


def assert_promotion(engine, promotion, count):
    job_id, _, course_id, assessment_id = promotion
    with Session(engine) as observer:
        job = observer.get(DocumentImportJob, job_id)
        assert job.status == ("COMPLETED" if count else "REVIEW_REQUIRED")
        assert (job.completed_at is not None) == bool(count)
        questions = observer.query(Question).filter_by(course_id=course_id).all()
        assert len(questions) == count
        question_ids = [question.id for question in questions]
        assert observer.query(QuestionRevision).count() == count
        assert observer.query(QuestionProvenance).count() == count
        assignments = (
            observer.query(AssessmentQuestionAssignment)
            .filter_by(assessment_id=assessment_id)
            .all()
        )
        assert sorted(item.question_id for item in assignments) == sorted(question_ids)
        imports = observer.query(ImportQuestion).filter_by(import_job_id=job_id).all()
        promoted_ids = [item.approved_question_id for item in imports if item.approved_question_id]
        assert sorted(promoted_ids) == sorted(question_ids)
        return sorted(str(question.public_id) for question in questions)


@pytest.mark.parametrize("transport", ["api", "instructor"])
def test_http_invalid_second_item_rollback_corrected_retry_and_completed_conflict(
    app, promotion, instructor_user, foreign_instructor, http_server, transport
):
    engine = db.engine
    job_id, public_id, _, _ = promotion
    second = db.session.query(ImportQuestion).filter_by(import_job_id=job_id, ordinal=2).one()
    second.detected_type = "SINGLE_CHOICE"
    second.choices_json = "[]"
    second_id = str(second.public_id)
    db.session.commit()
    owner = authenticated_http(app, instructor_user, transport)
    foreign = authenticated_http(app, foreign_instructor, transport)
    db.session.remove()
    url = f"{http_server}/{transport}/imports/{public_id}"
    denied = http_request(foreign, "POST", f"{url}/commit")
    assert denied.status_code == 403
    assert_promotion(engine, promotion, 0)
    failed = http_request(owner, "POST", f"{url}/commit")
    assert failed.status_code == 400, failed.text
    assert_promotion(engine, promotion, 0)
    corrected = http_request(
        owner,
        "PATCH",
        f"{url}/questions/{second_id}",
        {"question_type": "ESSAY", "review_state": "ACCEPTED"},
    )
    assert corrected.status_code == 200, corrected.text
    committed = http_request(owner, "POST", f"{url}/commit")
    assert committed.status_code == 200, committed.text
    payload = committed.json()
    assert payload["status"] == "COMPLETED"
    assert payload["imported_count"] == 2
    durable_ids = assert_promotion(engine, promotion, 2)
    assert sorted(payload["created_question_ids"]) == durable_ids
    repeated = http_request(owner, "POST", f"{url}/commit")
    assert repeated.status_code == 409, repeated.text
    fresh = http_request(owner, "GET", url)
    assert fresh.status_code == 200
    assert fresh.json()["status"] == "COMPLETED"
    assert assert_promotion(engine, promotion, 2) == durable_ids
    assert http_request(foreign, "POST", f"{url}/commit").status_code == 403
    assert assert_promotion(engine, promotion, 2) == durable_ids


def test_concurrent_cached_import_promotions_commit_once(app, promotion, instructor_user):
    engine = db.engine
    actor_id = instructor_user.id
    job_id, public_id, _, _ = promotion
    db.session.remove()
    barrier = threading.Barrier(2)
    spids = set()
    spid_lock = threading.Lock()

    def commit():
        with app.app_context(), Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 15000"))
            actor = session.get(User, actor_id)
            cached_job = session.get(DocumentImportJob, job_id)
            assert cached_job.status == "REVIEW_REQUIRED"
            with spid_lock:
                spids.add(session.execute(sa.text("SELECT @@SPID")).scalar())
            barrier.wait(timeout=10)
            try:
                result = import_service.commit_import_job(actor, public_id, session=session)
                session.commit()
                return result["status"]
            except DocumentImportStateViolationError:
                session.rollback()
                return "CONFLICT"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(commit) for _ in range(2)]
        results = [future.result(timeout=35) for future in futures]
    assert len(spids) == 2
    assert sorted(results) == ["COMPLETED", "CONFLICT"]
    assert_promotion(engine, promotion, 2)
