"""Concurrency and multi-tab race condition tests for attempt lease management (TASK-014).

Validates:
- Tab 1 vs Tab 2 takeover race: Tab 2 takeover immediately invalidates Tab 1 lease token.
- Tab 1 subsequent heartbeat receives AttemptLeaseConflictError (409 LEASE_CONFLICT).
- Rapid alternating takeover succession ensures only the latest token is active.
- Release-then-acquire sequence enables instant handover without waiting for 30s timeout.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    release_attempt_lease,
    renew_attempt_lease,
    start_assessment_attempt,
    takeover_attempt_lease,
    verify_attempt_lease,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import AttemptLeaseConflictError
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


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
    u = register_user("admin_race_l@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_race_l@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_race_l@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "RACE-101",
            "title": "Race Condition Course",
            "summary": "Concurrency Test Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_student(app: Flask, student_user: User, published_course: Course) -> User:
    """Enroll student into the published course."""
    enroll_student(student_user, published_course.id, session=db.session)
    db.session.commit()
    return student_user


def _make_assessment_with_question(instructor: User, course: Course) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "Race Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 60,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=24)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    section = create_section(
        instructor, assessment.id, {"title": "Main Section"}, session=db.session
    )

    q_payload: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Can multiple tabs hold lease simultaneously?",
        "default_points": 10.0,
        "choices": [
            {"content": "No, exactly one lease active", "is_correct": True, "position": 1},
            {"content": "Yes, all tabs share lease", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor, course.id, q_payload, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": section.id},
        session=db.session,
    )
    publish_assessment(instructor, assessment.id, session=db.session)
    db.session.commit()
    return assessment


def test_two_tabs_takeover_invalidates_tab_one(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Tab 1 starts exam, Tab 2 takes over; Tab 1 heartbeat receives 409 LEASE_CONFLICT."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, tab1_token = start_assessment_attempt(
        enrolled_student, assessment.id, session=db.session
    )

    # Tab 1 sends initial heartbeat successfully
    hb1 = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=tab1_token,
        session=db.session,
    )
    assert hb1["status"] == "IN_PROGRESS"
    assert verify_attempt_lease(attempt, tab1_token) is True

    # Tab 2 performs takeover
    taken_attempt, tab2_token = takeover_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        session=db.session,
    )
    assert tab2_token != tab1_token
    assert verify_attempt_lease(taken_attempt, tab2_token) is True

    # Tab 1 is immediately invalid
    assert verify_attempt_lease(taken_attempt, tab1_token) is False
    with pytest.raises(
        AttemptLeaseConflictError, match="Editing lease was lost or taken over by another window"
    ):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=tab1_token,
            session=db.session,
        )

    # Tab 2 renews successfully
    hb2 = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=tab2_token,
        session=db.session,
    )
    assert hb2["status"] == "IN_PROGRESS"


def test_rapid_sequential_takeovers_cascade(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify that multiple successive takeovers invalidate all predecessor tokens."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, initial_token = start_assessment_attempt(
        enrolled_student, assessment.id, session=db.session
    )

    tokens: list[str] = [initial_token]

    # Simulate 5 rapid tab takeovers
    for _ in range(5):
        _, new_token = takeover_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            session=db.session,
        )
        tokens.append(new_token)

    latest_token = tokens[-1]
    predecessor_tokens = tokens[:-1]

    # All predecessors must fail
    for old_tok in predecessor_tokens:
        assert verify_attempt_lease(attempt, old_tok) is False
        with pytest.raises(AttemptLeaseConflictError):
            renew_attempt_lease(
                actor=enrolled_student,
                attempt_id=attempt.id,
                raw_lease_token=old_tok,
                session=db.session,
            )

    # Only latest token succeeds
    assert verify_attempt_lease(attempt, latest_token) is True
    result = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=latest_token,
        session=db.session,
    )
    assert result["status"] == "IN_PROGRESS"


def test_voluntary_release_allows_clean_handover(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Tab 1 releases lease voluntarily; Tab 2 takes over immediately without delay."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, tab1_token = start_assessment_attempt(
        enrolled_student, assessment.id, session=db.session
    )

    # Tab 1 closes window and calls release
    release_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=tab1_token,
        session=db.session,
    )

    # Tab 1 token is no longer valid
    assert verify_attempt_lease(attempt, tab1_token) is False

    # Tab 2 acquires lease via takeover immediately
    taken_attempt, tab2_token = takeover_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        session=db.session,
    )

    assert verify_attempt_lease(taken_attempt, tab2_token) is True
    res = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=tab2_token,
        session=db.session,
    )
    assert res["status"] == "IN_PROGRESS"


def test_concurrent_threads_lease_takeover_race(tmp_path: Path) -> None:
    """Tab 1 heartbeat and Tab 2 takeover race: exactly one holds the active valid lease."""
    import concurrent.futures

    from pwd301 import create_app

    db_file = tmp_path / "lease_race.db"
    test_app = create_app(
        "testing",
        config_override={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file.as_posix()}?timeout=30"},
    )

    with test_app.app_context():
        db.create_all()
        sess = db.session

        for code, name in [
            ("STUDENT", "Student"),
            ("INSTRUCTOR", "Instructor"),
            ("ADMIN", "System Administrator"),
        ]:
            if not sess.query(Role).filter_by(code=code).first():
                sess.add(Role(code=code, name=name))
        sess.commit()

        inst = assign_role_to_user(
            register_user("l_inst@example.com", "Password@123", "L Inst").id, "INSTRUCTOR"
        )
        adm = assign_role_to_user(
            register_user("l_adm@example.com", "Password@123", "L Adm").id, "ADMIN"
        )
        student = assign_role_to_user(
            register_user("l_stud@example.com", "Password@123", "L Stud").id, "STUDENT"
        )

        course = create_course(
            inst,
            {"course_code": "LRACE-101", "title": "Lease Race Course"},
        )
        change_course_status(inst, course.id, "SUBMITTED_FOR_REVIEW")
        change_course_status(adm, course.id, "APPROVED")
        change_course_status(inst, course.id, "PUBLISHED")
        enroll_student(student, course.id, session=sess)
        sess.commit()

        assessment = _make_assessment_with_question(inst, course)
        attempt, tab1_token = start_assessment_attempt(student, assessment.id, session=sess)
        attempt_id = attempt.id
        student_id = student.id
        sess.commit()

        def tab1_renew() -> tuple[str, bool, str | None]:
            with test_app.app_context():
                w_sess = db.session
                actor = w_sess.get(User, student_id)
                assert actor is not None
                try:
                    renew_attempt_lease(
                        actor=actor,
                        attempt_id=attempt_id,
                        raw_lease_token=tab1_token,
                        session=w_sess,
                    )
                    return ("TAB1", True, tab1_token)
                except Exception as e:
                    return ("TAB1", False, str(e))

        def tab2_takeover() -> tuple[str, bool, str | None]:
            with test_app.app_context():
                w_sess = db.session
                actor = w_sess.get(User, student_id)
                assert actor is not None
                try:
                    _, tok2 = takeover_attempt_lease(
                        actor=actor,
                        attempt_id=attempt_id,
                        session=w_sess,
                    )
                    return ("TAB2", True, tok2)
                except Exception as e:
                    return ("TAB2", False, str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(tab1_renew)
            f2 = executor.submit(tab2_takeover)
            _ = f1.result()
            res2 = f2.result()

        sess.expire_all()
        final_attempt = sess.get(AssessmentAttempt, attempt_id)
        assert final_attempt is not None

        # Tab 2 takeover must succeed
        assert res2[1] is True
        tab2_token = res2[2]
        assert tab2_token is not None

        # At the end of the race, Tab 2 holds the valid lease
        assert verify_attempt_lease(final_attempt, tab2_token) is True
        # Tab 1 token must not be valid
        assert verify_attempt_lease(final_attempt, tab1_token) is False
