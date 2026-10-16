"""Question drafts retain approved identities and revisions until one course review applies."""

from __future__ import annotations

import hashlib
import inspect
import json
import uuid
from functools import wraps

import sqlalchemy as sa

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
)
from pwd301.models.course import CourseChangeRequest
from pwd301.models.file_import import QuestionRevisionResource
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.course_workflow_service import (
    active_changeset,
    applying_course_review,
    ensure_course_authoring,
    payload_for,
    should_stage,
    stage_course_operation,
    working_changeset,
)
from pwd301.services.exceptions import ConflictError, QuestionNotFoundError


def _columns(row, omitted=()):
    return {
        column.key: getattr(row, column.key)
        for column in sa.inspect(type(row)).columns
        if column.key not in omitted
    }


def question_snapshot(question):
    revision = question.current_revision
    return {
        "question_type": revision.question_type,
        "content": revision.content,
        "explanation": revision.explanation,
        "short_answer_match_mode": revision.short_answer_match_mode,
        "difficulty": question.difficulty,
        "learning_objective": question.learning_objective,
        "lesson_id": str(question.lesson.public_id) if question.lesson else None,
        "change_type": revision.change_type,
        "reason": revision.change_reason,
        "choices": [
            {
                "choice_key": str(choice.choice_key),
                "content": choice.content,
                "is_correct": choice.is_correct,
                "position": choice.position,
                "is_fixed_position": choice.is_fixed_position,
            }
            for choice in sorted(revision.choices, key=lambda item: item.position)
        ],
        "accepted_answers": [
            {"answer_text": answer.answer_text, "position": answer.position}
            for answer in sorted(revision.accepted_answers, key=lambda item: item.position)
        ],
        "resources": [
            {
                "asset_id": str(resource.file_asset.public_id),
                "position": resource.position,
                "resource_role": resource.resource_role,
            }
            for resource in sorted(revision.resources, key=lambda item: item.position)
        ],
    }


def _semantic_snapshot(question):
    snapshot = question_snapshot(question)
    snapshot.pop("reason")
    snapshot.pop("change_type")
    return snapshot


def question_version(question):
    content = [
        _semantic_snapshot(question),
        question.status,
        question.current_revision.id,
        question.current_revision.revision_no,
    ]
    return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()


def _working_question(actor, original, record, session):
    if original.change_request_id == record.id:
        return original
    candidate = (
        session.query(Question)
        .filter_by(
            previous_question_id=original.id,
            change_request_id=record.id,
        )
        .first()
    )
    if candidate:
        return candidate
    fields = _columns(
        original, ("id", "public_id", "row_version", "change_request_id", "previous_question_id")
    )
    fields.update(status="DRAFT", deleted_at=None, deleted_by_user_id=None, restore_until=None)
    candidate = Question(
        **fields,
        public_id=uuid.uuid4(),
        change_request_id=record.id,
        previous_question_id=original.id,
    )
    session.add(candidate)
    session.flush()
    source = original.current_revision
    revision_fields = _columns(
        source,
        (
            "id",
            "question_id",
            "is_current",
            "approved_by_user_id",
            "approved_at",
            "was_student_exposed",
            "was_used_for_grading",
        ),
    )
    revision = QuestionRevision(
        **revision_fields,
        question_id=candidate.id,
        is_current=False,
        was_student_exposed=False,
        was_used_for_grading=False,
    )
    session.add(revision)
    session.flush()
    for cls, rows in (
        (QuestionRevisionChoice, source.choices),
        (QuestionRevisionAcceptedAnswer, source.accepted_answers),
        (QuestionRevisionResource, source.resources),
    ):
        for row in rows:
            session.add(
                cls(
                    **_columns(row, ("id", "question_revision_id")),
                    question_revision_id=revision.id,
                )
            )
    for provenance in session.query(QuestionProvenance).filter_by(question_id=original.id).all():
        session.add(
            QuestionProvenance(
                **_columns(provenance, ("id", "question_id", "question_revision_id")),
                question_id=candidate.id,
                question_revision_id=revision.id,
            )
        )
    session.flush()
    revision.is_current = True
    session.flush()
    session.expire(candidate, ["current_revision"])
    return candidate


