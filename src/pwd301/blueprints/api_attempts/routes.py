"""REST API route handlers for Assessment Attempts & Delivery per 08_ATTEMPT_API.md."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.api_attempts import api_attempt_bp
from pwd301.extensions import db
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import _normalize_dt
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    get_attempt_grade_history,
    get_attempt_result_for_student,
    grade_essay_question,
    list_student_assessment_attempts,
    release_attempt_lease,
    renew_attempt_lease,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
    sync_offline_answers,
    takeover_attempt_lease,
)
from pwd301.services.authorization_service import require_authenticated_actor
from pwd301.services.exceptions import AttemptValidationError
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.regrade_worker import (
    get_regrade_job_detail,
    retry_regrade_job,
)


def _extract_lease_token() -> str | None:
    """Extract raw lease token from headers or JSON body."""
    token = request.headers.get("X-Attempt-Lease-Token") or request.headers.get("X-Lease-Token")
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
        "lease_epoch": attempt.lease_epoch or 1,
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
        "lease_epoch": attempt.lease_epoch or 1,
        "remaining_seconds": remaining_seconds,
        "server_time": now.isoformat(),
    }
    return jsonify(response_payload), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/answers/<attempt_question_id>", methods=["PUT"])
@jwt_required
def save_attempt_answer_route(
    attempt_id: str,
    attempt_question_id: str,
) -> tuple[Response, int] | Response:
    """Save an answer during an active attempt (autosave).

    PUT /api/attempts/<attempt_id>/answers/<attempt_question_id>
    """
    actor = require_authenticated_actor()
    raw_token = _extract_lease_token()
    payload = request.get_json(silent=True) or {}
    result = save_attempt_answer(
        actor=actor,
        attempt_id=attempt_id,
        attempt_question_id=attempt_question_id,
        payload=payload,
        raw_lease_token=raw_token,
        session=db.session,
    )
    return jsonify(result), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/answers/sync", methods=["POST"])
@jwt_required
def sync_offline_answers_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Synchronize a batch of offline answers accumulated while disconnected.

    POST /api/attempts/<attempt_id>/answers/sync
    """
    actor = require_authenticated_actor()
    raw_token = _extract_lease_token()
    body = request.get_json(silent=True)
    if isinstance(body, list):
        answers_batch = body
    elif isinstance(body, dict):
        answers_batch = body.get("answers") or body.get("items") or []
    else:
        answers_batch = []

    result = sync_offline_answers(
        actor=actor,
        attempt_id=attempt_id,
        answers_batch=answers_batch,
        raw_lease_token=raw_token,
        session=db.session,
    )
    return jsonify(result), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/submit", methods=["POST"])
@jwt_required
def submit_assessment_attempt_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Submit assessment attempt with idempotency protection.

    POST /api/attempts/<attempt_id>/submit
    """
    actor = require_authenticated_actor()
    raw_token = _extract_lease_token()

    idempotency_key = request.headers.get("X-Submission-Idempotency-Key") or request.headers.get(
        "X-Idempotency-Key"
    )
    if not idempotency_key and request.is_json:
        body = request.get_json(silent=True) or {}
        idempotency_key = body.get("submission_idempotency_key") or body.get("idempotency_key")

    result = submit_assessment_attempt(
        actor=actor,
        attempt_id=attempt_id,
        idempotency_key=idempotency_key,
        raw_lease_token=raw_token,
        session=db.session,
    )
    return jsonify(result), 200


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


@api_attempt_bp.route("/api/attempts/<attempt_id>/result", methods=["GET"])
@jwt_required
def get_attempt_result_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Retrieve attempt result for the candidate student or authorized reviewer.

    GET /api/attempts/<attempt_id>/result
    """
    actor = require_authenticated_actor()
    result = get_attempt_result_for_student(
        actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    return jsonify(result), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/grades/<attempt_question_id>", methods=["POST"])
@jwt_required
def grade_attempt_question_route(
    attempt_id: str,
    attempt_question_id: str,
) -> tuple[Response, int] | Response:
    """Manual essay evaluation / score override endpoint per 08_ATTEMPT_API.md.

    POST /api/attempts/<attempt_id>/grades/<attempt_question_id>
    """
    actor = require_authenticated_actor()
    body = request.get_json(silent=True) or request.form.to_dict() or {}
    points = body.get("awarded_points")
    if points is None:
        points = body.get("score")
    if points is None:
        raise AttemptValidationError("awarded_points (or score) is required.")

    reason = body.get("reason") or body.get("feedback")
    result = grade_essay_question(
        actor=actor,
        attempt_id=attempt_id,
        attempt_question_id=attempt_question_id,
        awarded_points=points,
        reason=reason,
        session=db.session,
    )
    return jsonify(result), 200


@api_attempt_bp.route("/api/attempts/<attempt_id>/grade-history", methods=["GET"])
@jwt_required
def get_attempt_grade_history_route(attempt_id: str) -> tuple[Response, int] | Response:
    """Retrieve full audit history of score evaluations for an attempt.

    GET /api/attempts/<attempt_id>/grade-history
    """
    actor = require_authenticated_actor()
    result = get_attempt_grade_history(actor=actor, attempt_id=attempt_id, session=db.session)
    return jsonify(result), 200


@api_attempt_bp.route("/api/regrade-jobs/<job_id>", methods=["GET"])
@jwt_required
def get_regrade_job_route(job_id: str) -> tuple[Response, int] | Response:
    """Read regrade job status and progress per 08_ATTEMPT_API.md.

    GET /api/regrade-jobs/<job_id>
    """
    actor = require_authenticated_actor()
    result = get_regrade_job_detail(actor=actor, job_id=job_id, session=db.session)
    return jsonify(result), 200


@api_attempt_bp.route("/api/regrade-jobs/<job_id>/retry", methods=["POST"])
@jwt_required
def retry_regrade_job_route(job_id: str) -> tuple[Response, int] | Response:
    """Retry failed items in a regrade job.

    POST /api/regrade-jobs/<job_id>/retry
    """
    actor = require_authenticated_actor()
    result = retry_regrade_job(job_id=job_id, actor=actor, session=db.session)
    return jsonify(result), 200
