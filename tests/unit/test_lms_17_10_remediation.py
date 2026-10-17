"""Comprehensive test suite for fixes applied to the 5 LMS bug groups (17-10 report).

BUG-01: Course SLO weight validation (0-100%) and clear checklist detail for description vs SLOs.
BUG-02: Change detection & submission for curriculum edits without false "Không có thay đổi để gửi xét duyệt".
BUG-03: Unified course draft consistency and prevention of phantom changes.
BUG-04: Student course detail hero card includes "Xem chi tiết" button scrolling to #syllabus-section.
BUG-05: Quiz attempt history score synchronization and consistent release status.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import (
    _normalize_and_validate_slos,
    create_course,
    update_course,
)
from pwd301.services.course_workflow_service import AuthoringProjection, effective_course
from pwd301.services.exceptions import CourseValidationError, LessonValidationError
from pwd301.services.lesson_service import (
    create_lesson,
    get_course_changeset_status,
    submit_course_changeset,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from pwd301.blueprints.instructor.routes import validate_course_publish_readiness


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
    email = f"inst_lms1710_{uuid.uuid4().hex[:6]}@example.com"
    u = register_user(email, "Password@123", "Instructor 17-10")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    c = create_course(
        instructor_user,
        {
            "course_code": f"LMS1710-{uuid.uuid4().hex[:4].upper()}",
            "title": "LMS 17-10 Test Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


def test_bug01_slo_weight_validation() -> None:
    """BUG-01: SLO weights must be between 0% and 100% or raise CourseValidationError."""
    # Valid SLOs with percentage strings and numbers
    valid_slos = [
        {"title": "SLO 1: Foundation", "weight": "20%"},
        {"title": "SLO 2: Practical", "weight": 50},
        {"title": "SLO 3: Capstone", "weight": "30.0%"},
    ]
    normalized = _normalize_and_validate_slos(valid_slos)
    assert normalized is not None
    parsed = json.loads(normalized)
    assert len(parsed) == 3
    assert parsed[0]["weight"] == "20%"
    assert parsed[1]["weight"] == "50%"
    assert parsed[2]["weight"] == "30%"

    # Invalid: > 100% (e.g. 500% from bug report)
    invalid_500 = [{"title": "SLO Overweight", "weight": "500%"}]
    with pytest.raises(CourseValidationError, match="0% đến 100%"):
        _normalize_and_validate_slos(invalid_500)

    # Invalid: Negative weight
    invalid_neg = [{"title": "SLO Negative", "weight": "-10%"}]
    with pytest.raises(CourseValidationError, match="0% đến 100%"):
        _normalize_and_validate_slos(invalid_neg)

    # Invalid: Non-numeric weight
    invalid_str = [{"title": "SLO Bad String", "weight": "high"}]
    with pytest.raises(CourseValidationError, match="số phần trăm hợp lệ"):
        _normalize_and_validate_slos(invalid_str)


def test_bug01_publish_readiness_differentiates_slo_and_description(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-01: Checklist clearly indicates SLO presence even when description < 20 chars."""
    sess = db.session

    # Case: SLOs exist but description is too short (< 20 chars)
    test_course.description = "Too short"
    test_course.learning_objectives = json.dumps([
        {"title": "SLO 1: Master fundamentals", "weight": "50%"},
        {"title": "SLO 2: Build project", "weight": "50%"},
    ])
    sess.commit()

    checklist = validate_course_publish_readiness(test_course, actor=instructor_user, session=sess)
    course_info = next(c for c in checklist["criteria"] if c["id"] == "course_info")
    assert not course_info["passed"]
    # Detail must acknowledge SLOs are present (Đạt) and state description is what needs fixing
    assert "Chuẩn đầu ra: Đã có 2 mục (Đạt)" in course_info["detail"]
    assert "mô tả khóa học chưa đạt yêu cầu" in course_info["detail"]


def test_bug02_and_bug03_changeset_status_and_submit_lifecycle(
    app: Flask,
    instructor_user: User,
    test_course: Course,
) -> None:
    """BUG-02 & BUG-03: Changeset status reports no phantom changes, and submit works with draft lessons."""
    sess = db.session
    test_course.status = "PUBLISHED"
    sess.commit()

    # 1. Clean course should not report changes
    clean_status = get_course_changeset_status(instructor_user, test_course.id, session=sess)
    assert clean_status["changes_count"] == 0
    assert clean_status["has_changes"] is False

    # 2. Add a draft lesson
    lesson = create_lesson(
        instructor_user,
        test_course.id,
        {
            "title": "New Staged Lesson",
            "markdown_content": "# Staged content for 17-10",
            "status": "DRAFT",
        },
        session=sess,
    )
    sess.commit()

    # 3. Status must now report changes
    active_status = get_course_changeset_status(instructor_user, test_course.id, session=sess)
    assert active_status["has_changes"] is True
    assert active_status["changes_count"] >= 1

    # 4. Submit course changeset must succeed without throwing "Không có thay đổi để gửi xét duyệt"
    submitted = submit_course_changeset(
        instructor_user,
        test_course.id,
        {"version_title": "Đợt cập nhật 17-10", "summary": "Bổ sung bài học mới"},
        session=sess,
    )
    sess.commit()
    assert submitted is not None
    assert submitted.status == "PENDING"


