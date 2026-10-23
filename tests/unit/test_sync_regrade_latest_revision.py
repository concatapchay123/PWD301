"""Answer corrections must not restore a superseded answer key."""

import uuid
from decimal import Decimal

import pytest

from pwd301.extensions import db
from pwd301.models.attempt_regrade import (
    AssessmentResult,
    AssessmentResultHistory,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    RegradeJob,
)
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.question_bank_service import create_question, create_question_revision
from pwd301.services.regrade_worker import process_regrade_job
from tests.unit.test_assessment_regrading_traceability import active_course as active_course
from tests.unit.test_assessment_regrading_traceability import admin_user as admin_user
from tests.unit.test_assessment_regrading_traceability import enrolled_students as enrolled_students
from tests.unit.test_assessment_regrading_traceability import instructor_user as instructor_user
from tests.unit.test_assessment_regrading_traceability import setup_roles as setup_roles
from tests.unit.test_assessment_regrading_traceability import student_one as student_one
from tests.unit.test_assessment_regrading_traceability import student_two as student_two


@pytest.fixture(autouse=True)
def _enable_assessment_authoring(app):
    """Enable direct assessment authoring & live publishing in regrade revision tests."""
    db.session.info["course_workflow_applying"] = True
    yield
    db.session.info.pop("course_workflow_applying", None)


@pytest.mark.parametrize("job_order", [(1, 0), (0, 1)])
@pytest.mark.parametrize("first_correction_type", ["ANSWER_ONLY", "CONTENT_OR_CHOICES"])
def test_older_answer_correction_cannot_revert_latest_approved_key(
    app, instructor_user, active_course, enrolled_students, job_order, first_correction_type
):
    question = create_question(
        instructor_user,
        active_course.id,
        {
            "content": "Latest approved answer",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 10,
            "choices": [
                {"content": "A", "is_correct": True, "position": 1},
                {"content": "B", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assessment = create_assessment(
        instructor_user,
        active_course.id,
        {"title": "Out of order correction jobs", "assessment_type": "QUIZ"},
    )
    assign_question(
        instructor_user, assessment.id, {"question_id": str(question.public_id), "points": 10}
    )
    publish_assessment(instructor_user, assessment.id)
    student = enrolled_students[0]
    attempt, lease = start_assessment_attempt(student, assessment.id)
    snapshot = attempt.attempt_questions[0]
    original_revision_id = snapshot.source_question_revision_id
    original_choices = [
        (str(c.choice_key_snapshot), c.content_snapshot) for c in snapshot.choice_snapshots
    ]
    choice_b = next(c for c in snapshot.choice_snapshots if c.content_snapshot == "B")
    save_attempt_answer(
        student,
        attempt.id,
        snapshot.id,
        {
            "selected_choice_keys": [str(choice_b.choice_key_snapshot)],
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "lease_epoch": attempt.lease_epoch,
        },
        raw_lease_token=lease,
    )
    submit_assessment_attempt(student, attempt.id, raw_lease_token=lease)

    corrections = []
    latest_revision = None
    for index, correct_answer in enumerate(("B", "A")):
        correction_type = first_correction_type if index == 0 else "ANSWER_ONLY"
        corrected_content = (
            "Corrected question content"
            if first_correction_type == "CONTENT_OR_CHOICES"
            else "Latest approved answer"
        )
        latest_revision, correction = create_question_revision(
            instructor_user,
            question.id,
            {
                "content": corrected_content,
                "reason": f"Approved key is {correct_answer}",
                "correction_type": correction_type,
                "choices": [
                    {"content": "A", "is_correct": correct_answer == "A", "position": 1},
                    {"content": "B", "is_correct": correct_answer == "B", "position": 2},
                ],
            },
        )
        corrections.append(correction)

    jobs = [
        db.session.query(RegradeJob).filter_by(question_correction_id=c.id).one()
        for c in corrections
    ]
    for index in job_order:
        process_regrade_job(jobs[index].id, actor=instructor_user)
    db.session.expire_all()
    result = db.session.query(AssessmentResult).filter_by(attempt_id=attempt.id).one()
    grade = db.session.query(AttemptQuestionGrade).filter_by(attempt_question_id=snapshot.id).one()
    expected_score = Decimal("10" if first_correction_type == "CONTENT_OR_CHOICES" else "0")
    assert result.raw_score == expected_score, "Correction ordering changed the canonical result"
    assert grade.awarded_points == expected_score
    if first_correction_type == "ANSWER_ONLY":
        assert grade.graded_against_revision_id == latest_revision.id
    else:
        assert grade.grading_status == "FULL_CREDIT"
        assert grade.grading_rule == "CONTENT_FULL_CREDIT"
    assert snapshot.source_question_revision_id == original_revision_id
    assert [
        (str(c.choice_key_snapshot), c.content_snapshot) for c in snapshot.choice_snapshots
    ] == original_choices

    history_counts = (
        db.session.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=snapshot.id)
        .count(),
        db.session.query(AssessmentResultHistory).filter_by(attempt_id=attempt.id).count(),
    )
    process_regrade_job(jobs[0].id, actor=instructor_user)
    process_regrade_job(jobs[1].id, actor=instructor_user)
    assert history_counts == (
        db.session.query(AttemptQuestionGradeHistory)
        .filter_by(attempt_question_id=snapshot.id)
        .count(),
        db.session.query(AssessmentResultHistory).filter_by(attempt_id=attempt.id).count(),
    )
