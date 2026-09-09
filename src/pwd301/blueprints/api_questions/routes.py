"""REST API route handlers for Question Bank per 06_QUESTION_BANK_API.md."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.api_questions import api_question_bp
from pwd301.extensions import db
from pwd301.services.authorization_service import get_authenticated_actor
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.question_bank_service import (
    _serialize_question,
    get_question_detail,
    restore_question,
    trash_question,
)


@api_question_bp.route("/<question_id>", methods=["GET"])
@jwt_required
def get_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Retrieve question details and current revision.

    GET /api/questions/<question_id>
    """
    actor = get_authenticated_actor()
    assert actor is not None

    data = get_question_detail(actor, question_id, session=db.session)
    return jsonify(data), 200


@api_question_bp.route("/<question_id>/trash", methods=["POST"])
@jwt_required
def trash_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a question to TRASH with 30-day restore window.

    POST /api/questions/<question_id>/trash
    """
    actor = get_authenticated_actor()
    assert actor is not None

    body = request.get_json(silent=True) or {}
    reason = body.get("reason")

    question = trash_question(actor, question_id, reason=reason, session=db.session)
    db.session.commit()

    return jsonify(
        {
            "message": "Question moved to trash.",
            "question": _serialize_question(question),
        }
    ), 200


@api_question_bp.route("/<question_id>", methods=["DELETE"])
@jwt_required
def delete_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Soft-delete question (DELETE alias per 06_QUESTION_BANK_API.md).

    DELETE /api/questions/<question_id>
    """
    actor = get_authenticated_actor()
    assert actor is not None

    body = request.get_json(silent=True) or {}
    reason = body.get("reason")

    question = trash_question(actor, question_id, reason=reason, session=db.session)
    db.session.commit()

    return jsonify(
        {
            "message": "Question moved to trash.",
            "question": _serialize_question(question),
        }
    ), 200


@api_question_bp.route("/<question_id>/restore", methods=["POST"])
@jwt_required
def restore_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Restore a question from TRASH back to ACTIVE.

    POST /api/questions/<question_id>/restore
    """
    actor = get_authenticated_actor()
    assert actor is not None

    body = request.get_json(silent=True) or {}
    reason = body.get("reason")

    question = restore_question(actor, question_id, reason=reason, session=db.session)
    db.session.commit()

    return jsonify(
        {
            "message": "Question restored from trash.",
            "question": _serialize_question(question),
        }
    ), 200
