"""Unit tests for Gemini Multi-Key Pool, Automatic Fallback, and Security Leakage Protection.

Enforces:
- Iron Law of TDD: Contract validation before implementation.
- Automatic key rotation upon 401, 403, 429, and 503 errors.
- Zero API key leakage in logs, exceptions, and requests.
- Dynamic health tracking (HEALTHY, RATE_LIMITED, INVALID).
- Multi-model fallback cascade.
"""

from __future__ import annotations

import json
import unittest.mock
from pathlib import Path
from typing import Any

from pwd301.services.gemini_service import (
    GeminiKeyPool,
    GeminiKeyStatus,
    RealGeminiClient,
    mask_api_key,
)


def test_mask_api_key_sanitization() -> None:
    """mask_api_key redacts any Google API key pattern from strings, URLs, and exceptions."""
    sample_key_aq = "AQ.TestDummyKeyForSanitizationVerification12345"
    sample_key_aiza = "AIzaSyDa-TestKeyExampleForSecurityAudit12345"

    text = (
        f"Error calling Gemini with key {sample_key_aq} on url "
        f"https://example.com?key={sample_key_aiza}"
    )
    sanitized = mask_api_key(text)

    assert sample_key_aq not in sanitized
    assert sample_key_aiza not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_key_pool_parsing_and_deduplication(tmp_path: Path) -> None:
    """GeminiKeyPool loads valid keys from keyfile, strips metadata and duplicates."""
    dummy_keyfile = tmp_path / "test_keys.md"
    dummy_keyfile.write_text(
        "--header--\n"
        "some_user@example.com\n"
        "AQ.TestDummyKeyForUnitTestingAlpha11111111111111\n"
        "AQ.TestDummyKeyForUnitTestingBeta222222222222222\n"
        "invalid_short_key\n"
        "# comment line\n"
        "AQ.TestDummyKeyForUnitTestingAlpha11111111111111\n"  # Duplicate
        "AIzaSyDa-ValidAIzaKeyExampleLength39Char1234\n",
        encoding="utf-8",
    )

    pool = GeminiKeyPool(keyfile_paths=[dummy_keyfile])
    assert len(pool.keys) == 3
    assert "AQ.TestDummyKeyForUnitTestingAlpha11111111111111" in pool.keys
    assert "AQ.TestDummyKeyForUnitTestingBeta222222222222222" in pool.keys
    assert "AIzaSyDa-ValidAIzaKeyExampleLength39Char1234" in pool.keys
    assert "invalid_short_key" not in pool.keys


def test_key_pool_health_transitions() -> None:
    """GeminiKeyPool transitions key status between HEALTHY, RATE_LIMITED, and INVALID."""
    pool = GeminiKeyPool(
        keys=[
            "AQ.KeyOne1111111111111111111111111111111111111111111",
            "AQ.KeyTwo2222222222222222222222222222222222222222222",
            "AQ.KeyThree333333333333333333333333333333333333333333",
        ]
    )

    k1 = pool.get_current_key()
    assert k1 == "AQ.KeyOne1111111111111111111111111111111111111111111"

    # Report 401 Unauthorized -> Should mark KeyOne as INVALID permanently
    pool.report_key_failure(k1, error_code=401, reason="Unauthorized")
    assert pool.get_key_status(k1) == GeminiKeyStatus.INVALID

    # Next key should be KeyTwo
    k2 = pool.get_current_key()
    assert k2 == "AQ.KeyTwo2222222222222222222222222222222222222222222"

    # Report 429 Quota Exceeded -> Should mark KeyTwo as RATE_LIMITED with cooldown
    pool.report_key_failure(k2, error_code=429, reason="Quota Exceeded")
    assert pool.get_key_status(k2) == GeminiKeyStatus.RATE_LIMITED

    # Next key should be KeyThree
    k3 = pool.get_current_key()
    assert k3 == "AQ.KeyThree333333333333333333333333333333333333333333"

    # Report success on KeyThree
    pool.report_key_success(k3)
    assert pool.get_key_status(k3) == GeminiKeyStatus.HEALTHY
    # Subsequent get_current_key should remain on working KeyThree
    assert pool.get_current_key() == k3


