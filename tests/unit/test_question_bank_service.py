"""Unit tests for Question Bank Management and Question Authoring Engine (TASK-010)."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import (
    QuestionProvenance,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    QuestionValidationError,
)
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import (
    create_question,
    list_course_questions,
    restore_question,
    trash_question,
)
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary instructor user."""
    u = register_user("qb_inst@example.com", "Password@123", "Question Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("qb_admin@example.com", "Password@123", "Question Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary instructor user."""
    u = register_user("qb_other@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def course(app: Flask, instructor_user: User) -> Course:
    """Create a course owned by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-QB101",
            "title": "Question Bank Authoring 101",
            "description": "Course for question bank unit tests",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def lesson(app: Flask, instructor_user: User, course: Course) -> Lesson:
    """Create a lesson in the course."""
    les = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Introduction to Question Types",
            "markdown_content": "# Intro",
            "position": 1,
        },
    )
    db.session.commit()
    return les


@pytest.fixture
def other_course(app: Flask, other_instructor: User) -> Course:
    """Create another course owned by other instructor."""
    c = create_course(
        other_instructor,
        {
            "course_code": "CS-QB999",
            "title": "Other Course",
            "description": "Other course for isolation testing",
            "category": "Testing",
            "difficulty": "BEGINNER",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def other_lesson(app: Flask, other_instructor: User, other_course: Course) -> Lesson:
    """Create a lesson in other course."""
    les = create_lesson(
        other_instructor,
        other_course.id,
        {
            "title": "Unrelated Lesson",
            "markdown_content": "# Unrelated",
            "position": 1,
        },
    )
    db.session.commit()
    return les


# ==============================================================================
# 1. QUESTION AUTHORING TESTS FOR 5 STANDARD TYPES
# ==============================================================================


def test_create_single_choice_question(
    app: Flask, instructor_user: User, course: Course, lesson: Lesson
) -> None:
    """Create SINGLE_CHOICE question with 4 options and 1 correct answer."""
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "What is the primary Python web framework used in PWD301?",
        "learning_objective": "Web Frameworks",
        "lesson_id": str(lesson.public_id),
        "default_points": 2.0,
        "choices": [
            {"content": "Flask", "is_correct": True, "position": 1},
            {"content": "Django", "is_correct": False, "position": 2},
            {"content": "FastAPI", "is_correct": False, "position": 3},
            {"content": "Tornado", "is_correct": False, "position": 4},
        ],
        "provenance": {"source_type": "MANUAL", "notes": "Handcrafted question"},
    }

    q = create_question(instructor_user, course.id, payload, session=db.session)
    db.session.commit()

    assert q.id is not None
    assert q.status == "ACTIVE"
    assert q.difficulty == "REMEMBER"
    assert q.learning_objective == "Web Frameworks"
    assert q.lesson_id == lesson.id

    rev = q.current_revision
    assert rev is not None
    assert rev.revision_no == 1
    assert rev.question_type == "SINGLE_CHOICE"
    assert rev.change_type == "INITIAL"
    assert len(rev.choices) == 4
    assert sum(1 for c in rev.choices if c.is_correct) == 1

    # Verify provenance
    prov = (
        db.session.query(QuestionProvenance).filter(QuestionProvenance.question_id == q.id).first()
    )
    assert prov is not None
    assert prov.source_type == "MANUAL"
    assert prov.notes == "Handcrafted question"

    # Verify AuditEvent
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_type == "QUESTION", AuditEvent.target_id == q.id)
        .first()
    )
    assert audit is not None
    assert audit.action == "QUESTION_CREATED"
    assert audit.after_json is not None
    assert "SINGLE_CHOICE" in audit.after_json


def test_create_multiple_choice_question(app: Flask, instructor_user: User, course: Course) -> None:
    """Create MULTIPLE_CHOICE question with 4 options and 2 correct answers."""
    payload = {
        "question_type": "MULTIPLE_CHOICE",
        "difficulty": "UNDERSTAND",
        "content": "Which of the following are valid HTTP methods in RESTful APIs?",
        "learning_objective": "REST Architecture",
        "choices": [
            {"content": "GET", "is_correct": True, "position": 1},
            {"content": "POST", "is_correct": True, "position": 2},
            {"content": "FETCH_ALL", "is_correct": False, "position": 3},
            {"content": "QUERY", "is_correct": False, "position": 4},
        ],
    }

    q = create_question(instructor_user, course.id, payload, session=db.session)
    db.session.commit()

    rev = q.current_revision
    assert rev is not None
    assert rev.question_type == "MULTIPLE_CHOICE"
    assert len(rev.choices) == 4
    assert sum(1 for c in rev.choices if c.is_correct) == 2


