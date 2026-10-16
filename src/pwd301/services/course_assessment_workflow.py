"""Copy-on-write assessment authoring within the owning course changeset."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime
from decimal import Decimal
from functools import wraps

import sqlalchemy as sa

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentBlueprint,
    AssessmentBlueprintRule,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
    AssessmentSection,
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
    write_payload,
)
from pwd301.services.exceptions import AssessmentNotFoundError, ConflictError


def _columns(obj, omitted=()):
    return {
        column.key: getattr(obj, column.key)
        for column in sa.inspect(type(obj)).columns
        if column.key not in omitted
    }


def assessment_snapshot(assessment):
    return {
        "fields": _columns(assessment, ("row_version",)),
        "sections": [_columns(item) for item in assessment.sections],
        "assignments": [_columns(item) for item in assessment.question_assignments],
        "blueprints": [
            {"fields": _columns(item), "rules": [_columns(rule) for rule in item.rules]}
            for item in assessment.blueprints
        ],
        "pool": [_columns(item) for item in assessment.question_pool],
    }


def copy_assessment_graph(source, target, session):
    sections = {}
    rules = {}
    for item in source.sections:
        child = AssessmentSection(
            **_columns(item, ("id", "assessment_id")), assessment_id=target.id
        )
        session.add(child)
        session.flush()
        sections[item.id] = child.id
    for item in source.question_assignments:
        data = _columns(item, ("id", "assessment_id", "section_id"))
        session.add(
            AssessmentQuestionAssignment(
                **data, assessment_id=target.id, section_id=sections.get(item.section_id)
            )
        )
    for item in source.blueprints:
        blueprint_copy = AssessmentBlueprint(
            **_columns(item, ("id", "assessment_id")), assessment_id=target.id
        )
        session.add(blueprint_copy)
        session.flush()
        for rule in item.rules:
            data = _columns(rule, ("id", "blueprint_id", "section_id"))
            copy = AssessmentBlueprintRule(
                **data, blueprint_id=blueprint_copy.id, section_id=sections.get(rule.section_id)
            )
            session.add(copy)
            session.flush()
            rules[rule.id] = copy.id
    for item in source.question_pool:
        data = _columns(item, ("id", "assessment_id", "blueprint_rule_id"))
        session.add(
            AssessmentQuestionPool(
                **data, assessment_id=target.id, blueprint_rule_id=rules.get(item.blueprint_rule_id)
            )
        )
    session.flush()
    return sections


def assessment_working_revision(actor, original, session):
    if original.change_request_id is not None:
        return original
    record = working_changeset(actor, original.course_id, session)
    existing = (
        session.query(Assessment)
        .filter(
            Assessment.previous_assessment_id == original.id,
            Assessment.change_request_id == record.id,
        )
        .first()
    )
    if existing is not None:
        return existing
    if original.status == "DRAFT" and original.published_at is None:
        original.change_request_id = record.id
        session.flush()
        return original
    fields = _columns(
        original, ("id", "public_id", "row_version", "change_request_id", "previous_assessment_id")
    )
    fields.update(status="DRAFT", created_at=utc_now(), updated_at=utc_now(), deleted_at=None)
    staged = Assessment(
        **fields,
        public_id=uuid.uuid4(),
        change_request_id=record.id,
        previous_assessment_id=original.id,
    )
    session.add(staged)
    session.flush()
    sections = copy_assessment_graph(original, staged, session)
    proposed = payload_for(record)
    maps = proposed.get("assessment_section_maps") or {}
    maps[str(staged.id)] = {str(key): value for key, value in sections.items()}
    proposed["assessment_section_maps"] = maps
    write_payload(record, proposed, session)
    return staged


def commit_assessment_mutation(session):
    if applying_course_review(session) or session.info.get("course_assessment_mutation_depth"):
        session.flush()
    else:
        session.commit()


def course_assessment_mutation(function):
    """Keep existing validation and publication locks on a persistent draft graph."""
    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        actor = bound.arguments["actor"]
        session = bound.arguments.get("session")
        sess = session if session is not None else db.session
        from pwd301.services import assessment_service as service

        original = None
        if "assessment_id" in bound.arguments:
            original = service._resolve_assessment(
                bound.arguments["assessment_id"], session=sess, include_deleted=True
            )
            if original is None:
                raise AssessmentNotFoundError("Assessment not found.")
            course = ensure_course_authoring(actor, original.course_id, session=sess)
        else:
            course = ensure_course_authoring(actor, bound.arguments["course_id"], session=sess)
        if not should_stage(actor, course, sess):
            return function(*args, **kwargs)
        record = working_changeset(actor, course, sess)
        staged = assessment_working_revision(actor, original, sess) if original else None
        previous_depth = int(sess.info.get("course_assessment_mutation_depth") or 0)
        previous_operation = (
            (payload_for(record).get("operations") or {}).get(f"assessment:{staged.public_id}")
            if staged
            else None
        )
        desired_status = (previous_operation or {}).get("target_status") or (
            original.status if original else "DRAFT"
        )
        if staged is not None:
            bound.arguments["assessment_id"] = staged
            if "section_id" in bound.arguments:
                section = bound.arguments["section_id"]
                section_id = getattr(section, "id", section)
                section_map = (payload_for(record).get("assessment_section_maps") or {}).get(
                    str(staged.id), {}
                )
                bound.arguments["section_id"] = section_map.get(str(section_id), section)
            staged.status = desired_status
            if function.__name__ == "publish_assessment":
                staged.status = "DRAFT"
                if bound.arguments.get("expected_authoring_token"):
                    expected = bound.arguments["expected_authoring_token"]
                    # The displayed identity is checked before redirecting an original to its draft.
                    if (
                        original is None
                        or service.assessment_authoring_token(original, sess) != expected
                    ) and service.assessment_authoring_token(staged, sess) != expected:
                        raise ConflictError(
                            "Assessment authoring changed; refresh before publishing."
                        )
                    bound.arguments["expected_authoring_token"] = None
        bound.arguments["session"] = sess
        sess.info["course_assessment_mutation_depth"] = previous_depth + 1
        try:
            result = function(*bound.args, **bound.kwargs)
            if staged is None:
                staged = result
                staged.change_request_id = record.id
            desired_status = staged.status
            staged.status = "DRAFT"
            staged.deleted_at = None
            stage_course_operation(
                actor,
                course,
                {
                    "action": "ASSESSMENT_REVISION",
                    "assessment_id": str(staged.public_id),
                    "target_status": desired_status,
                },
                key=f"assessment:{staged.public_id}",
                session=sess,
            )
            sess.flush()
        except Exception:
            sess.rollback()
            raise
        finally:
            if previous_depth:
                sess.info["course_assessment_mutation_depth"] = previous_depth
            else:
                sess.info.pop("course_assessment_mutation_depth", None)
        if bound.arguments.get("commit", True) and previous_depth == 0:
            sess.commit()
        return result

    return wrapped


def effective_assessment(actor, assessment, session):
    if not (actor and (actor.id == assessment.course.owner_instructor_id or actor.is_admin)):
        return assessment
    record = active_changeset(assessment.course_id, session)
    if record is None or assessment.change_request_id is not None:
        return assessment
    return (
        session.query(Assessment)
        .filter_by(previous_assessment_id=assessment.id, change_request_id=record.id)
        .first()
        or assessment
    )


def _typed_fields(model, values, omitted=()):
    result = {}
    for key, value in values.items():
        if key in omitted:
            continue
        column = model.__table__.columns[key]
        if value is not None:
            if key.endswith("_at") or key == "restore_until":
                value = datetime.fromisoformat(value) if isinstance(value, str) else value
            elif isinstance(column.type, sa.Numeric):
                value = Decimal(str(value))
            elif column.type.__class__.__name__ == "GUID":
                value = uuid.UUID(str(value))
        result[key] = value
    return result


def _replace_graph(target, snapshot, session):
    blueprint_ids = [item.id for item in target.blueprints]
    session.query(AssessmentQuestionPool).filter_by(assessment_id=target.id).delete(
        synchronize_session="fetch"
    )
    session.query(AssessmentQuestionAssignment).filter_by(assessment_id=target.id).delete(
        synchronize_session="fetch"
    )
    if blueprint_ids:
        session.query(AssessmentBlueprintRule).filter(
            AssessmentBlueprintRule.blueprint_id.in_(blueprint_ids)
        ).delete(synchronize_session="fetch")
    session.query(AssessmentBlueprint).filter_by(assessment_id=target.id).delete(
        synchronize_session="fetch"
    )
    session.query(AssessmentSection).filter_by(assessment_id=target.id).delete(
        synchronize_session="fetch"
    )
    sections, rules = {}, {}
    for item in snapshot["sections"]:
        child = AssessmentSection(
            **_typed_fields(AssessmentSection, item, ("id", "assessment_id")),
            assessment_id=target.id,
        )
        session.add(child)
        session.flush()
        sections[item["id"]] = child.id
    for item in snapshot["assignments"]:
        data = _typed_fields(
            AssessmentQuestionAssignment, item, ("id", "assessment_id", "section_id")
        )
        session.add(
            AssessmentQuestionAssignment(
                **data, assessment_id=target.id, section_id=sections.get(item["section_id"])
            )
        )
    for item in snapshot["blueprints"]:
        blueprint_copy = AssessmentBlueprint(
            **_typed_fields(AssessmentBlueprint, item["fields"], ("id", "assessment_id")),
            assessment_id=target.id,
        )
        session.add(blueprint_copy)
        session.flush()
        for rule in item["rules"]:
            copy = AssessmentBlueprintRule(
                **_typed_fields(
                    AssessmentBlueprintRule, rule, ("id", "blueprint_id", "section_id")
                ),
                blueprint_id=blueprint_copy.id,
                section_id=sections.get(rule["section_id"]),
            )
            session.add(copy)
            session.flush()
            rules[rule["id"]] = copy.id
    for item in snapshot["pool"]:
        session.add(
            AssessmentQuestionPool(
                **_typed_fields(
                    AssessmentQuestionPool, item, ("id", "assessment_id", "blueprint_rule_id")
                ),
                assessment_id=target.id,
                blueprint_rule_id=rules.get(item["blueprint_rule_id"]),
            )
        )
    session.flush()
    session.expire(target, ["sections", "question_assignments", "blueprints", "question_pool"])


def _graph_signature(snapshot):
    """Compare reviewed structure independently of copy-on-write database identities."""
    sections = {item["id"]: item["position"] for item in snapshot["sections"]}
    rule_keys = {}
    blueprints = []
    for index, blueprint in enumerate(
        sorted(snapshot["blueprints"], key=lambda item: item["fields"]["id"])
    ):
        rules = []
        for rule in sorted(blueprint["rules"], key=lambda item: item["position"]):
            rule_keys[rule["id"]] = (index, rule["position"])
            values = _typed_fields(
                AssessmentBlueprintRule, rule, ("id", "blueprint_id", "section_id")
            )
            values["section"] = sections.get(rule["section_id"])
            rules.append(values)
        blueprints.append(
            {
                "fields": _typed_fields(
                    AssessmentBlueprint, blueprint["fields"], ("id", "assessment_id")
                ),
                "rules": rules,
            }
        )
    assignments = []
    for item in sorted(snapshot["assignments"], key=lambda row: row["position"]):
        values = _typed_fields(
            AssessmentQuestionAssignment, item, ("id", "assessment_id", "section_id")
        )
        values["section"] = sections.get(item["section_id"])
        assignments.append(values)
    pool = []
    for item in sorted(
        snapshot["pool"], key=lambda row: (row["position_hint"] or 0, row["question_id"])
    ):
        values = _typed_fields(
            AssessmentQuestionPool, item, ("id", "assessment_id", "blueprint_rule_id")
        )
        values["rule"] = rule_keys.get(item["blueprint_rule_id"])
        pool.append(values)
    return {
        "sections": [
            _typed_fields(AssessmentSection, item, ("id", "assessment_id"))
            for item in sorted(snapshot["sections"], key=lambda row: row["position"])
        ],
        "assignments": assignments,
        "blueprints": blueprints,
        "pool": pool,
    }


def apply_assessment_revision(actor, course_id, operation, session):
    from pwd301.models.attempt_regrade import AssessmentAttempt
    from pwd301.services import assessment_service as service
    from pwd301.services.exceptions import AssessmentLockedError, AssessmentValidationError

    snapshot = operation.get("snapshot")
    if not isinstance(snapshot, dict):
        raise AssessmentValidationError("Submitted assessment snapshot is missing.")
    fields = snapshot["fields"]
    draft = service._resolve_assessment(
        operation["assessment_id"], session=session, include_deleted=True
    )
    if draft is None or draft.course_id != course_id or draft.change_request_id is None:
        raise ConflictError("Submitted assessment draft is no longer available.")
    target = (
        session.get(Assessment, draft.previous_assessment_id)
        if draft.previous_assessment_id
        else draft
    )
    if target is None or target.course_id != course_id:
        raise AssessmentValidationError("Assessment revision must belong to this course.")
    target = service._lock_assessment_for_mutation(target, session)
    session.expire(target, ["sections", "question_assignments", "blueprints", "question_pool"])
    frozen = (
        target.first_attempt_started_at is not None
        or session.query(AssessmentAttempt.id).filter_by(assessment_id=target.id).first()
        is not None
    )
    if target.published_at is not None:
        for key in (
            "open_at",
            "close_at",
            "time_limit_minutes",
            "exam_layout",
            "monitoring_enabled",
            "request_fullscreen",
        ):
            proposed = _typed_fields(Assessment, {key: fields[key]})[key]
            current = getattr(target, key)
            if key.endswith("_at"):
                proposed = service._normalize_dt(proposed)
                current = service._normalize_dt(current)
            if proposed != current:
                raise AssessmentLockedError("Published assessment timing and policy remain locked.")
    if frozen and (
        _graph_signature(assessment_snapshot(target)) != _graph_signature(snapshot)
        or target.assessment_type != fields["assessment_type"]
        or target.random_question_count != fields["random_question_count"]
    ):
        raise AssessmentLockedError("Assessment structure is locked after a student starts.")
    writable = {
        "title",
        "description",
        "assessment_type",
        "open_at",
        "close_at",
        "time_limit_minutes",
        "attempt_limit",
        "scoring_policy",
        "passing_percent",
        "is_required_for_completion",
        "shuffle_questions",
        "shuffle_choices",
        "score_release_policy",
        "answer_visibility_policy",
        "exam_layout",
        "monitoring_enabled",
        "request_fullscreen",
        "random_question_count",
        "allow_student_view_results",
    }
    for key, value in _typed_fields(Assessment, fields).items():
        if key in writable:
            setattr(target, key, value)
    if not frozen:
        _replace_graph(target, snapshot, session)
    desired = operation.get("target_status") or "DRAFT"
    if desired == "PUBLISHED" and target.published_at is None:
        target.status = "DRAFT"
        service.publish_assessment(actor, target.id, session=session)
    else:
        target.status = desired
    if desired == "TRASH":
        target.deleted_at = utc_now()
        target.deleted_by_user_id = actor.id
    if desired == "CANCELLED":
        target.cancelled_at = utc_now()
        target.cancel_reason = fields.get("cancel_reason")
    target.change_request_id = None
    target.updated_at = utc_now()
    if target is not draft:
        draft.status = "ARCHIVED"
        draft.deleted_at = utc_now()
    session.flush()
