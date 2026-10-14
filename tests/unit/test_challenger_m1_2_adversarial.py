"""Adversarial stress and boundary tests for Milestone 1 (F05, F06, F07).

Authored by Challenger M1_2.
Adversarial dimensions:
- F05: Malformed matching tokens, extreme unicode/Vietnamese, missing separators,
       whitespace variations, empty/over/under selections, slot_results integrity & anti-leak,
       ordinary multiple choice non-regression.
- F06: Category casing/normalization, unauthorized categories for ADMIN_SYSTEM_MONITORING,
       unauthorized sub-admin roles (ADMIN_COURSE_REVIEW, ADMIN_TEACHING_ASSIGNMENT,
       ADMIN_INSTRUCTOR_REVIEW), service layer direct defense-in-depth, REST API RBAC.
- F07: Strict boundary testing ensuring ADMIN_TEACHING_ASSIGNMENT CANNOT review, publish,
       trash, restore, or approve changesets (must 403), while retaining read access and reassign rights.
       Testing unauthorized sub-admins and roles blocked from course management.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import (
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
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.notification_service import broadcast_system_notification
from pwd301.services.question_bank_service import create_question
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.user_service import assign_role_to_user, register_user

# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------


def _login_web_session(client: FlaskClient, user: User) -> None:
    _, raw_key = create_auth_session(user, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = user.auth_version
        sess["auth_source"] = "SESSION"


@pytest.fixture
def base_env(app: Flask) -> dict[str, Any]:
    """Base setup with seeded baseline and core roles."""
    sess: Session = db.session
    seed_baseline(sess)

    admin_role = sess.query(Role).filter_by(code="ADMIN").one()

    # Primary Admin
    primary_admin = register_user(
        f"primary_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Primary Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=primary_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Test Primary",
        )
    )

    # System Monitoring Admin
    sys_admin = register_user(
        f"sysmon_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "SysMon Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=sys_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_SYSTEM_MONITORING | Test SysMon",
        )
    )

    # Course Review Admin
    review_admin = register_user(
        f"crev_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Course Review Admin",
        session=sess,
    )
    sess.add(
        UserRole(
            user_id=review_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_COURSE_REVIEW | Test Course Review",
        )
    )

    # Teaching Assignment Admin
    teach_admin = register_user(
        f"teach_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Teaching Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=teach_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_TEACHING_ASSIGNMENT | Test Teaching Assign",
        )
    )

    # Instructor Review Admin
    inst_review_admin = register_user(
        f"irev_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Instructor Review Admin",
        session=sess,
    )
    sess.add(
        UserRole(
            user_id=inst_review_admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_INSTRUCTOR_REVIEW | Test Inst Review",
        )
    )

    # Standard Instructor
    instructor = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Test Instructor", session=sess
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    # Second Instructor (for reassign testing)
    instructor2 = register_user(
        f"inst2_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Second Instructor",
        session=sess,
    )
    assign_role_to_user(instructor2.id, "INSTRUCTOR", session=sess)

    # Standard Student
    student = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Test Student", session=sess
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # Course
    course = create_course(
        actor=instructor,
        data={
            "course_code": f"ADV-{uuid.uuid4().hex[:4].upper()}",
            "title": "Adversarial Testing Course",
            "category": "Testing",
            "capacity": 100,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    return {
        "primary_admin": primary_admin,
        "sys_admin": sys_admin,
        "review_admin": review_admin,
        "teach_admin": teach_admin,
        "inst_review_admin": inst_review_admin,
        "instructor": instructor,
        "instructor2": instructor2,
        "student": student,
        "course": course,
    }


# ===========================================================================
# F05 ADVERSARIAL TESTS (Drag-and-Drop Quiz Grading Engine)
# ===========================================================================


def test_f05_malformed_tokens_and_missing_markers_graceful_fail(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Malformed matching tokens (non-numeric group, zero group, invalid kind) must not crash and evaluate to 0."""
    sess: Session = db.session
    instructor = base_env["instructor"]
    student = base_env["student"]
    course = base_env["course"]

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Malformed Tokens Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 60.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    sec = create_section(instructor, assessment.id, {"title": "S1"}, session=sess)

    # Question with invalid non-numeric group id and missing group marker on distractor
    q_malformed = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Match with malformed tokens",
            "default_points": 10.0,
            "choices": [
                {
                    "content": "[[PWD301:G:MATCH:xyz]]HTTP|||Web transfer",
                    "is_correct": True,
                    "position": 1,
                },
                {
                    "content": "[[PWD301:G:MATCH:0]]FTP|||File transfer",
                    "is_correct": False,
                    "position": 2,
                },
                {
                    "content": "Unmarked choice without group prefix",
                    "is_correct": False,
                    "position": 3,
                },
            ],
        },
        session=sess,
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q_malformed.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor, assessment.id, session=sess)
    sess.commit()

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Submit whatever choice
    c = aq.choice_snapshots[0]
    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(c.choice_key_snapshot)],
        },
        raw_lease_token=lease_token,
        session=sess,
    )

    submitted = submit_assessment_attempt(
        actor=student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )

    assert submitted["status"] == "GRADED"
    sess.refresh(attempt)
    # Because markers were invalid/malformed, grading fails safely with 0.0 points, no crash
    assert float(attempt.result.raw_score) == 0.0