def test_create_true_false_question(app: Flask, instructor_user: User, course: Course) -> None:
    """Create TRUE_FALSE question with exactly 2 options and 1 correct answer."""
    payload = {
        "question_type": "TRUE_FALSE",
        "difficulty": "REMEMBER",
        "content": "Python is a compiled-only language without an interpreter.",
        "choices": [
            {"content": "True", "is_correct": False, "position": 1},
            {"content": "False", "is_correct": True, "position": 2},
        ],
    }

    q = create_question(instructor_user, course.id, payload, session=db.session)
    db.session.commit()

    rev = q.current_revision
    assert rev is not None
    assert rev.question_type == "TRUE_FALSE"
    assert len(rev.choices) == 2
    assert rev.choices[1].content == "False"
    assert rev.choices[1].is_correct is True


def test_create_short_answer_question(app: Flask, instructor_user: User, course: Course) -> None:
    """Create SHORT_ANSWER question with accepted answer patterns."""
    payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "APPLY",
        "content": "What keyword defines an anonymous function in Python?",
        "match_type": "NORMALIZED",
        "accepted_answers": ["lambda", "anonymous"],
    }

    q = create_question(instructor_user, course.id, payload, session=db.session)
    db.session.commit()

    rev = q.current_revision
    assert rev is not None
    assert rev.question_type == "SHORT_ANSWER"
    assert rev.short_answer_match_mode == "NORMALIZED"
    assert len(rev.accepted_answers) == 2
    assert rev.accepted_answers[0].answer_text == "lambda"
    assert rev.accepted_answers[0].answer_normalized == "lambda"
    assert rev.accepted_answers[1].answer_text == "anonymous"
    assert rev.accepted_answers[1].answer_normalized == "anonymous"


def test_create_essay_question(app: Flask, instructor_user: User, course: Course) -> None:
    """Create ESSAY question without choices or accepted answers."""
    payload = {
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "content": "Discuss the trade-offs between Server-side Sessions and JWT in RESTful APIs.",
        "explanation": "Grading rubric: mention scalability, revocation difficulty, and storage.",
    }

    q = create_question(instructor_user, course.id, payload, session=db.session)
    db.session.commit()

    rev = q.current_revision
    assert rev is not None
    assert rev.question_type == "ESSAY"
    assert len(rev.choices) == 0
    assert len(rev.accepted_answers) == 0
    assert rev.explanation is not None


# ==============================================================================
# 2. VALIDATION FAILURE TESTS
# ==============================================================================


def test_validation_single_choice_incorrect_correct_count(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """SINGLE_CHOICE must have exactly 1 correct answer."""
    # 0 correct answers
    payload_zero = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Zero correct choices test",
        "choices": [
            {"content": "A", "is_correct": False},
            {"content": "B", "is_correct": False},
        ],
    }
    with pytest.raises(QuestionValidationError, match="must have exactly 1 correct answer"):
        create_question(instructor_user, course.id, payload_zero, session=db.session)

    # 2 correct answers
    payload_two = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Two correct choices test",
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": True},
        ],
    }
    with pytest.raises(QuestionValidationError, match="must have exactly 1 correct answer"):
        create_question(instructor_user, course.id, payload_two, session=db.session)


