"""Tests for Instructor Course Creation Web Flow, Soft-Deleted Title Reuse, and Error Resilience."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy.exc
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course, trash_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an instructor user."""
    email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_create_course_reusing_soft_deleted_title(app: Flask, instructor_user: User) -> None:
    """Canonical invariant: Soft-deleted course title/code CAN be reused by active courses."""
    sess: Session = db.session

    # 1. Create a course and soft-delete it
    c1 = create_course(
        instructor_user,
        {
            "course_code": "CS-REUSE-01",
            "title": "Khóa Học Làm Người",
            "description": "Old deleted course",
        },
        session=sess,
    )
    sess.commit()

    trash_course(instructor_user, str(c1.public_id), reason="Trashing course", session=sess)
    sess.commit()

    assert c1.deleted_at is not None
    assert c1.status == "TRASH"

    # 2. Create another course with the EXACT SAME title (case-insensitive normalized)
    c2 = create_course(
        instructor_user,
        {
            "course_code": "CS-REUSE-02",
            "title": "khóa học làm người",
            "description": "New active course with same title",
        },
        session=sess,
    )
    sess.commit()

    assert c2.id is not None
    assert c2.title_normalized == "khóa học làm người"
    assert c2.status == "DRAFT"
    assert c2.deleted_at is None


