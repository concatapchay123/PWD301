"""Tests for F06: 2-Tier Broadcast Notification RBAC Backend.

Verifies:
- ADMIN_PRIMARY can broadcast notifications across all categories (SYSTEM, ACADEMIC, MAINTENANCE, EVENT).
- ADMIN_SYSTEM_MONITORING can broadcast category SYSTEM.
- ADMIN_SYSTEM_MONITORING is strictly forbidden (403) from broadcasting non-SYSTEM categories (ACADEMIC, MAINTENANCE, etc.).
- Other sub-admins (ADMIN_COURSE_REVIEW, ADMIN_TEACHING_ASSIGNMENT) and ordinary users get 403 on all broadcast requests.
- REST API endpoint POST /api/admin/notifications/broadcast enforces the exact same 2-tier RBAC rules.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.identity import User
from backend.seeds.baseline import seed_baseline
from backend.services.exceptions import ForbiddenError
from backend.services.jwt_auth_service import create_token_pair
from backend.services.notification_service import broadcast_system_notification
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def rbac_env(app: Flask) -> dict[str, Any]:
    """Setup users with different admin sub-roles and student."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Primary Admin (seeded by baseline as canonical super admin)
    primary_admin = sess.query(User).filter_by(email="tqtphamnguyenhoangphuc@gmail.com").one()

    # 2. System Monitoring Admin
    sys_admin = register_user(
        f"sysmon_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "SysMon Admin", session=sess
    )
    assign_role_to_user(
        sys_admin.id, "ADMIN", admin_sub_role="ADMIN_SYSTEM_MONITORING", session=sess
    )

    # 3. Course Review Admin
    review_admin = register_user(
        f"crev_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Course Review Admin",
        session=sess,
    )
    assign_role_to_user(
        review_admin.id, "ADMIN", admin_sub_role="ADMIN_COURSE_REVIEW", session=sess
    )

    # 4. Teaching Assignment Admin
    teach_admin = register_user(
        f"teach_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Teaching Admin", session=sess
    )
    assign_role_to_user(
        teach_admin.id, "ADMIN", admin_sub_role="ADMIN_TEACHING_ASSIGNMENT", session=sess
    )

    # 5. Regular Student
    student = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student", session=sess
    )

    sess.commit()

    return {
        "primary_admin": primary_admin,
        "sys_admin": sys_admin,
        "review_admin": review_admin,
        "teach_admin": teach_admin,
        "student": student,
    }


def test_primary_admin_can_broadcast_all_categories(app: Flask, rbac_env: dict[str, Any]) -> None:
    """ADMIN_PRIMARY can broadcast across SYSTEM, ACADEMIC, MAINTENANCE, EVENT."""
    sess: Session = db.session
    actor = rbac_env["primary_admin"]

    for cat in ("SYSTEM", "ACADEMIC", "MAINTENANCE", "EVENT"):
        count, is_replay = broadcast_system_notification(
            actor=actor,
            title=f"Primary Broadcast {cat}",
            body=f"Broadcast message for category {cat}",
            category=cat,
            session=sess,
        )
        assert count >= 0
        assert is_replay is False


def test_system_monitoring_admin_can_broadcast_system(app: Flask, rbac_env: dict[str, Any]) -> None:
    """ADMIN_SYSTEM_MONITORING can broadcast category SYSTEM."""
    sess: Session = db.session
    actor = rbac_env["sys_admin"]

    count, is_replay = broadcast_system_notification(
        actor=actor,
        title="System Notice",
        body="Server high load warning",
        category="SYSTEM",
        session=sess,
    )
    assert count >= 0
    assert is_replay is False


def test_system_monitoring_admin_forbidden_on_non_system(
    app: Flask, rbac_env: dict[str, Any]
) -> None:
    """ADMIN_SYSTEM_MONITORING is forbidden (403) from broadcasting ACADEMIC or MAINTENANCE."""
    sess: Session = db.session
    actor = rbac_env["sys_admin"]

    for cat in ("ACADEMIC", "MAINTENANCE", "EVENT"):
        with pytest.raises(ForbiddenError) as exc_info:
            broadcast_system_notification(
                actor=actor,
                title=f"Attempt {cat}",
                body="Should be blocked",
                category=cat,
                session=sess,
            )
        assert (
            "giám sát hệ thống" in str(exc_info.value).lower()
            or "quyền" in str(exc_info.value).lower()
        )


def test_other_sub_admins_and_students_forbidden(app: Flask, rbac_env: dict[str, Any]) -> None:
    """ADMIN_COURSE_REVIEW, ADMIN_TEACHING_ASSIGNMENT, and students are forbidden on all broadcasts."""
    sess: Session = db.session

    for actor_key in ("review_admin", "teach_admin", "student"):
        actor = rbac_env[actor_key]
        with pytest.raises(ForbiddenError):
            broadcast_system_notification(
                actor=actor,
                title="Unauthorized Broadcast",
                body="Should be blocked",
                category="SYSTEM",
                session=sess,
            )


def test_rest_api_broadcast_rbac(app: Flask, client: FlaskClient, rbac_env: dict[str, Any]) -> None:
    """REST API endpoint POST /api/admin/notifications/broadcast enforces 2-tier RBAC."""
    primary_admin = rbac_env["primary_admin"]
    sys_admin = rbac_env["sys_admin"]
    review_admin = rbac_env["review_admin"]

    # 1. Primary admin broadcasting ACADEMIC -> 200
    token_primary = create_token_pair(primary_admin)["access_token"]
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Academic Info", "body": "Class starts Monday", "category": "ACADEMIC"},
        headers={"Authorization": f"Bearer {token_primary}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True

    # 2. SysMon admin broadcasting SYSTEM -> 200
    token_sys = create_token_pair(sys_admin)["access_token"]
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Maintenance Notice", "body": "System restart", "category": "SYSTEM"},
        headers={"Authorization": f"Bearer {token_sys}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True

    # 3. SysMon admin broadcasting ACADEMIC -> 403
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Academic Info", "body": "Class starts Monday", "category": "ACADEMIC"},
        headers={"Authorization": f"Bearer {token_sys}"},
    )
    assert resp.status_code == 403

    # 4. Course Review admin broadcasting SYSTEM -> 403
    token_review = create_token_pair(review_admin)["access_token"]
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Review Notice", "body": "Course review alert", "category": "SYSTEM"},
        headers={"Authorization": f"Bearer {token_review}"},
    )
    assert resp.status_code == 403
