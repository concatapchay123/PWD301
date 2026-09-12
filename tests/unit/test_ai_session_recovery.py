"""TDD unit tests for Student AI session auto-renewal and self-healing (TASK-HOTFIX)."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.ai_service import create_conversation
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Seed standard roles for tests."""
    sess: Session = db.session
    roles = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        roles[code] = role
    sess.commit()
    return roles


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"student_chat_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Chat Student"
    )
    return assign_role_to_user(u.id, "STUDENT")


def _login_web(client: FlaskClient, user: User) -> None:
    _, raw_key = create_auth_session(user, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = user.auth_version
        sess["auth_source"] = "SESSION"


def test_student_ai_chat_auto_renews_expired_session(
    client: FlaskClient, student_user: User
) -> None:
    """When a conversation has expired (>5m), /student/ai/chat auto-renews without error."""
    _login_web(client, student_user)

    # 1. Create a conversation and artificially expire it past 5 minutes
    conv = create_conversation(actor=student_user, context_type="GLOBAL", session=db.session)
    old_conv_id = str(conv.public_id)
    now = utc_now()
    conv.created_at = now - timedelta(minutes=15)
    conv.last_activity_at = now - timedelta(minutes=10)
    conv.expires_at = now - timedelta(minutes=5)
    conv.status = "EXPIRED"
    db.session.commit()

    # Place the expired conversation ID in the student's Flask session
    with client.session_transaction() as sess:
        sess["active_ai_conversation_id"] = old_conv_id

    # 2. Student sends first message "hello"
    resp1 = client.post(
        "/student/ai/chat",
        json={"message": "hello"},
        headers={"Accept": "application/json"},
    )
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1["status"] == "success"
    # Reply must not be the generic stuck synchronization fallback
    assert "Hệ thống đang đồng bộ dữ liệu" not in data1["reply"]
    # Must have a new active conversation ID
    new_conv_id = data1.get("conversation_id")
    assert new_conv_id is not None
    assert new_conv_id != old_conv_id

    # 3. Student immediately sends follow-up message "bạn là ai"
    resp2 = client.post(
        "/student/ai/chat",
        json={"message": "bạn là ai"},
        headers={"Accept": "application/json"},
    )
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["status"] == "success"
    assert "Hệ thống đang đồng bộ dữ liệu" not in data2["reply"]
