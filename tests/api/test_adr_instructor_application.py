"""Tests for ADR-01, ADR-02, ADR-03: Zero Internal PK leakage in Instructor Applications."""

import json

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import InstructorApplication, User
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import (
    assign_role_to_user,
    get_instructor_application,
    register_user,
    review_instructor_application,
)


@pytest.fixture
def student_user(app: Flask) -> User:
    sess = db.session
    u = register_user(
        email="adr.student@example.edu.vn",
        password="Password123!",
        display_name="ADR Student",
        session=sess,
    )
    assign_role_to_user(u.id, "STUDENT", session=sess)
    sess.commit()
    return u


@pytest.fixture
def admin_user(app: Flask) -> User:
    sess = db.session
    u = register_user(
        email="adr.admin@example.edu.vn",
        password="Password123!",
        display_name="ADR Admin",
        session=sess,
    )
    assign_role_to_user(u.id, "ADMIN", session=sess)
    sess.commit()
    return u


def _auth_headers(user: User) -> dict[str, str]:
    tokens = create_token_pair(user)
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json",
    }


def test_adr03_service_resolves_application_by_uuid_and_int(
    app: Flask, admin_user: User, student_user: User
):
    """get_instructor_application and review_instructor_application resolve via public UUIDv5."""
    sess: Session = db.session
    app_record = InstructorApplication(
        applicant_user_id=student_user.id,
        status="PENDING",
        application_note=json.dumps({"statement": "I want to teach Python"}),
    )
    sess.add(app_record)
    sess.commit()

    pub_uuid = app_record.public_id
    pub_uuid_str = str(pub_uuid)

    # 1. Resolve by int
    by_int = get_instructor_application(app_record.id, session=sess)
    assert by_int is not None
    assert by_int.id == app_record.id

    # 2. Resolve by UUID object
    by_uuid = get_instructor_application(pub_uuid, session=sess)
    assert by_uuid is not None
    assert by_uuid.id == app_record.id

    # 3. Resolve by UUID string
    by_str = get_instructor_application(pub_uuid_str, session=sess)
    assert by_str is not None
    assert by_str.id == app_record.id

    # 4. Review using UUID string
    reviewed = review_instructor_application(
        application_id=pub_uuid_str,
        admin_user_id=admin_user.id,
        action="approve",
        reason="Excellent profile",
        session=sess,
    )
    assert reviewed.status == "APPROVED"
    assert reviewed.public_id == pub_uuid


def test_adr01_api_admin_uses_uuid_and_does_not_leak_pk(
    app: Flask, client: FlaskClient, admin_user: User, student_user: User
):
    """GET and POST /api/admin/instructor-applications routes use public_id."""
    sess: Session = db.session
    app_record = InstructorApplication(
        applicant_user_id=student_user.id,
        status="PENDING",
        application_note=json.dumps({"statement": "Teaching experience"}),
    )
    sess.add(app_record)
    sess.commit()

    pub_id_str = str(app_record.public_id)

    # List applications
    resp_list = client.get("/api/admin/instructor-applications", headers=_auth_headers(admin_user))
    assert resp_list.status_code == 200
    apps = resp_list.json["applications"]
    target_app = next((a for a in apps if a["id"] == pub_id_str), None)
    assert target_app is not None
    assert target_app["id"] == pub_id_str
    # Verify no raw integer ID leaks
    assert not isinstance(target_app["id"], int)
    assert target_app["applicant_user_id"] == str(student_user.public_id)

    # Detail application by UUID
    resp_detail = client.get(
        f"/api/admin/instructor-applications/{pub_id_str}",
        headers=_auth_headers(admin_user),
    )
    assert resp_detail.status_code == 200
    assert resp_detail.json["id"] == pub_id_str
    assert resp_detail.json["applicant_user_id"] == str(student_user.public_id)

    # Review application by UUID
    resp_rev = client.post(
        f"/api/admin/instructor-applications/{pub_id_str}/review",
        json={"action": "approve", "reason": "Approved via UUID route"},
        headers=_auth_headers(admin_user),
    )
    assert resp_rev.status_code == 200
    assert resp_rev.json["application_id"] == pub_id_str
    assert resp_rev.json["status"] == "APPROVED"
