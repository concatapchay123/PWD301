"""Unit tests for Question Revision Engine and Question Correction Mechanism (TASK-011)."""

from __future__ import annotations

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.attempt_regrade import AttemptQuestion, QuestionCorrection
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import (
    Question,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    QuestionImmutableError,
    QuestionRevisionNotFoundError,
    QuestionValidationError,
)
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import (
    _serialize_question_revision,
    create_question,
    create_question_revision,
    get_question_revision_detail,
    is_question_in_use,
    list_question_corrections,
    list_question_revisions,
    update_question,
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
    u = register_user("qr_inst@example.com", "Password@123", "Revision Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary instructor user."""
    u = register_user("qr_other@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def course(app: Flask, instructor_user: User) -> Course:
    """Create a course owned by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-QR101",
            "title": "Question Revision Course",
            "description": "Testing Question Revisions and Corrections",
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
            "title": "Lesson for Question Revisions",
            "markdown_content": "# Lesson 1",
            "position": 1,
        },
    )
    db.session.commit()
    return les


@pytest.fixture
def mcq_question(app: Flask, instructor_user: User, course: Course, lesson: Lesson) -> Question:
    """Create a standard multiple choice question."""
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "stem": "What is the capital of France?",
            "general_feedback": "Paris is the capital.",
            "default_points": 2.0,
            "difficulty": "REMEMBER",
            "lesson_id": lesson.id,
            "choices": [
                {"content": "Paris", "is_correct": True, "position": 1},
                {"content": "Berlin", "is_correct": False, "position": 2},
                {"content": "Rome", "is_correct": False, "position": 3},
            ],
        },
    )
    db.session.commit()
    return q


@pytest.fixture
def sa_question(app: Flask, instructor_user: User, course: Course) -> Question:
    """Create a short answer question with accepted answers."""
    q = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SHORT_ANSWER",
            "stem": "Who created Python?",
            "default_points": 1.5,
            "difficulty": "UNDERSTAND",
            "accepted_answers": ["Guido van Rossum", "Guido"],
        },
    )
    db.session.commit()
    return q


# --- In-Use Detection Tests ---


def test_is_question_in_use_new_unused(mcq_question: Question) -> None:
    """A freshly created question with no assessments or attempts is not in use."""
    assert is_question_in_use(mcq_question, session=db.session) is False


def test_is_question_in_use_usage_count(mcq_question: Question) -> None:
    """Question with usage_count > 0 is recognized as in-use."""
    mcq_question.usage_count = 1
    db.session.commit()
    assert is_question_in_use(mcq_question, session=db.session) is True


def test_is_question_in_use_first_used_at(mcq_question: Question) -> None:
    """Question with first_used_at set is recognized as in-use."""
    mcq_question.first_used_at = utc_now()
    db.session.commit()
    assert is_question_in_use(mcq_question, session=db.session) is True


def test_is_question_in_use_revision_exposed(mcq_question: Question) -> None:
    """Question whose revision has was_student_exposed is recognized as in-use."""
    mcq_question.current_revision.was_student_exposed = True
    db.session.commit()
    assert is_question_in_use(mcq_question, session=db.session) is True


def test_is_question_in_use_revision_graded_count(mcq_question: Question) -> None:
    """Question whose revision has was_used_for_grading is recognized as in-use."""
    mcq_question.current_revision.was_used_for_grading = True
    db.session.commit()
    assert is_question_in_use(mcq_question, session=db.session) is True


def test_is_question_in_use_published_assessment(
    mcq_question: Question, course: Course, instructor_user: User
) -> None:
    """Question assigned to a PUBLISHED assessment is recognized as in-use."""
    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Published Midterm Exam",
        assessment_type="MIDTERM",
        status="PUBLISHED",
    )
    db.session.add(assessment)
    db.session.flush()

    assignment = AssessmentQuestionAssignment(
        assessment_id=assessment.id,
        question_id=mcq_question.id,
        position=1,
        points=2.0,
        source_type="BANK",
    )
    db.session.add(assignment)
    db.session.commit()

    assert is_question_in_use(mcq_question, session=db.session) is True


def test_is_question_in_use_draft_assessment_ignored(
    mcq_question: Question, course: Course, instructor_user: User
) -> None:
    """Question assigned ONLY to a DRAFT assessment is NOT in-use."""
    assessment = Assessment(
        course_id=course.id,
        creator_user_id=instructor_user.id,
        title="Draft Quiz",
        assessment_type="QUIZ",
        status="DRAFT",
    )
    db.session.add(assessment)
    db.session.flush()

    assignment = AssessmentQuestionAssignment(
        assessment_id=assessment.id,
        question_id=mcq_question.id,
        position=1,
        points=2.0,
        source_type="BANK",
    )
    db.session.add(assignment)
    db.session.commit()

    assert is_question_in_use(mcq_question, session=db.session) is False


def test_is_question_in_use_attempt_question(mcq_question: Question) -> None:
    """Question present in attempt_questions is recognized as in-use."""
    attempt_q = AttemptQuestion(
        attempt_id=1,  # dummy id for test
        source_question_id=mcq_question.id,
        source_question_revision_id=mcq_question.current_revision.id,
        position=1,
        points_assigned=2.0,
        question_type_snapshot="SINGLE_CHOICE",
        content_snapshot="Snapshot content",
    )
    db.session.add(attempt_q)
    db.session.commit()

    assert is_question_in_use(mcq_question, session=db.session) is True


# --- Branching Update Tests ---


def test_update_question_unused_in_place(mcq_question: Question, instructor_user: User) -> None:
    """Updating an unused question mutates the current revision in-place without new revision."""
    orig_rev_id = mcq_question.current_revision.id
    updated = update_question(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "What is the capital city of France?",
            "general_feedback": "Updated feedback: Paris.",
        },
        session=db.session,
    )
    db.session.commit()

    assert updated.id == mcq_question.id
    assert updated.current_revision.id == orig_rev_id
    assert updated.current_revision.revision_no == 1
    assert updated.current_revision.content == "What is the capital city of France?"
    assert updated.current_revision.explanation == "Updated feedback: Paris."

    # No QuestionCorrection should exist
    corrections = (
        db.session.query(QuestionCorrection)
        .filter(QuestionCorrection.question_id == mcq_question.id)
        .all()
    )
    assert len(corrections) == 0


def test_update_question_in_use_branches_new_revision(
    mcq_question: Question, instructor_user: User
) -> None:
    """Updating in-use question freezes old revision and creates revision 2 + QuestionCorrection."""
    mcq_question.usage_count = 1
    db.session.commit()

    rev1 = mcq_question.current_revision
    rev1_content = rev1.content
    rev1_id = rev1.id

    updated = update_question(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "Corrected: Capital of France?",
            "change_type": "TYPO_FIX",
            "change_reason": "Fix minor phrasing in question stem",
        },
        session=db.session,
    )
    db.session.commit()

    # Question current revision should now be revision 2
    assert updated.current_revision.revision_no == 2
    assert updated.current_revision.id != rev1_id
    assert updated.current_revision.content == "Corrected: Capital of France?"
    assert updated.current_revision.change_type == "TYPO_FIX"
    assert updated.current_revision.change_reason == "Fix minor phrasing in question stem"

    # Revision 1 should remain untouched
    db.session.refresh(rev1)
    assert rev1.content == rev1_content
    assert rev1.revision_no == 1

    # QuestionCorrection record created
    correction = (
        db.session.query(QuestionCorrection)
        .filter(QuestionCorrection.question_id == mcq_question.id)
        .first()
    )
    assert correction is not None
    assert correction.from_revision_id == rev1_id
    assert correction.to_revision_id == updated.current_revision.id
    assert correction.correction_type == "CONTENT_OR_CHOICES"  # TYPO_FIX modifies content
    assert correction.status == "PENDING"
    assert correction.reason == "Fix minor phrasing in question stem"


def test_update_question_in_use_missing_reason_fails(
    mcq_question: Question, instructor_user: User
) -> None:
    """Updating an in-use question without change_reason must raise QuestionValidationError."""
    mcq_question.usage_count = 1
    db.session.commit()

    with pytest.raises(QuestionValidationError) as exc_info:
        update_question(
            actor=instructor_user,
            question_id=mcq_question.public_id,
            payload={"stem": "New stem without reason"},
            session=db.session,
        )
    assert "change_reason is required" in str(exc_info.value)


def test_update_question_in_use_type_mutation_fails(
    mcq_question: Question, instructor_user: User
) -> None:
    """Changing question_type of an in-use question must raise QuestionImmutableError."""
    mcq_question.usage_count = 1
    db.session.commit()

    with pytest.raises(QuestionImmutableError) as exc_info:
        update_question(
            actor=instructor_user,
            question_id=mcq_question.public_id,
            payload={
                "question_type": "TRUE_FALSE",
                "change_reason": "Want to switch type",
            },
            session=db.session,
        )
    assert "Cannot change question_type" in str(exc_info.value)


# --- Explicit Revision Creation Tests ---


def test_create_question_revision_explicit_increment(
    mcq_question: Question, instructor_user: User
) -> None:
    """create_question_revision creates an incremented revision (revision_no = 2)."""
    rev2, correction = create_question_revision(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "What is the capital of the French Republic?",
            "change_type": "CONTENT_CHANGE",
            "change_reason": "Formalize country name",
        },
        session=db.session,
    )
    db.session.commit()

    assert rev2.revision_no == 2
    assert rev2.content == "What is the capital of the French Republic?"
    assert rev2.change_type == "CONTENT_CHANGE"
    assert rev2.change_reason == "Formalize country name"
    serialized = _serialize_question_revision(rev2)
    assert serialized["revision_no"] == 2
    assert serialized["content"] == "What is the capital of the French Republic?"

    # Choices should have been cloned from revision 1
    choices = (
        db.session.query(QuestionRevisionChoice)
        .filter(QuestionRevisionChoice.question_revision_id == rev2.id)
        .order_by(QuestionRevisionChoice.position)
        .all()
    )
    assert len(choices) == 3
    assert choices[0].content == "Paris"
    assert choices[0].is_correct is True
    # Cloned choices must have their own distinct public_ids and IDs
    rev1 = [r for r in mcq_question.revisions if r.revision_no == 1][0]
    rev1_choice_ids = [c.id for c in rev1.choices]
    for c in choices:
        assert c.id not in rev1_choice_ids


def test_create_question_revision_deep_clones_sa_answers(
    sa_question: Question, instructor_user: User
) -> None:
    """create_question_revision clones accepted_answers when not explicitly provided."""
    rev2, _ = create_question_revision(
        actor=instructor_user,
        question_id=sa_question.public_id,
        payload={
            "stem": "Who is the primary creator of Python?",
            "change_type": "TYPO_FIX",
            "change_reason": "Grammar polish",
        },
        session=db.session,
    )
    db.session.commit()

    assert rev2.revision_no == 2
    assert len(rev2.accepted_answers) == 2
    texts = {a.answer_text for a in rev2.accepted_answers}
    assert "Guido van Rossum" in texts
    assert "Guido" in texts


def test_create_question_revision_with_new_choices_infers_content_or_choices(
    mcq_question: Question, instructor_user: User
) -> None:
    """Supplying new choices in revision creation updates choices and infers CONTENT_OR_CHOICES."""
    mcq_question.usage_count = 1
    db.session.commit()

    rev2, correction = create_question_revision(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "Which of these is the capital of France?",
            "change_type": "CONTENT_CHANGE",
            "change_reason": "Add Lyon as option",
            "choices": [
                {"content": "Paris", "is_correct": True, "position": 1},
                {"content": "Berlin", "is_correct": False, "position": 2},
                {"content": "Rome", "is_correct": False, "position": 3},
                {"content": "Lyon", "is_correct": False, "position": 4},
            ],
        },
        session=db.session,
    )
    db.session.commit()

    assert rev2.revision_no == 2
    assert len(rev2.choices) == 4
    assert correction is not None
    assert correction.correction_type == "CONTENT_OR_CHOICES"


def test_list_question_revisions_and_detail(mcq_question: Question, instructor_user: User) -> None:
    """list_question_revisions and get_question_revision_detail return expected items."""
    # Create revision 2
    create_question_revision(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "What is France's capital?",
            "change_type": "TYPO_FIX",
            "change_reason": "Shorter phrasing",
        },
        session=db.session,
    )
    db.session.commit()

    items, total, page, per_page, total_pages = list_question_revisions(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        session=db.session,
    )
    assert total == 2
    assert len(items) == 2
    # Should be ordered by revision_no DESC
    assert items[0]["revision_no"] == 2
    assert items[1]["revision_no"] == 1

    # Detail of revision 1
    detail1 = get_question_revision_detail(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        revision_no=1,
        session=db.session,
    )
    assert detail1["revision_no"] == 1
    assert detail1["stem"] == "What is the capital of France?"
    assert len(detail1["choices"]) == 3

    # Non-existent revision
    with pytest.raises(QuestionRevisionNotFoundError):
        get_question_revision_detail(
            actor=instructor_user,
            question_id=mcq_question.public_id,
            revision_no=999,
            session=db.session,
        )


def test_list_question_corrections(mcq_question: Question, instructor_user: User) -> None:
    """list_question_corrections retrieves existing corrections for a question."""
    mcq_question.usage_count = 1
    db.session.commit()

    create_question_revision(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "Corrected capital of France question",
            "change_type": "ANSWER_CHANGE",
            "change_reason": "Updated answer key",
        },
        session=db.session,
    )
    db.session.commit()

    corrections = list_question_corrections(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        session=db.session,
    )
    assert len(corrections) == 1
    c = corrections[0]
    assert c["from_revision_no"] == 1
    assert c["to_revision_no"] == 2
    assert c["status"] == "PENDING"
    assert c["reason"] == "Updated answer key"
    assert "correction_id" in c


def test_audit_trail_recorded_for_revision_and_correction(
    mcq_question: Question, instructor_user: User
) -> None:
    """QUESTION_REVISED and QUESTION_CORRECTION_CREATED audit events are persisted."""
    mcq_question.usage_count = 1
    db.session.commit()

    create_question_revision(
        actor=instructor_user,
        question_id=mcq_question.public_id,
        payload={
            "stem": "Audit trail test stem",
            "change_type": "TYPO_FIX",
            "change_reason": "Audit verification",
        },
        session=db.session,
    )
    db.session.commit()

    events = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.action.in_(["QUESTION_REVISED", "QUESTION_CORRECTION_CREATED"]))
        .all()
    )
    action_types = {e.action for e in events}
    assert "QUESTION_REVISED" in action_types
    assert "QUESTION_CORRECTION_CREATED" in action_types