def commit_question_mutation(session):
    if applying_course_review(session) or session.info.get("course_question_mutation_depth"):
        session.flush()
    else:
        session.commit()


def course_question_mutation(function):
    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        actor = bound.arguments["actor"]
        session = bound.arguments.get("session")
        sess = session if session is not None else db.session
        if sess.info.get("course_question_mutation_depth"):
            return function(*args, **kwargs)
        from pwd301.services.authorization_service import require_question_manager

        original = None
        if "question_id" in bound.arguments:
            original = require_question_manager(actor, bound.arguments["question_id"], session=sess)
            course = ensure_course_authoring(actor, original.course_id, session=sess)
        else:
            course = ensure_course_authoring(actor, bound.arguments["course_id"], session=sess)
        if not should_stage(actor, course, sess):
            return function(*args, **kwargs)
        record = working_changeset(actor, course, sess)
        baseline = (
            sess.get(Question, original.previous_question_id)
            if original and original.previous_question_id
            else original
        )
        key = f"question:{baseline.public_id}" if baseline else None
        previous = (payload_for(record).get("operations") or {}).get(key, {})
        candidate = _working_question(actor, original, record, sess) if original else None
        baseline_version = previous.get("baseline_version") or (
            question_version(baseline) if baseline and baseline.change_request_id is None else None
        )
        if candidate:
            candidate.status = previous.get("target_status") or (baseline or candidate).status
            if candidate.status == "DRAFT" and candidate.previous_question_id:
                candidate.status = "ACTIVE"
            bound.arguments["question_id"] = candidate
        requested_commit = bound.arguments.get("commit", True)
        if "commit" in bound.arguments:
            bound.arguments["commit"] = False
        bound.arguments["session"] = sess
        sess.info["course_question_mutation_depth"] = 1
        try:
            result = function(*bound.args, **bound.kwargs)
            if candidate is None:
                candidate = result
                candidate.change_request_id = record.id
            sess.expire(candidate, ["current_revision", "lesson"])
            target_status = candidate.status
            operation = {
                "action": "QUESTION_REVISION",
                "question_id": str(candidate.public_id),
                "original_question_id": str(baseline.public_id)
                if baseline and baseline.id != candidate.id
                else None,
                "target_status": target_status,
                "snapshot": question_snapshot(candidate),
                "baseline_version": baseline_version,
                "force_revision": bool(
                    previous.get("force_revision")
                    or function.__name__ == "create_question_revision"
                ),
            }
            candidate.status = "DRAFT"
            candidate.deleted_at = None
            candidate.restore_until = None
            stage_course_operation(
                actor, course, operation, key=key or f"question:{candidate.public_id}", session=sess
            )
            sess.flush()
            if requested_commit:
                sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.info.pop("course_question_mutation_depth", None)
        return result

    return wrapped


def effective_question(actor, question, session):
    if question.change_request_id is not None:
        return question
    record = active_changeset(question.course_id, session)
    if (
        record is None
        or not actor
        or not (actor.is_admin or actor.id == question.course.owner_instructor_id)
    ):
        return question
    return (
        session.query(Question)
        .filter_by(previous_question_id=question.id, change_request_id=record.id)
        .first()
        or question
    )


def effective_question_query(query, course_id, session):
    record = active_changeset(course_id, session)
    if record is None:
        return query.filter(Question.change_request_id.is_(None))
    replacements = session.query(Question.previous_question_id).filter(
        Question.change_request_id == record.id,
        Question.previous_question_id.isnot(None),
    )
    return query.filter(
        sa.or_(
            Question.change_request_id == record.id,
            sa.and_(Question.change_request_id.is_(None), Question.id.notin_(replacements)),
        )
    )


def question_display_status(question, session):
    if question.change_request_id is None:
        return question.status
    record = session.get(CourseChangeRequest, question.change_request_id)
    if record is None or record.status not in {"DRAFT", "PENDING"}:
        return question.status
    for operation in (payload_for(record).get("operations") or {}).values():
        if operation.get("action") == "QUESTION_REVISION" and operation.get("question_id") == str(
            question.public_id
        ):
            return operation["target_status"]
    return question.status


