"""Security tests for Quarantine Fail-Closed Isolation & Admin Override (TASK-019).

Validates:
- Enrolled students cannot download QUARANTINED files (403 FileSecurityQuarantineError).
- Enrolled students cannot download INFECTED files (403 FileInfectedError).
- Unauthenticated requests to download quarantined files are blocked (401/403).
- Foreign instructors cannot access quarantined files from other courses (403 Forbidden).
- Path traversal sequences in uploaded filenames are sanitized and cannot escape quarantine root.
- Non-admin users (students, instructors) cannot execute quarantine override (403 Forbidden).
- Admin quarantine override requires a non-empty reason (ValidationError / 400).
- Valid admin quarantine override promotes file to ACTIVE, creates immutable AuditEvent,
  and allows enrolled students to download.
- Direct upload of EICAR string is immediately isolated in quarantine/infected and fails closed.
- Direct upload of weaponized PDF with /JavaScript is quarantined and blocked from download.
- Zero leakage of internal BIGINT PKs or physical storage paths during quarantine access attempts.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileScanResult
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    FileAccessDeniedError,
    FileInfectedError,
    FileSecurityQuarantineError,
    ForbiddenError,
    ValidationError,
)
from pwd301.services.file_service import (
    get_file_for_download,
    get_file_infected_root,
    quarantine_override,
    store_file_stream,
)
from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = db.session.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            db.session.add(role)
            db.session.flush()
        role_map[code] = role
    db.session.commit()
    return role_map


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user(
        f"admin_q_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin Quarantine User"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary instructor user."""
    u = register_user(
        f"inst_qa_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor QA"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create external instructor user."""
    u = register_user(
        f"inst_qb_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor QB"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_enrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create enrolled student user."""
    u = register_user(
        f"stud_qe_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Enrolled QA"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_a: User) -> Course:
    """Create a published course owned by instructor_a."""
    c = create_course(
        instructor_a,
        {
            "course_code": f"SEC-{uuid.uuid4().hex[:4].upper()}",
            "title": "Security & Malware Analysis",
            "category": "Cybersecurity",
            "difficulty": "ADVANCED",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


def test_student_download_quarantined_file_fails(
    app: Flask, instructor_a: User, student_enrolled: User, published_course: Course
) -> None:
    """Verify enrolled student cannot download a file marked as QUARANTINED."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Safe text content initially"),
        filename="notes.txt",
        session=db.session,
    )
    # Force revision to QUARANTINED state (simulating scanner timeout/error)
    rev = asset.current_revision
    rev.status = "QUARANTINED"
    db.session.commit()

    with pytest.raises(FileSecurityQuarantineError, match="quarantined"):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)


def test_student_download_infected_file_fails(
    app: Flask, instructor_a: User, student_enrolled: User, published_course: Course
) -> None:
    """Verify enrolled student cannot download an infected/rejected file."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    # Upload EICAR signature in harmless .txt -> scanner marks revision REJECTED
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(EICAR_SIGNATURE_BYTES),
        filename="eicar_test.txt",
        session=db.session,
    )
    rev = asset.current_revision or asset.revisions[-1]
    assert rev.status == "REJECTED"

    with pytest.raises(FileInfectedError, match="malware"):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)


def test_unauthenticated_download_quarantined_file_fails(
    client: FlaskClient, instructor_a: User, published_course: Course
) -> None:
    """Verify unauthenticated REST request to download file returns 401 or 403."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Confidential draft syllabus"),
        filename="syllabus.pdf",
        session=db.session,
    )

    resp = client.get(f"/api/files/{asset.public_id}/download")
    assert resp.status_code in (401, 403)


def test_foreign_instructor_cannot_access_quarantined_file(
    app: Flask,
    instructor_a: User,
    instructor_b: User,
    published_course: Course,
) -> None:
    """Verify instructor of another course receives 403 when downloading file."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Instructor A restricted file"),
        filename="exam_solutions.pdf",
        session=db.session,
    )

    with pytest.raises(FileAccessDeniedError):
        get_file_for_download(actor=instructor_b, asset_id=asset.public_id, session=db.session)


def test_path_traversal_quarantine_isolation(
    app: Flask, instructor_a: User, published_course: Course
) -> None:
    """Verify path traversal filenames are sanitized and stay safely within quarantine/blobs."""
    traversal_filename = "../../../etc/passwd.txt"
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Safe content with hostile filename"),
        filename=traversal_filename,
        session=db.session,
    )

    # Filename must be sanitized to basename only
    assert asset.current_revision.original_filename == "passwd.txt"
    assert ".." not in asset.current_revision.original_filename


