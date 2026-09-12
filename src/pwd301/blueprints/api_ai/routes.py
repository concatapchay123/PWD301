"""REST API route handlers for AI, Gemini integration, and Course Recommendations.

Complies with 10_AI_API.md and ADR-002 Zero Internal PK Leakage.
"""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_ai import api_ai_bp
from pwd301.extensions import db
from pwd301.services.ai_service import (
    approve_question_draft,
    create_conversation,
    draft_course_questions,
    get_conversation,
    get_course_drafts,
    purge_expired_ai_conversations,
    reject_question_draft,
    send_chat_message,
)
from pwd301.services.authorization_service import (
    instructor_required,
    require_authenticated_actor,
)
from pwd301.services.exceptions import AIValidationError, ForbiddenError
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.rag_service import (
    ask_course_rag,
    delete_knowledge_source,
    get_course_knowledge_sources,
    ingest_course_knowledge,
    ingest_lesson_content,
)
from pwd301.services.rate_limit_service import check_ai_rate_limit
from pwd301.services.recommendation_service import generate_course_recommendations


@api_ai_bp.route("/recommendations", methods=["GET"])
@jwt_required
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
@jwt_required
@instructor_required
def draft_questions_api() -> tuple[Response, int] | Response:
    """Draft structured assessment questions for an instructor course using Gemini."""
    actor = require_authenticated_actor()
    check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
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
@jwt_required
@instructor_required
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


@api_ai_bp.route("/questions/drafts/<draft_id>/approve", methods=["POST"])
@jwt_required
@instructor_required
def approve_draft_api(draft_id: str) -> tuple[Response, int] | Response:
    """Approve an AI question draft and persist to Question Bank (Revision 1)."""
    actor = require_authenticated_actor()
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict() or {}

    draft, question = approve_question_draft(
        actor=actor,
        draft_id=draft_id,
        edits=data,
        session=db.session,
    )
    return (
        jsonify(
            {
                "message": "Question draft successfully approved and added to Question Bank.",
                "draft": draft.to_dict(),
                "question_id": str(question.public_id),
            }
        ),
        200,
    )


@api_ai_bp.route("/questions/drafts/<draft_id>/reject", methods=["POST"])
@jwt_required
@instructor_required
def reject_draft_api(draft_id: str) -> tuple[Response, int] | Response:
    """Reject an AI question draft."""
    actor = require_authenticated_actor()
    draft = reject_question_draft(
        actor=actor,
        draft_id=draft_id,
        session=db.session,
    )
    return (
        jsonify(
            {
                "message": "Question draft rejected.",
                "draft": draft.to_dict(),
            }
        ),
        200,
    )


@api_ai_bp.route("/conversations", methods=["POST"])
@jwt_required
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
@jwt_required
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
@jwt_required
def send_message_api(conversation_id: str) -> tuple[Response, int] | Response:
    """Send a user chat message, reset 5-minute inactivity timer, and return assistant response."""
    actor = require_authenticated_actor()
    check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    content = data.get("message") or data.get("content")
    if not content:
        raise AIValidationError("Field 'message' or 'content' is required.")

    user_msg, asst_msg = send_chat_message(
        actor=actor,
        conversation_id=conversation_id,
        content=content,
        raise_out_of_scope=True,
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
@jwt_required
def unified_chat_api() -> tuple[Response, int] | Response:
    """LMS-scoped AI chat endpoint per 10_AI_API.md."""
    actor = require_authenticated_actor()
    check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
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
        raise_out_of_scope=True,
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
@jwt_required
def cleanup_conversations_api() -> tuple[Response, int] | Response:
    """Purge raw messages from conversations inactive > 5 minutes (admin or system maintenance)."""
    actor = require_authenticated_actor()
    if not actor.is_admin:
        raise ForbiddenError("Administrative privileges required to run conversation cleanup.")

    count = purge_expired_ai_conversations(session=db.session)
    return jsonify({"purged_conversations": count}), 200


# ---------------------------------------------------------------------------
# RAG Knowledge Lifecycle & Semantic Retrieval Endpoints (TASK-024)
# ---------------------------------------------------------------------------


@api_ai_bp.route("/courses/<course_id>/ingest", methods=["POST"])
@jwt_required
@instructor_required
def ingest_course_knowledge_api(course_id: str) -> tuple[Response, int] | Response:
    """Ingest/re-index all published lessons and clean file resources for a course."""
    actor = require_authenticated_actor()
    res = ingest_course_knowledge(actor=actor, course_id=course_id, session=db.session)
    return jsonify(res), 201


@api_ai_bp.route("/lessons/<lesson_id>/ingest", methods=["POST"])
@jwt_required
@instructor_required
def ingest_lesson_knowledge_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Ingest/re-index a specific lesson into RAG knowledge."""
    actor = require_authenticated_actor()
    doc, ver, chunks = ingest_lesson_content(actor=actor, lesson_id=lesson_id, session=db.session)
    return (
        jsonify(
            {
                "lesson_id": lesson_id,
                "source_id": str(doc.public_id),
                "version_no": ver.version_no,
                "chunks_count": len(chunks),
            }
        ),
        201,
    )


@api_ai_bp.route("/courses/<course_id>/query", methods=["POST"])
@jwt_required
def query_course_rag_api(course_id: str) -> tuple[Response, int] | Response:
    """Grounded semantic retrieval and question answering over course knowledge."""
    actor = require_authenticated_actor()
    check_ai_rate_limit(actor, role=actor.primary_role, client_ip=request.remote_addr)
    data: dict[str, Any] = request.get_json(silent=True) or request.form.to_dict()

    query = data.get("query") or data.get("question") or data.get("message")
    if not query:
        raise AIValidationError("Field 'query' is required.")

    try:
        top_k = int(data.get("top_k", 3))
        top_k = max(1, min(top_k, 10))
    except (ValueError, TypeError):
        top_k = 3

    result = ask_course_rag(
        actor=actor,
        course_id=course_id,
        query=query,
        top_k=top_k,
        session=db.session,
    )
    return jsonify(result), 200


@api_ai_bp.route("/courses/<course_id>/sources", methods=["GET"])
@jwt_required
def list_course_sources_api(course_id: str) -> tuple[Response, int] | Response:
    """List ingested knowledge sources for a course."""
    actor = require_authenticated_actor()
    include_chunks = request.args.get("include_chunks", "false").lower() == "true"
    sources = get_course_knowledge_sources(actor=actor, course_id=course_id, session=db.session)
    return (
        jsonify(
            {
                "sources": [s.to_dict(include_chunks=include_chunks) for s in sources],
                "count": len(sources),
            }
        ),
        200,
    )


@api_ai_bp.route("/sources/<source_id>", methods=["DELETE"])
@jwt_required
@instructor_required
def delete_source_api(source_id: str) -> tuple[Response, int] | Response:
    """Delete a knowledge source from the RAG index."""
    actor = require_authenticated_actor()
    delete_knowledge_source(actor=actor, source_id=source_id, session=db.session)
    return (
        jsonify({"message": "Knowledge source successfully deleted.", "source_id": source_id}),
        200,
    )