def test_validation_multiple_choice_zero_correct(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """MULTIPLE_CHOICE must have at least 1 correct answer."""
    payload = {
        "question_type": "MULTIPLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Zero correct choices multi-select test",
        "choices": [
            {"content": "A", "is_correct": False},
            {"content": "B", "is_correct": False},
        ],
    }
    with pytest.raises(QuestionValidationError, match="must have at least 1 correct answer"):
        create_question(instructor_user, course.id, payload, session=db.session)


def test_validation_true_false_choice_count(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """TRUE_FALSE must have exactly 2 choices."""
    payload_three = {
        "question_type": "TRUE_FALSE",
        "difficulty": "REMEMBER",
        "content": "3 choices TF test",
        "choices": [
            {"content": "True", "is_correct": True},
            {"content": "False", "is_correct": False},
            {"content": "Maybe", "is_correct": False},
        ],
    }
    with pytest.raises(QuestionValidationError, match="must have exactly 2 choices"):
        create_question(instructor_user, course.id, payload_three, session=db.session)


def test_validation_short_answer_empty_or_choices_conflict(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """SHORT_ANSWER cannot have choices and must have at least 1 accepted answer."""
    # With choices
    payload_with_choices = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "REMEMBER",
        "content": "Conflict test",
        "choices": [{"content": "A", "is_correct": True}],
        "accepted_answers": ["ans"],
    }
    with pytest.raises(QuestionValidationError, match="cannot have choices"):
        create_question(instructor_user, course.id, payload_with_choices, session=db.session)

    # Empty accepted answers
    payload_empty = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "REMEMBER",
        "content": "Empty answers test",
        "accepted_answers": [],
    }
    with pytest.raises(QuestionValidationError, match="must have at least 1 accepted answer"):
        create_question(instructor_user, course.id, payload_empty, session=db.session)


def test_validation_essay_with_choices_or_answers(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """ESSAY cannot have choices or accepted answers."""
    payload_with_choices = {
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "content": "Essay with choices test",
        "choices": [{"content": "Option A", "is_correct": False}],
    }
    with pytest.raises(QuestionValidationError, match="cannot have choices"):
        create_question(instructor_user, course.id, payload_with_choices, session=db.session)

    payload_with_answers = {
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "content": "Essay with answers test",
        "accepted_answers": ["answer"],
    }
    with pytest.raises(QuestionValidationError, match="cannot have predefined accepted answers"):
        create_question(instructor_user, course.id, payload_with_answers, session=db.session)


def test_validation_invalid_difficulty_and_points(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """Difficulty must be REMEMBER/UNDERSTAND/APPLY and points > 0."""
    # Invalid difficulty
    payload_diff = {
        "question_type": "ESSAY",
        "difficulty": "SUPER_HARD",
        "content": "Difficulty test",
    }
    with pytest.raises(QuestionValidationError, match="Invalid difficulty"):
        create_question(instructor_user, course.id, payload_diff, session=db.session)

    # Negative points
    payload_pts = {
        "question_type": "ESSAY",
        "difficulty": "REMEMBER",
        "content": "Points test",
        "default_points": -2.5,
    }
    with pytest.raises(QuestionValidationError, match="must be greater than zero"):
        create_question(instructor_user, course.id, payload_pts, session=db.session)


def test_validation_cross_course_lesson_assignment(
    app: Flask,
    instructor_user: User,
    course: Course,
    other_lesson: Lesson,
) -> None:
    """Rejects assigning a lesson belonging to a different course."""
    payload = {
        "question_type": "ESSAY",
        "difficulty": "REMEMBER",
        "content": "Cross course test",
        "lesson_id": str(other_lesson.public_id),
    }
    with pytest.raises(
        QuestionValidationError, match="Lesson does not belong to the specified course"
    ):
        create_question(instructor_user, course.id, payload, session=db.session)


# ==============================================================================
# 3. LISTING, FILTERING & PAGINATION TESTS
# ==============================================================================


def test_list_course_questions_filters_and_pagination(
    app: Flask, instructor_user: User, course: Course, lesson: Lesson
) -> None:
    """List questions with filters by difficulty, question_type, and pagination."""
    # Create 3 questions
    create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "SearchTarget question about Python",
            "choices": [
                {"content": "A", "is_correct": True},
                {"content": "B", "is_correct": False},
            ],
            "lesson_id": str(lesson.public_id),
        },
        session=db.session,
    )
    create_question(
        instructor_user,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Another question about databases",
            "choices": [
                {"content": "SQL", "is_correct": True},
                {"content": "NoSQL", "is_correct": True},
            ],
        },
        session=db.session,
    )
    create_question(
        instructor_user,
        course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "APPLY",
            "content": "Essay question on architecture",
        },
        session=db.session,
    )
    db.session.commit()

    # Filter by difficulty
    items, total, p, pp, total_pages = list_course_questions(
        instructor_user,
        course.id,
        filters={"difficulty": "REMEMBER"},
        session=db.session,
    )
    assert total == 1
    assert items[0]["difficulty"] == "REMEMBER"

    # Filter by question_type
    items, total, _, _, _ = list_course_questions(
        instructor_user,
        course.id,
        filters={"question_type": "MULTIPLE_CHOICE"},
        session=db.session,
    )
    assert total == 1
    assert items[0]["current_revision"]["question_type"] == "MULTIPLE_CHOICE"

    # Search keyword
    items, total, _, _, _ = list_course_questions(
        instructor_user,
        course.id,
        filters={"search": "SearchTarget"},
        session=db.session,
    )
    assert total == 1
    assert "SearchTarget" in items[0]["current_revision"]["content"]

    # Pagination
    items, total, p, pp, total_pages = list_course_questions(
        instructor_user,
        course.id,
        page=1,
        per_page=2,
        session=db.session,
    )
    assert total == 3
    assert len(items) == 2
    assert total_pages == 2


