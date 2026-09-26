"""Integration tests for Assessment Attempt Delivery REST API endpoints (TASK-013)."""

from __future__ import annotations

import re
import io
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.file_import import QuestionRevisionResource
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import store_file_stream
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def assert_adr002_and_security_clean(data: Any) -> None:
    """Recursively verify no internal BIGINT PKs, FKs, or answers/explanations leak (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal FK 'creator_user_id' leaked: {data}"
            assert k != "student_user_id", f"Internal FK 'student_user_id' leaked: {data}"
            assert k != "course_internal_id", f"Internal FK 'course_internal_id' leaked: {data}"
            assert k != "is_correct", f"Security violation: 'is_correct' leaked: {data}"
            assert k != "explanation", f"Security violation: 'explanation' leaked: {data}"
            assert k != "source_choice_id", f"Internal FK 'source_choice_id' leaked: {data}"
            assert k != "source_question_id", f"Internal FK 'source_question_id' leaked: {data}"

            if (
                k
                in (
                    "attempt_id",
                    "assessment_id",
                    "course_id",
                    "attempt_question_id",
                    "choice_key",
                    "public_id",
                )
                and v is not None
            ):
                assert isinstance(v, str), f"Field '{k}' should be string, got {type(v)}: {v}"
                assert UUID_REGEX.match(v), f"Field '{k}' is not a valid UUID: {v}"

            assert_adr002_and_security_clean(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002_and_security_clean(item)


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
    u = register_user("attempt_api_inst@example.com", "Password@123", "Attempt API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an unrelated Instructor User."""
    u = register_user("attempt_api_other_inst@example.com", "Password@123", "Other API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin User."""
    u = register_user("attempt_api_admin@example.com", "Password@123", "Attempt API Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User A."""
    u = register_user("attempt_api_stud_a@example.com", "Password@123", "Student API User A")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_user_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User B."""
    u = register_user("attempt_api_stud_b@example.com", "Password@123", "Student API User B")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_headers(student_user: User) -> dict[str, str]:
    """JWT headers for Student A."""
    tokens = create_token_pair(student_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def student_b_headers(student_user_b: User) -> dict[str, str]:
    """JWT headers for Student B."""
    tokens = create_token_pair(student_user_b)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def instructor_headers(instructor_user: User) -> dict[str, str]:
    """JWT headers for Instructor."""
    tokens = create_token_pair(instructor_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def other_instructor_headers(other_instructor: User) -> dict[str, str]:
    """JWT headers for Other Instructor."""
    tokens = create_token_pair(other_instructor)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    """JWT headers for Admin."""
    tokens = create_token_pair(admin_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_published_assessment_helper(
    instructor_user: User,
    course: Course,
    title: str,
    open_at: datetime | None = None,
    close_at: datetime | None = None,
    time_limit_minutes: int = 60,
    attempt_limit: int = 2,
) -> Assessment:
    """Helper to create and publish an assessment with a question."""
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "APPLY",
            "content": "Which protocol is REST based on?",
            "explanation": "Secret explanation: REST uses HTTP!",
            "default_points": 5.0,
            "choices": [
                {"content": "HTTP", "is_correct": True, "position": 1},
                {"content": "FTP", "is_correct": False, "position": 2},
                {"content": "SMTP", "is_correct": False, "position": 3},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=db.session,
    )
    db.session.commit()

    now = datetime.now(UTC)
    if open_at is None:
        open_at = now - timedelta(hours=1)
    if close_at is None:
        close_at = now + timedelta(days=2)

    asm = create_assessment(
        instructor_user,
        course.id,
        {
            "title": title,
            "assessment_type": "MIDTERM",
            "scoring_policy": "HIGHEST",
            "time_limit_minutes": time_limit_minutes,
            "attempt_limit": attempt_limit,
            "open_at": open_at.isoformat(),
            "close_at": close_at.isoformat(),
            "shuffle_questions": True,
            "shuffle_choices": True,
        },
        session=db.session,
    )
    sec = create_section(
        instructor_user,
        asm.id,
        {"title": "Section 1", "position": 1},
        session=db.session,
    )
    db.session.commit()

    assign_question(
        instructor_user,
        asm.id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 5.0},
        session=db.session,
    )
    db.session.commit()

    publish_assessment(instructor_user, asm.id, session=db.session)
    db.session.commit()
    return asm


@pytest.fixture
def published_assessment(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> Assessment:
    """Create course, enroll student, create question, create assessment, and publish."""
    c = create_course(
        instructor_user,
        {
            "course_code": "ATT-API-101",
            "title": "Attempt API Testing Course",
            "summary": "Course for testing assessment attempts via REST API",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    enroll_student(student_user, c.id, session=db.session)

    return _create_published_assessment_helper(
        instructor_user,
        c,
        title="Midterm Exam",
        time_limit_minutes=60,
        attempt_limit=2,
    )


def test_start_attempt_api_success(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
) -> None:
    """Test starting an assessment attempt via POST /api/assessments/<id>/attempts."""
    res = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res.status_code == 201
    data = res.get_json()

    assert data["assessment_id"] == str(published_assessment.public_id)
    assert data["attempt_number"] == 1
    assert data["status"] == "IN_PROGRESS"
    assert "lease_token" in data
    assert len(data["lease_token"]) == 64
    assert data["total_questions"] == 1
    assert data["total_points"] == 5.0
    assert data["remaining_seconds"] > 0
    assert "questions" in data
    assert len(data["questions"]) == 1

    # Verify choices delivery
    q_data = data["questions"][0]
    assert len(q_data["choices"]) == 3
    for ch in q_data["choices"]:
        assert "choice_key" in ch
        assert UUID_REGEX.match(ch["choice_key"])

    # Strict ADR-002 and security checks
    assert_adr002_and_security_clean(data)


def test_get_attempt_delivery_api(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
    instructor_user: User,
) -> None:
    """Test delivery resumes candidate answers and includes clean question images."""
    assignment = (
        db.session.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == published_assessment.id)
        .first()
    )
    image = store_file_stream(
        actor=instructor_user,
        course_id=published_assessment.course_id,
        file_stream=io.BytesIO(b"\x89PNG\r\n\x1a\nimage-data"),
        filename="question.png",
        content_type="image/png",
        asset_type="RESOURCE",
        session=db.session,
    )
    image.status = "ACTIVE"
    if image.revisions:
        image.revisions[0].status = "ACTIVE"
    db.session.add(
        QuestionRevisionResource(
            question_revision_id=assignment.question.current_revision.id,
            file_asset_id=image.id,
            position=1,
            resource_role="IMAGE",
        )
    )
    db.session.commit()

    start_res = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert start_res.status_code == 201
    started = start_res.get_json()
    attempt_id = started["attempt_id"]

    res = client.get(f"/api/attempts/{attempt_id}", headers=student_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["attempt_id"] == attempt_id
    assert data["assessment_id"] == str(published_assessment.public_id)
    assert data["status"] == "IN_PROGRESS"
    assert data["remaining_seconds"] > 0
    assert len(data["questions"]) == 1

    question = data["questions"][0]
    selected_key = question["choices"][0]["choice_key"]
    save_res = client.put(
        f"/api/attempts/{attempt_id}/answers/{question['attempt_question_id']}",
        headers={**student_headers, "X-Attempt-Lease-Token": started["lease_token"]},
        json={"selected_choice_keys": [selected_key]},
    )
    assert save_res.status_code == 200

    resumed_res = client.get(f"/api/attempts/{attempt_id}", headers=student_headers)
    assert resumed_res.status_code == 200
    resumed_question = resumed_res.get_json()["questions"][0]
    assert resumed_question["selected_choice_keys"] == [selected_key]
    assert resumed_question["choices"][0]["is_selected"] is True
    assert resumed_question["resources"][0]["url"].endswith("?disposition=inline")
    assert_adr002_and_security_clean(resumed_res.get_json())


def test_batch_created_question_keeps_course_image_in_attempt_delivery(
    client: FlaskClient,
    published_assessment: Assessment,
    instructor_user: User,
    instructor_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    """Instructor question images must be attached and delivered only after scan success."""
    image = store_file_stream(
        actor=instructor_user,
        course_id=published_assessment.course_id,
        file_stream=io.BytesIO(b"\x89PNG\r\n\x1a\nimage-data"),
        filename="exam-question.png",
        content_type="image/png",
        asset_type="RESOURCE",
        session=db.session,
    )
    image.status = "ACTIVE"
    if image.revisions:
        image.revisions[0].status = "ACTIVE"
    db.session.commit()

    create_response = client.post(
        f"/instructor/assessments/{published_assessment.public_id}/questions/batch",
        headers=instructor_headers,
        json={
            "questions": [
                {
                    "question_type": "SINGLE_CHOICE",
                    "content": "Which protocol image is attached?",
                    "points": 1,
                    "choices": [
                        {"content": "HTTP", "is_correct": True},
                        {"content": "FTP", "is_correct": False},
                    ],
                    "image_asset_id": str(image.public_id),
                }
            ]
        },
    )
    assert create_response.status_code == 201

    started = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert started.status_code == 201
    delivery = client.get(
        f"/api/attempts/{started.get_json()['attempt_id']}", headers=student_headers
    )
    assert delivery.status_code == 200
    question = next(
        item
        for item in delivery.get_json()["questions"]
        if item["content"] == "Which protocol image is attached?"
    )
    assert len(question["resources"]) == 1
    assert question["resources"][0]["url"].endswith("?disposition=inline")
    assert_adr002_and_security_clean(delivery.get_json())


def test_interactive_question_groups_are_delivered_without_answer_keys(
    client: FlaskClient,
    published_assessment: Assessment,
    instructor_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    """Grouped drag choices and typed blanks survive authoring without leaking keys."""
    created = client.post(
        f"/instructor/assessments/{published_assessment.public_id}/questions/batch",
        headers=instructor_headers,
        json={
            "questions": [
                {
                    "question_type": "MULTIPLE_CHOICE",
                    "content": "Protocol ___ uses method ___.",
                    "points": 2,
                    "choices": [
                        {"content": "[[PWD301:G:DRAG:1]]HTTP", "is_correct": True},
                        {"content": "[[PWD301:G:DRAG:1]]FTP", "is_correct": False},
                        {"content": "[[PWD301:G:DRAG:2]]GET", "is_correct": True},
                        {"content": "[[PWD301:G:DRAG:2]]POST", "is_correct": False},
                    ],
                },
                {
                    "question_type": "SHORT_ANSWER",
                    "content": "[[PWD301:FI_V1]]Protocol ___ uses method ___.",
                    "points": 2,
                    "accepted_answers": [
                        "[[PWD301:FI:1]]HTTP",
                        "[[PWD301:FI:1]]Hypertext Transfer Protocol",
                        "[[PWD301:FI:2]]GET",
                        "[[PWD301:FI:2]]Retrieval",
                    ],
                },
                {
                    "question_type": "MULTIPLE_CHOICE",
                    "content": "Match each protocol to its description.",
                    "points": 2,
                    "choices": [
                        {"content": "[[PWD301:G:MATCH:1]]HTTP|||Web transfer", "is_correct": True},
                        {"content": "[[PWD301:G:MATCH:1]]FTP|||File transfer", "is_correct": False},
                        {"content": "[[PWD301:G:MATCH:2]]FTP|||File transfer", "is_correct": True},
                        {"content": "[[PWD301:G:MATCH:2]]HTTP|||Web transfer", "is_correct": False},
                    ],
                },
            ]
        },
    )
    assert created.status_code == 201

    started = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert started.status_code == 201
    delivery = client.get(
        f"/api/attempts/{started.get_json()['attempt_id']}", headers=student_headers
    )
    assert delivery.status_code == 200
    questions = delivery.get_json()["questions"]
    drag_question = next(
        question for question in questions if question["interaction_type"] == "DRAG_DROP"
    )
    assert drag_question["content"] == "Protocol ___ uses method ___."
    assert sorted({choice["interaction_group"] for choice in drag_question["choices"]}) == [1, 2]
    assert {choice["content"] for choice in drag_question["choices"]} == {
        "HTTP",
        "FTP",
        "GET",
        "POST",
    }
    assert all("is_correct" not in choice for choice in drag_question["choices"])

    fill_question = next(
        question for question in questions if question["interaction_type"] == "FILL_IN"
    )
    assert fill_question["content"] == "Protocol ___ uses method ___."
    assert fill_question["choices"] == []
    assert "accepted_answers" not in fill_question
    matching_question = next(
        question for question in questions if question["interaction_type"] == "MATCHING"
    )
    assert len(matching_question["choices"]) == 4
    assert {choice["interaction_left"] for choice in matching_question["choices"]} == {
        "HTTP",
        "FTP",
    }
    assert all("is_correct" not in choice for choice in matching_question["choices"])
    assert "[[PWD301:" not in str(delivery.get_json())


def test_list_assessment_attempts_api(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
) -> None:
    """Test listing attempts for an assessment via GET /api/assessments/<id>/attempts."""
    # Start attempt
    client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )

    res = client.get(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res.status_code == 200
    data = res.get_json()

    assert data["total"] == 1
    assert len(data["attempts"]) == 1
    attempt_info = data["attempts"][0]
    assert attempt_info["attempt_number"] == 1
    assert attempt_info["status"] == "IN_PROGRESS"
    assert_adr002_and_security_clean(data)


def test_start_attempt_unauthorized(
    client: FlaskClient,
    published_assessment: Assessment,
) -> None:
    """Test starting attempt without authentication returns 401."""
    res = client.post(f"/api/assessments/{published_assessment.public_id}/attempts")
    assert res.status_code == 401


def test_start_attempt_not_enrolled(
    client: FlaskClient,
    published_assessment: Assessment,
    student_b_headers: dict[str, str],
) -> None:
    """Test starting attempt when student is not enrolled returns 400 VALIDATION_ERROR."""
    res = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_b_headers,
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_start_attempt_active_conflict(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
) -> None:
    """Test starting a second attempt while one is already in progress returns 409."""
    res1 = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res1.status_code == 201

    res2 = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res2.status_code == 409
    data = res2.get_json()
    assert data["error"]["code"] == "CONFLICT"


def test_start_attempt_limit_exceeded(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
) -> None:
    """Test exceeding attempt_limit returns 409 ATTEMPT_LIMIT."""
    # published_assessment has attempt_limit = 2
    res1 = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res1.status_code == 201

    # Simulate submission of attempt 1
    att1 = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.attempt_number == 1).first()
    assert att1 is not None
    att1.status = "SUBMITTED"
    att1.submitted_at = datetime.now(UTC)
    db.session.commit()

    # Attempt 2 should succeed
    res2 = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res2.status_code == 201

    # Simulate submission of attempt 2
    att2 = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.attempt_number == 2).first()
    assert att2 is not None
    att2.status = "SUBMITTED"
    att2.submitted_at = datetime.now(UTC)
    db.session.commit()

    # Attempt 3 should fail with 409 ATTEMPT_LIMIT
    res3 = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert res3.status_code == 409
    data = res3.get_json()
    assert data["error"]["code"] == "ATTEMPT_LIMIT"


def test_start_attempt_not_open(
    client: FlaskClient,
    student_headers: dict[str, str],
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Test starting attempt before open_at returns 400 NOT_OPEN."""
    c = create_course(
        instructor_user,
        {"course_code": "NOT-OPEN-101", "title": "Future Course", "summary": "Test"},
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    enroll_student(student_user, c.id, session=db.session)

    now = datetime.now(UTC)
    asm = _create_published_assessment_helper(
        instructor_user,
        c,
        title="Future Exam",
        open_at=now + timedelta(days=1),
        close_at=now + timedelta(days=3),
    )

    res = client.post(
        f"/api/assessments/{asm.public_id}/attempts",
        headers=student_headers,
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"]["code"] == "NOT_OPEN"


def test_start_attempt_closed(
    client: FlaskClient,
    student_headers: dict[str, str],
    instructor_user: User,
    admin_user: User,
    student_user: User,
) -> None:
    """Test starting attempt after close_at returns 400 CLOSED."""
    c = create_course(
        instructor_user,
        {"course_code": "CLOSED-101", "title": "Past Course", "summary": "Test"},
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    enroll_student(student_user, c.id, session=db.session)

    now = datetime.now(UTC)
    asm = _create_published_assessment_helper(
        instructor_user,
        c,
        title="Past Exam",
        open_at=now - timedelta(days=3),
        close_at=now - timedelta(days=1),
    )

    res = client.post(
        f"/api/assessments/{asm.public_id}/attempts",
        headers=student_headers,
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"]["code"] == "CLOSED"


def test_attempt_not_found(
    client: FlaskClient,
    student_headers: dict[str, str],
) -> None:
    """Test 404 on non-existent attempt or assessment."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    res1 = client.get(f"/api/attempts/{fake_uuid}", headers=student_headers)
    assert res1.status_code == 404
    assert res1.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    res2 = client.post(f"/api/assessments/{fake_uuid}/attempts", headers=student_headers)
    assert res2.status_code == 404
    assert res2.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_attempt_idor_defense_via_api(
    client: FlaskClient,
    published_assessment: Assessment,
    student_headers: dict[str, str],
    student_b_headers: dict[str, str],
    other_instructor_headers: dict[str, str],
    instructor_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    """Test that only the owning student or admin can access candidate delivery."""
    # Student A starts attempt
    start_res = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert start_res.status_code == 201
    attempt_id = start_res.get_json()["attempt_id"]

    # Student A can access own delivery
    res_a = client.get(f"/api/attempts/{attempt_id}", headers=student_headers)
    assert res_a.status_code == 200

    # Student B should get 403 Forbidden
    res_b = client.get(f"/api/attempts/{attempt_id}", headers=student_b_headers)
    assert res_b.status_code == 403

    # Unrelated instructor should get 403 Forbidden
    res_other = client.get(f"/api/attempts/{attempt_id}", headers=other_instructor_headers)
    assert res_other.status_code == 403

    # Course instructor should also get 403 Forbidden (student active exam is private)
    res_inst = client.get(f"/api/attempts/{attempt_id}", headers=instructor_headers)
    assert res_inst.status_code == 403

    # Admin should get 200 OK
    res_admin = client.get(f"/api/attempts/{attempt_id}", headers=admin_headers)
    assert res_admin.status_code == 200
