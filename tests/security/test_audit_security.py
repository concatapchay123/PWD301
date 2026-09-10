"""Security and IDOR test suite for Audit Logging Engine & Admin Actions (TASK-022).

Validates:
- RBAC Enforcement: Students and Instructors receive 403 Forbidden on all audit
  and sensitive admin endpoints.
- Authentication Enforcement: Unauthenticated (anonymous) requests receive 401 Unauthorized.
- Append-Only Invariant (ADR-010): Audit logs cannot be updated or deleted via API
  (405 Method Not Allowed).
- ADR-002 Zero Internal PK Leakage: Verify no BIGINT primary or foreign keys leak in JSON payloads.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.audit_service import record_audit_event
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(
        f"sec_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Security Admin"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"sec_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Security Instructor"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user(
        f"sec_stud_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Security Student"
    )
    return assign_role_to_user(u.id, "STUDENT")


def test_anonymous_access_blocked(client: FlaskClient, student_user: User) -> None:
    """Unauthenticated requests to admin audit endpoints receive HTTP 401."""
    # List audit logs
    r1 = client.get("/api/admin/audit-logs")
    assert r1.status_code == 401
    assert r1.get_json()["error"]["code"] == "UNAUTHORIZED"

    # Detail audit log
    r2 = client.get(f"/api/admin/audit-logs/{uuid.uuid4()}")
    assert r2.status_code == 401

    # Suspend user
    r3 = client.post(
        f"/api/admin/users/{student_user.public_id}/suspend",
        json={"reason": "Testing auth"},
    )
    assert r3.status_code == 401

    # Unsuspend user
    r4 = client.post(
        f"/api/admin/users/{student_user.public_id}/unsuspend",
        json={"reason": "Testing auth"},
    )
    assert r4.status_code == 401

    # Revoke sessions
    r5 = client.post(f"/api/admin/users/{student_user.public_id}/revoke-sessions")
    assert r5.status_code == 401


def test_student_and_instructor_blocked_from_audit_logs(
    client: FlaskClient, student_user: User, instructor_user: User
) -> None:
    """Students and Instructors receive HTTP 403 when accessing audit log endpoints."""
    student_tokens = create_token_pair(student_user)
    instructor_tokens = create_token_pair(instructor_user)

    s_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}
    i_headers = {"Authorization": f"Bearer {instructor_tokens['access_token']}"}

    # Student cannot list audit logs
    resp_s = client.get("/api/admin/audit-logs", headers=s_headers)
    assert resp_s.status_code == 403
    assert resp_s.get_json()["error"]["code"] == "FORBIDDEN"

    # Instructor cannot list audit logs
    resp_i = client.get("/api/admin/audit-logs", headers=i_headers)
    assert resp_i.status_code == 403
    assert resp_i.get_json()["error"]["code"] == "FORBIDDEN"

    # Student cannot get detail
    dummy_id = str(uuid.uuid4())
    resp_detail_s = client.get(f"/api/admin/audit-logs/{dummy_id}", headers=s_headers)
    assert resp_detail_s.status_code == 403

    # Instructor cannot get detail
    resp_detail_i = client.get(f"/api/admin/audit-logs/{dummy_id}", headers=i_headers)
    assert resp_detail_i.status_code == 403


def test_non_admin_blocked_from_sensitive_admin_actions(
    client: FlaskClient, student_user: User, instructor_user: User
) -> None:
    """Students and Instructors cannot invoke suspend, unsuspend, or revoke-sessions."""
    student_tokens = create_token_pair(student_user)
    instructor_tokens = create_token_pair(instructor_user)

    s_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}
    i_headers = {"Authorization": f"Bearer {instructor_tokens['access_token']}"}

    target_id = str(student_user.public_id)

    # 1. Suspend
    assert (
        client.post(
            f"/api/admin/users/{target_id}/suspend",
            json={"reason": "Attack"},
            headers=s_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/users/{target_id}/suspend",
            json={"reason": "Attack"},
            headers=i_headers,
        ).status_code
        == 403
    )

    # 2. Unsuspend
    assert (
        client.post(
            f"/api/admin/users/{target_id}/unsuspend",
            json={"reason": "Attack"},
            headers=s_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/users/{target_id}/unsuspend",
            json={"reason": "Attack"},
            headers=i_headers,
        ).status_code
        == 403
    )

    # 3. Revoke sessions
    assert (
        client.post(
            f"/api/admin/users/{target_id}/revoke-sessions",
            headers=s_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/users/{target_id}/revoke-sessions",
            headers=i_headers,
        ).status_code
        == 403
    )


def test_append_only_immutability_endpoints(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Enforces ADR-010: No endpoints exist to modify or delete audit log entries."""
    admin_tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    event = record_audit_event(
        actor=admin_user,
        action="USER_SUSPEND",
        target_type="USER",
        target_id=student_user.public_id,
        reason="Initial entry",
        session=db.session,
        commit=True,
    )
    audit_id = str(event.event_id)

    # Attempt PUT on audit log
    r_put = client.put(
        f"/api/admin/audit-logs/{audit_id}",
        json={"reason": "Altered entry"},
        headers=headers,
    )
    assert r_put.status_code == 405

    # Attempt PATCH on audit log
    r_patch = client.patch(
        f"/api/admin/audit-logs/{audit_id}",
        json={"reason": "Altered entry"},
        headers=headers,
    )
    assert r_patch.status_code == 405

    # Attempt DELETE on audit log
    r_del = client.delete(f"/api/admin/audit-logs/{audit_id}", headers=headers)
    assert r_del.status_code == 405

    # Attempt DELETE on collection
    r_del_all = client.delete("/api/admin/audit-logs", headers=headers)
    assert r_del_all.status_code == 405


def test_adr002_zero_pk_leakage_audit_responses(
    client: FlaskClient, admin_user: User, student_user: User
) -> None:
    """Enforces ADR-002: Ensure no integer PKs or FKs leak in audit log responses."""
    sess: Session = db.session
    admin_tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    event = record_audit_event(
        actor=admin_user,
        action="USER_SUSPEND",
        target_type="USER",
        target_id=student_user.public_id,
        reason="Security test entry",
        session=sess,
        commit=True,
    )

    # 1. Check List response
    resp_list = client.get("/api/admin/audit-logs", headers=headers)
    assert resp_list.status_code == 200
    list_json = resp_list.get_json()

    def assert_no_bigint_keys(data: Any) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ("actor_user_id", "target_id", "user_id"):
                    assert not isinstance(v, int), (
                        f"Leaked internal BIGINT in field '{k}' with value {v}"
                    )
                assert_no_bigint_keys(v)
        elif isinstance(data, list):
            for item in data:
                assert_no_bigint_keys(item)

    assert_no_bigint_keys(list_json)

    # 2. Check Detail response
    resp_detail = client.get(f"/api/admin/audit-logs/{event.event_id}", headers=headers)
    assert resp_detail.status_code == 200
    detail_json = resp_detail.get_json()

    assert_no_bigint_keys(detail_json)
    assert isinstance(detail_json["id"], str)
    assert isinstance(detail_json["event_id"], str)
    assert isinstance(detail_json["actor_id"], str)
    assert isinstance(detail_json["target_id"], str)
    # Validate format is valid UUID
    uuid.UUID(detail_json["id"])
    uuid.UUID(detail_json["event_id"])
    uuid.UUID(detail_json["actor_id"])
    uuid.UUID(detail_json["target_id"])
