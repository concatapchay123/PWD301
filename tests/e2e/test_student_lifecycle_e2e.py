"""End-to-End Scenario 1: Comprehensive Student Lifecycle (TASK-028).

Validates complete multi-stage student workflow:
1. Registration -> email verification token -> session & JWT credentials.
2. Catalog browsing -> prerequisite barrier: blocked from Course B until Course A completed.
3. Enrollment in Course A -> sequential lesson progression -> heartbeat updates -> progress percent.
4. Assessment execution: start attempt -> frozen snapshot -> server timer -> editing lease granted.
5. Autosave debouncing with client sequence ordering.
6. Idempotent submission with idempotency key.
7. Objective grading -> score viewing.
8. Course completion evaluation -> CourseCompletionSummary persisted.
9. Recommendation engine -> recommends Course B.
10. Enrollment in Course B now succeeds with prerequisite satisfied.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import CourseCompletionSummary
from pwd301.models.identity import Role, User
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
from pwd301.services.auth_token_service import (
    create_security_token,
    verify_email_with_token,
)
from pwd301.services.completion_service import (
    calculate_course_progress,
    evaluate_course_completion,
    set_course_completion_rule,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
)
from pwd301.services.exceptions import (
    EnrollmentPrerequisiteError,
    StaleAnswerSequenceError,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    record_lesson_progress,
)
from pwd301.services.question_bank_service import create_question
from pwd301.services.recommendation_service import generate_course_recommendations
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.user_service import (
    assign_role_to_user,
    register_user,
)


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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("e2e_admin@example.com", "Password@123", "E2E Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("e2e_inst@example.com", "Password@123", "E2E Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_student_complete_lifecycle_e2e(
    app: Flask,
    instructor_user: User,
    admin_user: User,
) -> None:
    """Execute full student journey from onboarding to graduation and prerequisite progression."""
    sess: Session = db.session

    # -------------------------------------------------------------------------
    # 0. Infrastructure & Course Setup
    # -------------------------------------------------------------------------
    # Course A: Introduction to Python (Prerequisite course)
    course_a = create_course(
        instructor_user,
        {
            "course_code": "PY-101",
            "title": "Introduction to Python",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
            "capacity": 50,
        },
        session=sess,
    )
    change_course_status(instructor_user, course_a.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course_a.id, "APPROVED", session=sess)
    change_course_status(instructor_user, course_a.id, "PUBLISHED", session=sess)

    # Lessons for Course A
    l1 = create_lesson(
        instructor_user,
        course_a.id,
        {
            "title": "Python Basics & Syntax",
            "markdown_content": "# Python Basics\nWelcome to Python syntax.",
            "lesson_type": "VIDEO",
            "position": 1,
            "minimum_completion_seconds": 30,
        },
        session=sess,
    )
    change_lesson_status(instructor_user, l1.id, "PUBLISHED", session=sess)

    l2 = create_lesson(
        instructor_user,
        course_a.id,
        {
            "title": "Data Structures & Loops",
            "markdown_content": "# Data Structures\nLists, dicts, and sets.",
            "lesson_type": "TEXT",
            "position": 2,
            "minimum_completion_seconds": 30,
        },
        session=sess,
    )
    change_lesson_status(instructor_user, l2.id, "PUBLISHED", session=sess)

    # Assessment for Course A
    now = datetime.now(UTC)
    asm_payload = {
        "title": "Course A Final Exam",
        "assessment_type": "FINAL",
        "time_limit_minutes": 60,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=24)).isoformat(),
        "passing_score": 50.0,
        "score_release_policy": "IMMEDIATE",
        "is_required_for_completion": True,
    }
    assessment_a = create_assessment(instructor_user, course_a.id, asm_payload, session=sess)
    sec = create_section(instructor_user, assessment_a.id, {"title": "Core Concepts"}, session=sess)

    q_data: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "What is Python's list syntax?",
        "default_points": 100.0,
        "choices": [
            {"content": "Square brackets [ ]", "is_correct": True, "position": 1},
            {"content": "Curly braces { }", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor_user, course_a.id, q_data, session=sess)
    assign_question(
        instructor_user,
        assessment_a.id,
        {"question_id": q.id, "points_assigned": 100.0, "section_id": sec.id},
        session=sess,
    )
    publish_assessment(instructor_user, assessment_a.id, session=sess)

    # Set completion rule for Course A
    set_course_completion_rule(
        instructor_user,
        course_a.id,
        {
            "require_all_required_lessons": True,
            "require_required_assessments": True,
            "minimum_progress_percent": 100.0,
        },
        session=sess,
    )

    # Course B: Advanced Python (Requires Course A)
    course_b = create_course(
        instructor_user,
        {
            "course_code": "PY-201",
            "title": "Advanced Python Architecture",
            "category": "Computer Science",
            "difficulty": "INTERMEDIATE",
            "capacity": 20,
        },
        session=sess,
    )
    change_course_status(instructor_user, course_b.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin_user, course_b.id, "APPROVED", session=sess)
    change_course_status(instructor_user, course_b.id, "PUBLISHED", session=sess)

    # Set Course A as prerequisite for Course B
    add_course_prerequisite(instructor_user, course_b.id, course_a.id, session=sess)
    sess.commit()

    # -------------------------------------------------------------------------
    # 1. Registration, Verification, Session & JWT Login
    # -------------------------------------------------------------------------
    student = register_user("e2e_student@example.com", "Password@123", "Alice Student")
    student = assign_role_to_user(student.id, "STUDENT")
    sess.commit()

    # Verify email via security token
    _, raw_token = create_security_token(user_id=student.id, purpose="EMAIL_VERIFY", session=sess)
    sess.commit()
    verified_user = verify_email_with_token(raw_token, session=sess)
    assert verified_user.email_verified_at is not None

    # Authenticate via Session and JWT
    auth_session, session_key = create_auth_session(verified_user, session=sess)
    assert auth_session.revoked_at is None
    tokens = create_token_pair(verified_user)
    jwt_token = tokens["access_token"]
    assert jwt_token is not None and len(jwt_token) > 20

    # -------------------------------------------------------------------------
    # 2. Prerequisite Barrier: Attempt to enroll in Course B without Course A
    # -------------------------------------------------------------------------
    with pytest.raises(EnrollmentPrerequisiteError, match="Prerequisite courses not completed"):
        enroll_student(actor=verified_user, course_id=course_b.id, session=sess)

    # -------------------------------------------------------------------------
    # 3. Enroll in Course A and Complete Lessons Sequentially
    # -------------------------------------------------------------------------
    enrollment = enroll_student(actor=verified_user, course_id=course_a.id, session=sess)
    sess.commit()
    assert enrollment.status == "ACTIVE"
    assert enrollment.current_progress_percent == 0.0

    # Complete Lesson 1
    prog1 = record_lesson_progress(
        actor=verified_user,
        lesson_id=l1.id,
        seconds_increment=30,
        view_fraction=1.0,
        session=sess,
    )
    sess.commit()
    assert prog1.completed_at is not None

    # Verify 50% course progress
    progress_pct1 = calculate_course_progress(enrollment.id, session=sess)
    assert progress_pct1 == 50.0

    # Complete Lesson 2
    prog2 = record_lesson_progress(
        actor=verified_user,
        lesson_id=l2.id,
        seconds_increment=35,
        view_fraction=1.0,
        session=sess,
    )
    sess.commit()
    assert prog2.completed_at is not None

    # Verify 100% lesson completion
    progress_pct2 = calculate_course_progress(enrollment.id, session=sess)
    assert progress_pct2 == 100.0

    # -------------------------------------------------------------------------
    # 4. Assessment Attempt: Snapshot, Server Timer, Lease, Autosave
    # -------------------------------------------------------------------------
    attempt, lease_tok = start_assessment_attempt(verified_user, assessment_a.id, session=sess)
    sess.commit()
    assert attempt.status == "IN_PROGRESS"
    assert attempt.deadline_at is not None
    assert attempt.lease_token_hash is not None

    # Verify question snapshot exists
    delivery_qs = attempt.attempt_questions
    assert len(delivery_qs) == 1
    aq = delivery_qs[0]
    assert aq.points_assigned == 100.0
    q_rev = aq.source_question_revision
    correct_rev_choice = next(c for c in q_rev.choices if c.is_correct)
    correct_choice_snap = next(
        c for c in aq.choice_snapshots if c.source_choice_id == correct_rev_choice.id
    )

    # Autosave answer with client_sequence = 1
    save_attempt_answer(
        actor=verified_user,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "choice_keys": [str(correct_choice_snap.choice_key_snapshot)],
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=lease_tok,
        session=sess,
    )
    sess.commit()

    # Debounce rejection: Stale client sequence 1 after 1
    with pytest.raises(StaleAnswerSequenceError):
        save_attempt_answer(
            actor=verified_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.id,
            payload={
                "client_sequence": 1,
                "choice_keys": [str(correct_choice_snap.choice_key_snapshot)],
                "lease_epoch": attempt.lease_epoch,
            },
            raw_lease_token=lease_tok,
            session=sess,
        )

    # -------------------------------------------------------------------------
    # 5. Idempotent Submission & Objective Grading
    # -------------------------------------------------------------------------
    sub_key = uuid.uuid4()
    submit_res1 = submit_assessment_attempt(
        actor=verified_user,
        attempt_id=attempt.id,
        idempotency_key=sub_key,
        raw_lease_token=lease_tok,
        session=sess,
    )
    sess.commit()
    assert submit_res1["status"] in ("GRADED", "SUBMITTED")
    assert submit_res1["is_idempotent_replay"] is False

    # Replay submit with same key -> idempotent response
    submit_res2 = submit_assessment_attempt(
        actor=verified_user,
        attempt_id=attempt.id,
        idempotency_key=sub_key,
        raw_lease_token=lease_tok,
        session=sess,
    )
    assert submit_res2["is_idempotent_replay"] is True
    assert submit_res2["submission_idempotency_key"] == str(sub_key)

    # Check student result view
    student_result = get_attempt_result_for_student(verified_user, attempt.id, session=sess)
    assert student_result["raw_score"] == 100.0
    assert student_result["passed"] is True

    # -------------------------------------------------------------------------
    # 6. Automatic Course Completion & Summary Persistence
    # -------------------------------------------------------------------------
    is_completed, summary = evaluate_course_completion(enrollment.id, session=sess)
    sess.commit()
    assert is_completed is True

    summary = (
        sess.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == verified_user.id,
            CourseCompletionSummary.course_id == course_a.id,
        )
        .first()
    )
    assert summary is not None
    assert summary.ever_completed is True
    assert summary.prerequisite_eligible is True

    # -------------------------------------------------------------------------
    # 7. AI Course Recommendation suggests Course B
    # -------------------------------------------------------------------------
    recommendations = generate_course_recommendations(verified_user, limit=5, session=sess)
    rec_course_ids = [r["course_id"] for r in recommendations]
    assert str(course_b.public_id) in rec_course_ids

    # -------------------------------------------------------------------------
    # 8. Enroll in Course B now succeeds with prerequisite satisfied!
    # -------------------------------------------------------------------------
    enroll_b = enroll_student(actor=verified_user, course_id=course_b.id, session=sess)
    sess.commit()
    assert enroll_b.status == "ACTIVE"
    assert enroll_b.course_id == course_b.id
