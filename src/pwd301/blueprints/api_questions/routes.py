"""REST API route handlers for Question Bank per 06_QUESTION_BANK_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_questions import api_question_bp
from pwd301.extensions import db
from pwd301.services.authorization_service import get_authenticated_actor
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.question_bank_service import (
    _serialize_question,
    _serialize_question_correction,
    _serialize_question_revision,
    create_question_revision,
    get_question_detail,
    get_question_revision_detail,
    list_question_corrections,
    list_question_revisions,
    restore_question,
    trash_question,
    update_question,
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


@api_question_bp.route("/<question_id>", methods=["PATCH"])
@jwt_required
def patch_question_route(question_id: str) -> tuple[Response, int] | Response:
    """Edit question or revision per 06_QUESTION_BANK_API.md.

    PATCH /api/questions/<question_id>
    """
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    question = update_question(actor, question_id, payload, session=db.session)
    db.session.commit()

    return jsonify(_serialize_question(question)), 200


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


@api_question_bp.route("/<question_id>/revisions", methods=["GET"])
@jwt_required
def list_question_revisions_route(question_id: str) -> tuple[Response, int] | Response:
    """List all revisions for a question in descending revision_no order.

    GET /api/questions/<question_id>/revisions
    """
    actor = get_authenticated_actor()
    assert actor is not None

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    items, total, p, pp, total_pages = list_question_revisions(
        actor, question_id, page=page, per_page=per_page, session=db.session
    )
    return jsonify(
        {
            "question_id": question_id,
            "items": items,
            "revisions": items,
            "total": total,
            "page": p,
            "per_page": pp,
            "total_pages": total_pages,
        }
    ), 200


@api_question_bp.route("/<question_id>/revisions", methods=["POST"])
@jwt_required
def create_question_revision_route(question_id: str) -> tuple[Response, int] | Response:
    """Create a new incremented question revision or correction incident.

    POST /api/questions/<question_id>/revisions
    """
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    revision, correction = create_question_revision(actor, question_id, payload, session=db.session)
    db.session.commit()

    resp: dict[str, Any] = {
        "revision": _serialize_question_revision(revision),
    }
    if correction is not None:
        resp["correction"] = _serialize_question_correction(correction)

    return jsonify(resp), 201


@api_question_bp.route("/<question_id>/revisions/<int:revision_no>", methods=["GET"])
@jwt_required
def get_question_revision_detail_route(
    question_id: str, revision_no: int
) -> tuple[Response, int] | Response:
    """Get full details of a specific question revision.

    GET /api/questions/<question_id>/revisions/<revision_no>
    """
    actor = get_authenticated_actor()
    assert actor is not None

    data = get_question_revision_detail(actor, question_id, revision_no, session=db.session)
    return jsonify(data), 200


@api_question_bp.route("/<question_id>/corrections", methods=["GET"])
@jwt_required
def list_question_corrections_route(question_id: str) -> tuple[Response, int] | Response:
    """List all question corrections for a question.

    GET /api/questions/<question_id>/corrections
    """
    actor = get_authenticated_actor()
    assert actor is not None

    corrections = list_question_corrections(actor, question_id, session=db.session)
    return jsonify(
        {
            "question_id": question_id,
            "items": corrections,
            "corrections": corrections,
            "total": len(corrections),
        }
    ), 200
