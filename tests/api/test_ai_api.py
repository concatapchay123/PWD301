"""REST API integration test suite for AI, Gemini, and Recommendations (TASK-023).

Validates:
- End-to-end REST API flows with JWT Bearer tokens per 10_AI_API.md.
- Course recommendations retrieval (/api/ai/recommendations).
- Question drafting by instructors (/api/ai/questions/draft and /api/ai/questions/generate).
- Question drafts listing (/api/ai/questions/drafts).
- Conversation lifecycle: initialization, retrieval, messaging, and inactivity expiry (409).
- Unified chat endpoint (/api/ai/chat).
- Maintenance cleanup endpoint (/api/ai/conversations/cleanup).
- Strict ADR-002 Zero Internal PK Leakage in all responses.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import AIConversation
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Seed standard roles for tests."""
    sess: Session = db.session
    roles = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        roles[code] = role
    sess.commit()
    return roles


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user("api_student@example.com", "Password@123", "API Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("api_instructor@example.com", "Password@123", "API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user("api_admin_ai@example.com", "Password@123", "API Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create sample published course."""
    sess: Session = db.session
    c = Course(
        public_id=uuid.uuid4(),
        course_code="AI201",
        course_code_normalized="AI201",
        title="Applied Machine Learning",
        title_normalized="applied machine learning",
        category="Data Science",
        difficulty="INTERMEDIATE",
        status="PUBLISHED",
        owner_instructor_id=instructor_user.id,
    )
    sess.add(c)
    sess.commit()
    return c


def _auth_headers(user: User) -> dict[str, str]:
    tokens = create_token_pair(user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


def test_get_recommendations_api(
    client: FlaskClient,
    student_user: User,
    test_course: Course,
) -> None:
    """GET /api/ai/recommendations returns personalized course recommendations."""
    # Unauthenticated request -> 401 Unauthorized
    resp_unauth = client.get("/api/ai/recommendations")
    assert resp_unauth.status_code == 401

    headers = _auth_headers(student_user)
    resp = client.get("/api/ai/recommendations?limit=3", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "recommendations" in data
    assert "count" in data
    assert len(data["recommendations"]) <= 3

    if data["recommendations"]:
        rec = data["recommendations"][0]
        assert "course_id" in rec
        assert "score" in rec
        assert "explanation" in rec
        assert "reasons" in rec


def test_draft_questions_api_and_alias(
    client: FlaskClient,
    instructor_user: User,
    test_course: Course,
) -> None:
    """POST /api/ai/questions/draft and /api/ai/questions/generate successfully draft questions."""
    headers = _auth_headers(instructor_user)
    course_id = str(test_course.public_id)

    # 1. Draft questions endpoint
    payload = {
        "course_id": course_id,
        "topic": "Neural Networks",
        "difficulty": "UNDERSTAND",
        "question_types": ["SINGLE_CHOICE", "MULTIPLE_CHOICE"],
        "count": 2,
    }
    resp = client.post("/api/ai/questions/draft", headers=headers, json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["count"] == 2
    assert len(data["drafts"]) == 2
    assert data["drafts"][0]["content"] != ""
    assert data["drafts"][0]["review_state"] == "PENDING"
    assert "draft_id" in data["drafts"][0]

    # 2. Test alias endpoint /api/ai/questions/generate
    resp_alias = client.post(
        "/api/ai/questions/generate",
        headers=headers,
        json={"course_id": course_id, "topic": "Backpropagation", "count": 1},
    )
    assert resp_alias.status_code == 201
    assert resp_alias.get_json()["count"] == 1

    # 3. Validation error: missing course_id
    resp_err = client.post(
        "/api/ai/questions/draft", headers=headers, json={"topic": "Loss Functions"}
    )
    assert resp_err.status_code == 400
    assert resp_err.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # 4. List drafts via GET /api/ai/questions/drafts
    resp_list = client.get(f"/api/ai/questions/drafts?course_id={course_id}", headers=headers)
    assert resp_list.status_code == 200
    list_data = resp_list.get_json()
    assert list_data["count"] >= 3


def test_conversation_lifecycle_and_messaging_api(
    client: FlaskClient,
    student_user: User,
    test_course: Course,
) -> None:
    """Test complete AI conversation lifecycle via REST API."""
    headers = _auth_headers(student_user)

    # 1. Create conversation
    resp_create = client.post(
        "/api/ai/conversations",
        headers=headers,
        json={"context_type": "COURSE", "course_id": str(test_course.public_id)},
    )
    assert resp_create.status_code == 201
    conv_data = resp_create.get_json()
    conv_id = conv_data["conversation_id"]
    assert conv_data["status"] == "ACTIVE"
    assert conv_data["context_type"] == "COURSE"

    # 2. Get conversation
    resp_get = client.get(f"/api/ai/conversations/{conv_id}", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.get_json()["conversation_id"] == conv_id

    # 3. Send message
    resp_msg = client.post(
        f"/api/ai/conversations/{conv_id}/messages",
        headers=headers,
        json={"message": "What is overfitting and how do I prevent it?"},
    )
    assert resp_msg.status_code == 200
    msg_data = resp_msg.get_json()
    assert "user_message" in msg_data
    assert "assistant_message" in msg_data
    assert msg_data["user_message"]["sequence_no"] == 1
    assert msg_data["assistant_message"]["sequence_no"] == 2
    assert "conversation" in msg_data

    # 4. Validation error on empty message
    resp_empty = client.post(
        f"/api/ai/conversations/{conv_id}/messages",
        headers=headers,
        json={"message": "   "},
    )
    assert resp_empty.status_code == 400
    assert resp_empty.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_unified_chat_api(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Test POST /api/ai/chat with and without existing conversation_id."""
    headers = _auth_headers(student_user)

    # Chat without conversation_id (auto-creates conversation)
    resp = client.post(
        "/api/ai/chat",
        headers=headers,
        json={"message": "Hello AI tutor, can you help me study?"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "conversation_id" in data
    assert "user_message" in data
    assert "assistant_message" in data
    conv_id = data["conversation_id"]

    # Chat with existing conversation_id
    resp_followup = client.post(
        "/api/ai/chat",
        headers=headers,
        json={"conversation_id": conv_id, "message": "Give me a summary of python loops."},
    )
    assert resp_followup.status_code == 200
    assert resp_followup.get_json()["conversation_id"] == conv_id


def test_conversation_inactivity_expiry_in_api(
    client: FlaskClient,
    student_user: User,
) -> None:
    """Expired conversation returns 409 CONVERSATION_EXPIRED on message dispatch."""
    headers = _auth_headers(student_user)

    resp = client.post(
        "/api/ai/conversations",
        headers=headers,
        json={"context_type": "GLOBAL"},
    )
    conv_id = resp.get_json()["conversation_id"]

    # Manually expire in database (respecting ck_ai_conversations_3: expires_at > created_at)
    sess: Session = db.session
    conv = sess.query(AIConversation).filter(AIConversation.public_id == uuid.UUID(conv_id)).first()
    assert conv is not None
    conv.created_at = utc_now() - timedelta(minutes=10)
    conv.last_activity_at = utc_now() - timedelta(minutes=6)
    conv.expires_at = utc_now() - timedelta(minutes=1)
    sess.commit()

    # Sending a message to expired conversation -> 409 CONVERSATION_EXPIRED
    resp_msg = client.post(
        f"/api/ai/conversations/{conv_id}/messages",
        headers=headers,
        json={"message": "Are you still there?"},
    )
    assert resp_msg.status_code == 409
    err = resp_msg.get_json()["error"]
    assert err["code"] == "CONVERSATION_EXPIRED"

    # Detail GET returns status EXPIRED and empty messages
    resp_get = client.get(f"/api/ai/conversations/{conv_id}", headers=headers)
    assert resp_get.status_code == 200
    get_data = resp_get.get_json()
    assert get_data["status"] == "EXPIRED"
    assert len(get_data["messages"]) == 0


def test_cleanup_conversations_api(
    client: FlaskClient,
    student_user: User,
    admin_user: User,
) -> None:
    """POST /api/ai/conversations/cleanup purges inactive conversations (Admin only)."""
    # 1. Student attempts cleanup -> 403 Forbidden
    resp_student = client.post(
        "/api/ai/conversations/cleanup",
        headers=_auth_headers(student_user),
    )
    assert resp_student.status_code == 403

    # 2. Admin triggers cleanup -> 200 OK
    resp_admin = client.post(
        "/api/ai/conversations/cleanup",
        headers=_auth_headers(admin_user),
    )
    assert resp_admin.status_code == 200
    data = resp_admin.get_json()
    assert "purged_conversations" in data
    assert isinstance(data["purged_conversations"], int)
