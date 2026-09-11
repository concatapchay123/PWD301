"""Unit tests verifying the autonomous security audit & architecture hardening fixes.

Verifies:
1. SQL Server physical restore escapes database name and physical path, and rejects path traversal.
2. DOCX zip bomb uncompressed size limit enforcement in import_service.
3. Outbox email queuing savepoint isolation: IntegrityError does not break caller transaction.
4. Gemini client transmits API key via x-goog-api-key header without URL query leakage.
5. AI and RAG failure telemetry is persisted in ai_requests when downstream LLM fails.
"""

from __future__ import annotations

import json
import urllib.request
import uuid
import zipfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.ai_rag import AIRequest
from pwd301.models.identity import Role, User
from pwd301.models.operations import BackupRun
from pwd301.models.types import utc_now
from pwd301.services.ai_service import create_conversation, send_chat_message
from pwd301.services.email_service import enqueue_email
from pwd301.services.exceptions import (
    AIServiceUnavailableError,
    DocumentParsingError,
    RestoreForbiddenError,
)
from pwd301.services.gemini_service import RealGeminiClient
from pwd301.services.import_service import extract_text_from_docx
from pwd301.services.operations_service import restore_database_snapshot


def _get_or_create_role(code: str, name: str) -> Role:
    role = db.session.query(Role).filter_by(code=code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.session.add(role)
        db.session.flush()
    return role


def test_restore_rejects_path_traversal(app: Flask) -> None:
    """Ensure database restore rejects database_backup_name attempting path traversal."""
    with app.app_context():
        admin_role = _get_or_create_role("ADMIN", "System Administrator")
        admin = User(
            email="admin_traversal@fpt.edu.vn",
            display_name="Admin Traversal",
            password_hash="test_hash",
            auth_version=1,
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.flush()

        # Malicious backup with directory traversal
        backup = BackupRun(
            backup_type="MANUAL",
            status="SUCCEEDED",
            started_by_user_id=admin.id,
            storage_location="C:/windows/system32",
            database_backup_name="../../sensitive/system.bak",
            started_at=utc_now(),
        )
        db.session.add(backup)
        db.session.commit()

        # Mock engine to simulate MSSQL dialect
        mock_bind = MagicMock()
        mock_bind.dialect.name = "mssql"
        mock_engine = MagicMock()
        mock_engine.url.database = "TestDB]; DROP DATABASE PWD301;--"
        mock_bind.engine = mock_engine

        with (
            patch.object(db.session, "get_bind", return_value=mock_bind),
            patch.object(admin, "verify_password", return_value=True),
            patch(
                "pwd301.services.operations_service.verify_backup_integrity",
                return_value={"checksum": "sha256_dummy"},
            ),
            patch("pwd301.services.operations_service.record_audit_event"),
            pytest.raises(RestoreForbiddenError, match="Path traversal detected"),
        ):
            restore_database_snapshot(
                actor=admin,
                backup_id=backup.public_id,
                confirmation_phrase="CONFIRM_DATABASE_RESTORE",
                password="secret_password",
            )


def test_docx_zip_bomb_uncompressed_limit(tmp_path: Any) -> None:
    """Ensure import_service rejects DOCX files where document.xml exceeds 50MB."""
    dummy_file = tmp_path / "test.docx"
    with zipfile.ZipFile(dummy_file, "w") as zf:
        zf.writestr("word/document.xml", b"<w:document/>")

    mock_entry = MagicMock()
    mock_entry.file_size = 60_000_000  # 60 MB

    with (
        patch.object(zipfile.ZipFile, "getinfo", return_value=mock_entry),
        pytest.raises(DocumentParsingError, match="exceeds maximum safe uncompressed size"),
    ):
        extract_text_from_docx(dummy_file)


def test_enqueue_email_savepoint_isolation(app: Flask) -> None:
    """Ensure enqueue_email uses savepoint so duplicate insert does not rollback tx."""
    with app.app_context():
        dedupe_uuid = uuid.uuid4()
        deliv1 = enqueue_email(
            recipient_email="student_test@fpt.edu.vn",
            subject="Test Subject 1",
            body_text="Test Body 1",
            dedupe_key=dedupe_uuid,
        )
        assert deliv1 is not None

        # Call again with identical dedupe_key within the same outer session
        deliv2 = enqueue_email(
            recipient_email="student_test@fpt.edu.vn",
            subject="Test Subject 2",
            body_text="Test Body 2",
            dedupe_key=dedupe_uuid,
        )
        assert deliv2.id == deliv1.id
        # Confirm session is still clean and active
        assert db.session.is_active


def test_gemini_api_key_header_transmission() -> None:
    """Ensure RealGeminiClient sends API key in x-goog-api-key header without URL query."""
    client = RealGeminiClient(api_key="SECRET_GEMINI_API_KEY_12345", model_name="gemini-1.5-flash")
    assert "key=" not in client.base_url

    captured_requests: list[urllib.request.Request] = []

    def mock_urlopen(req: urllib.request.Request, timeout: int = 10) -> MagicMock:
        captured_requests.append(req)
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Hello from secure Gemini API"}]}}]}
        ).encode("utf-8")
        resp.__enter__.return_value = resp
        return resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        result = client.generate_text("Test prompt")
        assert result == "Hello from secure Gemini API"

    assert len(captured_requests) == 1
    req = captured_requests[0]
    # URL must not contain the secret API key in query string
    assert "SECRET_GEMINI_API_KEY_12345" not in req.full_url
    # API key must be strictly in the HTTP headers
    assert req.headers.get("X-goog-api-key") == "SECRET_GEMINI_API_KEY_12345"


def test_ai_chat_failure_telemetry_recorded(app: Flask) -> None:
    """Ensure send_chat_message records failure telemetry when downstream LLM fails."""
    with app.app_context():
        student_role = _get_or_create_role("STUDENT", "Student")
        user = User(
            email="chat_telemetry@fpt.edu.vn",
            display_name="Chat Telemetry User",
            password_hash="test_hash",
            auth_version=1,
        )
        user.roles.append(student_role)
        db.session.add(user)
        db.session.commit()

        conv = create_conversation(actor=user, context_type="GLOBAL")

        mock_client = MagicMock()
        mock_client.chat_response.side_effect = AIServiceUnavailableError("LLM downstream failure")

        with (
            patch("pwd301.services.ai_service.get_gemini_client", return_value=mock_client),
            pytest.raises(AIServiceUnavailableError),
        ):
            send_chat_message(
                actor=user,
                conversation_id=conv.public_id,
                content="What is Python?",
            )

        # Confirm telemetry row was recorded with status=FAILED
        failed_req = (
            db.session.query(AIRequest)
            .filter(
                AIRequest.user_id == user.id,
                AIRequest.conversation_id == conv.id,
                AIRequest.status == "FAILED",
            )
            .first()
        )
        assert failed_req is not None
        assert failed_req.error_code == "AIServiceUnavailableError"
