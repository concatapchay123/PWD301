"""Behavioral regressions for security transactions and durable workers."""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from backend.extensions import db
from backend.models.ai_rag import AIConversation, AIMessage
from backend.models.identity import User
from backend.models.types import utc_now
from backend.services import auth_token_service as tokens
from backend.services import background_job_service as jobs
from backend.services.operations_service import is_maintenance_active
from backend.services.user_service import register_user


def test_consumption_can_be_rolled_back_with_caller(app):
    with app.app_context():
        user = register_user("atomic@example.com", "StrongPassword123!", "Atomic")
        record, raw = tokens.create_security_token(user.id, "PASSWORD_RESET")
        token_id = record.id
        tokens.consume_security_token(raw, "PASSWORD_RESET", commit=False)
        db.session.rollback()
        assert db.session.get(type(record), token_id).consumed_at is None


def test_reset_notification_failure_rolls_back_password_and_token(app, monkeypatch):
    with app.app_context():
        user = register_user("rollback@example.com", "StrongPassword123!", "Rollback")
        old_hash = user.password_hash
        record, raw = tokens.create_security_token(user.id, "PASSWORD_RESET")
        from backend.services import notification_service

        monkeypatch.setattr(
            notification_service,
            "dispatch_notification",
            Mock(side_effect=RuntimeError("outbox unavailable")),
        )
        with pytest.raises(RuntimeError, match="outbox unavailable"):
            tokens.reset_password_with_token(raw, "AnotherStrongPassword123!")
        db.session.rollback()
        assert db.session.get(User, user.id).password_hash == old_hash
        assert db.session.get(type(record), record.id).consumed_at is None


def test_enqueue_never_submits_uncommitted_work(app, monkeypatch):
    with app.app_context():
        app.config["TESTING"] = False
        submit = Mock()
        monkeypatch.setattr(jobs._WORKER_EXECUTOR, "submit", submit)
        jobs.enqueue_background_job("EMAIL", run_async=True)
        assert not submit.called
        db.session.rollback()


def test_execute_requires_claimed_unexpired_job(app):
    with app.app_context():
        job = jobs.enqueue_background_job("EMAIL", run_async=False)
        db.session.commit()
        assert jobs.execute_background_job(job) is False
        assert job.status == "QUEUED"


def test_maintenance_database_failure_is_closed():
    sess = Mock()
    sess.query.side_effect = RuntimeError("database unavailable")
    active, _ = is_maintenance_active(session=sess)
    assert active is True


@pytest.mark.parametrize("failure", ["unknown_window", "exception"])
def test_sync057_http_admission_denies_unverifiable_maintenance(app, client, monkeypatch, failure):
    from backend.services import operations_service

    check = Mock(return_value=(True, None))
    if failure == "exception":
        check.side_effect = RuntimeError("Maintenance authority unavailable")
    monkeypatch.setattr(operations_service, "is_maintenance_active_cached", check)
    response = client.patch("/auth/preferences", json={"email_enabled": False})
    assert response.status_code == 503
    assert response.json["error"]["code"] == "MAINTENANCE_STATUS_UNAVAILABLE"
    assert response.headers["Retry-After"] == "60"
    assert client.get("/auth/login").status_code == 200


def test_stale_worker_cannot_finish_new_owner_claim(app, monkeypatch):
    with app.app_context():
        job = jobs.enqueue_background_job("EMAIL", run_async=False)
        db.session.commit()
        claimed = jobs.claim_next_background_job()
        from backend.services import email_service

        def take_over(**kwargs):
            claimed.attempt_count += 1
            claimed.claimed_at = utc_now()
            db.session.commit()

        monkeypatch.setattr(email_service, "process_email_queue", take_over)
        assert jobs.execute_background_job(claimed) is False
        db.session.refresh(claimed)
        assert claimed.status == "RUNNING"
        assert claimed.attempt_count == 2


def test_retention_batch_advances_past_empty_expired_parents(app):
    from backend.services.retention_service import purge_expired_ai_messages

    with app.app_context():
        user = register_user("retention@example.com", "StrongPassword123!", "Retention")
        now = utc_now()
        conversations = [
            AIConversation(
                user_id=user.id,
                context_type="GLOBAL",
                status="EXPIRED",
                created_at=now - timedelta(hours=1),
                expires_at=now - timedelta(minutes=50),
                last_activity_at=now - timedelta(hours=1),
            )
            for _ in range(3)
        ]
        db.session.add_all(conversations)
        db.session.flush()
        db.session.add(
            AIMessage(
                conversation_id=conversations[-1].id,
                sender="USER",
                content="private",
                sequence_no=1,
            )
        )
        db.session.commit()
        assert purge_expired_ai_messages(batch_size=1) == 1
        assert db.session.query(AIMessage).count() == 0


def test_lease_renewal_rejects_replaced_owner(app):
    with app.app_context():
        jobs.enqueue_background_job("EMAIL", run_async=False)
        db.session.commit()
        job = jobs.claim_next_background_job()
        assert jobs.renew_background_job_lease(job.id, job.claimed_at, job.attempt_count)
        assert not jobs.renew_background_job_lease(job.id, job.claimed_at, job.attempt_count - 1)


