"""Security negative and IDOR prevention tests for Question Revision Engine (TASK-011)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import (
    create_question,
    create_question_revision,
    get_question_revision_detail,
    list_question_corrections,
    list_question_revisions,
    update_question,
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
    u = register_user("idor_qr_inst_a@example.com", "Password@123", "Instructor Alpha")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor Beta."""
    u = register_user("idor_qr_inst_b@example.com", "Password@123", "Instructor Beta")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a student user."""
    u = register_user("idor_qr_student@example.com", "Password@123", "Student Charlie")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an administrator user."""
    u = register_user("idor_qr_admin@example.com", "Password@123", "Admin Delta")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Create course owned by Instructor Alpha."""
    c = create_course(
        instructor_a,
        {
            "course_code": "CS-SEC101",
            "title": "Security Course Alpha",
            "description": "Course Alpha Description",
            "category": "Security",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def question_a(app: Flask, instructor_a: User, course_a: Course) -> Question:
    """Create question owned by Instructor Alpha in Course Alpha."""
    q = create_question(
        instructor_a,
        course_a.id,
        {
            "question_type": "SINGLE_CHOICE",
            "stem": "Which cipher is asymmetric?",
            "general_feedback": "RSA is asymmetric.",
            "default_points": 1.0,
            "difficulty": "UNDERSTAND",
            "choices": [
                {"content": "RSA", "is_correct": True, "position": 1},
                {"content": "AES", "is_correct": False, "position": 2},
            ],
        },
    )
    db.session.commit()
    return q


@pytest.fixture
def instructor_a_token(instructor_a: User) -> str:
    tokens = create_token_pair(instructor_a)
    return tokens["access_token"]


@pytest.fixture
def instructor_b_token(instructor_b: User) -> str:
    tokens = create_token_pair(instructor_b)
    return tokens["access_token"]


@pytest.fixture
def student_token(student_user: User) -> str:
    tokens = create_token_pair(student_user)
    return tokens["access_token"]


@pytest.fixture
def admin_token(admin_user: User) -> str:
    tokens = create_token_pair(admin_user)
    return tokens["access_token"]


# --- REST API IDOR Tests ---


def test_idor_instructor_b_cannot_list_revisions_of_instructor_a(
    client: FlaskClient, question_a: Question, instructor_b_token: str
) -> None:
    """Instructor B cannot list revisions of Instructor A's question (403)."""
    headers = {"Authorization": f"Bearer {instructor_b_token}"}
    res = client.get(f"/api/questions/{question_a.public_id}/revisions", headers=headers)
    assert res.status_code == 403
    assert res.json is not None
    assert "error" in res.json