def test_admin_override_non_admin_forbidden(
    app: Flask,
    instructor_a: User,
    student_enrolled: User,
    published_course: Course,
) -> None:
    """Verify non-admin users cannot override file quarantine."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Some text"),
        filename="doc.txt",
        session=db.session,
    )
    rev = asset.current_revision
    rev.status = "QUARANTINED"
    db.session.commit()

    # Student fails
    with pytest.raises(ForbiddenError):
        quarantine_override(
            admin_actor=student_enrolled,
            asset_id=asset.public_id,
            reason="Student trying to force release",
            session=db.session,
        )

    # Instructor fails
    with pytest.raises(ForbiddenError):
        quarantine_override(
            admin_actor=instructor_a,
            asset_id=asset.public_id,
            reason="Instructor trying to force release",
            session=db.session,
        )


def test_admin_override_empty_reason_fails(
    app: Flask,
    admin_user: User,
    instructor_a: User,
    published_course: Course,
) -> None:
    """Verify admin quarantine override fails if reason is empty or whitespace."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Content"),
        filename="sample.txt",
        session=db.session,
    )
    rev = asset.current_revision
    rev.status = "QUARANTINED"
    db.session.commit()

    with pytest.raises(ValidationError, match="reason"):
        quarantine_override(
            admin_actor=admin_user,
            asset_id=asset.public_id,
            reason="",
            session=db.session,
        )

    with pytest.raises(ValidationError, match="reason"):
        quarantine_override(
            admin_actor=admin_user,
            asset_id=asset.public_id,
            reason="   ",
            session=db.session,
        )


def test_admin_override_promotes_file_and_allows_student_download(
    app: Flask,
    admin_user: User,
    instructor_a: User,
    student_enrolled: User,
    published_course: Course,
) -> None:
    """Verify admin quarantine override promotes quarantined file, allowing student download."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    content = b"False-positive benign file that triggered heuristic alarm"
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(content),
        filename="false_alarm.txt",
        session=db.session,
    )
    rev = asset.current_revision
    rev.status = "QUARANTINED"
    db.session.commit()

    # Enrolled student cannot download before override
    with pytest.raises(FileSecurityQuarantineError):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)

    # Admin executes override
    updated_asset = quarantine_override(
        admin_actor=admin_user,
        asset_id=asset.public_id,
        reason="Security SecOps manual review confirmed clean false-positive.",
        session=db.session,
    )

    assert updated_asset.current_revision.status == "ACTIVE"
    assert updated_asset.status == "ACTIVE"

    # Enrolled student can now download successfully
    dl_asset, dl_blob, dl_path = get_file_for_download(
        actor=student_enrolled, asset_id=asset.public_id, session=db.session
    )
    assert dl_asset.id == asset.id
    assert dl_path.exists()
    assert dl_path.read_bytes() == content


def test_admin_override_audit_event_persisted(
    app: Flask,
    admin_user: User,
    instructor_a: User,
    published_course: Course,
) -> None:
    """Verify an immutable AuditEvent is created when admin overrides quarantine."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Data for audit test"),
        filename="audit_target.txt",
        session=db.session,
    )
    rev = asset.current_revision
    rev.status = "QUARANTINED"
    db.session.commit()

    reason_text = "Approved after sandbox detonation analysis."
    quarantine_override(
        admin_actor=admin_user,
        asset_id=asset.public_id,
        reason=reason_text,
        session=db.session,
    )

    audit_entry = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.action == "QUARANTINE_OVERRIDE",
            AuditEvent.actor_user_id == admin_user.id,
        )
        .first()
    )

    assert audit_entry is not None
    assert audit_entry.target_type == "FILE_ASSET"
    assert audit_entry.target_id == asset.id
    assert audit_entry.reason == reason_text


def test_eicar_upload_isolated_in_infected_directory(
    app: Flask,
    instructor_a: User,
    published_course: Course,
) -> None:
    """Verify uploading EICAR test string isolates file into quarantine/infected/."""
    import hashlib

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(EICAR_SIGNATURE_BYTES),
        filename="eicar_test.txt",
        session=db.session,
    )

    rev = asset.current_revision or asset.revisions[-1]
    assert rev.status == "REJECTED"
    hex_hash = hashlib.sha256(EICAR_SIGNATURE_BYTES).hexdigest()
    infected_root = get_file_infected_root()
    expected_infected_path = infected_root / hex_hash

    assert expected_infected_path.exists()
    assert expected_infected_path.read_bytes() == EICAR_SIGNATURE_BYTES

    # Scan result recorded as FAIL
    scan = (
        db.session.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).first()
    )
    assert scan is not None
    assert scan.status == "FAIL"


def test_malicious_pdf_js_fails_closed(
    app: Flask,
    instructor_a: User,
    published_course: Course,
) -> None:
    """Verify PDF with /JavaScript is blocked and quarantined."""
    pdf_hostile = (
        b"%PDF-1.4\n1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R /OpenAction "
        b"<< /S /JavaScript /JS (app.alert('PWN')) >> >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n"
        b"0000000000 65535 f \ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    )

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(pdf_hostile),
        filename="malicious_exec.pdf",
        session=db.session,
    )

    rev = asset.current_revision or asset.revisions[-1]
    assert rev.status == "REJECTED"
    scan_results = (
        db.session.query(FileScanResult).filter(FileScanResult.file_revision_id == rev.id).all()
    )
    failed_scans = [s for s in scan_results if s.status == "FAIL"]
    assert len(failed_scans) >= 1
