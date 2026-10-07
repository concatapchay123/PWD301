"""Unit U05 Test: Assessment Question Synchronization and Validation.

Tests for SYNC-024 (Bloom difficulty validation without silent coercion),
SYNC-025 (Short answer accepted answers validation),
and Assessment Question APIs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.identity import Role
from pwd301.services.assessment_service import create_assessment
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def u05_setup(app: Flask) -> dict[str, Any]:
    sess = db.session
    for code, name in [("STUDENT", "Student"), ("INSTRUCTOR", "Instructor"), ("ADMIN", "Admin")]:
        r = sess.query(Role).filter_by(code=code).first()
        if not r:
            sess.add(Role(code=code, name=name))
    sess.commit()

    instructor = register_user(
        email=f"inst_u05_{datetime.now(UTC).timestamp()}@fpt.edu.vn",
        password="ValidPassword123!",
        display_name="Instructor U05",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    course = create_course(
        instructor,
        {
            "course_code": f"U05{int(datetime.now(UTC).timestamp()) % 10000}",
            "title": "U05 Assessment Sync Course",
            "summary": "Testing U05 fixes",
        },
        session=sess,
    )
    sess.commit()

    asm = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "U05 Assessment",
            "assessment_type": "QUIZ",
            "duration_minutes": 30,
            "attempt_limit": None,
        },
        session=sess,
    )
    sess.commit()

    return {"instructor": instructor, "course": course, "assessment": asm}


def test_create_question_bloom_difficulty_strict_validation(
    client: FlaskClient, u05_setup: dict[str, Any]
):
    """SYNC-024: Unsupported Bloom difficulty (e.g. ANALYZE, CREATE, INVALID) must be rejected explicitly."""
    instructor = u05_setup["instructor"]
    asm = u05_setup["assessment"]
    login_web_user(client, instructor)

    # 1. ANALYZE should be rejected with 400 ValidationError, not silently coerced to APPLY
    resp = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Analyze the time complexity of QuickSort.",
            "difficulty": "ANALYZE",
            "points": 2.0,
            "choices": [
                {"content": "O(N log N)", "is_correct": True},
                {"content": "O(N^2)", "is_correct": False},
            ],
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    err = data.get("error", {})
    msg = err.get("message", "") if isinstance(err, dict) else str(err)
    assert "Mức độ Bloom" in msg or "difficulty" in msg.lower()

    # 2. Canonical APPLY should succeed
    resp_ok = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json={
            "question_type": "SINGLE_CHOICE",
            "content": "Apply QuickSort to the array.",
            "difficulty": "APPLY",
            "points": 2.0,
            "choices": [
                {"content": "Sorted array", "is_correct": True},
                {"content": "Unsorted array", "is_correct": False},
            ],
        },
    )
    assert resp_ok.status_code == 201


def test_batch_create_bloom_difficulty_strict_validation(
    client: FlaskClient, u05_setup: dict[str, Any]
):
    """SYNC-024: Batch creation must reject invalid Bloom difficulty without silent coercion."""
    instructor = u05_setup["instructor"]
    asm = u05_setup["assessment"]
    login_web_user(client, instructor)

    resp = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/batch",
        json={
            "questions": [
                {
                    "question_type": "SINGLE_CHOICE",
                    "content": "Evaluate this algorithm.",
                    "difficulty": "EVALUATE",
                    "points": 1.0,
                    "choices": [
                        {"content": "Good", "is_correct": True},
                        {"content": "Bad", "is_correct": False},
                    ],
                }
            ]
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    err = data.get("error", {})
    msg = err.get("message", "") if isinstance(err, dict) else str(err)
    assert "Mức độ Bloom" in msg or "difficulty" in msg.lower()


def test_short_answer_requires_non_empty_accepted_answers(
    client: FlaskClient, u05_setup: dict[str, Any]
):
    """SYNC-025: Short answer questions must reject empty or missing accepted answers."""
    instructor = u05_setup["instructor"]
    asm = u05_setup["assessment"]
    login_web_user(client, instructor)

    # Single create with empty accepted_answers
    resp = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json={
            "question_type": "SHORT_ANSWER",
            "content": "What is the capital of Vietnam?",
            "difficulty": "REMEMBER",
            "points": 1.0,
            "accepted_answers": [],
        },
    )
    assert resp.status_code == 400
    err_obj = resp.get_json().get("error", {})
    err_msg = err_obj.get("message", "") if isinstance(err_obj, dict) else str(err_obj)
    assert "SHORT_ANSWER" in err_msg or "accepted answer" in err_msg.lower()

    # Batch create with empty accepted_answers
    resp_batch = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/batch",
        json={
            "questions": [
                {
                    "question_type": "SHORT_ANSWER",
                    "content": "What is the capital of France?",
                    "difficulty": "REMEMBER",
                    "points": 1.0,
                    "accepted_answers": [],
                }
            ]
        },
    )
    assert resp_batch.status_code == 400
    b_err = resp_batch.get_json().get("error", {})
    b_msg = b_err.get("message", "") if isinstance(b_err, dict) else str(b_err)
    assert "SHORT_ANSWER" in b_msg or "accepted answer" in b_msg.lower()
