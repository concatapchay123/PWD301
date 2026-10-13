"""Real independent SQL Server sessions for synchronization claim/progress fences."""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import LessonProgress, LessonProgressReceipt
from pwd301.models.identity import User
from pwd301.models.operations import BackgroundJob
from pwd301.models.types import utc_now
from pwd301.services.background_job_service import (
    claim_next_background_job,
    enqueue_background_job,
    execute_background_job,
    renew_background_job_lease,
)
from pwd301.services.lesson_service import record_lesson_progress
from tests.unit.test_sync_course_remediation import enrolled_progress

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


@pytest.fixture(autouse=True)
def sqlserver_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")


def test_claim_two_sessions_has_exactly_one_owner(app):
    job = enqueue_background_job("ANALYTICS", run_async=False)
    db.session.commit()
    job_id = job.id
    engine = db.engine
    barrier = threading.Barrier(2)

    def claim():
        with Session(engine) as session:
            barrier.wait(timeout=15)
            claimed = claim_next_background_job(session=session)
            return claimed.id if claimed else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: claim(), range(2)))
    assert outcomes.count(job_id) == 1
    assert outcomes.count(None) == 1
    db.session.expire_all()
    assert db.session.get(BackgroundJob, job_id).attempt_count == 1


def test_reclaimed_job_rejects_previous_owner_renewal_and_completion(app):
    job = enqueue_background_job("ANALYTICS", run_async=False)
    db.session.commit()
    job_id = job.id
    engine = db.engine
    with Session(engine) as old_session, Session(engine) as new_session:
        old_claim = claim_next_background_job(session=old_session)
        ownership = (old_claim.id, old_claim.claimed_at, old_claim.attempt_count)
        old_session.expunge(old_claim)
        new_job = new_session.get(BackgroundJob, job_id)
        new_job.lease_expires_at = utc_now() - timedelta(seconds=1)
        new_session.commit()
        new_claim = claim_next_background_job(session=new_session)
        assert new_claim.attempt_count == ownership[2] + 1
        assert renew_background_job_lease(*ownership, session=old_session) is False
        assert execute_background_job(old_claim, session=old_session) is False
        new_session.expire_all()
        persisted = new_session.get(BackgroundJob, job_id)
        assert persisted.status == "RUNNING"
        assert persisted.attempt_count == 2


def test_duplicate_progress_event_two_connections_is_credited_once(
    app, published_course, student_user
):
    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    ids = (student_user.id, lesson.id, progress.id)
    instant = utc_now().replace(microsecond=0)
    engine = db.engine
    barrier = threading.Barrier(2)

    def credit():
        with Session(engine) as session:
            actor = session.get(User, ids[0])
            session.get(LessonProgress, ids[2])
            barrier.wait(timeout=15)
            result = record_lesson_progress(
                actor, ids[1], 5, 0.1, "same-durable-event", now=instant, session=session
            )
            session.commit()
            return result.seconds_spent

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: credit(), range(2)))
    db.session.expire_all()
    assert db.session.get(LessonProgress, ids[2]).seconds_spent == 5
    assert db.session.query(LessonProgressReceipt).count() == 1


def test_progress_stale_session_preserves_committed_seconds(app, published_course, student_user):
    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    ids = (student_user.id, lesson.id, progress.id)
    with Session(db.engine) as stale, Session(db.engine) as writer:
        actor = stale.get(User, ids[0])
        cached = stale.get(LessonProgress, ids[2])
        assert cached.seconds_spent == 0
        fresh = writer.get(LessonProgress, ids[2])
        fresh.seconds_spent = 9
        writer.commit()
        record_lesson_progress(actor, ids[1], 5, 0.1, session=stale)
        stale.commit()
    db.session.expire_all()
    assert db.session.get(LessonProgress, ids[2]).seconds_spent == 14


def test_simultaneous_appeals_create_one_pending_request(
    app, published_course, student_user, instructor_user, monkeypatch
):
    from pwd301.models.assessment import Assessment
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.models.notification_audit import AuditEvent
    from pwd301.services import attempt_service
    from tests.conftest import login_web_user

    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Concurrent appeals",
        assessment_type="QUIZ",
        status="PUBLISHED",
    )
    attempt = AssessmentAttempt(
        assessment=assessment,
        enrollment_period_id=progress.enrollment_period_id,
        student_user_id=student_user.id,
        attempt_number=1,
        status="GRADED",
        started_at=utc_now(),
        submitted_at=utc_now(),
    )
    db.session.add(attempt)
    db.session.commit()
    route = f"/student/attempts/{attempt.public_id}/appeal"
    target_id = attempt.id
    clients = [app.test_client(), app.test_client()]
    for client in clients:
        login_web_user(client, student_user)
    barrier = threading.Barrier(2)
    original = attempt_service._resolve_attempt

    def simultaneous_resolve(*args, **kwargs):
        resolved = original(*args, **kwargs)
        barrier.wait(timeout=15)
        return resolved

    monkeypatch.setattr(attempt_service, "_resolve_attempt", simultaneous_resolve)

    def appeal(client):
        response = client.post(route, json={"reason": "Please review the score"})
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(appeal, clients))
    assert sorted(statuses) == [201, 409]
    db.session.expire_all()
    assert (
        db.session.query(AuditEvent)
        .filter_by(action="STUDENT_ATTEMPT_APPEAL", target_id=target_id)
        .count()
    ) == 1


