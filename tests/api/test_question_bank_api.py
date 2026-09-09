"""Integration tests for Question Bank REST API endpoints (TASK-010)."""

from __future__ import annotations

import re
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import (
    create_question,
)
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002_no_bigint_leaks(data: Any) -> None:
    """Recursively verify that no internal integer PKs or IDs are exposed (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            # Internal database primary keys should never be present in API output
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key 'creator_user_id' leaked: {data}"
            assert k != "question_revision_id", (
                f"Internal foreign key 'question_revision_id' leaked: {data}"
            )

            # If the field is an ID field, it should either be None or a valid UUID string
            if k in ("question_id", "course_id", "lesson_id", "public_id") and v is not None:
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
    """Create Instructor User."""
    u = register_user("qb_api_inst@example.com", "Password@123", "QB API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_tokens(instructor_user: User) -> dict[str, str]:
    """Generate JWT tokens for instructor."""
    return create_token_pair(instructor_user)


@pytest.fixture
def auth_headers(instructor_tokens: dict[str, str]) -> dict[str, str]:
    """Authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {instructor_tokens['access_token']}"}


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a course for question bank testing."""
    return create_course(
        instructor_user,
        {
            "course_code": "QB-API-101",
            "title": "Question Bank API Course",
            "description": "Integration testing course for Question Bank",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )


@pytest.fixture
def test_lesson(app: Flask, instructor_user: User, test_course: Course) -> Lesson:
    """Create a lesson in the test course."""
    return create_lesson(
        instructor_user,
        test_course.id,
        {
            "title": "Lesson 1: Introduction to Networks",
            "markdown_content": "# Intro to Networks",
        },
    )


def test_api_create_single_choice_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
    test_lesson: Lesson,
) -> None:
    """POST /api/courses/<course_id>/questions creates a SINGLE_CHOICE question."""
    payload = {
        "stem": "Which protocol operates at the Transport layer?",
        "question_type": "SINGLE_CHOICE",
        "difficulty": "UNDERSTAND",
        "default_points": 2.0,
        "lesson_id": str(test_lesson.public_id),
        "explanation": "TCP is a reliable transport layer protocol.",
        "choices": [
            {"content": "TCP", "is_correct": True, "fraction": 1.0, "position": 1},
            {"content": "IP", "is_correct": False, "fraction": 0.0, "position": 2},
            {"content": "HTTP", "is_correct": False, "fraction": 0.0, "position": 3},
            {"content": "Ethernet", "is_correct": False, "fraction": 0.0, "position": 4},
        ],
        "tags": ["networking", "protocols"],
    }

    resp = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.get_json()

    assert "question_id" in data
    assert data["course_id"] == str(test_course.public_id)
    assert data["lesson_id"] == str(test_lesson.public_id)
    assert data["difficulty"] == "UNDERSTAND"
    assert data["status"] == "ACTIVE"

    rev = data["current_revision"]
    assert rev["revision_no"] == 1
    assert rev["question_type"] == "SINGLE_CHOICE"
    assert rev["content"] == "Which protocol operates at the Transport layer?"
    assert rev["explanation"] == "TCP is a reliable transport layer protocol."
    assert len(data["choices"]) == 4

    # ADR-002 verification
    assert_adr002_no_bigint_leaks(data)


def test_api_create_multiple_choice_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
) -> None:
    """POST /api/courses/<course_id>/questions creates a MULTIPLE_CHOICE question."""
    payload = {
        "stem": "Select all connection-oriented protocols:",
        "question_type": "MULTIPLE_CHOICE",
        "difficulty": "APPLY",
        "choices": [
            {"content": "TCP", "is_correct": True, "fraction": 0.5, "position": 1},
            {"content": "SCTP", "is_correct": True, "fraction": 0.5, "position": 2},
            {"content": "UDP", "is_correct": False, "fraction": 0.0, "position": 3},
        ],
    }

    resp = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["current_revision"]["question_type"] == "MULTIPLE_CHOICE"
    assert len(data["choices"]) == 3
    assert_adr002_no_bigint_leaks(data)


def test_api_create_true_false_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
) -> None:
    """POST /api/courses/<course_id>/questions creates a TRUE_FALSE question."""
    payload = {
        "stem": "UDP provides guaranteed packet delivery.",
        "question_type": "TRUE_FALSE",
        "difficulty": "REMEMBER",
        "choices": [
            {"content": "True", "is_correct": False, "fraction": 0.0, "position": 1},
            {"content": "False", "is_correct": True, "fraction": 1.0, "position": 2},
        ],
    }

    resp = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["current_revision"]["question_type"] == "TRUE_FALSE"
    assert len(data["choices"]) == 2
    assert_adr002_no_bigint_leaks(data)


def test_api_create_short_answer_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
) -> None:
    """POST /api/courses/<course_id>/questions creates a SHORT_ANSWER question."""
    payload = {
        "stem": "What is the standard port for HTTPS?",
        "question_type": "SHORT_ANSWER",
        "difficulty": "REMEMBER",
        "match_type": "EXACT",
        "accepted_answers": [
            {"answer_text": "443"},
            {"answer_text": "port 443"},
        ],
    }

    resp = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["current_revision"]["question_type"] == "SHORT_ANSWER"
    assert data["current_revision"]["short_answer_match_mode"] == "EXACT"
    assert len(data["accepted_answers"]) == 2
    assert_adr002_no_bigint_leaks(data)


def test_api_create_essay_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
) -> None:
    """POST /api/courses/<course_id>/questions creates an ESSAY question."""
    payload = {
        "stem": "Explain the three-way handshake in TCP.",
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "explanation": "Must mention SYN, SYN-ACK, and ACK steps.",
    }

    resp = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["current_revision"]["question_type"] == "ESSAY"
    assert data["choices"] == []
    assert data["accepted_answers"] == []
    assert_adr002_no_bigint_leaks(data)


def test_api_create_question_validation_failures(
    client: FlaskClient,
    auth_headers: dict[str, str],
    test_course: Course,
) -> None:
    """POST /api/courses/<course_id>/questions validates input properly."""
    # 1. Missing stem
    resp1 = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json={"question_type": "SINGLE_CHOICE", "difficulty": "REMEMBER"},
    )
    assert resp1.status_code == 400
    assert resp1.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Invalid question type
    resp2 = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json={"stem": "Valid stem", "question_type": "INVALID_TYPE", "difficulty": "REMEMBER"},
    )
    assert resp2.status_code == 400
    assert resp2.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # 3. Invalid difficulty
    resp3 = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json={"stem": "Valid stem", "question_type": "SINGLE_CHOICE", "difficulty": "EASY_PEASY"},
    )
    assert resp3.status_code == 400
    assert resp3.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # 4. SINGLE_CHOICE without enough choices
    resp4 = client.post(
        f"/api/courses/{test_course.public_id}/questions",
        headers=auth_headers,
        json={
            "stem": "Valid stem",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [{"content": "Only one choice", "is_correct": True}],
        },
    )
    assert resp4.status_code == 400
    assert resp4.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_api_list_questions_pagination_and_filtering(
    client: FlaskClient,
    auth_headers: dict[str, str],
    instructor_user: User,
    test_course: Course,
) -> None:
    """GET /api/courses/<course_id>/questions supports pagination and filtering."""
    # Seed 3 questions
    create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "Filter Q1: DNS lookup process",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "fraction": 1.0},
                {"content": "B", "is_correct": False, "fraction": 0.0},
            ],
        },
    )
    create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "Filter Q2: BGP routing protocol",
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "APPLY",
            "choices": [
                {"content": "A", "is_correct": True, "fraction": 0.5},
                {"content": "B", "is_correct": True, "fraction": 0.5},
            ],
        },
    )
    create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "Filter Q3: ARP cache poison attack",
            "question_type": "TRUE_FALSE",
            "difficulty": "UNDERSTAND",
            "choices": [
                {"content": "True", "is_correct": True, "fraction": 1.0},
                {"content": "False", "is_correct": False, "fraction": 0.0},
            ],
        },
    )

    # 1. List all (page 1, page_size 2)
    resp = client.get(
        f"/api/courses/{test_course.public_id}/questions?page=1&page_size=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["total_items"] >= 3
    assert data["pagination"]["total_pages"] >= 2
    assert_adr002_no_bigint_leaks(data)

    # 2. Filter by question_type=MULTIPLE_CHOICE
    resp_type = client.get(
        f"/api/courses/{test_course.public_id}/questions?question_type=MULTIPLE_CHOICE",
        headers=auth_headers,
    )
    assert resp_type.status_code == 200
    type_items = resp_type.get_json()["items"]
    assert len(type_items) == 1
    assert type_items[0]["current_revision"]["question_type"] == "MULTIPLE_CHOICE"

    # 3. Filter by difficulty=APPLY
    resp_diff = client.get(
        f"/api/courses/{test_course.public_id}/questions?difficulty=APPLY",
        headers=auth_headers,
    )
    assert resp_diff.status_code == 200
    diff_items = resp_diff.get_json()["items"]
    assert len(diff_items) == 1
    assert diff_items[0]["difficulty"] == "APPLY"

    # 4. Filter by search keyword
    resp_search = client.get(
        f"/api/courses/{test_course.public_id}/questions?search=BGP",
        headers=auth_headers,
    )
    assert resp_search.status_code == 200
    search_items = resp_search.get_json()["items"]
    assert len(search_items) == 1
    assert "BGP" in search_items[0]["current_revision"]["content"]


def test_api_get_question_detail(
    client: FlaskClient,
    auth_headers: dict[str, str],
    instructor_user: User,
    test_course: Course,
) -> None:
    """GET /api/questions/<question_id> returns detailed question structure."""
    question = create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "What is the loopback IPv4 address?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "127.0.0.1", "is_correct": True, "fraction": 1.0},
                {"content": "192.168.1.1", "is_correct": False, "fraction": 0.0},
            ],
            "tags": ["ip", "loopback"],
        },
    )

    resp = client.get(
        f"/api/questions/{question.public_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["question_id"] == str(question.public_id)
    assert data["current_revision"]["content"] == "What is the loopback IPv4 address?"
    assert len(data["choices"]) == 2
    assert data["provenance"]["source_type"] == "MANUAL"
    assert_adr002_no_bigint_leaks(data)


def test_api_get_question_not_found(
    client: FlaskClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/questions/<non_existent_id> returns 404 QuestionNotFoundError."""
    random_uuid = str(uuid.uuid4())
    resp = client.get(
        f"/api/questions/{random_uuid}",
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_api_trash_and_restore_question_lifecycle(
    client: FlaskClient,
    auth_headers: dict[str, str],
    instructor_user: User,
    test_course: Course,
) -> None:
    """POST /api/questions/<id>/trash and /restore manage the 30-day lifecycle with idempotency."""
    question = create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "Temporary question for trash testing",
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "True", "is_correct": True, "fraction": 1.0},
                {"content": "False", "is_correct": False, "fraction": 0.0},
            ],
        },
    )

    # 1. Trash question
    resp_trash = client.post(
        f"/api/questions/{question.public_id}/trash",
        headers=auth_headers,
        json={"reason": "Retiring obsolete question"},
    )
    assert resp_trash.status_code == 200
    trash_data = resp_trash.get_json()["question"]
    assert trash_data["status"] == "TRASH"
    assert trash_data["deleted_at"] is not None
    assert trash_data["restore_until"] is not None
    assert_adr002_no_bigint_leaks(resp_trash.get_json())

    # 2. Duplicate trash is state-idempotent (returns 200 OK)
    resp_double_trash = client.post(
        f"/api/questions/{question.public_id}/trash",
        headers=auth_headers,
        json={"reason": "Duplicate delete attempt"},
    )
    assert resp_double_trash.status_code == 200
    assert resp_double_trash.get_json()["question"]["status"] == "TRASH"

    # 3. Restore question
    resp_restore = client.post(
        f"/api/questions/{question.public_id}/restore",
        headers=auth_headers,
    )
    assert resp_restore.status_code == 200
    restore_data = resp_restore.get_json()["question"]
    assert restore_data["status"] == "ACTIVE"
    assert restore_data["deleted_at"] is None
    assert restore_data["restore_until"] is None
    assert_adr002_no_bigint_leaks(resp_restore.get_json())

    # 4. Duplicate restore is state-idempotent (returns 200 OK)
    resp_double_restore = client.post(
        f"/api/questions/{question.public_id}/restore",
        headers=auth_headers,
    )
    assert resp_double_restore.status_code == 200
    assert resp_double_restore.get_json()["question"]["status"] == "ACTIVE"

    # 5. Cannot restore non-TRASH question (e.g. RETIRED returns 409 Conflict)
    question.status = "RETIRED"
    db.session.commit()
    resp_invalid_restore = client.post(
        f"/api/questions/{question.public_id}/restore",
        headers=auth_headers,
    )
    assert resp_invalid_restore.status_code == 409
    assert resp_invalid_restore.get_json()["error"]["code"] == "STATE_VIOLATION"


def test_api_delete_alias_soft_deletes_question(
    client: FlaskClient,
    auth_headers: dict[str, str],
    instructor_user: User,
    test_course: Course,
) -> None:
    """DELETE /api/questions/<id> acts as an alias to trash the question."""
    question = create_question(
        instructor_user,
        test_course.id,
        {
            "stem": "Question for DELETE alias test",
            "question_type": "TRUE_FALSE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "True", "is_correct": True, "fraction": 1.0},
                {"content": "False", "is_correct": False, "fraction": 0.0},
            ],
        },
    )

    resp = client.delete(
        f"/api/questions/{question.public_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Question moved to trash."
    assert data["question"]["status"] == "TRASH"
    assert_adr002_no_bigint_leaks(data)
