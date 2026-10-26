"""Question-bank authoring shares the sealed course aggregate without changing history."""

import json

import pytest

from backend.extensions import db
from backend.models.course import CourseChangeRequest
from backend.models.question_bank import Question, QuestionRevision
from backend.models.types import utc_now
from backend.services.exceptions import ConflictError, QuestionStateViolationError
from backend.services.lesson_service import approve_course_change_request, submit_course_changeset
from backend.services.question_bank_service import (
    create_question,
    create_question_revision,
    get_question_detail,
    list_course_questions,
    restore_question,
    trash_question,
    update_question,
)

pytest_plugins = ["tests.test_lesson_revision_lifecycle"]


def payload(content="Approved question"):
    return {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": content,
        "choices": [
            {"content": "Yes", "is_correct": True, "position": 1},
            {"content": "No", "is_correct": False, "position": 2},
        ],
    }


def draft_for(course):
    return (
        db.session.query(CourseChangeRequest)
        .filter_by(
            course_id=course.id,
            change_type="COURSE_VERSION_CHANGESET",
            status="DRAFT",
        )
        .one()
    )


def test_new_question_is_draft_owned_by_course_aggregate(app, published_course, instructor_user):
    course, _ = published_course
    question = create_question(
        instructor_user, course.id, payload("Proposed new question"), session=db.session
    )
    assert question.status == "DRAFT"
    assert question.change_request_id == draft_for(course).id
    assert question.previous_question_id is None
    operation = next(
        iter(json.loads(draft_for(course).proposed_payload_json)["operations"].values())
    )
    assert operation["action"] == "QUESTION_REVISION"
    assert operation["snapshot"]["content"] == "Proposed new question"


def test_existing_question_effective_read_and_search_preserve_live_revision(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    db.session.commit()
    revision_id = original.current_revision.id
    proposed = update_question(
        instructor_user, original.id, {"content": "Proposed searchable content"}, session=db.session
    )
    assert proposed.id != original.id
    assert original.current_revision.id == revision_id
    assert original.current_revision.content == "Approved question"
    assert (
        get_question_detail(instructor_user, original.id)["content"]
        == "Proposed searchable content"
    )
    items, count, *_ = list_course_questions(instructor_user, course.id, {"search": "searchable"})
    assert count == 1
    assert items[0]["content"] == "Proposed searchable content"
    assert (
        len(db.session.query(Question).filter_by(course_id=course.id, status="ACTIVE").all()) == 1
    )


@pytest.mark.parametrize("mutation", ["create", "update", "revision", "trash", "restore"])
def test_initial_pending_review_freezes_every_question_mutation(app, instructor_user, mutation):
    from backend.services.course_service import create_course

    course = create_course(
        instructor_user,
        {"course_code": "QB-PENDING", "title": "Initial pending question bank"},
        session=db.session,
    )
    question = create_question(instructor_user, course.id, payload(), session=db.session)
    course.status = "SUBMITTED_FOR_REVIEW"
    db.session.commit()
    calls = {
        "create": lambda: create_question(
            instructor_user, course.id, payload("Blocked"), session=db.session
        ),
        "update": lambda: update_question(
            instructor_user, question.id, {"content": "Blocked"}, session=db.session
        ),
        "revision": lambda: create_question_revision(
            instructor_user, question.id, {"content": "Blocked"}, session=db.session
        ),
        "trash": lambda: trash_question(instructor_user, question.id, session=db.session),
        "restore": lambda: restore_question(instructor_user, question.id, session=db.session),
    }
    with pytest.raises(ConflictError):
        calls[mutation]()


def test_question_approval_applies_sealed_content_preserving_original_identity(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    db.session.commit()
    old_revision = original.current_revision.id
    proposed = update_question(
        instructor_user, original.id, {"content": "Reviewed exact content"}, session=db.session
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Question update"}, session=db.session
    )
    proposed.current_revision.content = "Unreviewed database tampering"
    db.session.flush()
    approve_course_change_request(
        admin_user, pending.id, "Approve sealed question", session=db.session
    )
    db.session.expire(original)
    assert original.current_revision.content == "Reviewed exact content"
    assert original.id != proposed.id
    assert db.session.get(QuestionRevision, old_revision).content == "Approved question"


def test_used_question_type_lock_and_correction_are_preserved_until_approval(
    app, published_course, instructor_user, admin_user
):
    from backend.models.attempt_regrade import QuestionCorrection

    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    original.first_answered_at = utc_now()
    original.current_revision.was_student_exposed = True
    db.session.commit()
    with pytest.raises(QuestionStateViolationError):
        update_question(
            instructor_user,
            original.id,
            {"question_type": "ESSAY", "reason": "Still forbidden"},
            session=db.session,
        )
    proposed = update_question(
        instructor_user,
        original.id,
        {"content": "Reviewed correction", "reason": "Correct the prompt"},
        session=db.session,
    )
    assert original.current_revision.content == "Approved question"
    assert proposed.current_revision.content == "Reviewed correction"
    assert db.session.query(QuestionCorrection).count() == 0
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Correction"}, session=db.session
    )
    approve_course_change_request(admin_user, pending.id, "Approved correction", session=db.session)
    assert db.session.query(QuestionCorrection).filter_by(question_id=original.id).count() == 1


def test_new_question_approval_uses_sealed_payload_and_active_filter(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    candidate = create_question(
        instructor_user, course.id, payload("Reviewed new question"), session=db.session
    )
    items, count, *_ = list_course_questions(instructor_user, course.id, {"status": "ACTIVE"})
    assert count == 1
    assert items[0]["status"] == "ACTIVE"
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "New question"}, session=db.session
    )
    candidate.current_revision.content = "Unreviewed draft mutation"
    db.session.flush()
    approve_course_change_request(admin_user, pending.id, "Approve", session=db.session)
    assert candidate.status == "ACTIVE"
    assert candidate.change_request_id is None
    assert candidate.current_revision.content == "Reviewed new question"


