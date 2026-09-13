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
    """POST /instructor/courses with valid form data redirects to my_courses with success flash."""
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
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Khóa học mới đã được tạo thành công" in html
    assert "NEW-WEB-101" in html


def test_instructor_web_create_course_duplicate_active_title_graceful_flash(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """Duplicate active title must not return 500; must flash error and redirect."""
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
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    # Must NOT be 500 error!
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "500 INTERNAL_ERROR" not in html
    assert "already exists" in html or "đã tồn tại" in html


def test_instructor_web_create_course_db_integrity_error_graceful_flash(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB IntegrityError must not return 500; must flash danger error."""
    login_web_user(client, instructor_user)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"

    def mock_create(*args: object, **kwargs: object) -> None:
        raise sqlalchemy.exc.IntegrityError("INSERT...", {}, Exception("Duplicate key"))

    monkeypatch.setattr("pwd301.blueprints.instructor.routes.create_course", mock_create)

    resp = client.post(
        "/instructor/courses",
        data={"course_code": "DUP-101", "title": "Dup Title"},
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "500 INTERNAL_ERROR" not in html
    assert "trùng lặp" in html or "already exists" in html or "Không thể tạo" in html


def test_post_course_settings_update_route_success(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """POST /instructor/courses/<course_id> must NOT return 405.
    Must update metadata and redirect gracefully.
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
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    # Must be 200 after redirect, NOT 405 Method Not Allowed!
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "405 METHOD_NOT_ALLOWED" not in html
    assert "Cập nhật thông tin khóa học thành công" in html

    sess.refresh(course)
    assert course.title == "After Update Course Title"
    assert course.category == "Trí tuệ nhân tạo"
    assert course.capacity == 45


def test_instructor_publish_draft_course_warning(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """Instructor calling publish on DRAFT course gets graceful warning flash, not crash."""
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
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "405 METHOD_NOT_ALLOWED" not in html
    assert "500 INTERNAL_ERROR" not in html
    assert "cần" in html or "Bản thảo" in html or "xét duyệt" in html


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
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "đã được xuất bản chính thức thành công" in html

    sess.refresh(course)
    assert course.status == "PUBLISHED"
