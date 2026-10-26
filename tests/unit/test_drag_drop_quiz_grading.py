"""Tests for F05: Drag-and-Drop Quiz Grading Engine.

Verifies:
- Grouped choices graded correctly via choice key.
- Grouped choices graded correctly via token text variants (e.g., left token, right text, combined text).
- Wrong match graded 0 points.
- Completed attempt results include valid slot_results in student review results.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.seeds.baseline import seed_baseline
from backend.services.assessment_service import (
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
from backend.services.course_service import create_course
from backend.services.enrollment_service import enroll_student
from backend.services.question_bank_service import create_question
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture(autouse=True)
def _enable_assessment_authoring(app: Flask):
    """Enable direct assessment authoring & live publishing in drag drop unit tests."""
    db.session.info["course_workflow_applying"] = True
    yield
    db.session.info.pop("course_workflow_applying", None)


@pytest.fixture
def drag_drop_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, student, and assessment with drag-and-drop grouped question."""
    sess: Session = db.session
    seed_baseline(sess)

    inst = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor DD", session=sess
    )
    assign_role_to_user(inst.id, "INSTRUCTOR", session=sess)

    student = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student DD", session=sess
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    course = create_course(
        actor=inst,
        data={
            "course_code": f"DD-{uuid.uuid4().hex[:4].upper()}",
            "title": "Drag Drop Course",
            "category": "Testing",
            "capacity": 100,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    assessment = create_assessment(
        inst,
        course.id,
        {
            "title": "Drag-and-Drop Protocol Matching Quiz",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "passing_percent": 60.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    section = create_section(inst, assessment.id, {"title": "Section 1"}, session=sess)

    question = create_question(
        inst,
        course.id,
        {
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Match the protocol to its purpose.",
            "default_points": 10.0,
            "choices": [
                {
                    "content": "[[PWD301:G:MATCH:1]]HTTP|||Web transfer",
                    "is_correct": True,
                    "position": 1,
                },
                {
                    "content": "[[PWD301:G:MATCH:1]]FTP|||File transfer",
                    "is_correct": False,
                    "position": 2,
                },
                {
                    "content": "[[PWD301:G:MATCH:2]]FTP|||File transfer",
                    "is_correct": True,
                    "position": 3,
                },
                {
                    "content": "[[PWD301:G:MATCH:2]]HTTP|||Web transfer",
                    "is_correct": False,
                    "position": 4,
                },
            ],
        },
        session=sess,
    )
    assign_question(
        inst,
        assessment.id,
        {
            "question_id": question.id,
            "points_assigned": 10.0,
            "section_id": section.id,
        },
        session=sess,
    )
    publish_assessment(inst, assessment.id, session=sess)
    sess.commit()

    return {
        "instructor": inst,
        "student": student,
        "course": course,
        "assessment": assessment,
        "question": question,
    }


def test_drag_drop_quiz_grading_via_choice_keys(app: Flask, drag_drop_env: dict[str, Any]) -> None:
    """Grouped choices submitted using choice_keys evaluate to 100% correct."""
    sess: Session = db.session
    student = drag_drop_env["student"]
    assessment = drag_drop_env["assessment"]

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Find the correct choices by content
    c1 = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:1]]HTTP|||Web transfer"
    )
    c2 = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:2]]FTP|||File transfer"
    )

    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(c1.choice_key_snapshot), str(c2.choice_key_snapshot)],
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
    assert float(attempt.result.raw_score) == 10.0
    assert bool(attempt.result.passed) is True


def test_drag_drop_quiz_grading_via_clean_text_fallback(
    app: Flask, drag_drop_env: dict[str, Any]
) -> None:
    """Grouped choices submitted using text variants evaluate to correct score."""
    sess: Session = db.session
    student = drag_drop_env["student"]
    assessment = drag_drop_env["assessment"]

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Save answer using text fallback tokens ("Web transfer" and "File transfer" or combined)
    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": ["HTTP|||Web transfer", "FTP|||File transfer"],
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
    assert float(attempt.result.raw_score) == 10.0


def test_drag_drop_quiz_grading_wrong_match_zero_points(
    app: Flask, drag_drop_env: dict[str, Any]
) -> None:
    """Grouped choices with mismatched pairs evaluate to 0 points."""
    sess: Session = db.session
    student = drag_drop_env["student"]
    assessment = drag_drop_env["assessment"]

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Select wrong distractors
    c1_wrong = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:1]]FTP|||File transfer"
    )
    c2_wrong = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:2]]HTTP|||Web transfer"
    )

    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [
                str(c1_wrong.choice_key_snapshot),
                str(c2_wrong.choice_key_snapshot),
            ],
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
    assert float(attempt.result.raw_score) == 0.0


def test_drag_drop_quiz_student_result_includes_slot_results(
    app: Flask, drag_drop_env: dict[str, Any]
) -> None:
    """get_attempt_result_for_student populates slot_results with slot, is_correct, user_text, expected_text."""
    sess: Session = db.session
    student = drag_drop_env["student"]
    assessment = drag_drop_env["assessment"]

    attempt, lease_token = start_assessment_attempt(student, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Student answers: slot 0 correct, slot 1 wrong
    c1_correct = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:1]]HTTP|||Web transfer"
    )
    c2_wrong = next(
        c
        for c in aq.choice_snapshots
        if c.content_snapshot == "[[PWD301:G:MATCH:2]]HTTP|||Web transfer"
    )

    save_attempt_answer(
        actor=student,
        attempt_id=attempt.id,
        attempt_question_id=aq.id,
        payload={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [
                str(c1_correct.choice_key_snapshot),
                str(c2_wrong.choice_key_snapshot),
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

    # Get student result
    result_data = get_attempt_result_for_student(
        actor=student,
        attempt_id=attempt.id,
        session=sess,
    )

    questions = result_data.get("questions", [])
    assert len(questions) == 1
    q_data = questions[0]
    assert "slot_results" in q_data

    slot_results = q_data["slot_results"]
    assert len(slot_results) == 2

    # Slot 0 (group 1): correct
    slot_0 = slot_results[0]
    assert slot_0["slot"] == 0
    assert slot_0["is_correct"] is True
    assert slot_0["user_text"] == "HTTP|||Web transfer"
    assert slot_0["expected_text"] == "HTTP|||Web transfer"

    # Slot 1 (group 2): wrong
    slot_1 = slot_results[1]
    assert slot_1["slot"] == 1
    assert slot_1["is_correct"] is False
    assert slot_1["user_text"] == "HTTP|||Web transfer"
    assert slot_1["expected_text"] == "FTP|||File transfer"
