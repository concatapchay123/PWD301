import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, CoursePrerequisite
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_prerequisite_same_instructor_adds_directly(client: FlaskClient, instructor_user: User):
    """When same instructor owns both courses, prerequisite is added directly."""
    sess = db.session
    c1 = Course(
        course_code=f"PRQ_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"PRQ_{uuid.uuid4().hex[:4]}",
        title="Prereq Course 1",
        description="Intro",
        category="CNTT",
        difficulty="BEGINNER",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    c2 = Course(
        course_code=f"PRQ_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"PRQ_{uuid.uuid4().hex[:4]}",
        title="Advanced Course 2",
        description="Advanced",
        category="CNTT",
        difficulty="INTERMEDIATE",
        owner_instructor_id=instructor_user.id,
        status="DRAFT",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add_all([c1, c2])
    sess.commit()

    login_web_user(client, instructor_user)

    res = client.post(
        f"/instructor/courses/{c2.id}/prerequisites",
        json={"prerequisite_course_id": c1.id},
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["direct"] is True
    assert data["status"] == "success"

    link = (
        sess.query(CoursePrerequisite)
        .filter_by(course_id=c2.id, prerequisite_course_id=c1.id)
        .first()
    )
    assert link is not None


def test_prerequisite_cross_instructor_uses_course_admin_aggregate(
    client: FlaskClient, instructor_user: User
):
    """Published prerequisites join the same aggregate for one administrator review."""
    sess = db.session
    u2 = register_user(
        f"instructor2_{uuid.uuid4().hex[:8]}@example.com", "Password@123", "Instructor Two"
    )
    inst2 = assign_role_to_user(u2.id, "INSTRUCTOR")

    c_target = Course(
        course_code=f"TGT_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"TGT_{uuid.uuid4().hex[:4]}",
        title="Target Course",
        category="CNTT",
        owner_instructor_id=instructor_user.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    c_prereq = Course(
        course_code=f"PRQ_{uuid.uuid4().hex[:4]}",
        course_code_normalized=f"PRQ_{uuid.uuid4().hex[:4]}",
        title="Other Instructor Prereq",
        category="CNTT",
        owner_instructor_id=inst2.id,
        status="PUBLISHED",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add_all([c_target, c_prereq])
    sess.commit()

    # Log in as instructor_user (owner of target course)
    login_web_user(client, instructor_user)

    res = client.post(
        f"/instructor/courses/{c_target.id}/prerequisites",
        json={"prerequisite_course_id": c_prereq.id, "reason": "Academic requirement"},
    )
    assert res.status_code == 200, res.get_json()
    data = res.get_json()
    assert data["is_draft"] is True
    assert data["pending_approval"] is False
    request = sess.get(CourseChangeRequest, data["change_request_id"])
    assert request.change_type == "COURSE_VERSION_CHANGESET" and request.status == "DRAFT"
    assert sess.query(CoursePrerequisite).filter_by(course_id=c_target.id).count() == 0

    login_web_user(client, inst2)
    incoming = client.get("/instructor/prerequisite-requests")
    assert incoming.status_code == 200
    assert incoming.get_json()["incoming"] == []
    forbidden_alias = client.post(
        f"/instructor/prerequisite-requests/{request.id}/review", json={"action": "approve"}
    )
    assert forbidden_alias.status_code == 404

    from pwd301.services.lesson_service import (
        approve_course_change_request,
        submit_course_changeset,
    )

    admin = register_user(
        f"prereq_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Prerequisite Reviewer"
    )
    admin = assign_role_to_user(admin.id, "ADMIN")
    submitted = submit_course_changeset(instructor_user, c_target.id, {}, session=sess)
    approve_course_change_request(admin, submitted.id, session=sess)
    sess.commit()
    link = (
        sess.query(CoursePrerequisite)
        .filter_by(course_id=c_target.id, prerequisite_course_id=c_prereq.id)
        .one()
    )
    assert link.approval_status == "APPROVED"
