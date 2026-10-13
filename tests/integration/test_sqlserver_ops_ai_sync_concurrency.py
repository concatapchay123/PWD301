"""Real SQL Server retry, chat sequence, and scheduled retention evidence.

The AI provider object is replaced; conversation locking, classification, message
allocation, telemetry, and commits remain real. This is not Gemini integration.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import AIConversation, AIMessage
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.operations import BackgroundJob
from pwd301.models.types import utc_now
from pwd301.services import ai_service
from pwd301.services import background_job_service as jobs
from pwd301.services.exceptions import ConflictError
from pwd301.services.operations_service import retry_background_job
from pwd301.services.user_service import register_user


@pytest.fixture(autouse=True)
def sqlserver_only(app):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Disposable migrated SQL Server is required")


def test_retry_cannot_regress_a_claim_committed_after_retry_loaded_candidate(app):
    admin = register_user("opsrace@example.com", "StrongPassword123!", "Ops race")
    role = Role(code="ADMIN", name="Administrator")
    admin.roles.append(role)
    job = jobs.enqueue_background_job("ANALYTICS", run_async=False)
    job.status = "RUNNING"
    job.attempt_count = 1
    job.claimed_at = utc_now() - timedelta(minutes=10)
    job.lease_expires_at = utc_now() - timedelta(seconds=5)
    db.session.commit()
    admin_id, job_id, key = admin.id, job.id, str(job.job_key)
    engine = db.engine
    retry_at_update = threading.Event()
    claim_committed = threading.Event()

    def pause_retry_update(connection, cursor, statement, parameters, context, executemany):
        if threading.current_thread().name.startswith(
            "retry-race"
        ) and statement.lstrip().upper().startswith("UPDATE BACKGROUND_JOBS"):
            retry_at_update.set()
            assert claim_committed.wait(20), "Claim did not commit before retry CAS"

    def retry():
        with app.app_context(), Session(engine) as session:
            actor = session.get(User, admin_id)
            assert actor.is_admin
            try:
                retry_background_job(actor, key, session=session)
                return "accepted"
            except ConflictError:
                return "conflict"

    sa.event.listen(engine, "before_cursor_execute", pause_retry_update)
    try:
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="retry-race") as pool:
            pending = pool.submit(retry)
            assert retry_at_update.wait(20), "Retry did not reach its real conditional SQL update"
            with Session(engine) as session:
                claimed = jobs.claim_next_background_job(session=session)
                assert claimed.id == job_id
                assert claimed.attempt_count == 2
            claim_committed.set()
            assert pending.result(timeout=20) == "conflict"
    finally:
        claim_committed.set()
        sa.event.remove(engine, "before_cursor_execute", pause_retry_update)
    db.session.expire_all()
    final = db.session.get(BackgroundJob, job_id)
    assert final.status == "RUNNING"
    assert final.attempt_count == 2
    assert final.lease_expires_at.replace(tzinfo=UTC) > utc_now()
    assert (
        db.session.query(AuditEvent).filter_by(action="BACKGROUND_JOB_RETRY_REQUESTED").count() == 0
    )


@pytest.mark.parametrize("generated_reply", [False, True], ids=["refusal", "provider-reply"])
def test_concurrent_chat_sends_commit_unique_ordered_pairs_with_stale_parent_cache(
    app, monkeypatch, generated_reply
):
    user = register_user("chat-race@example.com", "StrongPassword123!", "Chat race")
    conv = ai_service.create_conversation(actor=user)
    user_id, conv_id, public_id = user.id, conv.id, str(conv.public_id)
    engine = db.engine
    barrier = threading.Barrier(2)
    provider_histories = []

    class ProviderBoundary:
        def chat_response(self, *, messages, context, skip_scope_check):
            assert skip_scope_check is True
            provider_histories.append(list(messages))
            return "Provider fixture reply: " + messages[-1]["content"]

    # Provider boundary only: real classifier and real history construction.
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: ProviderBoundary())

    def send(index):
        with app.app_context(), Session(engine) as session:
            actor = session.get(User, user_id)
            parent = session.get(AIConversation, conv_id)
            assert list(parent.messages) == []
            connection_id = session.execute(sa.text("SELECT @@SPID")).scalar_one()
            barrier.wait(timeout=20)
            pair = ai_service.send_chat_message(
                actor=actor,
                conversation_id=public_id,
                content=(
                    f"hello {index}"
                    if generated_reply
                    else f"Give me a cooking recipe number {index}"
                ),
                session=session,
            )
            return connection_id, tuple(message.sequence_no for message in pair)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(send, range(2)))
    assert len({connection for connection, _ in outcomes}) == 2
    assert sorted(pair for _, pair in outcomes) == [(1, 2), (3, 4)]
    db.session.expire_all()
    messages = (
        db.session.query(AIMessage)
        .filter_by(conversation_id=conv_id)
        .order_by(AIMessage.sequence_no)
        .all()
    )
    assert [(message.sequence_no, message.sender) for message in messages] == [
        (1, "USER"),
        (2, "ASSISTANT"),
        (3, "USER"),
        (4, "ASSISTANT"),
    ]
    assert len({message.content for message in messages if message.sender == "USER"}) == 2
    if generated_reply:
        assert sorted(len(history) for history in provider_histories) == [1, 3]
        assert len({message.content for message in messages if message.sender == "ASSISTANT"}) == 2
    else:
        assert provider_histories == []


def test_bounded_real_worker_loop_purges_expired_messages_and_keeps_parent(app):
    user = register_user("scheduled-retention@example.com", "StrongPassword123!", "Retention")
    now = utc_now()
    parent = AIConversation(
        user_id=user.id,
        context_type="GLOBAL",
        status="ACTIVE",
        created_at=now - timedelta(hours=1),
        last_activity_at=now - timedelta(hours=1),
        expires_at=now - timedelta(minutes=55),
    )
    db.session.add(parent)
    db.session.flush()
    db.session.add(
        AIMessage(
            conversation_id=parent.id, sender="USER", content="expired private body", sequence_no=1
        )
    )
    db.session.commit()
    parent_id = parent.id
    # No worker, enqueue, dispatch, retention, or SQL boundaries are mocked.
    jobs.run_worker_loop(max_iterations=3, poll_interval_seconds=0.01)
    db.session.expire_all()
    assert db.session.query(AIMessage).filter_by(conversation_id=parent_id).count() == 0
    assert db.session.get(AIConversation, parent_id).status == "EXPIRED"
    cleanup = db.session.query(BackgroundJob).filter_by(dedupe_key="ai-message-retention").one()
    assert cleanup.status == "SUCCEEDED"
    assert cleanup.attempt_count == 1
    assert cleanup.completed_at is not None


def test_real_worker_cadence_advances_across_more_than_one_hundred_raw_chats(
    app, tmp_path, monkeypatch
):
    monkeypatch.setenv("WORKER_HEARTBEAT_PATH", str(tmp_path / "retention-worker.json"))
    user = register_user("retention-batches@example.com", "StrongPassword123!", "Batch retention")
    now = utc_now()
    parents = [
        AIConversation(
            user_id=user.id,
            context_type="GLOBAL",
            status="ACTIVE",
            created_at=now - timedelta(hours=1),
            last_activity_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=55),
        )
        for _ in range(111)
    ]
    db.session.add_all(parents)
    db.session.flush()
    identifiers = [parent.id for parent in parents]
    db.session.add_all(
        [
            AIMessage(
                conversation_id=parent.id, sender="USER", content="expired raw body", sequence_no=1
            )
            for parent in parents
        ]
    )
    db.session.commit()
    # Actual monotonic time and sleeping exercise the 60-second scheduler period.
    # No provider, enqueue, dispatch, claim, retention or SQL boundary is replaced.
    jobs.run_worker_loop(max_iterations=70, poll_interval_seconds=1, max_idle_seconds=1)
    with Session(db.engine) as observer:
        assert (
            observer.query(AIMessage).filter(AIMessage.conversation_id.in_(identifiers)).count()
            == 0
        )
        assert (
            observer.query(AIConversation)
            .filter(AIConversation.id.in_(identifiers), AIConversation.status == "EXPIRED")
            .count()
            == 111
        )
        completed = (
            observer.query(BackgroundJob)
            .filter(BackgroundJob.job_type == "CLEANUP", BackgroundJob.status == "SUCCEEDED")
            .all()
        )
        assert sum('"scope": "ai-message-retention"' in job.payload_json for job in completed) >= 2
