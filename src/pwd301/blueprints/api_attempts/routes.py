"""REST API route handlers for Assessment Attempts & Delivery per 08_ATTEMPT_API.md."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.api_attempts import api_attempt_bp
from pwd301.extensions import db
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import _normalize_dt
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    list_student_assessment_attempts,
    release_attempt_lease,
    renew_attempt_lease,
    start_assessment_attempt,
    takeover_attempt_lease,
)
from pwd301.services.authorization_service import require_authenticated_actor
from pwd301.services.jwt_auth_service import jwt_required


def _extract_lease_token() -> str | None:
    """Extract raw lease token from X-Attempt-Lease-Token header or JSON body."""
    token = request.headers.get("X-Attempt-Lease-Token")
    if token:
        return token.strip()
    if request.is_json:
        body = request.get_json(silent=True) or {}
        t = body.get("lease_token") or body.get("raw_lease_token")
        if t and isinstance(t, str):
            return t.strip()
    return None


@api_attempt_bp.route("/api/assessments/<assessment_id>/attempts", methods=["POST"])
@jwt_required
def start_assessment_attempt_route(assessment_id: str) -> tuple[Response, int] | Response:
    """Start an eligible assessment attempt for the authenticated student.

    POST /api/assessments/<assessment_id>/attempts
    """
    actor = require_authenticated_actor()

    attempt, raw_lease_token = start_assessment_attempt(
        student_actor=actor,
        assessment_id=assessment_id,
        session=db.session,
    )

    delivery = get_attempt_delivery(
        student_actor=actor,
        attempt_id=str(attempt.public_id),
        session=db.session,
    )

    response_payload = {
        "attempt_id": str(attempt.public_id),
        "assessment_id": delivery["assessment_id"],
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "deadline_at": attempt.deadline_at.isoformat() if attempt.deadline_at else None,
        "server_time": delivery["server_time"],
        "remaining_seconds": delivery["remaining_seconds"],
        "raw_lease_token": raw_lease_token,
        "lease_token": raw_lease_token,
        "lease_expires_at": (
            attempt.lease_expires_at.isoformat() if attempt.lease_expires_at else None
        ),
        "total_questions": delivery["total_questions"],
        "total_points": delivery["total_points"],
        "delivery": delivery,
        "questions": delivery["questions"],
    }
    return jsonify(response_payload), 201


@api_attempt_bp.route("/api/attempts/<attempt_id>", methods=["GET"])
@jwt_required
def get_attempt_delivery_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Retrieve frozen assessment attempt delivery payload for candidate presentation.

    GET /api/attempts/<attempt_id>
    """
    actor = require_authenticated_actor()

    delivery = get_attempt_delivery(
        student_actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )

    return jsonify(delivery), 200


@api_attempt_bp.route("/api/assessments/<assessment_id>/attempts", methods=["GET"])
@jwt_required
def list_student_assessment_attempts_route(assessment_id: str) -> tuple[Response, int] | Response:
    """List history of attempts taken by the authenticated student for an assessment.

    GET /api/assessments/<assessment_id>/attempts
    """
    actor = require_authenticated_actor()

    attempts = list_student_assessment_attempts(
        student_actor=actor,
        assessment_id=assessment_id,
        session=db.session,
    )
    return jsonify({"attempts": attempts, "total": len(attempts)}), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/lease/heartbeat", methods=["POST"])
@api_attempt_bp.route("/api/attempts/<attempt_id>/heartbeat", methods=["POST"])
@jwt_required
def renew_attempt_lease_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Renew active editing lease for the authenticated student.

    POST /api/attempts/<attempt_id>/lease/heartbeat
    POST /api/attempts/<attempt_id>/heartbeat
    """
    actor = require_authenticated_actor()
    raw_token = _extract_lease_token()
    result = renew_attempt_lease(
        actor=actor,
        attempt_id=attempt_id,
        raw_lease_token=raw_token or "",
        session=db.session,
    )
    return jsonify(result), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/lease/takeover", methods=["POST"])
@api_attempt_bp.route("/api/attempts/<attempt_id>/lease", methods=["POST"])
@jwt_required
def takeover_attempt_lease_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Take over editing lease from another tab or window.

    POST /api/attempts/<attempt_id>/lease/takeover
    POST /api/attempts/<attempt_id>/lease
    """
    actor = require_authenticated_actor()
    attempt, raw_token = takeover_attempt_lease(
        actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )

    remaining_seconds: int | None = None
    now = utc_now()
    norm_now = _normalize_dt(now)
    deadline = _normalize_dt(attempt.deadline_at)
    if deadline is not None and norm_now is not None:
        diff = (deadline - norm_now).total_seconds()
        remaining_seconds = max(0, int(diff))

    response_payload = {
        "attempt_id": str(attempt.public_id),
        "status": attempt.status,
        "lease_token": raw_token,
        "raw_lease_token": raw_token,
        "lease_expires_at": (
            attempt.lease_expires_at.isoformat() if attempt.lease_expires_at else None
        ),
        "remaining_seconds": remaining_seconds,
        "server_time": now.isoformat(),
    }
    return jsonify(response_payload), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/lease/release", methods=["POST"])
@jwt_required
def release_attempt_lease_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Release active editing lease voluntarily when closing tab.

    POST /api/attempts/<attempt_id>/lease/release
    """
    actor = require_authenticated_actor()
    raw_token = _extract_lease_token()
    release_attempt_lease(
        actor=actor,
        attempt_id=attempt_id,
        raw_lease_token=raw_token or "",
        session=db.session,
    )
    return jsonify({"message": "Lease released successfully."}), 200
