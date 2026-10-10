"""Two live SQL Server reviewers cannot apply one curriculum revision twice."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseChangeRequest, Lesson
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.exceptions import LessonStateViolationError
from pwd301.services.lesson_service import approve_course_change_request
from tests.api.test_admin_change_requests_review import approval_env as approval_fixture
from tests.api.test_video_preview_stream import video_env as video_fixture


@pytest.mark.integration
def test_review_policy_downgrade_preserves_restricted_assessments(app, video_env, capsys):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires the migrated disposable SQL Server database")
    from pathlib import Path

    import sqlalchemy as sa
    from flask_migrate import downgrade

    from pwd301.models.assessment import Assessment
    from pwd301.services.assessment_service import create_assessment

    users, asset, _, _, _ = video_env
    assessment = create_assessment(
        users["owner"],
        asset.course_id,
        {
            "title": "Preserve restricted review on downgrade",
            "assessment_type": "QUIZ",
            "answer_visibility_policy": "CORRECT_WRONG_ONLY",
        },
    )
    assessment_id = assessment.id
    db.session.remove()
    with pytest.raises(SystemExit) as stopped:
        downgrade(
            directory=str(Path(__file__).resolve().parents[2] / "migrations"),
            revision="blobdefaultrepair20261009",
        )
    assert stopped.value.code == 1
    assert "Cannot downgrade while assessments use CORRECT_WRONG_ONLY" in capsys.readouterr().err
    assert (
        db.session.get(Assessment, assessment_id).answer_visibility_policy == "CORRECT_WRONG_ONLY"
    )
    assert (
        db.session.scalar(sa.text("SELECT version_num FROM alembic_version"))
        == "reviewpolicy20261010"
    )


@pytest.fixture
def video_env(app):
    return video_fixture.__wrapped__(app)


@pytest.fixture
def approval_env(video_env):
    return approval_fixture.__wrapped__(video_env)


@pytest.mark.integration
@pytest.mark.concurrency
def test_two_reviewers_apply_one_revision_and_one_audit(approval_env):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires disposable SQL Server to prove UPDLOCK/HOLDLOCK.")
    users, course, lesson, req = approval_env
    staged = Lesson(
        course_id=course.id,
        learning_unit_id=lesson.learning_unit_id,
        title="Concurrent revision",
        position=lesson.position,
        status="DRAFT",
        previous_lesson_id=lesson.id,
        change_request_id=req.id,
        markdown_content="New",
    )
    db.session.add(staged)
    db.session.commit()
    actor_id, req_id, staged_id, engine = users["reviewer"].id, req.id, staged.id, db.engine
    barrier = Barrier(2)

    def worker():
        try:
            with Session(engine) as session, session.begin():
                actor = session.get(User, actor_id)
                barrier.wait(timeout=15)
                approve_course_change_request(actor, req_id, session=session)
            return "APPROVED"
        except LessonStateViolationError:
            return "CONFLICT"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        results = [future.result(timeout=45) for future in futures]
    assert sorted(results) == ["APPROVED", "CONFLICT"]
    db.session.expire_all()
    assert db.session.get(CourseChangeRequest, req_id).status == "APPROVED"
    assert db.session.get(Lesson, staged_id).status == "PUBLISHED"
    assert (
        db.session.query(AuditEvent)
        .filter_by(
            target_type="COURSE_CHANGE_REQUEST", target_id=req_id, action="COURSE_CHANGE_APPROVED"
        )
        .count()
        == 1
    )


@pytest.mark.integration
@pytest.mark.concurrency
def test_concurrent_course_approval_emits_one_lifecycle_audit(approval_env, monkeypatch):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires disposable SQL Server to prove lifecycle serialization.")
    from pwd301.models.course import Course
    from pwd301.services import course_service

    users, course, _, _ = approval_env
    course.status = "SUBMITTED_FOR_REVIEW"
    db.session.commit()
    actor_id, course_id, engine = users["reviewer"].id, course.id, db.engine
    barrier = Barrier(2)
    resolve = course_service._resolve_course

    def synchronized_read(*args, **kwargs):
        loaded = resolve(*args, **kwargs)
        barrier.wait(timeout=15)
        return loaded

    monkeypatch.setattr(course_service, "_resolve_course", synchronized_read)

    def worker():
        with Session(engine) as session, session.begin():
            actor = session.get(User, actor_id)
            return course_service.change_course_status(
                actor, course_id, "APPROVED", session=session
            ).status

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        results = [future.result(timeout=45) for future in futures]
    assert results == ["APPROVED", "APPROVED"]
    db.session.expire_all()
    assert db.session.get(Course, course_id).status == "APPROVED"
    assert (
        db.session.query(AuditEvent)
        .filter_by(target_type="COURSE", target_id=course_id, action="COURSE_APPROVED")
        .count()
        == 1
    )
