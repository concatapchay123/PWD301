"""Course review rollback, retained intents and resource-only revisions on real SQL."""

import io
import json

import pytest
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest, Lesson
from pwd301.models.file_import import LessonResource
from pwd301.services import lesson_service
from pwd301.services.exceptions import ValidationError
from pwd301.services.file_service import store_file_stream
from tests.conftest import login_web_user
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server
from tests.test_lesson_revision_lifecycle import admin_user as admin_user
from tests.test_lesson_revision_lifecycle import instructor_user as instructor_user
from tests.test_lesson_revision_lifecycle import published_course as published_course
from tests.test_lesson_revision_lifecycle import setup_roles as setup_roles


@pytest.fixture
def course_http(app, instructor_user, admin_user, published_course):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    clients = []
    for actor in (instructor_user, admin_user):
        client = app.test_client()
        login_web_user(client, actor)
        cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
        clients.append({"Cookie": f"{cookie.key}={cookie.value}"})
    course, lesson = published_course
    return course, lesson, clients


def submit(base, headers, course, payload):
    public_id = course if isinstance(course, str) else str(course.public_id)
    response = http_request(
        headers, "POST", f"{base}/instructor/courses/{public_id}/changeset/submit", payload
    )
    assert response.status_code == 202, response.text
    return response.json()["change_request_id"]


def approve(base, headers, request_id):
    return http_request(
        headers,
        "POST",
        f"{base}/admin/course-changes/{request_id}/approve",
        {"reason": "Verified course update"},
    )


def test_http_submit_and_approval_preserve_unrelated_structure_intent(
    app, course_http, http_server
):
    course, lesson, clients = course_http
    unrelated = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=course.owner_instructor_id,
        change_type="LESSON_STRUCTURE",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json=json.dumps(
            {"action": "REORDER_UNITS", "units_order": [str(lesson.learning_unit.public_id)]}
        ),
    )
    db.session.add(unrelated)
    db.session.commit()
    unrelated_id, course_id = unrelated.id, course.id
    public_id, lesson_public_id = str(course.public_id), str(lesson.public_id)
    engine = db.engine
    db.session.remove()
    request_id = submit(
        http_server,
        clients[0],
        public_id,
        {
            "version_title": "Retained unrelated intent",
            "modified_lessons": [
                {"lesson_id": lesson_public_id, "title": "Reviewed changed title"}
            ],
        },
    )
    with Session(engine) as observer:
        assert observer.get(CourseChangeRequest, unrelated_id).status == "PENDING"
        assert observer.get(CourseChangeRequest, request_id).status == "PENDING"
    response = approve(http_server, clients[1], request_id)
    assert response.status_code == 200, response.text
    with Session(engine) as observer:
        assert observer.get(CourseChangeRequest, unrelated_id).status == "PENDING"
        assert observer.get(CourseChangeRequest, request_id).status == "APPROVED"
        assert (
            observer.query(Lesson)
            .filter_by(course_id=course_id, status="PUBLISHED", title="Reviewed changed title")
            .count()
            == 1
        )
    status = http_request(
        clients[0], "GET", f"{http_server}/instructor/courses/{public_id}/changeset/status"
    )
    assert status.status_code == 200
    assert status.json()["status"] != "PENDING"


@pytest.mark.parametrize(
    "field,value", [("label", "Reviewed label"), ("position", 2), ("is_required", True)]
)
def test_http_resource_only_revision_survives_cleanup_and_approval(
    app, course_http, instructor_user, http_server, field, value
):
    course, lesson, clients = course_http
    asset = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"Owned review document"),
        "review.txt",
        session=db.session,
    )
    db.session.add(LessonResource(lesson_id=lesson.id, file_asset_id=asset.id, position=1))
    db.session.commit()
    _, staged = lesson_service.create_lesson_change_request(
        instructor_user,
        course.id,
        {
            "target_id": lesson.id,
            "position": lesson.position,
            "title": lesson.title,
            "markdown_content": lesson.markdown_content,
            "learning_unit_id": str(lesson.learning_unit.public_id),
            "minimum_completion_seconds": lesson.minimum_completion_seconds,
            "viewed_fraction_required": float(lesson.viewed_fraction_required),
        },
        session=db.session,
    )
    lesson_service._copy_lesson_resources(lesson.id, staged.id, session=db.session)
    staged.previous_lesson_id = lesson.id
    resource = db.session.query(LessonResource).filter_by(lesson_id=staged.id).one()
    setattr(resource, field, value)
    db.session.commit()
    staged_id, original_id = staged.id, lesson.id
    public_id = str(course.public_id)
    engine = db.engine
    db.session.remove()
    request_id = submit(http_server, clients[0], public_id, {})
    with Session(engine) as observer:
        assert observer.get(Lesson, staged_id).deleted_at is None
        assert (
            getattr(observer.query(LessonResource).filter_by(lesson_id=staged_id).one(), field)
            == value
        )
    response = approve(http_server, clients[1], request_id)
    assert response.status_code == 200, response.text
    with Session(engine) as observer:
        assert observer.get(Lesson, staged_id).status == "PUBLISHED"
        assert observer.get(Lesson, original_id).status == "HISTORICAL"
        assert (
            getattr(observer.query(LessonResource).filter_by(lesson_id=staged_id).one(), field)
            == value
        )
        assert (
            getattr(observer.query(LessonResource).filter_by(lesson_id=original_id).one(), field)
            != value
        )


def test_http_deletion_failure_rolls_review_back_then_retry_applies_two_additions(
    app, course_http, http_server, monkeypatch
):
    course, lesson, clients = course_http
    course_id, original_id = course.id, lesson.id
    engine = db.engine
    request_id = submit(
        http_server,
        clients[0],
        course,
        {
            "version_title": "Atomic deletion and additions",
            "deleted_lessons": [str(lesson.public_id)],
            "added_lessons": [{"title": "First addition"}, {"title": "Second addition"}],
        },
    )
    db.session.remove()
    with Session(engine) as observer:
        before = [
            (row.id, row.status, row.position, row.deleted_at)
            for row in observer.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.id)
        ]

    def fail(*args, **kwargs):
        raise ValidationError("Injected deletion failure")

    with monkeypatch.context() as fault:
        fault.setattr(lesson_service, "trash_lesson", fail)
        response = approve(http_server, clients[1], request_id)
        assert response.status_code == 400, response.text
    with Session(engine) as observer:
        assert observer.get(CourseChangeRequest, request_id).status == "PENDING"
        after = [
            (row.id, row.status, row.position, row.deleted_at)
            for row in observer.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.id)
        ]
        assert after == before
    response = approve(http_server, clients[1], request_id)
    assert response.status_code == 200, response.text
    with Session(engine) as observer:
        assert observer.get(CourseChangeRequest, request_id).status == "APPROVED"
        assert observer.get(Lesson, original_id).deleted_at is not None
        active = (
            observer.query(Lesson)
            .filter_by(course_id=course_id, status="PUBLISHED")
            .order_by(Lesson.position)
            .all()
        )
        assert [row.title for row in active] == ["First addition", "Second addition"]
        assert len({row.position for row in active}) == 2
