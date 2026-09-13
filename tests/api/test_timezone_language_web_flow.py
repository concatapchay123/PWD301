"""Integration tests for Language (i18n) and Timezone switching web flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_set_language_web_and_json_flow(client: FlaskClient) -> None:
    """Test switching language via POST /auth/set-language."""
    # 1. Switch to English via JSON
    res = client.post("/auth/set-language", json={"lang": "en"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["lang"] == "en"

    # Verify session and cookie
    with client.session_transaction() as sess:
        assert sess.get("lang") == "en"
    cookie = client.get_cookie("pwd301_lang")
    assert cookie is not None
    assert cookie.value == "en"

    # 2. Switch back to Vietnamese via Form
    res2 = client.post("/auth/set-language", data={"lang": "vi"}, follow_redirects=False)
    assert res2.status_code in (302, 303)
    with client.session_transaction() as sess:
        assert sess.get("lang") == "vi"
    cookie_vi = client.get_cookie("pwd301_lang")
    assert cookie_vi is not None
    assert cookie_vi.value == "vi"


def test_set_timezone_web_and_json_flow(client: FlaskClient) -> None:
    """Test switching timezone via POST /auth/set-timezone."""
    # 1. Set timezone to GMT+1 (Paris/Berlin)
    res = client.post("/auth/set-timezone", json={"timezone": "GMT+1"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["timezone"] == "+01:00"
    assert "GMT+1" in data["label"]

    with client.session_transaction() as sess:
        assert sess.get("user_timezone") == "+01:00"
    cookie = client.get_cookie("pwd301_timezone")
    assert cookie is not None
    assert cookie.value == "+01:00"

    # 2. Set timezone to Asia/Ho_Chi_Minh (GMT+7)
    res2 = client.post("/auth/set-timezone", json={"timezone": "Asia/Ho_Chi_Minh"})
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["timezone"] == "+07:00"
    assert "GMT+7" in data2["label"]

    with client.session_transaction() as sess:
        assert sess.get("user_timezone") == "+07:00"