def test_f05_extreme_unicode_vietnamese_and_emojis(app: Flask, base_env: dict[str, Any]) -> None:
    """Extreme Unicode, Vietnamese diacritics, and Emojis are matched correctly across keys and text variants."""
    sess: Session = db.session
    instructor = base_env["instructor"]
    student = base_env["student"]
    course = base_env["course"]

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Vietnamese Unicode Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 50.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    sec = create_section(instructor, assessment.id, {"title": "S1"}, session=sess)

    # Vietnamese & Emojis with punctuation and diacritics
    vn_q = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Ghép nối định nghĩa Tiếng Việt",
            "default_points": 20.0,
            "choices": [
                {
                    "content": "[[PWD301:G:MATCH:1]]Tiếng Việt có dấu: Đặng Quốc Dũng|||Giảng viên môn PWD301 🎓",
                    "is_correct": True,
                    "position": 1,
                },
                {
                    "content": "[[PWD301:G:MATCH:1]]Sai lệch|||Thông tin giả mạo 🚫",
                    "is_correct": False,
                    "position": 2,
                },
                {
                    "content": "[[PWD301:G:MATCH:2]]Giao thức HTTP/3 🚀|||Quản lý luồng QUIC 🔥",
                    "is_correct": True,
                    "position": 3,
                },
                {
                    "content": "[[PWD301:G:MATCH:2]]Lỗi mạng|||Mất kết nối ❌",
                    "is_correct": False,
                    "position": 4,
                },
            ],
        },
        session=sess,
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": vn_q.id, "points_assigned": 20.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor, assessment.id, session=sess)
    sess.commit()

    # Attempt 1: Submit via clean text tokens with diacritics and differing casing
    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Student submits text variants in lowercase
    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [
                "tiếng việt có dấu: đặng quốc dũng|||giảng viên môn pwd301 🎓",
                "giao thức http/3 🚀|||quản lý luồng quic 🔥",
            ],
        },
        raw_lease_token=lease_token,
        session=sess,
    )

    submit_assessment_attempt(
        actor=student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )

    sess.refresh(attempt)
    assert float(attempt.result.raw_score) == 20.0
    assert bool(attempt.result.passed) is True

    # Check slot results contain the full clean text with emojis and diacritics
    res = get_attempt_result_for_student(actor=student, attempt_id=attempt.id, session=sess)
    slots = res["questions"][0]["slot_results"]
    assert len(slots) == 2
    assert slots[0]["is_correct"] is True
    assert "Đặng Quốc Dũng" in slots[0]["expected_text"]
    assert slots[1]["is_correct"] is True
    assert "HTTP/3 🚀" in slots[1]["expected_text"]


