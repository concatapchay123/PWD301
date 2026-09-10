"""Unit test suite for Algorithm 14 Course Recommendation Engine (TASK-023).

Validates:
- Rule-based cold-start beginner course recommendations for new students.
- Prerequisite satisfaction filtering: courses with unmet prerequisites are strictly excluded.
- Category matching (+30) and difficulty progression (+20) ranking.
- Exclusion of ACTIVE, COMPLETED, ARCHIVED, and deleted courses.
- Graceful degradation fallback to rule explanations when Gemini is unavailable or rate-limited.
- ADR-002 Zero Internal PK Leakage in all serialized recommendations.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CoursePrerequisite, Enrollment
from pwd301.models.identity import Role, User
from pwd301.services.gemini_service import (
    MockGeminiClient,
    set_gemini_client_override,
)
from pwd301.services.recommendation_service import generate_course_recommendations
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
    u = register_user(
        f"rec_student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Rec Student"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"rec_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Rec Instructor"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


def _create_course(
    session: Session,
    instructor_id: int,
    code: str,
    title: str,
    category: str,
    difficulty: str,
    status: str = "PUBLISHED",
) -> Course:
    c = Course(
        public_id=uuid.uuid4(),
        course_code=code,
        course_code_normalized=code.upper(),
        title=title,
        title_normalized=title.lower(),
        category=category,
        difficulty=difficulty,
        status=status,
        owner_instructor_id=instructor_id,
    )
    session.add(c)
    session.flush()
    return c


def test_cold_start_recommendation_prioritizes_beginner(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """New student with no prior courses is recommended beginner courses first."""
    sess: Session = db.session
    c_beg = _create_course(
        sess, instructor_user.id, "PY101", "Python Basics", "Programming", "BEGINNER"
    )
    c_adv = _create_course(
        sess, instructor_user.id, "PY301", "Advanced Python", "Programming", "ADVANCED"
    )
    sess.commit()

    recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    assert len(recs) >= 2
    top = recs[0]
    assert top["course_id"] == str(c_beg.public_id)
    assert "BEGINNER_FRIENDLY" in top["reasons"]
    assert top["score"] > recs[1]["score"]
    assert recs[1]["course_id"] == str(c_adv.public_id)


def test_prerequisite_filtering_and_satisfaction(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """Courses with unmet prerequisites are excluded; satisfied prerequisites receive bonuses."""
    sess: Session = db.session
    c_intro = _create_course(
        sess, instructor_user.id, "MATH101", "Intro Calculus", "Math", "BEGINNER"
    )
    c_adv = _create_course(
        sess, instructor_user.id, "MATH201", "Multivariable Calculus", "Math", "INTERMEDIATE"
    )

    # Add prerequisite link: MATH201 requires MATH101
    prereq = CoursePrerequisite(
        course_id=c_adv.id,
        prerequisite_course_id=c_intro.id,
        created_by_user_id=instructor_user.id,
    )
    sess.add(prereq)
    sess.commit()

    # Case 1: Student has NOT completed MATH101 -> MATH201 must NOT appear
    recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    rec_ids = [r["course_id"] for r in recs]
    assert str(c_intro.public_id) in rec_ids
    assert str(c_adv.public_id) not in rec_ids

    # Case 2: Student completes MATH101
    enrollment = Enrollment(
        student_user_id=student_user.id,
        course_id=c_intro.id,
        status="COMPLETED",
    )
    sess.add(enrollment)
    sess.commit()

    # Now MATH201 should be recommended with PREREQUISITES_SATISFIED
    recs_after = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    rec_ids_after = [r["course_id"] for r in recs_after]
    assert str(c_adv.public_id) in rec_ids_after
    adv_rec = next(r for r in recs_after if r["course_id"] == str(c_adv.public_id))
    assert "PREREQUISITES_SATISFIED" in adv_rec["reasons"]
    # Intro course should not be recommended since already COMPLETED
    assert str(c_intro.public_id) not in rec_ids_after


def test_category_matching_and_difficulty_progression(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """Completed courses trigger category match (+30) and difficulty progression (+20)."""
    sess: Session = db.session
    c_done = _create_course(
        sess, instructor_user.id, "DS101", "Data Science 1", "Data Science", "BEGINNER"
    )
    c_next = _create_course(
        sess, instructor_user.id, "DS201", "Data Science 2", "Data Science", "INTERMEDIATE"
    )
    _create_course(sess, instructor_user.id, "ART101", "Art History", "Humanities", "BEGINNER")

    # Mark DS101 as completed
    enrollment = Enrollment(
        student_user_id=student_user.id, course_id=c_done.id, status="COMPLETED"
    )
    sess.add(enrollment)
    sess.commit()

    recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    assert len(recs) >= 2
    top = recs[0]
    assert top["course_id"] == str(c_next.public_id)
    assert "CATEGORY_MATCH" in top["reasons"]
    assert "DIFFICULTY_PROGRESSION" in top["reasons"]
    assert top["score"] >= 50  # 30 category + 20 progression


def test_exclusion_of_active_and_archived_courses(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """Active enrollments and archived courses are strictly excluded from recommendations."""
    sess: Session = db.session
    c_active = _create_course(
        sess, instructor_user.id, "ACT101", "Active Course", "General", "BEGINNER"
    )
    c_archived = _create_course(
        sess,
        instructor_user.id,
        "OLD101",
        "Archived Course",
        "General",
        "BEGINNER",
        status="ARCHIVED",
    )
    c_avail = _create_course(
        sess, instructor_user.id, "AVL101", "Available Course", "General", "BEGINNER"
    )

    # Student actively enrolled in ACT101
    sess.add(Enrollment(student_user_id=student_user.id, course_id=c_active.id, status="ACTIVE"))
    sess.commit()

    recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    rec_ids = [r["course_id"] for r in recs]
    assert str(c_avail.public_id) in rec_ids
    assert str(c_active.public_id) not in rec_ids
    assert str(c_archived.public_id) not in rec_ids


def test_graceful_degradation_on_gemini_failure(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """When Gemini throws errors (timeout, quota), recommendation service falls back gracefully."""
    sess: Session = db.session
    c = _create_course(sess, instructor_user.id, "AI101", "AI Overview", "Tech", "BEGINNER")
    sess.commit()

    # Inject simulated timeout in mock client
    mock_client = MockGeminiClient()
    mock_client.simulate_timeout = True
    set_gemini_client_override(mock_client)

    try:
        recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
        assert len(recs) >= 1
        assert recs[0]["course_id"] == str(c.public_id)
        # Fallback explanation should be present without crashing
        assert recs[0]["explanation"] != ""
        assert (
            "introductory" in recs[0]["explanation"].lower()
            or "relevant" in recs[0]["explanation"].lower()
        )
    finally:
        set_gemini_client_override(None)


def test_zero_internal_pk_leakage_in_recommendations(
    app: Flask,
    student_user: User,
    instructor_user: User,
) -> None:
    """Recommendations return only public UUIDs and no BIGINT PKs/FKs (ADR-002)."""
    sess: Session = db.session
    _create_course(
        sess, instructor_user.id, "SEC101", "Security Fundamentals", "Cybersecurity", "BEGINNER"
    )
    sess.commit()

    recs = generate_course_recommendations(actor=student_user, limit=5, session=sess)
    assert len(recs) > 0
    for r in recs:
        assert "id" not in r
        assert "owner_instructor_id" not in r
        assert "course_id" in r
        # Validate UUID structure
        uuid.UUID(r["course_id"])
