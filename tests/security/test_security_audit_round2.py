"""Unit and security tests verifying fixes from Cycle 2 of the autonomous audit.

Verifies:
1. forgot_password masks reset_token when current_app.config['TESTING'] is False
   and enqueues outbox email.
2. BuiltinHeuristicScanner streaming chunked scanner logic for large files.
3. verify_backup_integrity chunked streaming sha256 calculation.
4. regrade_worker synthetic UUID caches.
5. Core public catalog ignores soft-deleted courses.
6. Retention trash pruning cleans up knowledge documents, versions, chunks, and drafts.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from typing import Any
from unittest.mock import MagicMock

from flask import Flask

from pwd301.extensions import db
from pwd301.models.ai_rag import (
    AIGeneratedQuestionDraft,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeVersion,
)
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import EmailDelivery
from pwd301.models.operations import BackupRun
from pwd301.models.types import utc_now
from pwd301.services.operations_service import verify_backup_integrity
from pwd301.services.regrade_worker import (
    _SYNTHETIC_CORRECTION_CACHE,
    _SYNTHETIC_JOB_CACHE,
    _resolve_question_correction,
    _resolve_regrade_job,
)
from pwd301.services.retention_service import prune_trash_entities
from pwd301.services.scanner_service import BuiltinHeuristicScanner


def _get_or_create_role(code: str, name: str) -> Role:
    role = db.session.query(Role).filter_by(code=code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.session.add(role)
        db.session.flush()
    return role


def test_forgot_password_masks_token_in_production(client: Any, app: Flask) -> None:
    """Ensure forgot-password does not leak the reset_token in production mode."""
    with app.app_context():
        student_role = _get_or_create_role("STUDENT", "Student")
        user = User(
            email="victim_user@fpt.edu.vn",
            display_name="Victim User",
            password_hash="hashed_pw",
            auth_version=1,
        )
        user.roles.append(student_role)
        db.session.add(user)
        db.session.commit()

        # Temporarily turn off TESTING flag to simulate production
        app.config["TESTING"] = False
        try:
            resp = client.post(
                "/auth/forgot-password",
                json={"email": "victim_user@fpt.edu.vn"},
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert "reset_token" not in data

            # Verify an outbox email was enqueued
            email = (
                db.session.query(EmailDelivery)
                .filter_by(recipient_email_snapshot="victim_user@fpt.edu.vn")
                .first()
            )
            assert email is not None
            assert email.template_code == "PASSWORD_RESET"
        finally:
            app.config["TESTING"] = True


def test_scanner_streaming_chunked_for_large_files(tmp_path: Any) -> None:
    """Verify BuiltinHeuristicScanner does not read whole files into memory."""
    scanner = BuiltinHeuristicScanner()

    # Create a dummy large file (60MB of zeros)
    dummy_file = tmp_path / "large_file.dat"
    with open(dummy_file, "wb") as f:
        f.seek(60 * 1024 * 1024 - 1)
        f.write(b"\0")

    result = scanner.scan_file(dummy_file)
    assert result.status == "PASS"
    assert result.signature_name is None

    # Now create a file > 50MB that contains the EICAR string across a chunk boundary
    eicar_bytes = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    eicar_file = tmp_path / "large_eicar.dat"
    with open(eicar_file, "wb") as f:
        f.write(b"0" * (51 * 1024 * 1024))
        f.write(eicar_bytes)
        f.write(b"0" * 1024)

    eicar_result = scanner.scan_file(eicar_file)
    assert eicar_result.status == "FAIL"
    assert eicar_result.signature_name == "EICAR-Test-Signature"


def test_verify_backup_integrity_streaming_hash(app: Flask, tmp_path: Any) -> None:
    """Verify verify_backup_integrity calculates SHA-256 via streaming without OOM."""
    with app.app_context():
        admin_role = _get_or_create_role("ADMIN", "System Administrator")
        admin = User(
            email="admin_backup_hash@fpt.edu.vn",
            display_name="Admin Backup Hash",
            password_hash="test_hash",
            auth_version=1,
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.flush()

        test_file = tmp_path / "backup_snapshot.json"
        snapshot_payload = json.dumps(
            {"metadata": {"format": "PWD301_SNAPSHOT", "tables": {}}}
        ).encode("utf-8")
        test_file.write_bytes(snapshot_payload)

        backup = BackupRun(
            backup_type="MANUAL",
            status="SUCCEEDED",
            started_by_user_id=admin.id,
            storage_location=str(test_file),
            database_backup_name=test_file.name,
            started_at=utc_now(),
        )
        db.session.add(backup)
        db.session.commit()

        res = verify_backup_integrity(actor=admin, backup_id=str(backup.public_id))
        assert res["status"] == "VERIFIED"
        assert res["verified"] is True
        assert res["checksum"] == hashlib.sha256(snapshot_payload).hexdigest()
        assert res["file_size"] == len(snapshot_payload)


def test_regrade_worker_synthetic_uuid_cache() -> None:
    """Ensure synthetic UUID resolution populates and uses the cache."""
    mock_session = MagicMock()
    mock_session.query.return_value.all.return_value = [(12345,)]
    fake_job = MagicMock()
    fake_job.id = 12345
    mock_session.get.return_value = fake_job

    _SYNTHETIC_JOB_CACHE.clear()
    syn_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "pwd301.regrade_job.12345")
    resolved = _resolve_regrade_job(syn_uuid, session=mock_session)
    assert resolved == fake_job
    assert _SYNTHETIC_JOB_CACHE.get(syn_uuid) == 12345

    # Resolution from cache directly
    cached_job = _resolve_regrade_job(syn_uuid, session=mock_session)
    assert cached_job == fake_job

    # Question correction cache
    _SYNTHETIC_CORRECTION_CACHE.clear()
    mock_session.query.return_value.all.return_value = [(67890,)]
    fake_corr = MagicMock()
    fake_corr.id = 67890
    mock_session.get.return_value = fake_corr

    corr_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "pwd301.question_correction.67890")
    res_corr = _resolve_question_correction(corr_uuid, session=mock_session)
    assert res_corr == fake_corr
    assert _SYNTHETIC_CORRECTION_CACHE.get(corr_uuid) == 67890


def test_public_catalog_filters_soft_deleted_courses(client: Any, app: Flask) -> None:
    """Verify that the core public homepage does not render soft-deleted courses."""
    with app.app_context():
        instructor_role = _get_or_create_role("INSTRUCTOR", "Instructor")
        inst = User(
            email="inst_catalog@fpt.edu.vn",
            display_name="Instructor Catalog",
            password_hash="hash",
            auth_version=1,
        )
        inst.roles.append(instructor_role)
        db.session.add(inst)
        db.session.flush()

        active_crs = Course(
            course_code="ACT101",
            course_code_normalized="ACT101",
            title="Active Course Title",
            title_normalized="ACTIVE COURSE TITLE",
            status="PUBLISHED",
            owner_instructor_id=inst.id,
        )
        deleted_crs = Course(
            course_code="DEL101",
            course_code_normalized="DEL101",
            title="Deleted Course Title",
            title_normalized="DELETED COURSE TITLE",
            status="PUBLISHED",
            owner_instructor_id=inst.id,
            deleted_at=utc_now(),
        )
        db.session.add_all([active_crs, deleted_crs])
        db.session.commit()

        resp = client.get("/", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "ACT101" in html
        assert "DEL101" not in html


def test_prune_trash_entities_cascading_knowledge_and_drafts(app: Flask) -> None:
    """Verify prune_trash_entities deletes knowledge sources and drafts before deleting courses."""
    with app.app_context():
        inst_role = _get_or_create_role("INSTRUCTOR", "Instructor")
        inst = User(
            email="prune_test_inst@fpt.edu.vn",
            display_name="Prune Instructor",
            password_hash="hash",
            auth_version=1,
        )
        inst.roles.append(inst_role)
        db.session.add(inst)
        db.session.flush()

        # Disposable course in TRASH with restore_until expired
        old_date = utc_now() - datetime.timedelta(days=60)
        course = Course(
            course_code="DISPOSABLE99",
            course_code_normalized="DISPOSABLE99",
            title="Disposable Course",
            title_normalized="DISPOSABLE COURSE",
            status="TRASH",
            restore_until=old_date,
            owner_instructor_id=inst.id,
            deleted_at=old_date,
        )
        db.session.add(course)
        db.session.flush()

        lesson = Lesson(
            course_id=course.id,
            title="Disposable Lesson",
            markdown_content="# Content",
            position=1,
            deleted_at=old_date,
        )
        db.session.add(lesson)
        db.session.flush()

        kdoc = KnowledgeDocument(
            course_id=course.id,
            lesson_id=lesson.id,
            source_type="LESSON",
            source_entity_id=lesson.id,
            status="ACTIVE",
        )
        db.session.add(kdoc)
        db.session.flush()

        kver = KnowledgeVersion(
            knowledge_document_id=kdoc.id,
            version_no=1,
            content_hash=b"0" * 32,
            status="ACTIVE",
        )
        db.session.add(kver)
        db.session.flush()

        kchunk = KnowledgeChunk(
            knowledge_version_id=kver.id,
            chunk_no=1,
            text_hash=b"0" * 32,
            vector_key="key_chunk_1",
        )
        db.session.add(kchunk)

        draft = AIGeneratedQuestionDraft(
            course_id=course.id,
            lesson_id=lesson.id,
            requested_by_user_id=inst.id,
            ordinal=1,
            question_type="SINGLE_CHOICE",
            difficulty="REMEMBER",
            content="Sample draft question?",
            review_state="PENDING",
        )
        db.session.add(draft)
        db.session.commit()

        # Cache entity IDs before deletion to avoid accessing deleted instances
        kchunk_id = kchunk.id
        kver_id = kver.id
        kdoc_id = kdoc.id
        draft_id = draft.id
        course_id = course.id

        # Run retention pruning
        stats = prune_trash_entities(session=db.session)
        assert stats["courses"] >= 1

        # Verify child records were deleted
        assert db.session.get(KnowledgeChunk, kchunk_id) is None
        assert db.session.get(KnowledgeVersion, kver_id) is None
        assert db.session.get(KnowledgeDocument, kdoc_id) is None
        assert db.session.get(AIGeneratedQuestionDraft, draft_id) is None
        assert db.session.get(Course, course_id) is None
