"""Integration and REST API tests for Question Revision Engine & Question Correction (TASK-011)."""

from __future__ import annotations

import re
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002_no_bigint_leaks(data: Any) -> None:
    """Recursively verify that no internal integer PKs or IDs are exposed (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key 'creator_user_id' leaked: {data}"
            assert k != "question_revision_id", (
                f"Internal foreign key 'question_revision_id' leaked: {data}"
            )
            assert k != "actor_user_id", f"Internal foreign key 'actor_user_id' leaked: {data}"

            # Check that UUID fields are strictly valid UUID strings when non-None
            if (
                k
                in (
                    "question_id",
                    "course_id",
                    "lesson_id",
                    "public_id",
                    "choice_id",
                    "choice_key",
                    "correction_id",
                    "from_revision_id",
                    "to_revision_id",
                    "actor_id",
                )
                and v is not None
            ):
                assert isinstance(v, str), (
                    f"Field '{k}' should be a UUID string, got {type(v)}: {v}"
                )
                assert UUID_REGEX.match(v), f"Field '{k}' is not a valid UUID: {v}"

            assert_adr002_no_bigint_leaks(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002_no_bigint_leaks(item)


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
    """Create instructor user."""
    u = register_user("api_qr_inst@example.com", "Password@123", "API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_headers(instructor_user: User) -> dict[str, str]:
    tokens = create_token_pair(instructor_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def course(app: Flask, instructor_user: User) -> Course:
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-API-QR",
            "title": "API Question Revision Course",
            "description": "API testing course",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def lesson(app: Flask, instructor_user: User, course: Course) -> Lesson:
    les = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "API Lesson",
            "markdown_content": "# API Lesson",
            "position": 1,
        },
    )
    db.session.commit()
    return les


@pytest.fixture
def test_question(app: Flask, instructor_user: User, course: Course, lesson: Lesson) -> Question:
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "stem": "Which protocol operates at Layer 4?",
            "general_feedback": "TCP and UDP operate at Transport Layer.",
            "default_points": 1.0,
            "difficulty": "UNDERSTAND",
            "lesson_id": lesson.id,
            "choices": [
                {"content": "TCP", "is_correct": True, "position": 1},
                {"content": "IP", "is_correct": False, "position": 2},
                {"content": "HTTP", "is_correct": False, "position": 3},
            ],
        },
    )
    db.session.commit()
    return q


# --- REST API Tests ---


def test_api_list_question_revisions(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """GET /api/questions/<question_id>/revisions returns paginated revisions list."""
    res = client.get(
        f"/api/questions/{test_question.public_id}/revisions",
        headers=instructor_headers,
    )
    assert res.status_code == 200
    data = res.json
    assert data is not None
    assert data["total"] == 1
    assert len(data["items"]) == 1
    rev = data["items"][0]
    assert rev["revision_no"] == 1
    assert rev["question_type"] == "SINGLE_CHOICE"
    assert rev["content"] == "Which protocol operates at Layer 4?"
    assert len(rev["choices"]) == 3
    assert_adr002_no_bigint_leaks(data)


def test_api_create_question_revision(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """POST /api/questions/<question_id>/revisions creates a new incremented revision."""
    payload = {
        "stem": "Which protocol operates at the Transport layer (Layer 4)?",
        "change_type": "CONTENT_CHANGE",
        "change_reason": "Provide OSI reference model clarification",
    }
    res = client.post(
        f"/api/questions/{test_question.public_id}/revisions",
        json=payload,
        headers=instructor_headers,
    )
    assert res.status_code == 201
    data = res.json
    assert data is not None
    assert "revision" in data
    rev = data["revision"]
    assert rev["revision_no"] == 2
    assert rev["content"] == "Which protocol operates at the Transport layer (Layer 4)?"
    assert rev["change_type"] == "CONTENT_CHANGE"
    assert rev["change_reason"] == "Provide OSI reference model clarification"
    # Choices cloned from revision 1
    assert len(rev["choices"]) == 3
    assert_adr002_no_bigint_leaks(data)


def test_api_get_question_revision_detail(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """GET /api/questions/<question_id>/revisions/<revision_no> returns revision detail."""
    res = client.get(
        f"/api/questions/{test_question.public_id}/revisions/1",
        headers=instructor_headers,
    )
    assert res.status_code == 200
    data = res.json
    assert data is not None
    assert data["revision_no"] == 1
    assert data["stem"] == "Which protocol operates at Layer 4?"
    assert len(data["choices"]) == 3
    assert_adr002_no_bigint_leaks(data)


def test_api_get_question_revision_detail_not_found(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """GET /api/questions/<question_id>/revisions/<revision_no> returns 404 for invalid revision."""
    res = client.get(
        f"/api/questions/{test_question.public_id}/revisions/999",
        headers=instructor_headers,
    )
    assert res.status_code == 404
    data = res.json
    assert data is not None
    assert "error" in data


def test_api_patch_question_unused_in_place(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """PATCH /api/questions/<question_id> on unused question mutates revision in-place."""
    payload = {
        "stem": "In OSI model, which protocol operates at Layer 4?",
        "general_feedback": "Transport layer protocol: TCP/UDP",
    }
    res = client.patch(
        f"/api/questions/{test_question.public_id}",
        json=payload,
        headers=instructor_headers,
    )
    assert res.status_code == 200
    data = res.json
    assert data is not None
    assert data["current_revision"]["revision_no"] == 1
    assert (
        data["current_revision"]["content"] == "In OSI model, which protocol operates at Layer 4?"
    )
    assert_adr002_no_bigint_leaks(data)


def test_api_patch_question_in_use_branches_new_revision(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """PATCH /api/questions/<id> on in-use question branches revision 2 and creates correction."""
    test_question.usage_count = 1
    db.session.commit()

    payload = {
        "stem": "Which transport protocol provides reliable data transfer?",
        "change_type": "TYPO_FIX",
        "change_reason": "Fix ambiguity in layer naming",
    }
    res = client.patch(
        f"/api/questions/{test_question.public_id}",
        json=payload,
        headers=instructor_headers,
    )
    assert res.status_code == 200
    data = res.json
    assert data is not None
    assert data["current_revision"]["revision_no"] == 2
    assert (
        data["current_revision"]["content"]
        == "Which transport protocol provides reliable data transfer?"
    )
    assert_adr002_no_bigint_leaks(data)

    # Verify that a QuestionCorrection was created
    c_res = client.get(
        f"/api/questions/{test_question.public_id}/corrections",
        headers=instructor_headers,
    )
    assert c_res.status_code == 200
    c_data = c_res.json
    assert c_data is not None
    assert len(c_data["items"]) == 1
    corr = c_data["items"][0]
    assert corr["from_revision_no"] == 1
    assert corr["to_revision_no"] == 2
    assert corr["status"] == "PENDING"
    assert corr["reason"] == "Fix ambiguity in layer naming"
    assert_adr002_no_bigint_leaks(c_data)


def test_api_patch_question_in_use_missing_reason_fails(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """PATCH on in-use question without change_reason returns 400 Bad Request."""
    test_question.usage_count = 1
    db.session.commit()

    payload = {"stem": "New stem without mandatory change_reason"}
    res = client.patch(
        f"/api/questions/{test_question.public_id}",
        json=payload,
        headers=instructor_headers,
    )
    assert res.status_code == 400
    data = res.json
    assert data is not None
    assert "error" in data
    assert "change_reason is required" in data["error"]["message"]


def test_api_patch_question_in_use_type_mutation_fails(
    client: FlaskClient, test_question: Question, instructor_headers: dict[str, str]
) -> None:
    """PATCH on in-use question attempting question_type mutation returns 409 Conflict."""
    test_question.usage_count = 1
    db.session.commit()

    payload = {
        "question_type": "TRUE_FALSE",
        "change_reason": "Attempting to change type on locked question",
    }
    res = client.patch(
        f"/api/questions/{test_question.public_id}",
        json=payload,
        headers=instructor_headers,
    )
    assert res.status_code == 409
    data = res.json
    assert data is not None
    assert "error" in data
    assert "Cannot change question_type" in data["error"]["message"]


def test_api_question_revisions_not_found(
    client: FlaskClient, instructor_headers: dict[str, str]
) -> None:
    """GET /api/questions/<non_existent_uuid>/revisions returns 404."""
    non_existent = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/api/questions/{non_existent}/revisions", headers=instructor_headers)
    assert res.status_code == 404
    data = res.json
    assert data is not None
    assert "error" in data
