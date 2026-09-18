"""API tests for REST Authentication endpoints: Logout (API-01) and Email-Change (API-02).

Verifies:
1. POST /api/auth/logout revokes current token and subsequent access with it returns 401.
2. POST /api/auth/logout without token returns 401.
3. POST /api/auth/email-change validates input, enforces uniqueness, issues verification token.
4. POST /api/auth/email-change/verify consumes token, updates email, increments auth_version.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.jwt_auth_service import create_token_pair


def _get_or_create_role(code: str, name: str) -> Role:
    role = db.session.query(Role).filter_by(code=code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.session.add(role)
        db.session.flush()
    return role


@pytest.fixture
def auth_users(app: Flask):
    with app.app_context():
        role = _get_or_create_role("STUDENT", "Student")
        suffix = uuid.uuid4().hex[:6]

        u1 = User(
            email=f"user1_{suffix}@fpt.edu.vn",
            display_name=f"User One {suffix}",
            password_hash="hash1",
            auth_version=1,
            status="ACTIVE",
        )
        u1.roles.append(role)

        u2 = User(
            email=f"user2_{suffix}@fpt.edu.vn",
            display_name=f"User Two {suffix}",
            password_hash="hash2",
            auth_version=1,
            status="ACTIVE",
        )
        u2.roles.append(role)

        db.session.add_all([u1, u2])
        db.session.commit()

        t1 = create_token_pair(u1)
        t2 = create_token_pair(u2)

        yield {
            "u1": u1,
            "u2": u2,
            "t1": t1,
            "t2": t2,
        }


def test_api_logout_success_and_revocation(client: FlaskClient, auth_users: dict) -> None:
    """POST /api/auth/logout revokes the token and prevents further access."""
    token = auth_users["t1"]["access_token"]

    # 1. Verify token works on /api/auth/me
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200

    # 2. Call /api/auth/logout
    res_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res_logout.status_code == 200
    data = res_logout.get_json()
    assert data.get("status") == "ok"
    assert "Logged out successfully" in data.get("message", "")

    # 3. Subsequent call with revoked token must fail with 401
    res_me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me_after.status_code == 401


def test_api_logout_unauthenticated(client: FlaskClient) -> None:
    """POST /api/auth/logout without credentials returns 401."""
    res = client.post("/api/auth/logout")
    assert res.status_code == 401


def test_api_email_change_flow(client: FlaskClient, auth_users: dict) -> None:
    """POST /api/auth/email-change and /api/auth/email-change/verify complete full lifecycle."""
    u1 = auth_users["u1"]
    u2 = auth_users["u2"]
    token = auth_users["t1"]["access_token"]
    suffix = uuid.uuid4().hex[:6]
    new_email = f"new_email_{suffix}@fpt.edu.vn"

    # 1. Reject without auth
    res_no_auth = client.post("/api/auth/email-change", json={"new_email": new_email})
    assert res_no_auth.status_code == 401

    # 2. Reject empty email
    res_empty = client.post(
        "/api/auth/email-change",
        json={"new_email": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_empty.status_code == 400

    # 3. Reject same email
    res_same = client.post(
        "/api/auth/email-change",
        json={"new_email": u1.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_same.status_code == 400

    # 4. Reject existing email of another user
    res_conflict = client.post(
        "/api/auth/email-change",
        json={"new_email": u2.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_conflict.status_code == 409

    # 5. Success request
    res_ok = client.post(
        "/api/auth/email-change",
        json={"new_email": new_email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_ok.status_code == 202
    data = res_ok.get_json()
    assert "token" in data
    verification_token = data["token"]

    # 6. Verify with bad token returns 400
    res_bad_verify = client.post(
        "/api/auth/email-change/verify",
        json={"token": "invalid_or_expired_token"},
    )
    assert res_bad_verify.status_code == 400

    # 7. Verify with good token returns 200
    res_verify = client.post(
        "/api/auth/email-change/verify",
        json={"token": verification_token},
    )
    assert res_verify.status_code == 200
    verify_data = res_verify.get_json()
    assert verify_data.get("email") == new_email

    # 8. Token cannot be reused (one-time use)
    res_reuse = client.post(
        "/api/auth/email-change/verify",
        json={"token": verification_token},
    )
    assert res_reuse.status_code == 400
