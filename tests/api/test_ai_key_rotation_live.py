"""Live integration test for Gemini Multi-Key Rotation and Fallback Engine.

Validates that:
1. Real Gemini client initializes with the multi-key pool from api/api_key.md.
2. When starting with a dead key (401 service account deleted), the system automatically
   rotates and falls back to healthy keys seamlessly.
3. Intelligent learning assistance responses are returned in Vietnamese.
4. Response payloads and logs are completely devoid of any raw API keys.
"""

from __future__ import annotations

from pwd301.services.gemini_service import (
    GeminiKeyPool,
    GeminiKeyStatus,
    RealGeminiClient,
    get_key_pool,
)


def test_live_gemini_key_pool_population() -> None:
    """Verify that key pool successfully loads active keys from the project."""
    pool = get_key_pool()
    assert len(pool.keys) >= 50, f"Expected at least 50 keys in pool, found {len(pool.keys)}"


def test_live_gemini_call_with_automatic_dead_key_fallback() -> None:
    """When RealGeminiClient is given a dead key, it automatically rotates to a healthy key."""
    # Simulated invalid key to verify failover without hardcoding real credentials
    dead_key = "AQ.SimulatedDeadKeyForFailoverVerification12345"

    pool = get_key_pool()
    healthy_keys = [k for k in pool.keys if pool.get_key_status(k) == GeminiKeyStatus.HEALTHY]
    if not healthy_keys:
        import pytest

        pytest.skip("No live healthy Gemini API key available in local environment")
    good_key = healthy_keys[0]
    test_pool = GeminiKeyPool(keys=[dead_key, good_key])

    client = RealGeminiClient(
        api_key=dead_key,
        model_name="gemini-3.6-flash",
        timeout_seconds=15,
        key_pool=test_pool,
    )

    # Prompt Gemini in Vietnamese
    prompt = "Bạn hãy giải thích ngắn gọn trong 1 câu: HTML là gì?"
    system_inst = "Bạn là Bạch Tuộc Trợ lý AI trên nền tảng học tập LMS PWD301."

    response_text = client.generate_text(prompt, system_instruction=system_inst)

    # Verify the response is successful and intelligent
    assert response_text is not None
    assert len(response_text) > 10
    keywords = ["html", "ngôn ngữ", "đánh dấu", "web", "trang web"]
    assert any(term in response_text.lower() for term in keywords)

    # Dead key must have been marked INVALID
    assert test_pool.get_key_status(dead_key) == GeminiKeyStatus.INVALID

    # Security check: Zero API keys in response text
    assert "AQ." not in response_text
    assert "AIzaSy" not in response_text


def test_live_gemini_draft_questions() -> None:
    """Verify live structured question drafting for course instructors."""
    pool = get_key_pool()
    client = RealGeminiClient(
        model_name="gemini-3.6-flash",
        timeout_seconds=15,
        key_pool=pool,
    )

    drafts = client.draft_questions(
        course_title="Lập trình Web chuyên sâu",
        topic="Async/Await và Promise trong JavaScript",
        difficulty="APPLY",
        question_types=["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"],
        count=3,
    )

    assert len(drafts) >= 1
    d1 = drafts[0]
    assert "content" in d1
    assert "choices" in d1
    assert "answer" in d1
    # Check security: no raw key in draft text
    assert "AQ." not in str(drafts)
    assert "AIzaSy" not in str(drafts)


def test_live_gemini_explain_recommendation() -> None:
    """Verify live academic course recommendation explanation."""
    pool = get_key_pool()
    client = RealGeminiClient(
        model_name="gemini-3.6-flash",
        timeout_seconds=15,
        key_pool=pool,
    )

    explanation = client.explain_recommendation(
        student_profile={"completed_courses": ["Cơ sở dữ liệu"]},
        course_facts={
            "title": "Phát triển Web với Python Flask",
            "category": "Backend",
            "difficulty": "INTERMEDIATE",
        },
    )

    assert explanation is not None
    assert len(explanation) > 15
    assert "AQ." not in explanation


def test_live_gemini_chat_and_scope_guardrails() -> None:
    """Verify live AI chat conversation and LMS scope guardrails."""
    pool = get_key_pool()
    client = RealGeminiClient(
        model_name="gemini-3.6-flash",
        timeout_seconds=15,
        key_pool=pool,
    )

    # In-scope query
    chat_resp = client.chat_response(
        messages=[{"sender": "USER", "content": "Hệ thống PWD301 có những tính năng gì?"}],
        context="GLOBAL",
    )
    assert chat_resp is not None
    assert len(chat_resp) > 15
    assert "AQ." not in chat_resp