def test_real_gemini_client_rotates_on_401_unauthorized() -> None:
    """When a key returns HTTP 401, client automatically marks it dead and tries next key."""
    dead_key = "AQ.DeadKey11111111111111111111111111111111111111111"
    good_key = "AQ.GoodKey22222222222222222222222222222222222222222"

    pool = GeminiKeyPool(keys=[dead_key, good_key])
    client = RealGeminiClient(api_key=dead_key, key_pool=pool, timeout_seconds=2)

    call_records: list[dict[str, Any]] = []

    def fake_urlopen(req: Any, timeout: Any = None) -> Any:
        import urllib.error

        used_key = req.headers.get("X-goog-api-key")
        call_records.append({"url": req.full_url, "key": used_key})

        if used_key == dead_key:
            err = urllib.error.HTTPError(
                url=req.full_url,
                code=401,
                msg="Unauthorized",
                hdrs=unittest.mock.MagicMock(),
                fp=unittest.mock.MagicMock(),
            )
            err.read = lambda: b'{"error": {"code": 401, "message": "Service account disabled"}}'  # type: ignore[assignment]
            raise err

        # Good key succeeds
        mock_resp = unittest.mock.MagicMock()
        payload = {
            "candidates": [
                {"content": {"parts": [{"text": "Hello from resilient key fallback!"}]}}
            ]
        }
        mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with unittest.mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        resp = client.generate_text("Test prompt")

    assert "resilient key fallback" in resp
    assert len(call_records) == 2
    assert call_records[0]["key"] == dead_key
    assert call_records[1]["key"] == good_key
    assert pool.get_key_status(dead_key) == GeminiKeyStatus.INVALID
    assert pool.get_key_status(good_key) == GeminiKeyStatus.HEALTHY


def test_real_gemini_client_header_security() -> None:
    """API key is strictly transmitted via x-goog-api-key header and never in URL query."""
    key = "AQ.SecurityTestKey1111111111111111111111111111111111"
    pool = GeminiKeyPool(keys=[key])
    client = RealGeminiClient(api_key=key, key_pool=pool, timeout_seconds=2)

    captured_reqs: list[Any] = []

    def fake_urlopen(req: Any, timeout: Any = None) -> Any:
        captured_reqs.append(req)
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Security verified"}]}}]}
        ).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with unittest.mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        client.generate_text("Check request security")

    assert len(captured_reqs) == 1
    req = captured_reqs[0]
    # URL must not have ?key=
    assert "key=" not in req.full_url
    # Header must carry key
    assert req.headers.get("X-goog-api-key") == key


def test_real_gemini_client_model_fallback_on_503() -> None:
    """When a model returns 503 (high demand), client cascades to next model candidate."""
    key = "AQ.TestKeyWorking11111111111111111111111111111111111"
    pool = GeminiKeyPool(keys=[key])
    client = RealGeminiClient(
        api_key=key,
        model_name="gemini-3.8-flash",
        key_pool=pool,
        timeout_seconds=2,
    )

    models_attempted: list[str] = []

    def fake_urlopen(req: Any, timeout: Any = None) -> Any:
        import urllib.error

        for m in ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest"]:
            if m in req.full_url:
                models_attempted.append(m)
                break

        if "gemini-3.8-flash" in req.full_url:
            err = urllib.error.HTTPError(
                url=req.full_url,
                code=503,
                msg="Service Unavailable",
                hdrs=unittest.mock.MagicMock(),
                fp=unittest.mock.MagicMock(),
            )
            err.read = lambda: b'{"error": {"code": 503, "message": "High demand"}}'  # type: ignore[assignment]
            raise err

        # Fallback model succeeds
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Fallback model response"}]}}]}
        ).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with unittest.mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        text = client.generate_text("Hi")

    assert "Fallback model response" in text
    assert "gemini-3.8-flash" in models_attempted
    assert len(models_attempted) >= 2
