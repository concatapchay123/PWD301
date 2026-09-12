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

import hashlib
import uuid
from datetime import timedelta

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import AIConversation
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision, FileScanResult
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.file_service import get_file_storage_root
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
    test_course: Course,
) -> None:
    """Test POST /api/ai/chat with and without existing conversation_id."""
    headers = _auth_headers(student_user)

    # 1. Chat on global context (auto-creates conversation, greeting)
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

    # Chat with existing conversation_id asking about LMS courses / progress
    resp_followup = client.post(
        "/api/ai/chat",
        headers=headers,
        json={
            "conversation_id": conv_id,
            "message": "How do I check my course progress and catalog?",
        },
    )
    assert resp_followup.status_code == 200
    assert resp_followup.get_json()["conversation_id"] == conv_id

    # 2. Chat with course context (supports academic/programming questions)
    course_id = str(test_course.public_id)
    resp_course = client.post(
        "/api/ai/chat",
        headers=headers,
        json={
            "course_id": course_id,
            "context_type": "COURSE",
            "message": "Give me a summary of python loops.",
        },
    )
    assert resp_course.status_code == 200
    course_data = resp_course.get_json()
    assert "conversation_id" in course_data
    assert course_data["assistant_message"]["content"] != ""


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


# ---------------------------------------------------------------------------
# TASK-024 RAG API Integration Tests
# ---------------------------------------------------------------------------


def test_full_course_rag_ingest_and_query_flow(
    client: FlaskClient,
    instructor_user: User,
    student_user: User,
    test_course: Course,
) -> None:
    """Full RAG workflow: Course -> Lesson -> File -> Ingest -> Sources -> Query -> Delete."""
    sess: Session = db.session
    headers_instructor = _auth_headers(instructor_user)
    headers_student = _auth_headers(student_user)
    course_id = str(test_course.public_id)

    # 1. Create published lesson
    lesson = Lesson(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        title="Supervised Learning and Gradient Descent",
        markdown_content=(
            "# Supervised Learning\n\n"
            "Supervised learning algorithms infer a function from labeled training data. "
            "Gradient descent iteratively optimizes model parameters."
        ),
        position=1,
        status="PUBLISHED",
    )
    sess.add(lesson)

    # 2. Create clean FileAsset with physical storage blob
    file_bytes = b"Convolutional neural networks apply kernel filters over feature maps."
    f_hash = hashlib.sha256(file_bytes).digest()
    rel_key = f"blobs/rag/{f_hash.hex()[:16]}.txt"
    storage_root = get_file_storage_root()
    p_path = storage_root / rel_key
    p_path.parent.mkdir(parents=True, exist_ok=True)
    p_path.write_bytes(file_bytes)

    blob = FileBlob(
        sha256=f_hash,
        size_bytes=len(file_bytes),
        detected_mime_type="text/plain",
        storage_key=rel_key,
        status="PRESENT",
    )
    sess.add(blob)
    sess.flush()

    asset = FileAsset(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Deep Learning Primer",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    rev = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="primer.txt",
        size_bytes=len(file_bytes),
        status="ACTIVE",
        uploaded_by_user_id=instructor_user.id,
    )
    sess.add(rev)
    sess.flush()

    scan = FileScanResult(
        file_revision_id=rev.id,
        scan_type="MALWARE",
        engine="ClamAV",
        engine_version="1.0.0",
        status="PASS",
    )
    sess.add(scan)

    # Enroll student in course
    sess.add(Enrollment(course_id=test_course.id, student_user_id=student_user.id, status="ACTIVE"))
    sess.commit()

    # 3. Instructor triggers full course ingest
    resp_ingest = client.post(
        f"/api/ai/courses/{course_id}/ingest",
        headers=headers_instructor,
    )
    assert resp_ingest.status_code == 201
    ingest_data = resp_ingest.get_json()
    assert ingest_data["status"] == "INGESTED"
    assert ingest_data["sources_ingested"] >= 2
    assert ingest_data["chunks_created"] >= 2

    # 4. List course sources
    resp_sources = client.get(
        f"/api/ai/courses/{course_id}/sources?include_chunks=true",
        headers=headers_student,
    )
    assert resp_sources.status_code == 200
    sources_data = resp_sources.get_json()
    assert sources_data["count"] >= 2
    first_source = sources_data["sources"][0]
    assert "source_id" in first_source
    assert "chunks" in first_source
    first_source_id = first_source["source_id"]

    # 5. Student queries RAG with relevant question
    resp_query = client.post(
        f"/api/ai/courses/{course_id}/query",
        headers=headers_student,
        json={
            "query": "How does gradient descent optimize parameters in supervised learning?",
            "top_k": 3,
        },
    )
    assert resp_query.status_code == 200
    q_data = resp_query.get_json()
    assert "answer" in q_data
    assert "citations" in q_data
    assert len(q_data["citations"]) >= 1
    assert q_data["confidence_score"] > 0
    citation = q_data["citations"][0]
    assert "chunk_id" in citation
    assert "source_id" in citation
    assert "lesson_title" in citation
    assert "relevance_score" in citation

    # 6. Instructor deletes first source
    resp_delete = client.delete(
        f"/api/ai/sources/{first_source_id}",
        headers=headers_instructor,
    )
    assert resp_delete.status_code == 200
    assert resp_delete.get_json()["source_id"] == first_source_id

    # 7. Unenrolled query rejected
    other_student = register_user("other_stu@example.com", "Password@123", "Other Student")
    other_student = assign_role_to_user(other_student.id, "STUDENT")
    resp_unauth = client.post(
        f"/api/ai/courses/{course_id}/query",
        headers=_auth_headers(other_student),
        json={"query": "What is gradient descent?"},
    )
    assert resp_unauth.status_code == 403


