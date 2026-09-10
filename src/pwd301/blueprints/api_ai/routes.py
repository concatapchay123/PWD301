"""REST API route handlers for AI, Gemini integration, and Course Recommendations.

Complies with 10_AI_API.md and ADR-002 Zero Internal PK Leakage.
"""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_ai import api_ai_bp
from pwd301.extensions import db
from pwd301.services.ai_service import (
    create_conversation,
    draft_course_questions,
    get_conversation,
    get_course_drafts,
    purge_expired_ai_conversations,
    send_chat_message,
)
from pwd301.services.authorization_service import (
    require_authenticated_actor,
)
from pwd301.services.exceptions import AIValidationError, ForbiddenError
from pwd301.services.recommendation_service import generate_course_recommendations


@api_ai_bp.route("/recommendations", methods=["GET"])
def get_recommendations_api() -> tuple[Response, int] | Response:
    """Retrieve personalized course recommendations adhering to Algorithm 14."""
    actor = require_authenticated_actor()

    try:
        limit = int(request.args.get("limit", 5))
        limit = max(1, min(limit, 20))
    except (ValueError, TypeError):
        limit = 5

    recs = generate_course_recommendations(actor=actor, limit=limit, session=db.session)
    return jsonify({"recommendations": recs, "count": len(recs)}), 200


@api_ai_bp.route("/questions/draft", methods=["POST"])
@api_ai_bp.route("/questions/generate", methods=["POST"])
def draft_questions_api() -> tuple[Response, int] | Response:
    """Draft structured assessment questions for an instructor course using Gemini."""
    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    course_id = data.get("course_id")
    if not course_id:
        raise AIValidationError("Field 'course_id' is required.")

    topic = data.get("topic") or data.get("learning_objective")
    if not topic:
        raise AIValidationError("Field 'topic' or 'learning_objective' is required.")

    difficulty = data.get("difficulty", "UNDERSTAND")

    q_types = data.get("question_types")
    if q_types is None and "question_type" in data:
        q_types = [data["question_type"]]
    elif isinstance(q_types, str):
        q_types = [t.strip() for t in q_types.split(",")]

    try:
        count = int(data.get("count", 3))
    except (ValueError, TypeError):
        count = 3

    lesson_id = data.get("lesson_id")

    drafts = draft_course_questions(
        actor=actor,
        course_id=course_id,
        topic=topic,
        difficulty=difficulty,
        question_types=q_types,
        count=count,
        lesson_id=lesson_id,
        session=db.session,
    )

    return (
        jsonify(
            {
                "drafts": [d.to_dict() for d in drafts],
                "count": len(drafts),
            }
        ),
        201,
    )


@api_ai_bp.route("/questions/drafts", methods=["GET"])
def list_drafts_api() -> tuple[Response, int] | Response:
    """List generated question drafts for a course."""
    actor = require_authenticated_actor()
    course_id = request.args.get("course_id")
    if not course_id:
        raise AIValidationError("Query parameter 'course_id' is required.")

    review_state = request.args.get("review_state")
    drafts = get_course_drafts(
        actor=actor,
        course_id=course_id,
        review_state=review_state,
        session=db.session,
    )
    return jsonify({"drafts": [d.to_dict() for d in drafts], "count": len(drafts)}), 200


@api_ai_bp.route("/conversations", methods=["POST"])
def create_conversation_api() -> tuple[Response, int] | Response:
    """Initialize a new AI conversation session with 5-minute inactivity deadline."""
    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    context_type = data.get("context_type", "GLOBAL")
    course_id = data.get("course_id")
    lesson_id = data.get("lesson_id")

    conv = create_conversation(
        actor=actor,
        context_type=context_type,
        course_id=course_id,
        lesson_id=lesson_id,
        session=db.session,
    )
    return jsonify(conv.to_dict(include_messages=True)), 201


@api_ai_bp.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation_api(conversation_id: str) -> tuple[Response, int] | Response:
    """Retrieve details and messages of an active AI conversation session."""
    actor = require_authenticated_actor()
    conv = get_conversation(
        actor=actor,
        conversation_id=conversation_id,
        session=db.session,
    )
    return jsonify(conv.to_dict(include_messages=True)), 200


@api_ai_bp.route("/conversations/<conversation_id>/messages", methods=["POST"])
def send_message_api(conversation_id: str) -> tuple[Response, int] | Response:
    """Send a user chat message, reset 5-minute inactivity timer, and return assistant response."""
    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    content = data.get("message") or data.get("content")
    if not content:
        raise AIValidationError("Field 'message' or 'content' is required.")

    user_msg, asst_msg = send_chat_message(
        actor=actor,
        conversation_id=conversation_id,
        content=content,
        session=db.session,
    )
    conv = get_conversation(actor=actor, conversation_id=conversation_id, session=db.session)

    return (
        jsonify(
            {
                "user_message": user_msg.to_dict(),
                "assistant_message": asst_msg.to_dict(),
                "conversation": conv.to_dict(include_messages=False),
            }
        ),
        200,
    )


@api_ai_bp.route("/chat", methods=["POST"])
def unified_chat_api() -> tuple[Response, int] | Response:
    """LMS-scoped AI chat endpoint per 10_AI_API.md."""
    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    content = data.get("message") or data.get("content")
    if not content:
        raise AIValidationError("Field 'message' or 'content' is required.")

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        context_type = data.get("context_type", "GLOBAL")
        course_id = data.get("course_id")
        conv = create_conversation(
            actor=actor,
            context_type=context_type,
            course_id=course_id,
            session=db.session,
        )
        conversation_id = str(conv.public_id)

    user_msg, asst_msg = send_chat_message(
        actor=actor,
        conversation_id=conversation_id,
        content=content,
        session=db.session,
    )
    conv = get_conversation(actor=actor, conversation_id=conversation_id, session=db.session)

    return (
        jsonify(
            {
                "conversation_id": str(conv.public_id),
                "user_message": user_msg.to_dict(),
                "assistant_message": asst_msg.to_dict(),
                "expires_at": conv.expires_at.isoformat() if conv.expires_at else None,
            }
        ),
        200,
    )


@api_ai_bp.route("/conversations/cleanup", methods=["POST"])
def cleanup_conversations_api() -> tuple[Response, int] | Response:
    """Purge raw messages from conversations inactive > 5 minutes (admin or system maintenance)."""
    actor = require_authenticated_actor()
    if not actor.is_admin:
        raise ForbiddenError("Administrative privileges required to run conversation cleanup.")

    count = purge_expired_ai_conversations(session=db.session)
    return jsonify({"purged_conversations": count}), 200