def test_bug04_frontend_hero_xem_chi_tiet_button_contract() -> None:
    """BUG-04: Student course hero must have 'Xem chi tiết' button scrolling to #syllabus-section."""
    student_js = Path("frontend/assets/js/views/student.js").read_text(encoding="utf-8")

    # Button presence
    assert 'id="btn-scroll-to-syllabus"' in student_js
    assert '<span>Xem chi tiết</span>' in student_js

    # Wire to smooth scroll to #syllabus-section
    assert "btn-scroll-to-syllabus" in student_js
    assert "syllabus-section" in student_js
    assert "scrollIntoView({ behavior: 'smooth', block: 'start' })" in student_js


def test_bug05_assessment_attempt_score_and_table_contract() -> None:
    """BUG-05: Assessment student service supplies score, and frontend handles it synchronously."""
    from pwd301.services.assessment_student_service import student_assessment_summary

    student_js = Path("frontend/assets/js/views/student.js").read_text(encoding="utf-8")

    # Check student.js handles score/raw_score synchronization and doesn't mismatch "Chờ công bố" with "Chưa đạt"
    assert "attemptScore" in student_js
    assert "att.score" in student_js
    assert "att.raw_score" in student_js
    assert "${attemptScore} / ${maxScore}" in student_js
    assert "isReleased" in student_js
    assert "scoreDisplay" in student_js
    assert "Chưa công bố" in student_js


def test_bug05_student_assessment_summary_attempts_history(app: Flask, setup_roles: dict[str, Role]) -> None:
    """BUG-05: Ensure student_assessment_summary computes score & result safely for attempts."""
    from types import SimpleNamespace
    from pwd301.services.assessment_student_service import student_assessment_summary

    # Create mock actor, assessment and attempt
    actor = SimpleNamespace(id=999)
    assessment = SimpleNamespace(
        id=888,
        course_id=777,
        title="Final Exam",
        assessment_type="FINAL_EXAM",
        scoring_policy="HIGHEST",
        attempt_limit=3,
        passing_percent=50.0,
        open_at=None,
        close_at=None,
        score_release_policy="INSTRUCTOR_RELEASE",
    )

    class MockResult:
        def __init__(self, raw, max_s, status, passed):
            self.raw_score = raw
            self.max_score = max_s
            self.status = status
            self.passed = passed

    class MockAttempt:
        def __init__(self, att_id, num, status, result):
            self.id = att_id
            self.public_id = uuid.uuid4()
            self.assessment_id = 888
            self.student_user_id = 999
            self.enrollment_period_id = 1
            self.attempt_number = num
            self.status = status
            self.started_at = None
            self.deadline_at = None
            self.submitted_at = None
            self.result = result
            self.assessment = assessment
            self.attempt_questions = []

    # Attempt 1: unreleased result (status = 'PENDING')
    att1 = MockAttempt(1, 1, "GRADED", MockResult(8.0, 10.0, "PENDING", True))
    enrollment = SimpleNamespace(current_period_id=1, status="ACTIVE")

    summary = student_assessment_summary(
        actor,
        assessment,
        attempts=[att1],
        enrollment=enrollment,
    )

    assert len(summary["attempts"]) == 1
    h1 = summary["attempts"][0]
    assert h1["is_score_released"] is False
    assert h1["score"] is None
    assert h1["passed"] is None

    # Attempt 2: released result (status = 'RELEASED')
    att2 = MockAttempt(2, 2, "GRADED", MockResult(9.0, 10.0, "RELEASED", True))
    summary2 = student_assessment_summary(
        actor,
        assessment,
        attempts=[att2],
        enrollment=enrollment,
    )
    assert len(summary2["attempts"]) == 1
    h2 = summary2["attempts"][0]
    assert h2["is_score_released"] is True
    assert h2["score"] == 9.0
    assert h2["max_score"] == 10.0
    assert h2["passed"] is True

