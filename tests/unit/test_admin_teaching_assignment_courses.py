"""Tests for F07: Teaching Assignment Course Access (RBAC).

Verifies:
- ADMIN_TEACHING_ASSIGNMENT can access GET /admin/courses and GET /admin/courses/<course_id>.
- ADMIN_TEACHING_ASSIGNMENT can access GET /api/admin/courses and GET /api/admin/courses/<course_id>.
- ADMIN_COURSE_REVIEW and ADMIN_PRIMARY retain full access (200 OK).
- Other sub-roles without COURSE_REVIEW or TEACHING_ASSIGNMENT (e.g., ADMIN_SYSTEM_MONITORING) receive 403 Forbidden.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.identity import Role, User, UserRole
from backend.seeds.baseline import seed_baseline
from backend.services.course_service import create_course
from backend.services.jwt_auth_service import create_token_pair
from backend.services.session_auth_service import create_auth_session
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def f07_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, published course, and admins with different sub-roles."""
    sess: Session = db.session
    seed_baseline(sess)

    admin_role = sess.query(Role).filter_by(code="ADMIN").one()

    # Instructor & Course
    inst = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor F07", session=sess
    )
    assign_role_to_user(inst.id, "INSTRUCTOR", session=sess)

    course = create_course(
        actor=inst,
        data={
            "course_code": f"F07-{uuid.uuid4().hex[:4].upper()}",
            "title": "Teaching Assignment Target Course",
            "category": "Testing",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    # 1. Primary Admin
    primary_admin = register_user(
        f"primary_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Primary Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=primary_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Test Primary",
        )
    )

    # 2. Teaching Assignment Admin
    teach_admin = register_user(
        f"teach_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Teaching Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=teach_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_TEACHING_ASSIGNMENT | Test Teaching Assign",
        )
    )

    # 3. Course Review Admin
    review_admin = register_user(
        f"crev_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Course Review Admin",
        session=sess,
    )
    sess.add(
        UserRole(
            user_id=review_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_COURSE_REVIEW | Test Course Review",
        )
    )

    # 4. System Monitoring Admin (Unauthorized for course management)
    sys_admin = register_user(
        f"sysmon_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "SysMon Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=sys_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_SYSTEM_MONITORING | Test SysMon",
        )
    )

    sess.commit()

    return {
        "course": course,
        "primary_admin": primary_admin,
        "teach_admin": teach_admin,
        "review_admin": review_admin,
        "sys_admin": sys_admin,
    }


def _login_web_session(client: FlaskClient, user: User) -> None:
    _, raw_key = create_auth_session(user, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = user.auth_version
        sess["auth_source"] = "SESSION"


def test_teaching_admin_web_course_access(
    app: Flask, client: FlaskClient, f07_env: dict[str, Any]
) -> None:
    """ADMIN_TEACHING_ASSIGNMENT can access Web GET /admin/courses and GET /admin/courses/<id>."""
    teach_admin = f07_env["teach_admin"]
    course = f07_env["course"]

    _login_web_session(client, teach_admin)

    # List courses
    resp_list = client.get("/admin/courses")
    assert resp_list.status_code == 200
    data_list = resp_list.get_json()
    assert "courses" in data_list

    # Course detail
    resp_detail = client.get(f"/admin/courses/{course.public_id}")
    assert resp_detail.status_code == 200
    data_detail = resp_detail.get_json()
    assert data_detail["course_id"] == str(course.public_id)


def test_teaching_admin_api_course_access(
    app: Flask, client: FlaskClient, f07_env: dict[str, Any]
) -> None:
    """ADMIN_TEACHING_ASSIGNMENT can access REST API GET /api/admin/courses and GET /api/admin/courses/<id>."""
    teach_admin = f07_env["teach_admin"]
    course = f07_env["course"]

    token = create_token_pair(teach_admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List courses
    resp_list = client.get("/api/admin/courses", headers=headers)
    assert resp_list.status_code == 200
    data_list = resp_list.get_json()
    assert "courses" in data_list

    # Course detail
    resp_detail = client.get(f"/api/admin/courses/{course.public_id}", headers=headers)
    assert resp_detail.status_code == 200
    data_detail = resp_detail.get_json()
    assert data_detail["course_id"] == str(course.public_id)


def test_unauthorized_sub_role_blocked(
    app: Flask, client: FlaskClient, f07_env: dict[str, Any]
) -> None:
    """ADMIN_SYSTEM_MONITORING is strictly forbidden (403) from accessing courses list and detail."""
    sys_admin = f07_env["sys_admin"]
    course = f07_env["course"]

    # 1. Web session check
    _login_web_session(client, sys_admin)
    resp_web_list = client.get("/admin/courses")
    assert resp_web_list.status_code == 403

    resp_web_detail = client.get(f"/admin/courses/{course.public_id}")
    assert resp_web_detail.status_code == 403

    # 2. REST API check
    token = create_token_pair(sys_admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp_api_list = client.get("/api/admin/courses", headers=headers)
    assert resp_api_list.status_code == 403

    resp_api_detail = client.get(f"/api/admin/courses/{course.public_id}", headers=headers)
    assert resp_api_detail.status_code == 403


def test_course_review_and_primary_admin_access(
    app: Flask, client: FlaskClient, f07_env: dict[str, Any]
) -> None:
    """ADMIN_PRIMARY and ADMIN_COURSE_REVIEW retain 200 OK on both Web and API endpoints."""
    course = f07_env["course"]

    for admin_key in ("primary_admin", "review_admin"):
        admin_user = f07_env[admin_key]
        token = create_token_pair(admin_user)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp_list = client.get("/api/admin/courses", headers=headers)
        assert resp_list.status_code == 200

        resp_detail = client.get(f"/api/admin/courses/{course.public_id}", headers=headers)
        assert resp_detail.status_code == 200