def test_idor_instructor_b_cannot_create_revision_for_instructor_a(
    client: FlaskClient, question_a: Question, instructor_b_token: str
) -> None:
    """Instructor B cannot create a revision for Instructor A's question (403)."""
    headers = {"Authorization": f"Bearer {instructor_b_token}"}
    payload = {
        "stem": "Malicious revision by Instructor B",
        "change_type": "TYPO_FIX",
        "change_reason": "Unauthorized fix attempt",
    }
    res = client.post(
        f"/api/questions/{question_a.public_id}/revisions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json is not None
    assert "error" in res.json


def test_idor_instructor_b_cannot_get_revision_detail_of_instructor_a(
    client: FlaskClient, question_a: Question, instructor_b_token: str
) -> None:
    """Instructor B cannot get revision details of Instructor A's question (403)."""
    headers = {"Authorization": f"Bearer {instructor_b_token}"}
    res = client.get(f"/api/questions/{question_a.public_id}/revisions/1", headers=headers)
    assert res.status_code == 403
    assert res.json is not None
    assert "error" in res.json


def test_idor_instructor_b_cannot_list_corrections_of_instructor_a(
    client: FlaskClient, question_a: Question, instructor_b_token: str
) -> None:
    """Instructor B cannot list corrections of Instructor A's question (403)."""
    headers = {"Authorization": f"Bearer {instructor_b_token}"}
    res = client.get(f"/api/questions/{question_a.public_id}/corrections", headers=headers)
    assert res.status_code == 403
    assert res.json is not None
    assert "error" in res.json


def test_idor_instructor_b_cannot_patch_question_of_instructor_a(
    client: FlaskClient, question_a: Question, instructor_b_token: str
) -> None:
    """Instructor B cannot update Instructor A's question via PATCH (403)."""
    headers = {"Authorization": f"Bearer {instructor_b_token}"}
    res = client.patch(
        f"/api/questions/{question_a.public_id}",
        json={"stem": "Hacked stem"},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json is not None
    assert "error" in res.json


def test_student_cannot_access_revisions_or_corrections(
    client: FlaskClient, question_a: Question, student_token: str
) -> None:
    """Students are strictly forbidden from question revision and correction endpoints (403)."""
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. List revisions
    r1 = client.get(f"/api/questions/{question_a.public_id}/revisions", headers=headers)
    assert r1.status_code == 403

    # 2. Create revision
    r2 = client.post(
        f"/api/questions/{question_a.public_id}/revisions",
        json={"stem": "Student attempt"},
        headers=headers,
    )
    assert r2.status_code == 403

    # 3. Get revision detail
    r3 = client.get(f"/api/questions/{question_a.public_id}/revisions/1", headers=headers)
    assert r3.status_code == 403

    # 4. List corrections
    r4 = client.get(f"/api/questions/{question_a.public_id}/corrections", headers=headers)
    assert r4.status_code == 403

    # 5. Patch question
    r5 = client.patch(
        f"/api/questions/{question_a.public_id}",
        json={"stem": "Student patch"},
        headers=headers,
    )
    assert r5.status_code == 403


def test_unauthenticated_requests_return_401(client: FlaskClient, question_a: Question) -> None:
    """Unauthenticated requests to revision/correction endpoints return 401."""
    r1 = client.get(f"/api/questions/{question_a.public_id}/revisions")
    assert r1.status_code == 401

    r2 = client.post(
        f"/api/questions/{question_a.public_id}/revisions",
        json={"stem": "Unauthenticated attempt"},
    )
    assert r2.status_code == 401

    r3 = client.get(f"/api/questions/{question_a.public_id}/corrections")
    assert r3.status_code == 401

    r4 = client.patch(
        f"/api/questions/{question_a.public_id}",
        json={"stem": "Unauthenticated patch"},
    )
    assert r4.status_code == 401


def test_invalid_or_malformed_token_returns_401(client: FlaskClient, question_a: Question) -> None:
    """Malformed or invalid JWT token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    r1 = client.get(f"/api/questions/{question_a.public_id}/revisions", headers=headers)
    assert r1.status_code == 401


def test_admin_can_access_and_create_revisions(
    client: FlaskClient, question_a: Question, admin_token: str
) -> None:
    """Administrator can manage question revisions and view corrections across all courses."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin can list revisions
    r1 = client.get(f"/api/questions/{question_a.public_id}/revisions", headers=headers)
    assert r1.status_code == 200
    assert r1.json is not None
    assert r1.json["total"] == 1

    # 2. Admin can create revision
    r2 = client.post(
        f"/api/questions/{question_a.public_id}/revisions",
        json={
            "stem": "Admin updated stem for clarity",
            "change_type": "TYPO_FIX",
            "change_reason": "Admin maintenance",
        },
        headers=headers,
    )
    assert r2.status_code == 201
    assert r2.json is not None
    assert r2.json["revision"]["revision_no"] == 2

    # 3. Admin can list corrections
    r3 = client.get(f"/api/questions/{question_a.public_id}/corrections", headers=headers)
    assert r3.status_code == 200
    assert r3.json is not None
    assert "items" in r3.json


def test_service_level_idor_forbidden_error(instructor_b: User, question_a: Question) -> None:
    """Service functions reject unauthorized instructor with ForbiddenError."""
    with pytest.raises(ForbiddenError):
        list_question_revisions(
            actor=instructor_b,
            question_id=question_a.public_id,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        create_question_revision(
            actor=instructor_b,
            question_id=question_a.public_id,
            payload={
                "stem": "Unauthorized service revision",
                "change_type": "TYPO_FIX",
                "change_reason": "Exploit attempt",
            },
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        get_question_revision_detail(
            actor=instructor_b,
            question_id=question_a.public_id,
            revision_no=1,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        list_question_corrections(
            actor=instructor_b,
            question_id=question_a.public_id,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        update_question(
            actor=instructor_b,
            question_id=question_a.public_id,
            payload={"stem": "Unauthorized update"},
            session=db.session,
        )
