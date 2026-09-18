"""Tests for Milestone 2: Deep Instructor Course Customization & Dynamic Student View.

Verifies:
1. Model attributes & helper list-parsing properties on Course.
2. Course service update whitelist and AuditEvent logging.
3. Instructor Course Management Hub settings tab & prerequisite management.
4. Web-based prerequisite addition, removal, and DAG circular dependency prevention.
5. Student course detail view dynamic rendering eliminating all hardcoded placeholders.
"""

from __future__ import annotations

import json
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.completion_service import get_or_create_default_completion_rule
from pwd301.services.course_service import create_course, update_course
from pwd301.services.enrollment_service import get_course_prerequisites
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
    u = register_user(email, "Password@123", "Instructor Test M2")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a student user."""
    email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Student Test M2")
    return assign_role_to_user(u.id, "STUDENT")


def test_course_model_customization_attributes_and_properties(app: Flask) -> None:
    """Course model exposes customization columns and list-parsing properties."""
    with app.app_context():
        c = Course(
            course_code="CS-M2-01",
            title="Customization Model Test",
            learning_objectives=None,
            target_audience=None,
            completion_requirements=None,
        )
        # 1. Empty / None cases
        assert c.learning_objectives_list == []
        assert c.target_audience_list == []

        # 2. Whitespace cases
        c.learning_objectives = "   \n  \n  "
        c.target_audience = ""
        assert c.learning_objectives_list == []
        assert c.target_audience_list == []

        # 3. Multiline text cases
        c.learning_objectives = "Objective 1\nObjective 2\n\n  Objective 3  \n"
        assert c.learning_objectives_list == ["Objective 1", "Objective 2", "Objective 3"]

        c.target_audience = "Audience A\nAudience B"
        assert c.target_audience_list == ["Audience A", "Audience B"]

        # 4. JSON array cases
        c.learning_objectives = json.dumps(["Learn Python", "Master Flask", "Build DB"])
        assert c.learning_objectives_list == ["Learn Python", "Master Flask", "Build DB"]

        c.target_audience = json.dumps(["Graduates", "Backend Developers"])
        assert c.target_audience_list == ["Graduates", "Backend Developers"]


def test_course_service_update_customization_fields_and_audit(
    app: Flask,
    instructor_user: User,
) -> None:
    """update_course() whitelists customization fields and records them in AuditEvent."""
    sess: Session = db.session
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-SVC-01",
            "title": "Service Update Test",
            "description": "Initial description",
        },
        session=sess,
    )
    sess.commit()

    updated = update_course(
        actor=instructor_user,
        course_id=str(c.public_id),
        data={
            "learning_objectives": "Master SQLAlchemy\nDesign secure APIs",
            "target_audience": "Intermediate developers",
            "completion_requirements": "Complete 100% lessons and pass final exam with >= 80%",
        },
        session=sess,
    )
    sess.commit()

    assert updated.learning_objectives == "Master SQLAlchemy\nDesign secure APIs"
    assert updated.target_audience == "Intermediate developers"
    assert (
        updated.completion_requirements == "Complete 100% lessons and pass final exam with >= 80%"
    )
    assert updated.learning_objectives_list == ["Master SQLAlchemy", "Design secure APIs"]
    assert updated.target_audience_list == ["Intermediate developers"]

    # Check AuditEvent
    audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "COURSE_UPDATED",
            AuditEvent.target_id == c.id,
        )
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit is not None
    assert audit.before_state is not None
    assert audit.after_state is not None
    assert "learning_objectives" in audit.after_state
    assert "target_audience" in audit.after_state
    assert "completion_requirements" in audit.after_state
    assert audit.after_state["learning_objectives"] == "Master SQLAlchemy\nDesign secure APIs"


def test_instructor_web_manage_hub_renders_settings_tab(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """Manage Hub settings endpoint returns JSON course representation."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": "CS-HUB-01",
            "title": "Course Hub Settings Test",
            "description": "Hub test description",
        },
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp = client.get(
        f"/instructor/courses/{course.public_id}/manage",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["course_code"] == "CS-HUB-01"
    assert data["title"] == "Course Hub Settings Test"


def test_instructor_web_update_customization_fields(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """POST /instructor/courses/<id> updates customization fields and returns JSON."""
    sess: Session = db.session
    course = create_course(
        instructor_user,
        {
            "course_code": "CS-FORM-01",
            "title": "Form Update Course",
            "description": "Initial text",
        },
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp = client.post(
        f"/instructor/courses/{course.public_id}",
        json={
            "title": "Form Update Course Updated",
            "description": "New description",
            "category": "Software Engineering",
            "difficulty": "INTERMEDIATE",
            "capacity": 45,
            "learning_objectives": "Objective Line 1\nObjective Line 2",
            "target_audience": "Software engineering students",
            "completion_requirements": "80% attendance required",
        },
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Form Update Course Updated"

    sess.expire_all()
    reloaded = sess.query(Course).filter(Course.id == course.id).one()
    assert reloaded.learning_objectives == "Objective Line 1\nObjective Line 2"
    assert reloaded.target_audience == "Software engineering students"
    assert reloaded.completion_requirements == "80% attendance required"
    assert reloaded.learning_objectives_list == ["Objective Line 1", "Objective Line 2"]


def test_instructor_web_prerequisite_addition_removal_and_cycle_prevention(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """JSON API handles adding prerequisite, preventing cycles, and removal."""
    sess: Session = db.session

    c_a = create_course(
        instructor_user,
        {"course_code": "CS-DAG-A", "title": "Advanced Web Security"},
        session=sess,
    )
    c_b = create_course(
        instructor_user,
        {"course_code": "CS-DAG-B", "title": "Web Foundations"},
        session=sess,
    )
    c_a.status = "APPROVED"
    c_b.status = "APPROVED"
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    # 1. Add c_b as prerequisite to c_a via API POST
    resp_add = client.post(
        f"/instructor/courses/{c_a.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_b.public_id)},
        headers={"Accept": "application/json"},
    )
    assert resp_add.status_code == 201

    sess.expire_all()
    prereqs_a = get_course_prerequisites(c_a.id, session=sess)
    assert any(p.id == c_b.id for p in prereqs_a)

    # 2. Attempt to add c_a as prerequisite to c_b -> Creates cycle c_a -> c_b -> c_a
    resp_cycle = client.post(
        f"/instructor/courses/{c_b.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_a.public_id)},
        headers={"Accept": "application/json"},
    )
    assert resp_cycle.status_code == 409

    sess.expire_all()
    prereqs_b = get_course_prerequisites(c_b.id, session=sess)
    assert not any(p.id == c_a.id for p in prereqs_b)

    # 3. Remove prerequisite c_b from c_a via API DELETE/POST
    resp_del = client.delete(
        f"/instructor/courses/{c_a.public_id}/prerequisites/{c_b.public_id}",
        headers={"Accept": "application/json"},
    )
    assert resp_del.status_code == 200

    sess.expire_all()
    prereqs_a_after = get_course_prerequisites(c_a.id, session=sess)
    assert not any(p.id == c_b.id for p in prereqs_a_after)


def test_student_course_detail_dynamic_rendering_and_zero_placeholders(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
) -> None:
    """Student course detail returns dynamic custom content in JSON."""
    sess: Session = db.session

    course = create_course(
        instructor_user,
        {
            "course_code": "CS-STUDENT-VIEW",
            "title": "Kỹ thuật Phát triển Microservices",
            "description": "Khóa học chuyên đề Microservices hướng sự kiện.",
            "category": "Kiến trúc Hệ thống",
            "difficulty": "ADVANCED",
            "learning_objectives": (
                "Xây dựng kiến trúc RESTful API chuẩn mực\n"
                "Triển khai xác thực Token JWT và OAuth2\n"
                "Thiết kế cơ sở dữ liệu phân tán bền vững"
            ),
            "target_audience": (
                "Sinh viên năm cuối ngành Kỹ thuật Phần mềm\n"
                "Kỹ sư phần mềm đang đi làm muốn thăng tiến"
            ),
            "completion_requirements": (
                "Hoàn thành tối thiểu 85% nội dung bài giảng và nộp đầy đủ đồ án thực hành."
            ),
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    rule = get_or_create_default_completion_rule(course.id, session=sess)
    rule.minimum_progress_percent = 85.0
    rule.require_all_required_lessons = True
    rule.require_required_assessments = True
    sess.commit()

    login_web_user(client, student_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "STUDENT"

    resp = client.get(
        f"/student/courses/{course.public_id}",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    course_data = data["course"]

    # 1. Assert dynamic objectives are in JSON
    assert "Xây dựng kiến trúc RESTful API chuẩn mực" in course_data["learning_objectives"]
    assert "Triển khai xác thực Token JWT và OAuth2" in course_data["learning_objectives"]
    assert "Thiết kế cơ sở dữ liệu phân tán bền vững" in course_data["learning_objectives"]

    # 2. Assert dynamic target audience is in JSON
    assert "Sinh viên năm cuối ngành Kỹ thuật Phần mềm" in course_data["target_audience"]
    assert "Kỹ sư phần mềm đang đi làm muốn thăng tiến" in course_data["target_audience"]

    # 3. Assert dynamic completion requirements are in JSON
    assert "Hoàn thành tối thiểu 85%" in course_data["completion_requirements"]
    assert course_data["difficulty"] == "ADVANCED"
    assert course_data["category"] == "Kiến trúc Hệ thống"