def test_ai_send_lock_refreshes_stale_messages_before_allocation(app):
    from backend.services.ai_service import _lock_conversation_for_send

    with app.app_context():
        user = register_user("sequence@example.com", "StrongPassword123!", "Sequence")
        now = utc_now()
        conv = AIConversation(
            user_id=user.id,
            context_type="GLOBAL",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
            last_activity_at=now,
        )
        db.session.add(conv)
        db.session.commit()
        assert list(conv.messages) == []
        db.session.add(
            AIMessage(conversation_id=conv.id, sender="USER", content="previous", sequence_no=1)
        )
        db.session.flush()
        _lock_conversation_for_send(conv, db.session)
        assert [m.sequence_no for m in conv.messages] == [1]


def test_worker_schedules_ai_retention_on_first_iteration(app, monkeypatch):
    with app.app_context():
        monkeypatch.setattr(jobs, "run_worker_once", lambda: True)
        jobs.run_worker_loop(max_iterations=1)
        scheduled = (
            db.session.query(jobs.BackgroundJob)
            .filter_by(dedupe_key="ai-message-retention")
            .first()
        )
        assert scheduled is not None
        assert "ai-message-retention" in scheduled.payload_json


def test_stale_verified_token_cannot_be_consumed_twice(app, monkeypatch):
    from backend.models.identity import UserSecurityToken
    from backend.services.exceptions import TokenAlreadyConsumedError

    with app.app_context():
        user = register_user("consume@example.com", "StrongPassword123!", "Consume")
        record, raw = tokens.create_security_token(user.id, "PASSWORD_RESET")
        verify = tokens.verify_security_token

        def concurrent_consume(*args, **kwargs):
            result = verify(*args, **kwargs)
            db.session.query(UserSecurityToken).filter_by(id=record.id).update(
                {"consumed_at": utc_now()}, synchronize_session=False
            )
            return result

        monkeypatch.setattr(tokens, "verify_security_token", concurrent_consume)
        with pytest.raises(TokenAlreadyConsumedError):
            tokens.consume_security_token(raw, "PASSWORD_RESET")


def test_refresh_loses_conditional_rotation_without_new_pair(app, monkeypatch):
    from backend.models.identity import JwtTokenGrant
    from backend.services import jwt_auth_service as jwt_service
    from backend.services.exceptions import JwtTokenRevokedError

    with app.app_context():
        user = register_user("rotation@example.com", "StrongPassword123!", "Rotation")
        pair = jwt_service.create_token_pair(user)
        now = utc_now()

        def competing_rotation():
            db.session.query(JwtTokenGrant).filter_by(user_id=user.id, token_type="REFRESH").update(
                {"revoked_at": now}, synchronize_session=False
            )
            return now

        monkeypatch.setattr(jwt_service, "utc_now", competing_rotation)
        with pytest.raises(JwtTokenRevokedError):
            jwt_service.refresh_tokens(pair["refresh_token"])
        assert db.session.query(JwtTokenGrant).count() == 2


@pytest.mark.parametrize(
    "module_name, function_name",
    [("admin", "admin_suspend_user"), ("api_admin", "api_admin_suspend_user")],
)
def test_both_suspend_routes_reject_missing_phrase(app, monkeypatch, module_name, function_name):
    import importlib
    from inspect import unwrap

    from backend.services.exceptions import ValidationError

    module = importlib.import_module(f"backend.blueprints.{module_name}.routes")
    actor = Mock()
    actor.verify_password.return_value = True
    monkeypatch.setattr(module, "require_authenticated_actor", lambda: actor)
    with (
        app.test_request_context(json={"password": "valid", "reason": "valid reason"}),
        pytest.raises(ValidationError),
    ):
        unwrap(getattr(module, function_name))("user-key")


def test_replaced_cached_claim_never_dispatches_domain_work(app, monkeypatch):
    """A replaced database claim must fence side effects before dispatch."""
    from backend.services import email_service

    with app.app_context():
        jobs.enqueue_background_job("EMAIL", run_async=False)
        db.session.commit()
        cached_claim = jobs.claim_next_background_job()
        previous_attempt = cached_claim.attempt_count
        db.session.query(jobs.BackgroundJob).filter_by(id=cached_claim.id).update(
            {"attempt_count": previous_attempt + 1, "claimed_at": utc_now()},
            synchronize_session=False,
        )
        dispatch = Mock()
        monkeypatch.setattr(email_service, "process_email_queue", dispatch)
        assert jobs.execute_background_job(cached_claim) is False
        dispatch.assert_not_called()


def test_claim_replaced_during_handler_cannot_commit_domain_mutation(app, monkeypatch):
    from sqlalchemy import text

    from backend.services import email_service

    with app.app_context():
        user = register_user("fenced@example.com", "StrongPassword123!", "Before")
        jobs.enqueue_background_job("EMAIL", run_async=False)
        db.session.commit()
        claim = jobs.claim_next_background_job()

        def dispatch(**kwargs):
            db.session.query(jobs.BackgroundJob).filter_by(id=claim.id).update(
                {"attempt_count": claim.attempt_count + 1}, synchronize_session=False
            )
            user.display_name = "Stale mutation"
            db.session.commit()

        monkeypatch.setattr(email_service, "process_email_queue", dispatch)
        assert jobs.execute_background_job(claim) is False
        db.session.expire_all()
        assert (
            db.session.execute(
                text("SELECT display_name FROM users WHERE id=:id"), {"id": user.id}
            ).scalar_one()
            == "Before"
        )