@pytest.mark.parametrize("purpose", ["JWT_REFRESH", "PASSWORD_RESET"])
def test_simultaneous_token_consumption_has_one_winner(app, student_user, purpose):
    from pwd301.models.identity import JwtTokenGrant, UserSecurityToken
    from pwd301.services import auth_token_service, jwt_auth_service
    from pwd301.services.exceptions import JwtTokenRevokedError, TokenAlreadyConsumedError

    if purpose == "JWT_REFRESH":
        raw = jwt_auth_service.create_token_pair(student_user)["refresh_token"]
        table = "jwt_token_grants"
    else:
        _, raw = auth_token_service.create_security_token(student_user.id, purpose)
        table = "user_security_tokens"
    engine = db.engine
    barrier = threading.Barrier(2)

    def align_compare_and_swap(connection, cursor, statement, parameters, context, executemany):
        # Both independent connections already verified the same persisted token.
        # Scheduling at the UPDATE boundary does not fake verification or row state.
        if statement.lstrip().upper().startswith("UPDATE " + table.upper()):
            barrier.wait(timeout=15)

    sa.event.listen(engine, "before_cursor_execute", align_compare_and_swap)

    def consume():
        with app.app_context(), Session(engine) as session:
            try:
                if purpose == "JWT_REFRESH":
                    jwt_auth_service.refresh_tokens(raw, session=session)
                else:
                    auth_token_service.consume_security_token(raw, purpose, session=session)
                return "winner"
            except (JwtTokenRevokedError, TokenAlreadyConsumedError):
                session.rollback()
                return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: consume(), range(2)))
    finally:
        sa.event.remove(engine, "before_cursor_execute", align_compare_and_swap)
    assert sorted(outcomes) == ["conflict", "winner"]
    db.session.expire_all()
    if purpose == "JWT_REFRESH":
        assert db.session.query(JwtTokenGrant).filter_by(user_id=student_user.id).count() == 4
    else:
        assert (
            db.session.query(UserSecurityToken)
            .filter(UserSecurityToken.consumed_at.is_not(None))
            .count()
        ) == 1


def test_retention_rechecks_activity_committed_after_candidate_read(app, student_user):
    from pwd301.models.ai_rag import AIConversation, AIMessage
    from pwd301.services.ai_service import _lock_conversation_for_send
    from pwd301.services.retention_service import purge_expired_ai_messages

    now = utc_now()
    conv = AIConversation(
        user_id=student_user.id,
        context_type="GLOBAL",
        status="ACTIVE",
        created_at=now - timedelta(hours=1),
        expires_at=now - timedelta(seconds=1),
        last_activity_at=now - timedelta(minutes=6),
    )
    db.session.add(conv)
    db.session.flush()
    db.session.add(
        AIMessage(conversation_id=conv.id, sender="USER", content="study", sequence_no=1)
    )
    db.session.commit()
    conv_id = conv.id
    renewed = False
    with Session(db.engine) as purger, Session(db.engine) as sender:

        def renew_after_read(state):
            nonlocal renewed
            if state.is_select and not renewed:
                result = state.invoke_statement()
                renewed = True
                active = sender.get(AIConversation, conv_id)
                _lock_conversation_for_send(active, sender)
                active.last_activity_at = now
                active.expires_at = now + timedelta(minutes=5)
                sender.commit()
                return result

        sa.event.listen(purger, "do_orm_execute", renew_after_read, retval=True)
        assert purge_expired_ai_messages(session=purger, cutoff_date=now) == 0
        purger.commit()
    db.session.expire_all()
    assert renewed
    assert db.session.get(AIConversation, conv_id).status == "ACTIVE"
    assert db.session.query(AIMessage).filter_by(conversation_id=conv_id).count() == 1


def test_two_expired_lease_takeovers_have_one_winner(
    app, published_course, student_user, instructor_user
):
    import hashlib

    from pwd301.models.assessment import Assessment
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.services.attempt_service import takeover_attempt_lease
    from pwd301.services.exceptions import AttemptLeaseConflictError

    course, lesson = published_course
    progress = enrolled_progress(course, lesson, student_user)
    now = utc_now()
    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Concurrent editing leases",
        assessment_type="QUIZ",
        status="PUBLISHED",
    )
    attempt = AssessmentAttempt(
        assessment=assessment,
        enrollment_period_id=progress.enrollment_period_id,
        student_user_id=student_user.id,
        attempt_number=1,
        status="IN_PROGRESS",
        started_at=now,
        deadline_at=now + timedelta(minutes=10),
        lease_token_hash=hashlib.sha256(b"previous-owner").digest(),
        lease_expires_at=now - timedelta(seconds=1),
        lease_epoch=1,
    )
    db.session.add(attempt)
    db.session.commit()
    ids = (student_user.id, attempt.id)
    engine = db.engine
    barrier = threading.Barrier(2)

    def takeover():
        with Session(engine) as session:
            actor = session.get(User, ids[0])
            cached = session.get(AssessmentAttempt, ids[1])
            assert cached.lease_epoch == 1
            barrier.wait(timeout=15)
            try:
                takeover_attempt_lease(actor, ids[1], session=session)
                return "winner"
            except AttemptLeaseConflictError:
                session.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: takeover(), range(2)))
    assert sorted(outcomes) == ["conflict", "winner"]
    db.session.expire_all()
    assert db.session.get(AssessmentAttempt, ids[1]).lease_epoch == 2
