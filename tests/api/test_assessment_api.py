"""Integration tests for Assessment REST API endpoints (TASK-012)."""

from __future__ import annotations

import re
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002_no_bigint_leaks(data: Any) -> None:
    """Recursively verify that no internal integer PKs or IDs are exposed (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key 'creator_user_id' leaked: {data}"
            assert k != "course_internal_id", f"Internal foreign key leaked: {data}"

            if (
                k
                in (
                    "assessment_id",
                    "course_id",
                    "question_id",
                    "section_id",
                    "assignment_id",
                    "blueprint_id",
                    "rule_id",
                    "public_id",
                )
                and v is not None
            ):
                assert isinstance(v, str), f"Field '{k}' should be string, got {type(v)}: {v}"
                assert UUID_REGEX.match(v), f"Field '{k}' is not a valid UUID: {v}"

            assert_adr002_no_bigint_leaks(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002_no_bigint_leaks(item)


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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor User."""
    u = register_user("assess_api_inst@example.com", "Password@123", "Assessment API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    u = register_user("assess_api_student@example.com", "Password@123", "Student API User")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def instructor_tokens(instructor_user: User) -> dict[str, str]:
    """Generate JWT tokens for instructor."""
    return create_token_pair(instructor_user)


@pytest.fixture
def auth_headers(instructor_tokens: dict[str, str]) -> dict[str, str]:
    """Authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {instructor_tokens['access_token']}"}


@pytest.fixture
def student_tokens(student_user: User) -> dict[str, str]:
    """Generate JWT tokens for student."""
    return create_token_pair(student_user)


@pytest.fixture
def student_headers(student_tokens: dict[str, str]) -> dict[str, str]:
    """Student authorization headers."""
    return {"Authorization": f"Bearer {student_tokens['access_token']}"}


@pytest.fixture
def course(app: Flask, instructor_user: User) -> Course:
    """Create test course."""
    c = create_course(
        instructor_user,
        {
            "course_code": "ASM-API-101",
            "title": "Assessment API Testing Course",
            "summary": "Testing assessment endpoints",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def question(app: Flask, instructor_user: User, course: Course) -> Question:
    """Create test question in course."""
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Sample API Question?",
            "default_points": 2.0,
            "choices": [
                {"content": "Alpha", "is_correct": True, "position": 1},
                {"content": "Beta", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
    )
    db.session.commit()
    return q


def test_create_and_get_assessment(
    client: FlaskClient, auth_headers: dict[str, str], course: Course
) -> None:
    """Test creating an assessment via POST and fetching it via GET."""
    payload = {
        "title": "API Quiz 1",
        "description": "Integration test assessment",
        "assessment_type": "QUIZ",
        "scoring_policy": "HIGHEST",
        "time_limit_minutes": 45,
    }

    # Create via course-scoped endpoint
    res = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json=payload,
        headers=auth_headers,
    )
    assert res.status_code == 201
    created_data = res.get_json()
    assert created_data["title"] == "API Quiz 1"
    assert created_data["status"] == "DRAFT"
    assert_adr002_no_bigint_leaks(created_data)

    assessment_id = created_data["assessment_id"]

    # Fetch via GET
    res_get = client.get(f"/api/assessments/{assessment_id}", headers=auth_headers)
    assert res_get.status_code == 200
    get_data = res_get.get_json()
    assert get_data["assessment_id"] == assessment_id
    assert get_data["title"] == "API Quiz 1"
    assert_adr002_no_bigint_leaks(get_data)


def test_patch_assessment(
    client: FlaskClient, auth_headers: dict[str, str], course: Course
) -> None:
    """Test updating assessment metadata via PATCH."""
    res_create = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json={"title": "Original Title", "assessment_type": "QUIZ"},
        headers=auth_headers,
    )
    assert res_create.status_code == 201
    asm_id = res_create.get_json()["assessment_id"]

    res_patch = client.patch(
        f"/api/assessments/{asm_id}",
        json={"title": "Patched Title", "time_limit_minutes": 60},
        headers=auth_headers,
    )
    assert res_patch.status_code == 200
    patch_data = res_patch.get_json()
    assert patch_data["title"] == "Patched Title"
    assert patch_data["time_limit_minutes"] == 60
    assert_adr002_no_bigint_leaks(patch_data)


def test_sections_api(client: FlaskClient, auth_headers: dict[str, str], course: Course) -> None:
    """Test creating and deleting sections via REST API."""
    res_create = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json={"title": "Section Exam", "assessment_type": "FINAL"},
        headers=auth_headers,
    )
    asm_id = res_create.get_json()["assessment_id"]

    # Create Section
    res_sec = client.post(
        f"/api/assessments/{asm_id}/sections",
        json={"title": "Section 1", "position": 1, "instructions": "Read carefully"},
        headers=auth_headers,
    )
    assert res_sec.status_code == 201
    sec_data = res_sec.get_json()
    assert sec_data["title"] == "Section 1"
    assert_adr002_no_bigint_leaks(sec_data)

    sec_id = sec_data["section_id"]

    # Delete Section
    res_del = client.delete(
        f"/api/assessments/{asm_id}/sections/{sec_id}",
        headers=auth_headers,
    )
    assert res_del.status_code == 200
    assert res_del.get_json()["message"] == "Section deleted successfully."


def test_question_assignment_and_publish_flow(
    client: FlaskClient,
    auth_headers: dict[str, str],
    course: Course,
    question: Question,
) -> None:
    """Test assigning a question, publishing the assessment, and unassignment."""
    res_create = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json={"title": "Flow Quiz", "assessment_type": "QUIZ"},
        headers=auth_headers,
    )
    asm_id = res_create.get_json()["assessment_id"]

    # Assign question
    res_assign = client.post(
        f"/api/assessments/{asm_id}/questions",
        json={
            "question_id": str(question.public_id),
            "points": 5.0,
            "position": 1,
        },
        headers=auth_headers,
    )
    assert res_assign.status_code == 201
    assign_data = res_assign.get_json()
    assert assign_data["points"] == 5.0
    assert_adr002_no_bigint_leaks(assign_data)

    # Publish assessment
    res_pub = client.post(f"/api/assessments/{asm_id}/publish", headers=auth_headers)
    assert res_pub.status_code == 200
    pub_data = res_pub.get_json()
    assert pub_data["status"] == "PUBLISHED"
    assert pub_data["published_at"] is not None
    assert_adr002_no_bigint_leaks(pub_data)

    # Cancel assessment
    res_cancel = client.post(
        f"/api/assessments/{asm_id}/cancel",
        json={"reason": "Testing cancellation"},
        headers=auth_headers,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["assessment"]["status"] == "CANCELLED"


def test_blueprint_configuration_and_materialization(
    client: FlaskClient,
    auth_headers: dict[str, str],
    course: Course,
    question: Question,
) -> None:
    """Test configuring blueprint and materializing question pool via REST API."""
    res_create = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json={"title": "Blueprint Quiz", "assessment_type": "QUIZ"},
        headers=auth_headers,
    )
    asm_id = res_create.get_json()["assessment_id"]

    # Configure blueprint
    res_bp = client.post(
        f"/api/assessments/{asm_id}/blueprint",
        json={
            "name": "API Blueprint",
            "rules": [
                {
                    "difficulty": "REMEMBER",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 1,
                    "points_each": 2.0,
                    "position": 1,
                }
            ],
        },
        headers=auth_headers,
    )
    assert res_bp.status_code == 200
    bp_data = res_bp.get_json()
    assert bp_data["name"] == "API Blueprint"
    assert_adr002_no_bigint_leaks(bp_data)

    # Materialize pool
    res_mat = client.post(
        f"/api/assessments/{asm_id}/blueprint/materialize",
        headers=auth_headers,
    )
    assert res_mat.status_code == 200
    mat_data = res_mat.get_json()
    assert mat_data["pool_count"] == 1


def test_list_course_assessments_pagination(
    client: FlaskClient, auth_headers: dict[str, str], course: Course
) -> None:
    """Test GET /api/courses/<course_id>/assessments with pagination."""
    # Create 3 assessments
    for i in range(1, 4):
        client.post(
            f"/api/courses/{course.public_id}/assessments",
            json={"title": f"Quiz {i}", "assessment_type": "QUIZ"},
            headers=auth_headers,
        )

    res = client.get(
        f"/api/courses/{course.public_id}/assessments?page=1&per_page=2",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["total_pages"] == 2
    assert_adr002_no_bigint_leaks(data)


def test_authentication_required(client: FlaskClient, course: Course) -> None:
    """Test endpoints reject unauthenticated requests with 401."""
    res = client.post(
        f"/api/courses/{course.public_id}/assessments",
        json={"title": "No Auth Quiz"},
    )
    assert res.status_code == 401

    res_get = client.get(f"/api/courses/{course.public_id}/assessments")
    assert res_get.status_code == 401
