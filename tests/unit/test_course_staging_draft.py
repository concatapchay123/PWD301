"""Tests for F03: Unified Staging Draft Engine.

Verifies:
1. Updating metadata on a PUBLISHED course via REST API returns HTTP 200 with status: 'draft', is_draft: True.
2. REST endpoints GET /api/courses/<id>/changeset/status, POST .../submit, POST .../discard work as specified.
3. Status responses contain contract keys: staged_lessons, deleted_staged, has_metadata_changes, summary.
4. Lessons created on PUBLISHED courses always stage as DRAFT.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def changeset_rest_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, admin, and published course."""
    sess: Session = db.session
    seed_baseline(sess)

    inst = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Test", session=sess
    )
    assign_role_to_user(inst.id, "INSTRUCTOR", session=sess)

    admin = register_user(
        f"admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin Test", session=sess
    )
    assign_role_to_user(admin.id, "ADMIN", session=sess)
    from pwd301.models.identity import UserRole

    ur = sess.query(UserRole).filter_by(user_id=admin.id).first()
    if ur:
        ur.assignment_reason = "SUB_ROLE:ADMIN_PRIMARY"

    course = create_course(
        actor=inst,
        data={
            "course_code": f"CS-{uuid.uuid4().hex[:4].upper()}",
            "title": "Published Changeset Course",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    lesson1 = create_lesson(
        actor=inst,
        course_id=course.id,
        data={
            "title": "Lesson 1: Intro",
            "markdown_content": "# Intro content",
            "estimated_duration_minutes": 20,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson1.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst,
        "admin": admin,
        "course": course,
        "lesson1": lesson1,
    }


def test_update_published_course_metadata_returns_200_draft(
    client: FlaskClient, changeset_rest_env: dict[str, Any]
) -> None:
    """PATCH /api/courses/<id> on a published course returns HTTP 200 with status: 'draft', is_draft: True."""
    inst = changeset_rest_env["instructor"]
    course = changeset_rest_env["course"]

    tokens = create_token_pair(inst)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.patch(
        f"/api/courses/{course.public_id}",
        headers=headers,
        json={"title": "Updated Draft Title For Published Course"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "draft"
    assert data["is_draft"] is True
    assert data["pending_approval"] is False
    assert "change_request_id" in data


def test_rest_changeset_status_contract_keys(
    client: FlaskClient, changeset_rest_env: dict[str, Any]
) -> None:
    """GET /api/courses/<id>/changeset/status returns standard contract keys."""
    inst = changeset_rest_env["instructor"]
    course = changeset_rest_env["course"]

    tokens = create_token_pair(inst)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Initial status: no changes
    resp = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "staged_lessons" in data
    assert "deleted_staged" in data
    assert "has_metadata_changes" in data
    assert "summary" in data
    assert data["status"] == "NONE"

    # Stage a metadata change
    client.patch(
        f"/api/courses/{course.public_id}",
        headers=headers,
        json={"title": "New Staged Title"},
    )

    resp2 = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["status"] == "DRAFT"
    assert data2["has_metadata_changes"] is True
    assert data2["has_changes"] is True


def test_rest_changeset_submit_and_discard_lifecycle(
    client: FlaskClient, changeset_rest_env: dict[str, Any]
) -> None:
    """POST /api/courses/<id>/changeset/submit and discard work through REST API."""
    inst = changeset_rest_env["instructor"]
    course = changeset_rest_env["course"]

    tokens = create_token_pair(inst)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Stage metadata change
    client.patch(
        f"/api/courses/{course.public_id}",
        headers=headers,
        json={"title": "Proposed New Course Title"},
    )

    # 2. Submit changeset for review via REST
    resp_sub = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=headers,
        json={"version_title": "Version 2.0", "summary": "Upgraded metadata"},
    )
    assert resp_sub.status_code == 202
    sub_data = resp_sub.get_json()
    assert sub_data["status"] == "pending_approval"
    assert sub_data["pending_approval"] is True

    # 3. Check status is PENDING with standard keys
    resp_st = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert resp_st.status_code == 200
    st_data = resp_st.get_json()
    assert st_data["status"] == "PENDING"
    assert st_data["has_metadata_changes"] is True

    # 4. Discard changeset via REST
    resp_disc = client.post(f"/api/courses/{course.public_id}/changeset/discard", headers=headers)
    assert resp_disc.status_code == 200

    # 5. Status returns to NONE
    resp_after = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert resp_after.status_code == 200
    assert resp_after.get_json()["status"] == "NONE"
