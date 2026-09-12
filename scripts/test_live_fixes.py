"""Test verification script for live AI chat auto-renewal and admin health route."""

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.ai_service import create_conversation
from pwd301.models.types import utc_now
from datetime import timedelta
import re

app = create_app()
client = app.test_client()

with app.app_context():
    u = db.session.query(User).join(User.roles).filter_by(code="ADMIN").first()
    _, raw_key = create_auth_session(u, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(u.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = u.auth_version
        sess["auth_source"] = "SESSION"

    # 1. Test /admin/health with Accept: */* (Browser view)
    r_browser = client.get("/admin/health", headers={"Accept": "*/*"})
    print("Browser View /admin/health:")
    print("  Status:", r_browser.status_code)
    print("  Content-Type:", r_browser.content_type)
    print("  Length:", len(r_browser.data))
    assert r_browser.status_code == 200
    assert r_browser.content_type.startswith("text/html")
    assert "Trung tâm Giám sát Sức khỏe" in r_browser.get_data(as_text=True)

    # 2. Test /admin/health?format=json (API View)
    r_json = client.get("/admin/health?format=json")
    print("API View /admin/health?format=json:")
    print("  Status:", r_json.status_code)
    print("  Content-Type:", r_json.content_type)
    assert r_json.status_code == 200
    assert r_json.content_type == "application/json"
    assert "components" in r_json.get_json()

    # 3. Test AI Chat auto-renewal with expired session
    conv = create_conversation(actor=u, context_type="GLOBAL", session=db.session)
    old_id = str(conv.public_id)
    now = utc_now()
    conv.created_at = now - timedelta(minutes=15)
    conv.last_activity_at = now - timedelta(minutes=10)
    conv.expires_at = now - timedelta(minutes=5)
    conv.status = "EXPIRED"
    db.session.commit()

    # Get CSRF token from dashboard
    resp = client.get("/admin/dashboard")
    html_text = resp.get_data(as_text=True)
    match = re.search(r'name="csrf-token" content="([^"]+)"', html_text)
    csrf_token = match.group(1) if match else ""
    headers = {"X-CSRFToken": csrf_token}

    with client.session_transaction() as sess:
        sess["active_ai_conversation_id"] = old_id

    # Send message 1: "hello"
    r_chat1 = client.post("/student/ai/chat", json={"message": "hello"}, headers=headers)
    print("Chat 1 Response:")
    print("  Status:", r_chat1.status_code)
    data1 = r_chat1.get_json()
    print("  Reply:", data1.get("reply"))
    print("  Conv ID:", data1.get("conversation_id"))
    assert r_chat1.status_code == 200
    assert data1.get("status") == "success"
    assert "Hệ thống đang đồng bộ dữ liệu" not in data1.get("reply", "")
    assert data1.get("conversation_id") != old_id

    # Send message 2: "bạn là ai"
    r_chat2 = client.post("/student/ai/chat", json={"message": "bạn là ai"}, headers=headers)
    print("Chat 2 Response:")
    print("  Status:", r_chat2.status_code)
    data2 = r_chat2.get_json()
    print("  Reply:", data2.get("reply"))
    print("  Conv ID:", data2.get("conversation_id"))
    assert r_chat2.status_code == 200
    assert data2.get("status") == "success"
    assert "Hệ thống đang đồng bộ dữ liệu" not in data2.get("reply", "")

    print("\nALL VERIFICATIONS SUCCEEDED!")