def test_f05_whitespace_and_missing_separator_variations(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Whitespace variations (tabs, newlines) and choices without ||| (single drag token) grade properly."""
    sess: Session = db.session
    instructor = base_env["instructor"]
    student = base_env["student"]
    course = base_env["course"]

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Whitespace & Drag Tokens Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 50.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    sec = create_section(instructor, assessment.id, {"title": "S1"}, session=sess)

    # Choice without ||| (pure DRAG token) and choice with irregular whitespace around |||
    drag_q = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Drag tokens with irregular whitespace",
            "default_points": 10.0,
            "choices": [
                {
                    # Single drag token without separator
                    "content": "[[PWD301:G:DRAG:1]]PostgreSQL Database",
                    "is_correct": True,
                    "position": 1,
                },
                {
                    "content": "[[PWD301:G:DRAG:1]]SQLite",
                    "is_correct": False,
                    "position": 2,
                },
                {
                    # Extreme whitespace padding around |||
                    "content": "[[PWD301:G:MATCH:2]] \t Redis Cache \n ||| \r\n In-Memory Store \t ",
                    "is_correct": True,
                    "position": 3,
                },
                {
                    "content": "[[PWD301:G:MATCH:2]]Memcached|||Disk Store",
                    "is_correct": False,
                    "position": 4,
                },
            ],
        },
        session=sess,
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": drag_q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor, assessment.id, session=sess)
    sess.commit()

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Submit using stripped normalized tokens
    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [
                "PostgreSQL Database",  # matches right text of group 1
                "redis cache|||in-memory store",  # matches combined text of group 2
            ],
        },
        raw_lease_token=lease_token,
        session=sess,
    )

    submit_assessment_attempt(
        actor=student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )

    sess.refresh(attempt)
    assert float(attempt.result.raw_score) == 10.0


def test_f05_empty_partial_and_over_selections_evaluated_zero(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Empty answers, under-selections (1 of 2), and over-selections (2 in 1 slot) must receive 0 points."""
    sess: Session = db.session
    instructor = base_env["instructor"]
    student = base_env["student"]
    course = base_env["course"]

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Boundary Selections Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 60.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    sec = create_section(instructor, assessment.id, {"title": "S1"}, session=sess)

    q = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "2 Slots Required",
            "default_points": 10.0,
            "choices": [
                {"content": "[[PWD301:G:MATCH:1]]A|||1", "is_correct": True, "position": 1},
                {"content": "[[PWD301:G:MATCH:1]]A|||2", "is_correct": False, "position": 2},
                {"content": "[[PWD301:G:MATCH:2]]B|||2", "is_correct": True, "position": 3},
                {"content": "[[PWD301:G:MATCH:2]]B|||1", "is_correct": False, "position": 4},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor, assessment.id, session=sess)
    sess.commit()

    # Scenario A: Under-selection (selects only slot 1, missing slot 2)
    attempt1, lease1 = start_assessment_attempt(student, assessment.id, session=sess)
    aq1 = attempt1.attempt_questions[0]
    c1 = next(c for c in aq1.choice_snapshots if c.content_snapshot == "[[PWD301:G:MATCH:1]]A|||1")

    save_attempt_answer(
        actor=student,
        attempt_id=attempt1.id,
        attempt_question_id=aq1.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(c1.choice_key_snapshot)],
        },
        raw_lease_token=lease1,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student,
        attempt_id=attempt1.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease1,
        session=sess,
    )
    sess.refresh(attempt1)
    assert float(attempt1.result.raw_score) == 0.0

    # Scenario B: Over-selection (selects both choices for slot 1, slot 2 missing)
    attempt2, lease2 = start_assessment_attempt(student, assessment.id, session=sess)
    aq2 = attempt2.attempt_questions[0]
    c1_a = next(
        c for c in aq2.choice_snapshots if c.content_snapshot == "[[PWD301:G:MATCH:1]]A|||1"
    )
    c1_b = next(
        c for c in aq2.choice_snapshots if c.content_snapshot == "[[PWD301:G:MATCH:1]]A|||2"
    )

    save_attempt_answer(
        actor=student,
        attempt_id=attempt2.id,
        attempt_question_id=aq2.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(c1_a.choice_key_snapshot), str(c1_b.choice_key_snapshot)],
        },
        raw_lease_token=lease2,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student,
        attempt_id=attempt2.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease2,
        session=sess,
    )
    sess.refresh(attempt2)
    assert float(attempt2.result.raw_score) == 0.0


