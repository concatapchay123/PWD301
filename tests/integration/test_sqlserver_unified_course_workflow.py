"""Unified authoring invariants across independent real SQL Server transactions."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.course import Course, CourseChangeRequest, CoursePrerequisite
from backend.models.identity import User
from backend.services.course_service import create_course, update_course
from backend.services.enrollment_service import add_course_prerequisite
from backend.services.exceptions import ConflictError, PrerequisiteCycleError
from backend.services.lesson_service import approve_course_change_request, submit_course_changeset

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


@pytest.fixture(autouse=True)
def sql_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Guarded disposable migrated SQL Server required")
    from tests.conftest import require_disposable_sqlserver_target

    require_disposable_sqlserver_target(db.engine.url.render_as_string(hide_password=False))


def test_concurrent_authors_share_one_draft_without_losing_fields(
    app, published_course, instructor_user
):
    course, _ = published_course
    course_id, owner_id = course.id, instructor_user.id
    engine = db.engine
    db.session.remove()
    barrier = threading.Barrier(2)

    def edit(change):
        with app.app_context(), Session(engine) as session:
            owner = session.get(User, owner_id)
            barrier.wait(timeout=15)
            result = update_course(owner, course_id, change, session=session)
            session.commit()
            return result.id

    with ThreadPoolExecutor(max_workers=2) as workers:
        ids = list(
            workers.map(
                edit,
                [{"category": "Concurrent category"}, {"target_audience": "Concurrent audience"}],
            )
        )
    assert ids[0] == ids[1]
    with Session(engine) as session:
        records = (
            session.query(CourseChangeRequest).filter_by(course_id=course_id, status="DRAFT").all()
        )
        assert len(records) == 1
        fields = json.loads(records[0].proposed_payload_json)["course_metadata"]
        assert fields["category"] == "Concurrent category"
        assert fields["target_audience"] == "Concurrent audience"
        assert session.get(Course, course_id).category != "Concurrent category"


def test_stale_author_session_observes_pending_freeze(app, published_course, instructor_user):
    course, _ = published_course
    course_id, owner_id = course.id, instructor_user.id
    engine = db.engine
    db.session.remove()
    with Session(engine) as stale, Session(engine) as writer:
        cached = stale.get(Course, course_id)
        owner = stale.get(User, owner_id)
        fresh_owner = writer.get(User, owner_id)
        update_course(fresh_owner, course_id, {"category": "Submitted"}, session=writer)
        record = submit_course_changeset(fresh_owner, course_id, {}, session=writer)
        writer.commit()
        assert record.status == "PENDING"
        with pytest.raises(ConflictError):
            update_course(owner, cached, {"target_audience": "Must remain frozen"}, session=stale)
        stale.rollback()


def test_concurrent_opposite_prerequisites_cannot_create_projected_cycle(
    app, published_course, instructor_user
):
    first, _ = published_course
    second = create_course(
        instructor_user,
        {"course_code": "SQL-CYCLE095", "title": "Concurrent second course"},
        session=db.session,
    )
    second.status = "PUBLISHED"
    db.session.commit()
    edges = [(first.id, second.id), (second.id, first.id)]
    owner_id = instructor_user.id
    engine = db.engine
    db.session.remove()
    barrier = threading.Barrier(2)

    def add(edge):
        with app.app_context(), Session(engine) as session:
            owner = session.get(User, owner_id)
            barrier.wait(timeout=15)
            try:
                add_course_prerequisite(owner, edge[0], edge[1], session=session)
                session.commit()
                return "draft"
            except PrerequisiteCycleError:
                session.rollback()
                return "cycle"

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(add, edges))
    assert sorted(outcomes) == ["cycle", "draft"]
    with Session(engine) as session:
        assert session.query(CoursePrerequisite).count() == 0
        assert session.query(CourseChangeRequest).filter_by(status="DRAFT").count() == 1


def test_concurrent_approval_has_one_atomic_winner(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    update_course(
        instructor_user, course.id, {"category": "Approved exactly once"}, session=db.session
    )
    record = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    db.session.commit()
    record_id, admin_id, course_id = record.id, admin_user.id, course.id
    engine = db.engine
    db.session.remove()
    barrier = threading.Barrier(2)

    def approve(_):
        with app.app_context(), Session(engine) as session:
            admin = session.get(User, admin_id)
            barrier.wait(timeout=15)
            try:
                approve_course_change_request(admin, record_id, session=session)
                session.commit()
                return "approved"
            except ConflictError:
                session.rollback()
                return "stale"

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(approve, range(2)))
    assert sorted(outcomes) == ["approved", "stale"]
    with Session(engine) as session:
        assert session.get(Course, course_id).category == "Approved exactly once"
        assert session.get(CourseChangeRequest, record_id).status == "APPROVED"


def test_filtered_unique_index_rejects_duplicate_active_aggregate(
    app, published_course, instructor_user
):
    course, _ = published_course
    update_course(
        instructor_user, course.id, {"category": "Only working aggregate"}, session=db.session
    )
    db.session.commit()
    duplicate = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="COURSE_VERSION_CHANGESET",
        target_type="COURSE",
        target_id=course.id,
        status="PENDING",
        proposed_payload_json="{}",
    )
    db.session.add(duplicate)
    with pytest.raises(sa.exc.IntegrityError):
        db.session.flush()
    db.session.rollback()
    assert (
        db.session.query(CourseChangeRequest).filter_by(course_id=course.id, status="DRAFT").count()
        == 1
    )
