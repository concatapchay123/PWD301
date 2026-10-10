"""Tests for Assessment Review Policy engine (CORRECT_WRONG_ONLY, NEVER, IMMEDIATE)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from pwd301.extensions import db
from pwd301.models.identity import Role
from pwd301.services.assessment_service import (
    ALLOWED_ANSWER_VISIBILITY_POLICIES,
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    get_attempt_result_for_student,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


def test_allowed_answer_visibility_policies_contains_correct_wrong_only():
    """Ensure CORRECT_WRONG_ONLY is a recognized answer visibility policy."""
    assert "CORRECT_WRONG_ONLY" in ALLOWED_ANSWER_VISIBILITY_POLICIES
    assert "IMMEDIATE" in ALLOWED_ANSWER_VISIBILITY_POLICIES
    assert "NEVER" in ALLOWED_ANSWER_VISIBILITY_POLICIES


@pytest.fixture
def review_attempt(app):
    for code in ("STUDENT", "INSTRUCTOR", "ADMIN"):
        db.session.add(Role(code=code, name=code))
    db.session.commit()
    users = {}
    for role in ("STUDENT", "INSTRUCTOR", "ADMIN"):
        user = register_user(f"review-{role.lower()}@example.com", "Password@123", role)
        users[role] = assign_role_to_user(user.id, role)
    instructor = users["INSTRUCTOR"]
    student = users["STUDENT"]
    course = create_course(instructor, {"course_code": "REVIEW-090", "title": "Review policy"})
    change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(users["ADMIN"], course.id, "APPROVED")
    change_course_status(users["ADMIN"], course.id, "PUBLISHED")
    enroll_student(student, course.id)
    now = datetime.now(UTC)
    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Review assessment",
            "assessment_type": "QUIZ",
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
            "open_at": (now - timedelta(hours=1)).isoformat(),
            "close_at": (now + timedelta(hours=1)).isoformat(),
        },
    )
    section = create_section(instructor, assessment.id, {"title": "Questions"})
    question = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Select the two correct choices",
            "default_points": 10,
            "explanation": "Protected explanation",
            "choices": [
                {"content": "First correct", "is_correct": True, "position": 1},
                {"content": "Missed correct", "is_correct": True, "position": 2},
                {"content": "Selected wrong", "is_correct": False, "position": 3},
            ],
        },
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": question.id, "section_id": section.id, "points_assigned": 10},
    )
    publish_assessment(instructor, assessment.id)
    attempt, lease = start_assessment_attempt(student, assessment.id)
    aq = attempt.attempt_questions[0]
    selected = [
        str(c.choice_key_snapshot)
        for c in aq.choice_snapshots
        if c.content_snapshot != "Missed correct"
    ]
    save_attempt_answer(
        student,
        attempt.id,
        aq.id,
        {"selected_choice_keys": selected, "client_sequence": 1, "change_id": str(uuid.uuid4())},
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student, attempt.id, uuid.uuid4(), raw_lease_token=lease)
    return student, instructor, assessment, attempt


def test_never_returns_empty_detail_list_on_result_api(client, review_attempt):
    student, _, assessment, attempt = review_attempt
    assessment.answer_visibility_policy = "NEVER"
    db.session.commit()
    token = create_token_pair(student)["access_token"]
    response = client.get(
        f"/api/attempts/{attempt.public_id}/result", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["score_status"] == "RELEASED"
    assert response.json["questions"] == []


def test_restricted_policy_reveals_only_selected_choice_correctness(review_attempt):
    student, _, assessment, attempt = review_attempt
    assessment.answer_visibility_policy = "CORRECT_WRONG_ONLY"
    db.session.commit()
    result = get_attempt_result_for_student(student, attempt.id)
    question = result["questions"][0]
    assert "explanation" not in question
    assert "feedback" not in question
    assert "correct_answer" not in question
    choices = {c["content"]: c for c in question["choices"]}
    assert choices["First correct"]["is_correct"] is True
    assert choices["Selected wrong"]["is_correct"] is False
    assert "is_correct" not in choices["Missed correct"]


def test_full_review_uses_historical_revision_when_choice_link_is_missing(review_attempt):
    student, _, _, attempt = review_attempt
    aq = attempt.attempt_questions[0]
    for choice in aq.choice_snapshots:
        choice.source_choice = None
    db.session.commit()
    question = get_attempt_result_for_student(student, attempt.id)["questions"][0]
    assert question["explanation"] == "Protected explanation"
    choices = {c["content"]: c for c in question["choices"]}
    assert choices["First correct"]["is_correct"] is True
    assert choices["Missed correct"]["is_correct"] is True
    assert choices["Selected wrong"]["is_correct"] is False