def test_f05_ordinary_multiple_choice_completely_unimpacted(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Standard multiple-choice questions without [[PWD301:G: markers grade normally without slot_results."""
    sess: Session = db.session
    instructor = base_env["instructor"]
    student = base_env["student"]
    course = base_env["course"]

    assessment = create_assessment(
        instructor,
        course.id,
        {
            "title": "Standard Multiple Choice Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 50.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    sec = create_section(instructor, assessment.id, {"title": "S1"}, session=sess)

    # Question 1: Single choice correct
    q_single = create_question(
        instructor,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "What is 2+2?",
            "default_points": 5.0,
            "choices": [
                {"content": "3", "is_correct": False, "position": 1},
                {"content": "4", "is_correct": True, "position": 2},
                {"content": "5", "is_correct": False, "position": 3},
            ],
        },
        session=sess,
    )
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q_single.id, "points_assigned": 5.0, "section_id": sec.id},
        session=sess,
    )

    publish_assessment(instructor, assessment.id, session=sess)
    sess.commit()

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]
    correct_choice = next(c for c in aq.choice_snapshots if c.content_snapshot == "4")

    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(correct_choice.choice_key_snapshot)],
        },
        raw_lease_token=lease_token,
        session=sess,
    )
    submit_assessment_attempt(
        actor=student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )

    sess.refresh(attempt)
    assert float(attempt.result.raw_score) == 5.0

    res = get_attempt_result_for_student(actor=student, attempt_id=attempt.id, session=sess)
    q_data = res["questions"][0]
    # Standard question must NOT have slot_results
    assert "slot_results" not in q_data


# ===========================================================================
# F06 ADVERSARIAL TESTS (2-Tier Broadcast Notification RBAC)
# ===========================================================================


def test_f06_category_casing_and_normalization_service(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Service layer normalizes category casing ('system' -> 'SYSTEM') and enforces RBAC."""
    sess: Session = db.session
    sys_admin = base_env["sys_admin"]

    # Lowercase 'system' and padded '  System  ' must normalize to SYSTEM and succeed
    for valid_casing in ("system", " System ", "sYsTeM"):
        count, _ = broadcast_system_notification(
            actor=sys_admin,
            title="System Alert",
            body="Load alert",
            category=valid_casing,
            session=sess,
        )
        assert count >= 0

    # Lowercase 'academic' or 'maintenance' must normalize and raise 403 Forbidden
    for invalid_casing in ("academic", " Academic ", "MAINTENANCE", "event", "security"):
        with pytest.raises(ForbiddenError):
            broadcast_system_notification(
                actor=sys_admin,
                title="Unauthorized",
                body="Blocked alert",
                category=invalid_casing,
                session=sess,
            )


def test_f06_unauthorized_categories_for_sysmon_all_blocked(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """ADMIN_SYSTEM_MONITORING is blocked from all non-SYSTEM categories, while PRIMARY_ADMIN succeeds."""
    sess: Session = db.session
    sys_admin = base_env["sys_admin"]
    primary_admin = base_env["primary_admin"]

    unauthorized_cats = [
        "ACADEMIC",
        "MAINTENANCE",
        "EVENT",
        "SECURITY",
        "COURSE",
        "GRADE",
        "UNKNOWN_CATEGORY_XYZ",
    ]

    for cat in unauthorized_cats:
        # SysMon Admin must be strictly forbidden (403)
        with pytest.raises(ForbiddenError) as exc_info:
            broadcast_system_notification(
                actor=sys_admin,
                title="Broadcast Attempt",
                body=f"Category {cat}",
                category=cat,
                session=sess,
            )
        assert (
            "giám sát hệ thống" in str(exc_info.value).lower()
            or "quyền" in str(exc_info.value).lower()
        )

        # Primary Admin must succeed for all categories
        count, _ = broadcast_system_notification(
            actor=primary_admin,
            title="Primary Broadcast",
            body=f"Category {cat}",
            category=cat,
            session=sess,
        )
        assert count >= 0


def test_f06_unauthorized_subadmins_and_service_defense(
    app: Flask, base_env: dict[str, Any]
) -> None:
    """Service layer directly blocks ADMIN_COURSE_REVIEW, ADMIN_TEACHING_ASSIGNMENT, ADMIN_INSTRUCTOR_REVIEW, instructors, and students."""
    sess: Session = db.session

    blocked_actors = [
        ("review_admin", "ADMIN_COURSE_REVIEW"),
        ("teach_admin", "ADMIN_TEACHING_ASSIGNMENT"),
        ("inst_review_admin", "ADMIN_INSTRUCTOR_REVIEW"),
        ("instructor", "INSTRUCTOR"),
        ("student", "STUDENT"),
    ]

    for actor_key, role_label in blocked_actors:
        actor = base_env[actor_key]
        with pytest.raises(ForbiddenError, match="quyền|administrators"):
            broadcast_system_notification(
                actor=actor,
                title="Unauthorized Sub-Admin Attempt",
                body=f"Sent by {role_label}",
                category="SYSTEM",
                session=sess,
            )

    # Actor=None must raise ForbiddenError
    with pytest.raises(ForbiddenError):
        broadcast_system_notification(
            actor=None,
            title="Anonymous Attempt",
            body="No actor",
            category="SYSTEM",
            session=sess,
        )


def test_f06_rest_api_broadcast_rbac_adversarial(
    app: Flask, client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """REST API endpoint POST /api/admin/notifications/broadcast enforces 2-tier RBAC and rejects invalid calls."""
    sys_admin = base_env["sys_admin"]
    review_admin = base_env["review_admin"]
    teach_admin = base_env["teach_admin"]
    student = base_env["student"]

    token_sys = create_token_pair(sys_admin)["access_token"]
    token_rev = create_token_pair(review_admin)["access_token"]
    token_teach = create_token_pair(teach_admin)["access_token"]
    token_stud = create_token_pair(student)["access_token"]

    # 1. SysMon broadcasting with lowercase 'system' -> 200 OK
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Sys Alert", "body": "Load high", "category": "system"},
        headers={"Authorization": f"Bearer {token_sys}"},
    )
    assert resp.status_code == 200

    # 2. SysMon broadcasting with unauthorized 'academic' -> 403 Forbidden
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Sys Alert", "body": "Load high", "category": "academic"},
        headers={"Authorization": f"Bearer {token_sys}"},
    )
    assert resp.status_code == 403

    # 3. Course Review Admin attempting broadcast -> 403 Forbidden
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Notice", "body": "Review alert", "category": "SYSTEM"},
        headers={"Authorization": f"Bearer {token_rev}"},
    )
    assert resp.status_code == 403

    # 4. Teaching Assignment Admin attempting broadcast -> 403 Forbidden
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Notice", "body": "Assign alert", "category": "SYSTEM"},
        headers={"Authorization": f"Bearer {token_teach}"},
    )
    assert resp.status_code == 403

    # 5. Student attempting broadcast -> 403 Forbidden
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Notice", "body": "Student spam", "category": "SYSTEM"},
        headers={"Authorization": f"Bearer {token_stud}"},
    )
    assert resp.status_code == 403

    # 6. Anonymous attempting broadcast -> 401 Unauthorized
    resp = client.post(
        "/api/admin/notifications/broadcast",
        json={"title": "Notice", "body": "Anon spam", "category": "SYSTEM"},
    )
    assert resp.status_code == 401


