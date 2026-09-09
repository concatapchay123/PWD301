"""Security negative and IDOR prevention tests for Question Bank Management (TASK-010)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import ForbiddenError, QuestionValidationError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import (
    create_question,
    trash_question,
)
from pwd301.services.user_service import assign_role_to_user, register_user


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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Alpha."""
    u = register_user("idor_qb_inst_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Beta."""
    u = register_user("idor_qb_inst_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User."""
    return register_user("idor_qb_student@example.com", "Password@123", "Student User")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("idor_qb_admin@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Course owned by Instructor A."""
    return create_course(
        instructor_a,
        {
            "course_code": "QB-SEC-A",
            "title": "Question Bank Security Course A",
            "description": "Owned by Alpha",
            "category": "Security",
            "difficulty": "INTERMEDIATE",
        },
    )


@pytest.fixture
def course_b(app: Flask, instructor_b: User) -> Course:
    """Course owned by Instructor B."""
    return create_course(
        instructor_b,
        {
            "course_code": "QB-SEC-B",
            "title": "Question Bank Security Course B",
            "description": "Owned by Beta",
            "category": "Security",
            "difficulty": "INTERMEDIATE",
        },
    )


@pytest.fixture
def lesson_a(app: Flask, instructor_a: User, course_a: Course) -> Lesson:
    """Lesson belonging to Course A."""
    return create_lesson(
        instructor_a,
        course_a.id,
        {
            "title": "Alpha Lesson 1",
            "markdown_content": "# Lesson 1 Alpha",
        },
    )


@pytest.fixture
def lesson_b(app: Flask, instructor_b: User, course_b: Course) -> Lesson:
    """Lesson belonging to Course B."""
    return create_lesson(
        instructor_b,
        course_b.id,
        {
            "title": "Beta Lesson 1",
            "markdown_content": "# Lesson 1 Beta",
        },
    )


@pytest.fixture
def question_a(app: Flask, instructor_a: User, course_a: Course) -> Question:
    """Question created by Instructor A in Course A."""
    return create_question(
        actor=instructor_a,
        course_id=course_a.id,
        payload={
            "stem": "Which layer handles network routing?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 1.0,
            "choices": [
                {"content": "Network Layer", "is_correct": True, "fraction": 1.0},
                {"content": "Application Layer", "is_correct": False, "fraction": 0.0},
            ],
        },
    )


def test_instructor_b_cannot_create_question_in_instructor_a_course_service(
    instructor_b: User,
    course_a: Course,
) -> None:
    """Service level IDOR: Instructor B cannot create question in Course A."""
    with pytest.raises(ForbiddenError):
        create_question(
            actor=instructor_b,
            course_id=course_a.id,
            payload={
                "stem": "Illegally created question",
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "choices": [
                    {"content": "Yes", "is_correct": True, "fraction": 1.0},
                    {"content": "No", "is_correct": False, "fraction": 0.0},
                ],
            },
        )


def test_instructor_b_cannot_create_question_in_instructor_a_course_api(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
) -> None:
    """API level IDOR: Instructor B cannot create question in Course A (403 Forbidden)."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers,
        json={
            "stem": "Malicious question injection",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "A", "is_correct": True, "fraction": 1.0},
                {"content": "B", "is_correct": False, "fraction": 0.0},
            ],
        },
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_list_questions_in_instructor_a_course_api(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
    question_a: Question,
) -> None:
    """API level IDOR: Instructor B cannot list questions in Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.get(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_view_question_in_instructor_a_course_api(
    client: FlaskClient,
    instructor_b: User,
    question_a: Question,
) -> None:
    """API level IDOR: Instructor B cannot view question in Course A."""
    tokens = create_token_pair(instructor_b)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.get(
        f"/api/questions/{question_a.public_id}",
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"


def test_instructor_b_cannot_trash_or_restore_question_in_instructor_a_course_api(
    client: FlaskClient,
    instructor_a: User,
    instructor_b: User,
    question_a: Question,
) -> None:
    """API level IDOR: Instructor B cannot trash or restore question in Course A."""
    tokens_b = create_token_pair(instructor_b)
    headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    # Trash attempt by B
    resp_trash = client.post(
        f"/api/questions/{question_a.public_id}/trash",
        headers=headers_b,
        json={"reason": "Attacking Instructor A's question bank"},
    )
    assert resp_trash.status_code == 403
    assert resp_trash.get_json()["error"]["code"] == "FORBIDDEN"

    # DELETE alias attempt by B
    resp_del = client.delete(
        f"/api/questions/{question_a.public_id}",
        headers=headers_b,
    )
    assert resp_del.status_code == 403
    assert resp_del.get_json()["error"]["code"] == "FORBIDDEN"

    # Instructor A legally trashes the question
    trash_question(instructor_a, question_a.id, reason="Legal cleanup")

    # Restore attempt by B
    resp_restore = client.post(
        f"/api/questions/{question_a.public_id}/restore",
        headers=headers_b,
    )
    assert resp_restore.status_code == 403
    assert resp_restore.get_json()["error"]["code"] == "FORBIDDEN"


def test_cross_course_lesson_binding_prevented_service_and_api(
    client: FlaskClient,
    instructor_a: User,
    course_a: Course,
    lesson_b: Lesson,
) -> None:
    """Binding a lesson from Course B to a question in Course A is prohibited."""
    # 1. Direct service call
    with pytest.raises(QuestionValidationError, match="does not belong to the specified course"):
        create_question(
            actor=instructor_a,
            course_id=course_a.id,
            payload={
                "stem": "Cross course lesson test",
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "primary_lesson_id": lesson_b.id,
                "choices": [
                    {"content": "A", "is_correct": True, "fraction": 1.0},
                    {"content": "B", "is_correct": False, "fraction": 0.0},
                ],
            },
        )

    # 2. REST API call with UUID
    tokens_a = create_token_pair(instructor_a)
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    resp = client.post(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers_a,
        json={
            "stem": "Cross course lesson API test",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "primary_lesson_id": str(lesson_b.public_id),
            "choices": [
                {"content": "A", "is_correct": True, "fraction": 1.0},
                {"content": "B", "is_correct": False, "fraction": 0.0},
            ],
        },
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"
    assert "does not belong to the specified course" in resp.get_json()["error"]["message"]


def test_student_cannot_access_question_bank_endpoints(
    client: FlaskClient,
    student_user: User,
    course_a: Course,
    question_a: Question,
) -> None:
    """Student caller is forbidden from creating, listing, viewing, or trashing questions."""
    tokens = create_token_pair(student_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # List questions
    resp_list = client.get(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers,
    )
    assert resp_list.status_code == 403
    assert resp_list.get_json()["error"]["code"] == "FORBIDDEN"

    # Create question
    resp_create = client.post(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers,
        json={"stem": "Student trying to author questions"},
    )
    assert resp_create.status_code == 403
    assert resp_create.get_json()["error"]["code"] == "FORBIDDEN"

    # View question detail
    resp_detail = client.get(
        f"/api/questions/{question_a.public_id}",
        headers=headers,
    )
    assert resp_detail.status_code == 403
    assert resp_detail.get_json()["error"]["code"] == "FORBIDDEN"

    # Trash question
    resp_trash = client.post(
        f"/api/questions/{question_a.public_id}/trash",
        headers=headers,
    )
    assert resp_trash.status_code == 403
    assert resp_trash.get_json()["error"]["code"] == "FORBIDDEN"


def test_unauthenticated_request_rejected(
    client: FlaskClient,
    course_a: Course,
    question_a: Question,
) -> None:
    """Requests without JWT tokens are rejected with 401 Unauthorized."""
    endpoints = [
        ("GET", f"/api/courses/{course_a.public_id}/questions"),
        ("POST", f"/api/courses/{course_a.public_id}/questions"),
        ("GET", f"/api/questions/{question_a.public_id}"),
        ("POST", f"/api/questions/{question_a.public_id}/trash"),
        ("POST", f"/api/questions/{question_a.public_id}/restore"),
        ("DELETE", f"/api/questions/{question_a.public_id}"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json={})
        elif method == "DELETE":
            resp = client.delete(path)
        else:
            continue
        assert resp.status_code == 401, f"{method} {path} expected 401, got {resp.status_code}"
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_can_manage_any_course_questions(
    client: FlaskClient,
    admin_user: User,
    course_a: Course,
    question_a: Question,
) -> None:
    """Admin has global oversight to view, create, trash, and restore questions across courses."""
    tokens = create_token_pair(admin_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Admin list
    resp_list = client.get(
        f"/api/courses/{course_a.public_id}/questions",
        headers=headers,
    )
    assert resp_list.status_code == 200
    assert len(resp_list.get_json()["items"]) >= 1

    # Admin view detail
    resp_detail = client.get(
        f"/api/questions/{question_a.public_id}",
        headers=headers,
    )
    assert resp_detail.status_code == 200
    assert resp_detail.get_json()["public_id"] == str(question_a.public_id)

    # Admin trash
    resp_trash = client.post(
        f"/api/questions/{question_a.public_id}/trash",
        headers=headers,
        json={"reason": "Admin moderation"},
    )
    assert resp_trash.status_code == 200
    assert resp_trash.get_json()["question"]["status"] == "TRASH"

    # Admin restore
    resp_restore = client.post(
        f"/api/questions/{question_a.public_id}/restore",
        headers=headers,
    )
    assert resp_restore.status_code == 200
    assert resp_restore.get_json()["question"]["status"] == "ACTIVE"


def test_instructor_b_cannot_access_instructor_a_questions_web_ui(
    client: FlaskClient,
    instructor_b: User,
    course_a: Course,
    question_a: Question,
) -> None:
    """Instructor B cannot access Instructor A's questions via Web UI routes."""
    from tests.conftest import login_web_user

    login_web_user(client, instructor_b)

    # View question list in Course A
    resp = client.get(
        f"/instructor/courses/{course_a.public_id}/questions",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    # View question detail
    resp_det = client.get(
        f"/instructor/questions/{question_a.public_id}",
        headers={"Accept": "application/json"},
    )
    assert resp_det.status_code == 403
    assert resp_det.get_json()["error"]["code"] == "FORBIDDEN"

    # Trash question
    resp_tr = client.post(
        f"/instructor/questions/{question_a.public_id}/trash",
        headers={"Accept": "application/json"},
        json={"reason": "Web UI attack"},
    )
    assert resp_tr.status_code == 403
    assert resp_tr.get_json()["error"]["code"] == "FORBIDDEN"