def question_status_expression(course_id, session):
    record = active_changeset(course_id, session)
    if record is None:
        return Question.status
    proposed = {
        operation["question_id"]: operation["target_status"]
        for operation in (payload_for(record).get("operations") or {}).values()
        if operation.get("action") == "QUESTION_REVISION"
    }
    overrides = {
        row.id: proposed[str(row.public_id)]
        for row in session.query(Question.id, Question.public_id).filter_by(
            change_request_id=record.id
        )
        if str(row.public_id) in proposed
    }
    return (
        sa.case(overrides, value=Question.id, else_=Question.status)
        if overrides
        else Question.status
    )


def apply_course_question_operation(actor, course_id, operation, session):
    """Apply reviewed JSON, never a mutable draft's latest content; retain original identities."""
    from pwd301.services import question_bank_service as service
    from pwd301.services.authorization_service import _resolve_question
    from pwd301.services.file_service import get_file_for_download

    candidate = _resolve_question(operation["question_id"], session=session)
    if candidate is None or candidate.course_id != course_id:
        raise QuestionNotFoundError("The submitted question does not belong to this course.")
    snapshot = dict(operation["snapshot"])
    for resource in snapshot.get("resources") or []:
        get_file_for_download(actor, resource["asset_id"], session=session)
    original_id = operation.get("original_question_id")
    original = _resolve_question(original_id, session=session) if original_id else None
    if original_id and (original is None or original.course_id != course_id):
        raise QuestionNotFoundError("The original question does not belong to this course.")
    target = original or candidate
    if original and question_version(original) != operation.get("baseline_version"):
        raise ConflictError("Câu hỏi gốc đã thay đổi. Hãy rút bản gửi và kiểm tra lại nội dung.")
    target_status = operation["target_status"]
    if target.status == "TRASH" and target_status not in {"TRASH", "RETIRED"}:
        service.restore_question(actor, target.id, session=session)
    unchanged_terminal = target.status in {"TRASH", "RETIRED"} and target_status == target.status
    metadata = {key: snapshot[key] for key in ("difficulty", "learning_objective", "lesson_id")}
    if not unchanged_terminal:
        service.update_question(actor, target.id, metadata, session=session, commit=False)
    if original and not unchanged_terminal:
        before = _semantic_snapshot(original)
        proposed = {
            key: value for key, value in snapshot.items() if key not in {"reason", "change_type"}
        }
        if before != proposed or operation.get("force_revision"):
            revision_payload = dict(snapshot)
            if revision_payload.get("change_type") == "INITIAL":
                revision_payload["change_type"] = (
                    "CONTENT_CHANGE"
                    if service.is_question_in_use(original, session=session)
                    else "EDIT"
                )
            service.create_question_revision(
                actor, original.id, revision_payload, session=session, commit=False
            )
    elif not original:
        candidate.status = "DRAFT"
        service.update_question(actor, candidate.id, snapshot, session=session, commit=False)
    if target_status in {"TRASH", "RETIRED"}:
        service.trash_question(actor, target.id, reason=snapshot.get("reason"), session=session)
    else:
        target.status = target_status
        target.deleted_at = None
        target.change_request_id = None
    if original:
        candidate.status = "RETIRED"
        candidate.deleted_at = utc_now()
        staged_assessments = session.query(Assessment.id).filter(
            Assessment.change_request_id == candidate.change_request_id
        )
        session.query(AssessmentQuestionAssignment).filter(
            AssessmentQuestionAssignment.assessment_id.in_(staged_assessments),
            AssessmentQuestionAssignment.question_id == candidate.id,
        ).update({"question_id": original.id}, synchronize_session="fetch")
        session.query(AssessmentQuestionPool).filter(
            AssessmentQuestionPool.assessment_id.in_(staged_assessments),
            AssessmentQuestionPool.question_id == candidate.id,
        ).update({"question_id": original.id}, synchronize_session="fetch")
    session.flush()
    session.expire(target, ["current_revision"])
    return {candidate.id: target.id}
