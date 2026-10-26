"""Tests for Assessment Review Policy engine (CORRECT_WRONG_ONLY, NEVER, IMMEDIATE)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from backend.extensions import db
from backend.models.identity import Role
from backend.models.types import utc_now
from backend.services.assessment_service import (
    ALLOWED_ANSWER_VISIBILITY_POLICIES,
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from backend.services.attempt_service import (
    get_attempt_result_for_student,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from backend.services.course_service import change_course_status, create_course
from backend.services.enrollment_service import enroll_student
from backend.services.jwt_auth_service import create_token_pair
from backend.services.question_bank_service import create_question
from backend.services.user_service import assign_role_to_user, register_user


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
    change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(users["ADMIN"], course.id, "APPROVED")
    change_course_status(users["ADMIN"], course.id, "PUBLISHED")
    enroll_student(student, course.id)
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


@pytest.mark.parametrize("api", [False, True])
@pytest.mark.parametrize("active", [False, True])
def test_student_assessment_config_does_not_expose_explanations(
    client, review_attempt, api, active
):
    student, _, assessment, attempt = review_attempt
    assessment.allow_student_view_results = False
    assessment.answer_visibility_policy = "NEVER"
    attempt.status = "IN_PROGRESS" if active else "CANCELLED"
    db.session.commit()
    if api:
        token = create_token_pair(student)["access_token"]
        response = client.get(
            f"/api/assessments/{assessment.public_id}", headers={"Authorization": f"Bearer {token}"}
        )
    else:
        _login_review_student(client, student)
        response = client.get(f"/student/assessments/{assessment.public_id}")
    assert response.status_code == 200
    assert "Protected explanation" not in response.get_data(as_text=True)


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


def _login_review_student(client, student):
    from backend.services.session_auth_service import create_auth_session

    _, raw_key = create_auth_session(student, session=db.session)
    db.session.commit()
    with client.session_transaction() as session:
        session["_user_id"] = str(student.id)
        session["auth_session_key"] = raw_key
        session["auth_version"] = student.auth_version
        session["auth_source"] = "SESSION"


@pytest.mark.parametrize("api", [False, True])
def test_disabled_review_retains_released_total_but_no_question_details(
    client, review_attempt, api
):
    student, _, assessment, attempt = review_attempt
    assessment.allow_student_view_results = False
    db.session.commit()
    expected_score = float(attempt.result.raw_score)
    if api:
        token = create_token_pair(student)["access_token"]
        response = client.get(
            f"/api/attempts/{attempt.public_id}/result",
            headers={"Authorization": f"Bearer {token}"},
        )
    else:
        _login_review_student(client, student)
        response = client.get(f"/student/attempt/{attempt.public_id}/result")
    assert response.status_code == 200
    data = response.json
    assert data["score_status"] == "RELEASED"
    assert data["raw_score"] == expected_score
    assert data["passed"] == attempt.result.passed
    assert data["allow_student_view_results"] is False
    for question in data["questions"]:
        assert question["content"]
        assert question["choices"] == []
        assert question["selected_choice_keys"] == []
        assert question["awarded_points"] is None
        assert question["points_assigned"] is None
        assert question["is_correct"] is None
        assert "student_answer_text" not in question
        assert "slot_results" not in question


def test_disabled_review_preserves_never_and_unreleased_policies(review_attempt):
    student, _, assessment, attempt = review_attempt
    assessment.allow_student_view_results = False
    assessment.answer_visibility_policy = "NEVER"
    db.session.flush()
    data = get_attempt_result_for_student(student, attempt.id)
    assert data["score_status"] == "RELEASED"
    assert data["questions"] == []
    assessment.score_release_policy = "AFTER_CLOSE"
    db.session.flush()
    data = get_attempt_result_for_student(student, attempt.id)
    assert data["score_status"] == "SCORE_HIDDEN"
    assert data["raw_score"] is None


def test_disabled_review_masks_question_grade_history(review_attempt):
    from backend.models.attempt_regrade import AttemptQuestionGradeHistory
    from backend.services.attempt_service import get_attempt_grade_history

    student, instructor, assessment, attempt = review_attempt
    db.session.add(
        AttemptQuestionGradeHistory(
            attempt_question_id=attempt.attempt_questions[0].id,
            old_points=0,
            new_points=3,
            reason_code="MANUAL_REVISION",
            actor_user_id=instructor.id,
            reason="Protected grading explanation",
        )
    )
    db.session.flush()
    assert get_attempt_grade_history(student, attempt.id)["question_history"]
    assessment.allow_student_view_results = False
    db.session.flush()
    assert get_attempt_grade_history(student, attempt.id)["question_history"] == []
    assert get_attempt_grade_history(instructor, attempt.id)["question_history"]


def test_invalid_formula_pdf_returns_safe_validation_error(client, review_attempt):
    student, _, _, attempt = review_attempt
    attempt.attempt_questions[0].content_snapshot = r"Invalid $\frac{1}{$"
    db.session.commit()
    _login_review_student(client, student)
    response = client.get(f"/student/attempt/{attempt.public_id}/result.pdf")
    assert response.status_code == 400
    assert "công thức" in response.get_data(as_text=True)
    assert "render.cjs" not in response.get_data(as_text=True)
    assert "node_modules" not in response.get_data(as_text=True)


def test_review_policy_matrix_on_session_and_jwt_apis(client, review_attempt):
    student, _, assessment, attempt = review_attempt
    _login_review_student(client, student)
    token = create_token_pair(student)["access_token"]
    now = datetime.now(UTC)
    publication_cases = [
        ("IMMEDIATE", now + timedelta(hours=1), "FINAL", True),
        ("AFTER_CLOSE", now + timedelta(hours=1), "FINAL", False),
        ("AFTER_CLOSE", now - timedelta(minutes=1), "FINAL", True),
        ("INSTRUCTOR_RELEASE", now + timedelta(hours=1), "FINAL", False),
        ("INSTRUCTOR_RELEASE", now + timedelta(hours=1), "RELEASED", True),
    ]
    for release, close_at, result_status, released in publication_cases:
        assessment.score_release_policy = release
        assessment.close_at = close_at
        attempt.result.status = result_status
        for allow_review in (True, False):
            assessment.allow_student_view_results = allow_review
            for visibility in ALLOWED_ANSWER_VISIBILITY_POLICIES:
                assessment.answer_visibility_policy = visibility
                db.session.commit()
                responses = [
                    client.get(f"/student/attempt/{attempt.public_id}/result"),
                    client.get(
                        f"/api/attempts/{attempt.public_id}/result",
                        headers={"Authorization": f"Bearer {token}"},
                    ),
                ]
                for response in responses:
                    assert response.status_code == 200
                    data = response.json
                    assert data["score_status"] == ("RELEASED" if released else "SCORE_HIDDEN")
                    if not released:
                        assert data["raw_score"] is None
                        assert data["questions"] is None
                        continue
                    assert data["raw_score"] == float(attempt.result.raw_score)
                    assert data["passed"] == attempt.result.passed
                    if visibility == "NEVER":
                        assert data["questions"] == []
                    elif not allow_review:
                        for question in data["questions"]:
                            assert question["choices"] == []
                            assert question["selected_choice_keys"] == []
                            assert question["is_correct"] is None
                            assert question["awarded_points"] is None
                            assert "slot_results" not in question
                            assert "student_answer_text" not in question
                            assert "explanation" not in question


def test_summary_resume_at_limit_and_pending_are_not_completed(client, review_attempt):
    from backend.services.assessment_student_service import student_assessment_summary

    student, _, assessment, attempt = review_attempt
    assessment.attempt_limit = 1
    attempt.status = "IN_PROGRESS"
    attempt.deadline_at = datetime.now(UTC) + timedelta(minutes=15)
    db.session.flush()
    summary = student_assessment_summary(student, assessment)
    assert summary["is_attempt_limit_reached"] is True
    assert summary["active_attempt_id"] == str(attempt.public_id)
    assert summary["can_resume"] is True
    assert summary["start_block_reason"] is None
    assert summary["is_completed"] is False
    assert summary["completion_status"] == "IN_PROGRESS"
    assert summary["display_score"]["raw_score"] is None
    attempt.status = "PENDING_GRADING"
    db.session.flush()
    summary = student_assessment_summary(student, assessment)
    assert summary["completion_status"] == "PENDING_GRADING"
    assert summary["is_completed"] is False
    assert summary["display_score"]["raw_score"] is None
    attempt.status = "IN_PROGRESS"
    attempt.started_at = datetime.now(UTC) - timedelta(minutes=15)
    attempt.deadline_at = datetime.now(UTC) - timedelta(seconds=1)
    db.session.flush()
    summary = student_assessment_summary(student, assessment)
    assert summary["completion_status"] == "COMPLETED"
    assert summary["attempt_status"] == "EXPIRED"
    assert summary["can_resume"] is False
    assert attempt.status == "IN_PROGRESS"  # Read-only summary never finalizes an attempt.


def test_assessment_surfaces_share_count_attempts_and_released_score(client, review_attempt):
    student, _, assessment, attempt = review_attempt
    assessment.attempt_limit = 1
    db.session.commit()
    _login_review_student(client, student)
    listing = client.get("/student/assessments").json["items"]
    detail = client.get(f"/student/assessments/{assessment.public_id}").json
    course = client.get(f"/student/courses/{assessment.course.public_id}").json
    item = next(row for row in listing if row["assessment_id"] == str(assessment.public_id))
    course_item = next(
        row for row in course["assessments"] if row["assessment_id"] == str(assessment.public_id)
    )
    for data in (item, detail, course_item):
        assert data["questions_count"] == 1
        assert data["attempts_count"] == 1
        assert data["is_completed"] is True
        assert data["completion_status"] == "COMPLETED"
        assert data["start_block_reason"] == "EXHAUSTED"
        assert data["display_score"]["raw_score"] == float(attempt.result.raw_score)
        assert data["display_score"]["score_out_of_10"] == float(attempt.result.raw_score)
        assert data["best_attempt_id"] == str(attempt.public_id)
    assessment.score_release_policy = "AFTER_CLOSE"
    db.session.commit()
    item = client.get("/student/assessments").json["items"][0]
    assert item["display_score"]["raw_score"] is None
    assert item["raw_score"] is None


def test_assessment_surfaces_use_assigned_snapshot_instead_of_configured_totals(
    client, review_attempt
):
    from backend.models.attempt_regrade import AttemptQuestion
    from backend.models.identity import User

    student, _, assessment, attempt = review_attempt
    admin = db.session.query(User).filter_by(email="review-admin@example.com").one()
    extra = create_question(
        admin,
        assessment.course_id,
        {
            "question_type": "TRUE_FALSE",
            "content": "A historical question",
            "difficulty": "REMEMBER",
            "choices": [
                {"content": "True", "is_correct": True, "position": 1},
                {"content": "False", "is_correct": False, "position": 2},
            ],
        },
    )
    source = attempt.attempt_questions[0]
    db.session.add(
        AttemptQuestion(
            attempt_id=attempt.id,
            source_question_id=extra.id,
            source_question_revision_id=extra.current_revision.id,
            position=2,
            question_type_snapshot=source.question_type_snapshot,
            content_snapshot="An assigned historical question",
            points_assigned=3,
        )
    )
    db.session.commit()
    _login_review_student(client, student)
    listing = client.get("/student/assessments").json["items"]
    detail = client.get(f"/student/assessments/{assessment.public_id}").json
    course = client.get(f"/student/courses/{assessment.course.public_id}").json
    item = next(row for row in listing if row["assessment_id"] == str(assessment.public_id))
    course_item = next(
        row for row in course["assessments"] if row["assessment_id"] == str(assessment.public_id)
    )
    for data in (item, detail, course_item):
        assert data["questions_count"] == 2
        assert data["max_points"] == 13


@pytest.mark.parametrize(
    "policy,expected", [("FIRST", 2), ("LATEST", 4), ("HIGHEST", 8), ("AVERAGE", 14 / 3)]
)
def test_student_summary_obeys_scoring_policy(review_attempt, policy, expected):
    from backend.models.attempt_regrade import AssessmentAttempt, AssessmentResult
    from backend.services.assessment_student_service import student_assessment_summary

    student, _, assessment, first = review_attempt
    first.result.raw_score = 2
    first.result.percent_score = 20
    first.result.passed = False
    for number, score in [(2, 8), (3, 4)]:
        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            student_user_id=student.id,
            enrollment_period_id=first.enrollment_period_id,
            attempt_number=number,
            status="GRADED",
            started_at=utc_now(),
            submitted_at=utc_now(),
        )
        db.session.add(attempt)
        db.session.flush()
        db.session.add(
            AssessmentResult(
                attempt_id=attempt.id,
                raw_score=score,
                max_score=10,
                percent_score=score * 10,
                passed=score >= 5,
                status="RELEASED",
            )
        )
    assessment.scoring_policy = policy
    db.session.flush()
    summary = student_assessment_summary(student, assessment, session=db.session)
    assert summary["display_score"]["score_out_of_10"] == pytest.approx(expected)
    assert summary["display_score"]["scoring_policy"] == policy
    assert summary["best_attempt_id"] != str(first.public_id)
