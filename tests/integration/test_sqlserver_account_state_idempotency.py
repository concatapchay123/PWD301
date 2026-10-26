"""Actual SQL account-state retries with independently cached user identities."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.identity import User, UserRole
from backend.models.notification_audit import AuditEvent, EmailDelivery, NotificationEvent
from backend.services.audit_service import suspend_user_account, unsuspend_user_account
from backend.services.exceptions import AdminActionForbiddenError
from backend.services.user_service import suspend_user
from tests.test_admin_security_remediation import primary_admin as primary_admin
from tests.test_admin_security_remediation import student_user as student_user
from tests.test_admin_security_remediation import subordinate_admin as subordinate_admin


@pytest.mark.parametrize("entrypoint", ["audited", "lifecycle"])
def test_cached_role_link_cannot_suspend_newly_promoted_primary_admin(
    app, primary_admin, subordinate_admin, entrypoint
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    actor_id, target_id = primary_admin.id, subordinate_admin.id
    engine = db.engine
    db.session.remove()
    with Session(engine) as cached_session:
        actor = cached_session.get(User, actor_id)
        target = cached_session.get(User, target_id)
        assert target.admin_sub_role == "ADMIN_SYSTEM_MONITORING"
        cached_links = list(target.user_role_links)
        assert cached_links
        with Session(engine) as promoter:
            promoter.execute(
                sa.update(UserRole)
                .where(UserRole.user_id == target_id)
                .values(assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Verified promotion")
            )
            promoter.commit()
        with pytest.raises(AdminActionForbiddenError):
            if entrypoint == "audited":
                suspend_user_account(
                    actor, target_id, "Verified suspension reason", session=cached_session
                )
            else:
                suspend_user(target_id, "Verified suspension reason", session=cached_session)
        cached_session.rollback()
    with Session(engine) as observer:
        assert observer.get(User, target_id).status == "ACTIVE"


@pytest.mark.parametrize("action", ["audited_suspend", "lifecycle_suspend", "unsuspend"])
def test_account_state_replay_releases_lock_before_caller_cleanup(
    app, primary_admin, student_user, action
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    suspend_user_account(primary_admin, student_user.id, "Initial verified suspension")
    if action == "unsuspend":
        unsuspend_user_account(primary_admin, student_user.id, "Initial verified restoration")
    actor_id, target_id = primary_admin.id, student_user.id
    engine = db.engine
    db.session.remove()
    with Session(engine) as replay_session:
        actor = replay_session.get(User, actor_id)
        if action == "lifecycle_suspend":
            suspend_user(target_id, "Replay verified suspension", session=replay_session)
        elif action == "audited_suspend":
            suspend_user_account(
                actor, target_id, "Replay verified suspension", session=replay_session
            )
        else:
            unsuspend_user_account(
                actor, target_id, "Replay verified restoration", session=replay_session
            )
        with Session(engine) as writer:
            writer.execute(sa.text("SET LOCK_TIMEOUT 1000"))
            writer.execute(
                sa.update(User).where(User.id == target_id).values(auth_version=User.auth_version)
            )
            writer.rollback()


@pytest.mark.parametrize("action", ["audited_suspend", "lifecycle_suspend", "unsuspend"])
def test_cached_concurrent_account_transitions_emit_one_effect(
    app, primary_admin, student_user, action
):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    if action == "unsuspend":
        suspend_user_account(primary_admin, student_user.id, "Initial verified suspension")
    actor_id, target_id = primary_admin.id, student_user.id
    baseline = student_user.auth_version
    engine = db.engine
    db.session.remove()
    ready = threading.Barrier(2)
    connections = set()
    connection_guard = threading.Lock()

    def transition():
        with app.app_context(), Session(engine) as session:
            session.execute(sa.text("SET LOCK_TIMEOUT 15000"))
            actor = session.get(User, actor_id)
            cached = session.get(User, target_id)
            assert cached.auth_version == baseline
            with connection_guard:
                connections.add(session.execute(sa.text("SELECT @@SPID")).scalar())
            ready.wait(timeout=10)
            if action == "lifecycle_suspend":
                result = suspend_user(target_id, "Concurrent verified suspension", session=session)
            elif action == "audited_suspend":
                result = suspend_user_account(
                    actor, target_id, "Concurrent verified suspension", session=session
                )
            else:
                result = unsuspend_user_account(
                    actor, target_id, "Concurrent verified restoration", session=session
                )
            session.commit()
            return result.auth_version

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(transition) for _ in range(2)]
        versions = [future.result(timeout=35) for future in futures]
    assert len(connections) == 2
    assert versions == [baseline + 1, baseline + 1]
    with Session(engine) as observer:
        user = observer.get(User, target_id)
        assert user.status == ("ACTIVE" if action == "unsuspend" else "SUSPENDED")
        assert user.auth_version == baseline + 1
        audit_action = "USER_UNSUSPEND" if action == "unsuspend" else "USER_SUSPEND"
        assert observer.query(AuditEvent).filter_by(
            action=audit_action, target_id=target_id
        ).count() == (0 if action == "lifecycle_suspend" else 1)
        assert (
            observer.query(NotificationEvent).filter_by(event_type="ACCOUNT_SUSPENDED").count() == 1
        )
        assert observer.query(EmailDelivery).filter_by(recipient_user_id=target_id).count() == 1