def test_proposed_trash_and_restore_change_effective_bank_only(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    db.session.commit()
    candidate = trash_question(instructor_user, original.id, session=db.session)
    assert original.status == "ACTIVE"
    assert list_course_questions(instructor_user, course.id)[1] == 0
    items, count, *_ = list_course_questions(instructor_user, course.id, {"status": "TRASH"})
    assert count == 1
    assert items[0]["status"] == "TRASH"
    restore_question(instructor_user, candidate.id, session=db.session)
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Restore proposal"}, session=db.session
    )
    approve_course_change_request(admin_user, pending.id, "Approve", session=db.session)
    assert original.status == "ACTIVE"


def test_idempotent_trash_proposal_can_be_approved(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    trash_question(admin_user, original.id, session=db.session)
    db.session.commit()
    trash_question(instructor_user, original.id, session=db.session)
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Still trashed"}, session=db.session
    )
    approve_course_change_request(admin_user, pending.id, "Approve", session=db.session)
    assert original.status == "TRASH"


def test_grading_history_question_is_proposed_as_retired_without_changing_history(
    app, published_course, instructor_user, admin_user
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    original.current_revision.was_used_for_grading = True
    db.session.commit()
    candidate = trash_question(instructor_user, original.id, session=db.session)
    assert original.status == "ACTIVE"
    assert get_question_detail(instructor_user, candidate.id)["status"] == "RETIRED"
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Retire"}, session=db.session
    )
    approve_course_change_request(admin_user, pending.id, "Approve", session=db.session)
    assert original.status == "RETIRED"
    assert original.current_revision.was_used_for_grading is True


@pytest.mark.parametrize("decision", ["withdraw", "reject"])
def test_terminal_review_preserves_question_proposal_in_successor_draft(
    app, published_course, instructor_user, admin_user, decision
):
    from backend.services.lesson_service import (
        reject_course_change_request,
        retract_course_changeset,
    )

    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    db.session.commit()
    candidate = update_question(
        instructor_user, original.id, {"content": "Retained proposal"}, session=db.session
    )
    pending = submit_course_changeset(
        instructor_user, course.id, {"title": "Retained"}, session=db.session
    )
    sealed = pending.proposed_payload_json
    if decision == "withdraw":
        retract_course_changeset(instructor_user, course.id, session=db.session)
    else:
        reject_course_change_request(admin_user, pending.id, "Revise", session=db.session)
    assert pending.proposed_payload_json == sealed
    assert candidate.change_request_id == draft_for(course).id
    assert candidate.change_request_id != pending.id
    assert original.current_revision.content == "Approved question"
    assert get_question_detail(instructor_user, original.id)["content"] == "Retained proposal"
    update_question(
        instructor_user, original.id, {"content": "Resubmitted proposal"}, session=db.session
    )
    assert get_question_detail(instructor_user, original.id)["content"] == "Resubmitted proposal"


