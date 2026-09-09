"""REST API route handlers for Assessments per 07_ASSESSMENT_API.md."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.api_assessments import api_assessment_bp
from pwd301.extensions import db
from pwd301.services.assessment_service import (
    _serialize_assessment,
    _serialize_assignment,
    _serialize_blueprint,
    _serialize_section,
    assign_question,
    cancel_assessment,
    configure_blueprint,
    create_assessment,
    create_section,
    delete_section,
    get_assessment_detail,
    materialize_blueprint_pool,
    publish_assessment,
    release_assessment_scores,
    remove_question_assignment,
    restore_assessment,
    trash_assessment,
    trigger_assessment_regrade,
    update_assessment,
)
from pwd301.services.authorization_service import require_authenticated_actor
from pwd301.services.exceptions import AssessmentValidationError
from pwd301.services.jwt_auth_service import jwt_required


@api_assessment_bp.route("", methods=["POST"], strict_slashes=False)
@jwt_required
def create_assessment_route() -> tuple[Response, int] | Response:
    """Create a new Assessment (DRAFT status).

    POST /api/assessments
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or {}
    course_id = payload.get("course_id")
    if not course_id:
        raise AssessmentValidationError("course_id is required to create an assessment.")

    assessment = create_assessment(actor, course_id, payload, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 201


@api_assessment_bp.route("/<assessment_id>", methods=["GET"])
@jwt_required
def get_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Retrieve detailed assessment configuration.

    GET /api/assessments/<assessment_id>
    """
    actor = require_authenticated_actor()

    data = get_assessment_detail(actor, assessment_id, session=db.session)
    return jsonify(data), 200


@api_assessment_bp.route("/<assessment_id>", methods=["PATCH"])
@jwt_required
def patch_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Update assessment configuration (fails if timing/structure is locked).

    PATCH /api/assessments/<assessment_id>
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or {}
    assessment = update_assessment(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 200


@api_assessment_bp.route("/<assessment_id>/publish", methods=["POST"])
@jwt_required
def publish_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Publish assessment (DRAFT -> PUBLISHED). State-idempotent.

    POST /api/assessments/<assessment_id>/publish
    """
    actor = require_authenticated_actor()

    assessment = publish_assessment(actor, assessment_id, session=db.session)

    return jsonify(_serialize_assessment(assessment, full=False)), 200


@api_assessment_bp.route("/<assessment_id>/cancel", methods=["POST"])
@jwt_required
def cancel_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Cancel a published assessment.

    POST /api/assessments/<assessment_id>/cancel
    """
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or {}
    reason = body.get("reason")

    assessment = cancel_assessment(actor, assessment_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Assessment cancelled.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


@api_assessment_bp.route("/<assessment_id>/trash", methods=["POST"])
@jwt_required
def trash_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Move assessment to TRASH (soft-delete with 30-day restore window).

    POST /api/assessments/<assessment_id>/trash
    """
    actor = require_authenticated_actor()

    body = request.get_json(silent=True) or {}
    reason = body.get("reason")

    assessment = trash_assessment(actor, assessment_id, reason=reason, session=db.session)

    return jsonify(
        {
            "message": "Assessment moved to trash.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


@api_assessment_bp.route("/<assessment_id>/restore", methods=["POST"])
@jwt_required
def restore_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Restore assessment from TRASH back to DRAFT within 30 days.

    POST /api/assessments/<assessment_id>/restore
    """
    actor = require_authenticated_actor()

    assessment = restore_assessment(actor, assessment_id, session=db.session)

    return jsonify(
        {
            "message": "Assessment restored from trash.",
            "assessment": _serialize_assessment(assessment, full=False),
        }
    ), 200


@api_assessment_bp.route("/<assessment_id>/sections", methods=["POST"])
@jwt_required
def create_section_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Create a new section in the assessment.

    POST /api/assessments/<assessment_id>/sections
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or {}
    section = create_section(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_section(section)), 201


@api_assessment_bp.route("/<assessment_id>/sections/<section_id>", methods=["DELETE"])
@jwt_required
def delete_section_route(assessment_id: str, section_id: str) -> tuple[Response, int] | Response:
    """Delete a section from the assessment.

    DELETE /api/assessments/<assessment_id>/sections/<section_id>
    """
    actor = require_authenticated_actor()

    delete_section(actor, assessment_id, section_id, session=db.session)

    return jsonify({"message": "Section deleted successfully."}), 200


@api_assessment_bp.route("/<assessment_id>/questions", methods=["POST"])
@jwt_required
def assign_question_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Assign a fixed question to the assessment.

    POST /api/assessments/<assessment_id>/questions
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or {}
    assignment = assign_question(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_assignment(assignment)), 201


@api_assessment_bp.route("/<assessment_id>/questions/<question_id>", methods=["DELETE"])
@jwt_required
def remove_question_route(assessment_id: str, question_id: str) -> tuple[Response, int] | Response:
    """Remove a fixed question assignment from the assessment.

    DELETE /api/assessments/<assessment_id>/questions/<question_id>
    """
    actor = require_authenticated_actor()

    remove_question_assignment(actor, assessment_id, question_id, session=db.session)

    return jsonify({"message": "Question unassigned successfully."}), 200


@api_assessment_bp.route("/<assessment_id>/blueprint", methods=["POST"])
@jwt_required
def configure_blueprint_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Configure assessment blueprint rules.

    POST /api/assessments/<assessment_id>/blueprint
    """
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or {}
    blueprint = configure_blueprint(actor, assessment_id, payload, session=db.session)

    return jsonify(_serialize_blueprint(blueprint)), 200


@api_assessment_bp.route("/<assessment_id>/blueprint/materialize", methods=["POST"])
@jwt_required
def materialize_blueprint_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Materialize candidate question pool from blueprint rules (Algorithm 05).

    POST /api/assessments/<assessment_id>/blueprint/materialize
    """
    actor = require_authenticated_actor()

    pool = materialize_blueprint_pool(actor, assessment_id, session=db.session)

    return jsonify(
        {
            "message": "Candidate pool materialized successfully.",
            "pool_count": len(pool),
        }
    ), 200


@api_assessment_bp.route("/<assessment_id>/release-scores", methods=["POST"])
@jwt_required
def release_scores_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Release scores for an assessment (INSTRUCTOR_RELEASE policy).

    POST /api/assessments/<assessment_id>/release-scores
    """
    actor = require_authenticated_actor()
    result = release_assessment_scores(actor, assessment_id, session=db.session)
    return jsonify(result), 200


@api_assessment_bp.route("/<assessment_id>/regrade", methods=["POST"])
@jwt_required
def regrade_assessment_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Trigger assessment regrading per 07_ASSESSMENT_API.md and Algorithm 11.

    POST /api/assessments/<assessment_id>/regrade
    """
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    result = trigger_assessment_regrade(actor, assessment_id, payload=payload, session=db.session)
    return jsonify(result), 200