# ==============================================================================
# 4. LIFECYCLE: TRASH & RESTORE TESTS
# ==============================================================================


def test_trash_and_restore_question_lifecycle(
    app: Flask, instructor_user: User, course: Course
) -> None:
    """Soft-delete question to TRASH and restore back to ACTIVE."""
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "ESSAY",
            "difficulty": "REMEMBER",
            "content": "Lifecycle test question",
        },
        session=db.session,
    )
    db.session.commit()
    assert q.status == "ACTIVE"

    # Trash question
    trashed = trash_question(instructor_user, q.id, reason="Obsolete question", session=db.session)
    db.session.commit()
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None
    assert trashed.restore_until is not None

    # Idempotent trash
    trashed_again = trash_question(instructor_user, q.id, session=db.session)
    assert trashed_again.status == "TRASH"

    # Verify excluded from normal list
    items, total, _, _, _ = list_course_questions(instructor_user, course.id, session=db.session)
    assert total == 0

    # Restore question
    restored = restore_question(
        instructor_user, q.id, reason="Restored after review", session=db.session
    )
    db.session.commit()
    assert restored.status == "ACTIVE"
    assert restored.deleted_at is None
    assert restored.restore_until is None

    # Idempotent restore
    restored_again = restore_question(instructor_user, q.id, session=db.session)
    assert restored_again.status == "ACTIVE"

    # Verify back in normal list
    items, total, _, _, _ = list_course_questions(instructor_user, course.id, session=db.session)
    assert total == 1


# ==============================================================================
# 5. INSTRUCTOR WEB UI CONTROLLER TESTS
# ==============================================================================


def test_instructor_web_routes(
    client: FlaskClient, app: Flask, instructor_user: User, course: Course
) -> None:
    from tests.conftest import login_web_user

    login_web_user(client, instructor_user)

    # 1. POST create question
    resp = client.post(
        f"/instructor/courses/{course.public_id}/questions",
        json={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Web route test question",
            "choices": [
                {"content": "Opt 1", "is_correct": True},
                {"content": "Opt 2", "is_correct": False},
            ],
        },
    )
    assert resp.status_code == 201
    q_data = resp.get_json()
    q_id = q_data["question_id"]

    # 2. GET list questions
    resp = client.get(f"/instructor/courses/{course.public_id}/questions")
    assert resp.status_code == 200
    list_data = resp.get_json()
    assert list_data["total"] >= 1

    # 3. GET question detail
    resp = client.get(f"/instructor/questions/{q_id}")
    assert resp.status_code == 200
    detail = resp.get_json()
    assert detail["question_id"] == q_id

    # 4. POST trash question
    resp = client.post(
        f"/instructor/questions/{q_id}/trash",
        json={"reason": "Testing web trash"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["question"]["status"] == "TRASH"

    # 5. POST restore question
    resp = client.post(
        f"/instructor/questions/{q_id}/restore",
        json={"reason": "Testing web restore"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["question"]["status"] == "ACTIVE"