@pytest.mark.parametrize("mutation", ["create", "update", "revision", "trash", "restore"])
def test_pending_aggregate_freezes_every_question_mutation(
    app, published_course, instructor_user, admin_user, mutation
):
    course, _ = published_course
    original = create_question(admin_user, course.id, payload(), session=db.session)
    db.session.commit()
    update_question(instructor_user, original.id, {"content": "Review"}, session=db.session)
    submit_course_changeset(instructor_user, course.id, {"title": "Pending"}, session=db.session)
    calls = {
        "create": lambda: create_question(
            instructor_user, course.id, payload("Blocked"), session=db.session
        ),
        "update": lambda: update_question(
            instructor_user, original.id, {"content": "Blocked"}, session=db.session
        ),
        "revision": lambda: create_question_revision(
            instructor_user, original.id, {"content": "Blocked"}, session=db.session
        ),
        "trash": lambda: trash_question(instructor_user, original.id, session=db.session),
        "restore": lambda: restore_question(instructor_user, original.id, session=db.session),
    }
    with pytest.raises(ConflictError):
        calls[mutation]()


def test_blueprint_preflight_and_materialization_with_draft_questions(
    app, published_course, instructor_user, admin_user
):
    from backend.models.assessment import Assessment
    from backend.services.assessment_service import (
        configure_blueprint,
        create_assessment,
        publish_assessment,
    )
    from backend.services.course_workflow_service import payload_for

    course, _ = published_course
    # 1. Create a question in the draft changeset of this published course
    question = create_question(
        instructor_user,
        course.id,
        {
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "Draft question for blueprint test",
            "choices": [
                {"content": "Option A", "is_correct": True, "position": 1},
                {"content": "Option B", "is_correct": False, "position": 2},
            ],
        },
        session=db.session,
    )
    db.session.commit()

    # 2. Create an assessment in the same draft
    assessment = create_assessment(
        instructor_user,
        course.id,
        {
            "title": "Blueprint Draft Exam",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "passing_percent": 80,
        },
        session=db.session,
    )
    db.session.commit()

    # 3. Configure blueprint requiring 1 REMEMBER / SINGLE_CHOICE question
    configure_blueprint(
        instructor_user,
        assessment.id,
        {
            "name": "Quiz Blueprint",
            "rules": [
                {
                    "position": 1,
                    "difficulty": "REMEMBER",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 1,
                    "points_per_question": 10.0,
                }
            ],
        },
        session=db.session,
    )
    db.session.commit()

    # 4. Publish assessment within the draft (staged as target_status="PUBLISHED")
    staged_asm = publish_assessment(instructor_user, assessment.id, session=db.session)
    db.session.commit()
    assert staged_asm.status == "DRAFT"
    op = payload_for(draft_for(course))["operations"][f"assessment:{staged_asm.public_id}"]
    assert op["target_status"] == "PUBLISHED"

    # 5. Submit course changeset
    req = submit_course_changeset(instructor_user, course.id, {}, session=db.session)
    db.session.commit()
    assert req.status == "PENDING"

    # 6. Admin approves changeset
    approve_course_change_request(
        admin_user, req.id, review_reason="Approve exam with blueprint", session=db.session
    )
    db.session.commit()

    db.session.expire_all()
    live_asm = db.session.get(Assessment, staged_asm.id)
    assert live_asm.status == "PUBLISHED"
    assert live_asm.change_request_id is None
    # Pool was materialized and now has the question
    assert len(live_asm.question_pool) == 1
    assert live_asm.question_pool[0].question_id == question.id
