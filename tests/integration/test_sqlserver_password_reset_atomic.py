"""Real reset HTTP, CSRF and SQL rollback/outbox/credential admission chain."""

import logging
import uuid

import pytest
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.identity import AuthSession, JwtTokenGrant, Role, User, UserSecurityToken
from backend.models.notification_audit import EmailDelivery, NotificationEvent
from backend.services import auth_token_service, notification_service
from backend.services.exceptions import ServiceError
from backend.services.user_service import assign_role_to_user, register_user
from tests.integration.test_sqlserver_import_atomic_retry import http_request
from tests.integration.test_sqlserver_import_atomic_retry import http_server as http_server


class SecretString(str):
    def __repr__(self):
        return "<redacted test credential>"


@pytest.fixture
def reset_identity(app, monkeypatch):
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires a guarded disposable SQL Server database")
    # Generated credentials/tokens stay private; loopback access logging is disabled.
    monkeypatch.setattr(logging.getLogger("werkzeug"), "level", logging.ERROR)
    app.config["WTF_CSRF_ENABLED"] = True
    role = db.session.query(Role).filter_by(code="STUDENT").first()
    if role is None:
        db.session.add(Role(code="STUDENT", name="Student"))
        db.session.commit()
    password = "OriginalStrongPassword123!"
    user = register_user(
        f"reset-{uuid.uuid4().hex[:8]}@example.invalid", password, "Reset identity"
    )
    assign_role_to_user(user.id, "STUDENT")
    client = app.test_client()
    csrf = client.get("/auth/login").get_json()["csrf_token"]
    assert (
        client.post(
            "/auth/login",
            json={"email": user.email, "password": password},
            headers={"X-CSRFToken": csrf},
        ).status_code
        == 200
    )
    csrf = client.get("/auth/login").get_json()["csrf_token"]
    cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
    headers = {"Cookie": f"{cookie.key}={cookie.value}", "X-CSRFToken": csrf}
    jwt_response = client.post("/api/auth/login", json={"email": user.email, "password": password})
    assert jwt_response.status_code == 200
    access = jwt_response.get_json()["access_token"]
    record, raw = auth_token_service.create_security_token(user.id, "PASSWORD_RESET")
    data = (
        user.id,
        user.email,
        user.password_hash,
        user.auth_version,
        record.id,
        SecretString(raw),
        SecretString(access),
        headers,
    )
    db.session.remove()
    return data


def security_counts(observer, user_id):
    events = (
        observer.query(NotificationEvent).filter_by(event_type="SECURITY_PASSWORD_CHANGED").all()
    )
    deliveries = observer.query(EmailDelivery).filter_by(recipient_user_id=user_id).all()
    return len(events), len(deliveries)


def test_http_reset_fault_retry_consumption_outbox_and_fresh_authentication(
    app, reset_identity, http_server, monkeypatch
):
    user_id, email, old_hash, old_version, record_id, raw, access, headers = reset_identity
    engine = db.engine
    endpoint = f"{http_server}/auth/reset-password/{raw}"
    new_password = "ChangedStrongPassword456!"
    payload = {"new_password": new_password, "confirm_password": new_password}
    # Missing CSRF must fail before consuming a valid token.
    denied = http_request({}, "POST", endpoint, payload)
    assert denied.status_code == 400
    with Session(engine) as observer:
        assert observer.get(UserSecurityToken, record_id).consumed_at is None
        assert observer.get(User, user_id).password_hash == old_hash

    def fail_outbox(*args, **kwargs):
        raise ServiceError("Injected mandatory notification failure")

    with monkeypatch.context() as fault:
        fault.setattr(notification_service, "dispatch_notification", fail_outbox)
        failed = http_request(headers, "POST", endpoint, payload)
        assert failed.status_code == 400
    with Session(engine) as observer:
        user = observer.get(User, user_id)
        assert user.password_hash == old_hash
        assert user.auth_version == old_version
        assert observer.get(UserSecurityToken, record_id).consumed_at is None
        assert observer.query(AuthSession).filter_by(user_id=user_id, revoked_at=None).count() >= 1
        assert (
            observer.query(JwtTokenGrant).filter_by(user_id=user_id, revoked_at=None).count() == 2
        )
        assert security_counts(observer, user_id) == (0, 0)
    assert (
        http_request(
            {"Authorization": f"Bearer {access}"}, "GET", f"{http_server}/api/auth/me"
        ).status_code
        == 200
    )

    completed = http_request(headers, "POST", endpoint, payload)
    assert completed.status_code == 200
    with Session(engine) as observer:
        user = observer.get(User, user_id)
        assert user.password_hash != old_hash
        assert user.verify_password(new_password)
        assert user.auth_version == old_version + 1
        assert observer.get(UserSecurityToken, record_id).consumed_at is not None
        assert observer.query(AuthSession).filter_by(user_id=user_id, revoked_at=None).count() == 0
        assert (
            observer.query(JwtTokenGrant).filter_by(user_id=user_id, revoked_at=None).count() == 0
        )
        assert security_counts(observer, user_id) == (1, 1)
    assert http_request(
        {"Authorization": f"Bearer {access}"}, "GET", f"{http_server}/api/auth/me"
    ).status_code in (401, 403)
    old_session = http_request(headers, "GET", f"{http_server}/auth/login")
    assert old_session.json().get("status") != "authenticated"

    # A fresh anonymous session supplies CSRF for the consumed-token replay.
    fresh = app.test_client()
    # The shared pytest app context must not reuse another client's cached CSRF.
    with app.app_context():
        csrf = fresh.get("/auth/login").get_json()["csrf_token"]
    cookie = fresh.get_cookie(app.config["SESSION_COOKIE_NAME"])
    replay_headers = {"Cookie": f"{cookie.key}={cookie.value}", "X-CSRFToken": csrf}
    assert http_request(replay_headers, "POST", endpoint, payload).status_code == 400
    assert http_request(
        {},
        "POST",
        f"{http_server}/api/auth/login",
        {"email": email, "password": "OriginalStrongPassword123!"},
    ).status_code in (400, 401)
    assert (
        http_request(
            {}, "POST", f"{http_server}/api/auth/login", {"email": email, "password": new_password}
        ).status_code
        == 200
    )
    assert (
        fresh.post(
            "/auth/login",
            json={"email": email, "password": new_password},
            headers={"X-CSRFToken": csrf},
        ).status_code
        == 200
    )
    assert fresh.get("/auth/login").get_json()["status"] == "authenticated"
    with Session(engine) as observer:
        assert observer.get(User, user_id).auth_version == old_version + 1
        assert security_counts(observer, user_id) == (1, 1)