# ===========================================================================
# F07 ADVERSARIAL TESTS (Teaching Assignment Course Access & Boundaries)
# ===========================================================================


def test_f07_teaching_assignment_strictly_forbidden_from_course_mutations(
    app: Flask, client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """ADMIN_TEACHING_ASSIGNMENT is strictly forbidden (403) from review, publish, trash, restore, or pending queue."""
    teach_admin = base_env["teach_admin"]
    course = base_env["course"]
    cid = str(course.public_id)

    # 1. Web session checks
    _login_web_session(client, teach_admin)

    # Must be forbidden from viewing pending review queue
    assert client.get("/admin/courses/pending").status_code == 403

    # Must be forbidden from review (approve/reject)
    assert (
        client.post(f"/admin/courses/{cid}/review", json={"action": "approve"}).status_code == 403
    )

    # Must be forbidden from publish
    assert client.post(f"/admin/courses/{cid}/publish").status_code == 403

    # Must be forbidden from trash (POST and DELETE)
    assert client.post(f"/admin/courses/{cid}/trash").status_code == 403
    assert client.delete(f"/admin/courses/{cid}/trash").status_code == 403

    # Must be forbidden from restore
    assert client.post(f"/admin/courses/{cid}/restore").status_code == 403

    # Must be forbidden from changeset approve/reject
    assert (
        client.post(f"/admin/courses/{cid}/changeset/approve", json={"reason": "test"}).status_code
        == 403
    )
    assert (
        client.post(f"/admin/courses/{cid}/changeset/reject", json={"reason": "test"}).status_code
        == 403
    )

    # 2. REST API checks with JWT
    token = create_token_pair(teach_admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # API pending queue -> 403
    assert client.get("/api/admin/courses/pending", headers=headers).status_code == 403

    # API review -> 403
    assert (
        client.post(
            f"/api/admin/courses/{cid}/review", json={"action": "approve"}, headers=headers
        ).status_code
        == 403
    )

    # API publish -> 403
    assert client.post(f"/api/admin/courses/{cid}/publish", headers=headers).status_code == 403

    # API trash -> 403
    assert client.post(f"/api/admin/courses/{cid}/trash", headers=headers).status_code == 403
    assert client.delete(f"/api/admin/courses/{cid}/trash", headers=headers).status_code == 403

    # API restore -> 403
    assert client.post(f"/api/admin/courses/{cid}/restore", headers=headers).status_code == 403


def test_f07_unauthorized_subadmins_and_roles_blocked_from_course_listing(
    app: Flask, client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """ADMIN_SYSTEM_MONITORING, ADMIN_INSTRUCTOR_REVIEW, instructors, and students cannot access admin course endpoints."""
    course = base_env["course"]
    cid = str(course.public_id)

    unauthorized_actors = [
        base_env["sys_admin"],
        base_env["inst_review_admin"],
        base_env["instructor"],
        base_env["student"],
    ]

    for user in unauthorized_actors:
        token = create_token_pair(user)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # API course list -> 403
        resp_list = client.get("/api/admin/courses", headers=headers)
        assert resp_list.status_code == 403

        # API course detail -> 403
        resp_detail = client.get(f"/api/admin/courses/{cid}", headers=headers)
        assert resp_detail.status_code == 403


def test_f07_teaching_assignment_can_reassign_instructor(
    app: Flask, client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """ADMIN_TEACHING_ASSIGNMENT can view course details and reassign instructor owner."""
    teach_admin = base_env["teach_admin"]
    course = base_env["course"]
    inst2 = base_env["instructor2"]
    cid = str(course.public_id)

    # 1. Web session reassign
    _login_web_session(client, teach_admin)
    resp_web_detail = client.get(f"/admin/courses/{cid}")
    assert resp_web_detail.status_code == 200

    resp_reassign = client.post(
        f"/admin/courses/{cid}/reassign",
        json={"new_instructor_id": str(inst2.public_id), "reason": "Phân công giảng viên mới"},
    )
    assert resp_reassign.status_code == 200
    db.session.refresh(course)
    assert course.owner_instructor_id == inst2.id

    # 2. REST API reassign back
    inst1 = base_env["instructor"]
    token = create_token_pair(teach_admin)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp_api_reassign = client.post(
        f"/api/admin/courses/{cid}/reassign",
        json={"new_instructor_id": str(inst1.public_id), "reason": "Điều chuyển lại"},
        headers=headers,
    )
    assert resp_api_reassign.status_code == 200
    db.session.refresh(course)
    assert course.owner_instructor_id == inst1.id