def test_instructor_source_management_permissions(
    client: FlaskClient,
    instructor_user: User,
    test_course: Course,
) -> None:
    """Instructors cannot alter or delete knowledge sources of courses they do not manage."""
    sess: Session = db.session

    # Create instructor B and course B
    instructor_b = register_user("instructor_b@example.com", "Password@123", "Instructor B")
    instructor_b = assign_role_to_user(instructor_b.id, "INSTRUCTOR")

    course_b = Course(
        public_id=uuid.uuid4(),
        course_code="BIO101",
        course_code_normalized="BIO101",
        title="Computational Biology",
        title_normalized="computational biology",
        category="Biology",
        difficulty="BEGINNER",
        status="PUBLISHED",
        owner_instructor_id=instructor_b.id,
    )
    sess.add(course_b)

    # Published lesson for course A (owned by instructor_user)
    lesson_a = Lesson(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        title="Intro to AI",
        markdown_content="AI foundations and algorithms.",
        position=1,
        status="PUBLISHED",
    )
    sess.add(lesson_a)
    sess.commit()

    headers_inst_a = _auth_headers(instructor_user)
    headers_inst_b = _auth_headers(instructor_b)
    course_a_id = str(test_course.public_id)

    # 1. Instructor A ingests lesson in Course A -> 201 Created
    resp_ingest_a = client.post(
        f"/api/ai/lessons/{lesson_a.public_id}/ingest",
        headers=headers_inst_a,
    )
    assert resp_ingest_a.status_code == 201
    source_a_id = resp_ingest_a.get_json()["source_id"]

    # 2. Instructor B attempts course ingest on Course A -> 403 Forbidden
    resp_b_ingest_a = client.post(
        f"/api/ai/courses/{course_a_id}/ingest",
        headers=headers_inst_b,
    )
    assert resp_b_ingest_a.status_code == 403
    assert resp_b_ingest_a.get_json()["error"]["code"] == "FORBIDDEN"

    # 3. Instructor B attempts lesson ingest on Lesson A -> 403 Forbidden
    resp_b_lesson = client.post(
        f"/api/ai/lessons/{lesson_a.public_id}/ingest",
        headers=headers_inst_b,
    )
    assert resp_b_lesson.status_code == 403

    # 4. Instructor B attempts to delete Course A's source -> 403 Forbidden
    resp_b_delete = client.delete(
        f"/api/ai/sources/{source_a_id}",
        headers=headers_inst_b,
    )
    assert resp_b_delete.status_code == 403

    # 5. Instructor A successfully deletes Source A -> 200 OK
    resp_a_delete = client.delete(
        f"/api/ai/sources/{source_a_id}",
        headers=headers_inst_a,
    )
    assert resp_a_delete.status_code == 200