def test_instructor_web_create_course_success(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """POST /instructor/courses with valid data returns 201 JSON with created course."""
    login_web_user(client, instructor_user)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"

    resp = client.post(
        "/instructor/courses",
        data={
            "course_code": "NEW-WEB-101",
            "title": "Lập Trình Web Hiện Đại",
            "description": "Khóa học thử nghiệm",
            "category": "Phát triển Web",
            "difficulty": "BEGINNER",
        },
    )

    assert resp.status_code == 201
    assert resp.is_json
    data = resp.get_json()
    assert data["course_code"] == "NEW-WEB-101"
    assert data["title"] == "Lập Trình Web Hiện Đại"


def test_instructor_web_create_course_duplicate_active_title_graceful_flash(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """Duplicate active title must not return 500; must return 409 JSON error."""
    create_course(
        instructor_user,
        {
            "course_code": "EXISTING-101",
            "title": "Khóa Học Đang Hoạt Động",
            "description": "Active course",
        },
    )

    login_web_user(client, instructor_user)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"

    # Attempt to create duplicate active course
    resp = client.post(
        "/instructor/courses",
        data={
            "course_code": "ANOTHER-102",
            "title": "khóa học đang hoạt động",  # Same title in lower case
            "description": "Attempted duplicate",
        },
    )

    assert resp.status_code == 409
    assert resp.is_json
    data = resp.get_json()
    assert data["error"]["code"] == "CONFLICT"


def test_instructor_web_create_course_db_integrity_error_graceful_flash(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB IntegrityError must not return 500; must return 409 JSON error."""
    login_web_user(client, instructor_user)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"

    def mock_create(*args: object, **kwargs: object) -> None:
        raise sqlalchemy.exc.IntegrityError("INSERT...", {}, Exception("Duplicate key"))

    monkeypatch.setattr("pwd301.blueprints.instructor.routes.create_course", mock_create)

    resp = client.post(
        "/instructor/courses",
        data={"course_code": "DUP-101", "title": "Dup Title"},
    )

    assert resp.status_code == 409
    assert resp.is_json
    data = resp.get_json()
    assert data["error"]["code"] == "CONFLICT"


def test_post_course_settings_update_route_success(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """POST /instructor/courses/<course_id> must NOT return 405.
    Must update metadata and return 200 JSON.
    """
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {"course_code": "UPD-101", "title": "Before Update Course"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as s:
        s["active_role"] = "INSTRUCTOR"

    resp = client.post(
        f"/instructor/courses/{course.public_id}",
        data={
            "title": "After Update Course Title",
            "description": "Updated course description",
            "category": "Trí tuệ nhân tạo",
            "capacity": "45",
        },
    )

    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["title"] == "After Update Course Title"

    sess.refresh(course)
    assert course.title == "After Update Course Title"
    assert course.category == "Trí tuệ nhân tạo"
    assert course.capacity == 45


def test_instructor_publish_draft_course_warning(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """Instructor calling publish on DRAFT course gets 409 JSON error, not crash."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {"course_code": "PUB-DRAFT-101", "title": "Draft Course For Publish Test"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as s:
        s["active_role"] = "INSTRUCTOR"

    resp = client.post(
        f"/instructor/courses/{course.public_id}/publish",
    )

    assert resp.status_code == 409
    assert resp.is_json
    data = resp.get_json()
    assert data["error"]["code"] == "COURSE_STATE_VIOLATION"


def test_admin_publish_draft_course_direct_success(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Admin publishing a course can directly advance and publish."""
    sess: Session = db.session
    # Give instructor_user the ADMIN role as well
    assign_role_to_user(instructor_user.id, "ADMIN")
    course = create_course(
        instructor_user,
        {"course_code": "ADMIN-PUB-101", "title": "Admin Direct Publish Course"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as s:
        s["active_role"] = "INSTRUCTOR"

    resp = client.post(
        f"/instructor/courses/{course.public_id}/publish",
    )

    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["status"] == "PUBLISHED"

    sess.refresh(course)
    assert course.status == "PUBLISHED"


def test_admin_actor_can_list_all_courses_in_instructor_courses_endpoint(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Admin actor defaults to assigned courses, but can request scope=all for platform overview."""
    sess: Session = db.session

    # 1. Create a course owned by a regular instructor
    create_course(
        instructor_user,
        {"course_code": "FLOW-TEST-101", "title": "Flow Testing Course"},
        session=sess,
    )
    sess.commit()

    # 2. Create an admin user who does not own the course
    admin_user = register_user(
        f"admin_flow_{uuid.uuid4().hex[:8]}@example.com",
        "Password@123",
        "Admin Flow Test",
        session=sess,
    )
    assign_role_to_user(admin_user.id, "INSTRUCTOR", session=sess)
    assign_role_to_user(admin_user.id, "ADMIN", session=sess)
    sess.commit()

    # Also create 1 course owned by admin
    create_course(
        admin_user,
        {"course_code": "FLOW-ADM-101", "title": "Admin Owned Course"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, admin_user)
    with client.session_transaction() as s:
        s["active_role"] = "INSTRUCTOR"

    # Default scope is 'assigned': admin should only see their own course FLOW-ADM-101
    resp = client.get("/instructor/courses")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["scope"] == "assigned"
    assert data["data"]["is_admin"] is True
    assert data["data"]["assigned_count"] >= 1
    assert data["data"]["total_platform_count"] >= 2

    assigned_codes = [c["course_code"] for c in data["data"]["courses"]]
    assert "FLOW-ADM-101" in assigned_codes
    assert "FLOW-TEST-101" not in assigned_codes

    # Scope 'all': admin can see both FLOW-ADM-101 and FLOW-TEST-101
    resp_all = client.get("/instructor/courses?scope=all")
    assert resp_all.status_code == 200
    data_all = resp_all.get_json()
    assert data_all["data"]["scope"] == "all"
    all_codes = [c["course_code"] for c in data_all["data"]["courses"]]
    assert "FLOW-ADM-101" in all_codes
    assert "FLOW-TEST-101" in all_codes


def test_regular_instructor_cannot_view_all_platform_courses_via_scope(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Non-admin instructor should only ever see their own courses even if requesting scope=all."""
    sess: Session = db.session

    # Create another instructor and course
    other_ins = register_user(
        f"other_ins_{uuid.uuid4().hex[:8]}@example.com",
        "Password@123",
        "Other Instructor",
        session=sess,
    )
    assign_role_to_user(other_ins.id, "INSTRUCTOR", session=sess)
    sess.commit()

    create_course(
        other_ins,
        {"course_code": "OTHER-101", "title": "Other Instructor Course"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as s:
        s["active_role"] = "INSTRUCTOR"

    resp = client.get("/instructor/courses?scope=all")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["is_admin"] is False
    codes = [c["course_code"] for c in data["data"]["courses"]]
    assert "OTHER-101" not in codes

