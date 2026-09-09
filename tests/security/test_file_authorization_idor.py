"""Security and IDOR negative tests for File Storage & Authorization Engine (TASK-018).

Validates:
- Foreign instructors cannot upload, delete, restore, or add revisions to other courses.
- Unenrolled students cannot download course files (403 Forbidden).
- Enrolled students with active enrollment can download published course files and resources.
- Enrolled students cannot download resources attached exclusively to DRAFT lessons.
- Students cannot download files from an unpublished (DRAFT) course (403 Forbidden).
- Fail-closed security: Quarantined/infected files are rejected with FileSecurityQuarantineError.
- Admins possess platform-wide access to view and download all files.
- ADR-002: Zero leakage of internal BIGINT PK/FK or physical storage paths in serializers.
- Path traversal prevention: Filenames with traversal sequences are sanitized.
"""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.models.file_import import FileScanResult
from pwd301.models.identity import Role, User
from pwd301.models.types import utc_now
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    FileAccessDeniedError,
    FileSecurityQuarantineError,
    ForbiddenError,
)
from pwd301.services.file_service import (
    _serialize_file_asset,
    _serialize_lesson_resource,
    add_file_revision,
    attach_resource_to_lesson,
    detach_resource_from_lesson,
    get_file_for_download,
    restore_file_asset,
    store_file_stream,
    trash_file_asset,
)
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
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
        f"admin_file_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin User"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary course owner instructor."""
    u = register_user(f"inst_a_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor A")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create external rival instructor."""
    u = register_user(f"inst_b_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor B")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_enrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student who enrolls in the course."""
    u = register_user(
        f"stud_enrolled_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Enrolled"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_unenrolled(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student who is NOT enrolled in the course."""
    u = register_user(
        f"stud_unenrolled_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student Unenrolled"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(instructor_a: User) -> Course:
    """Create published course owned by Instructor A."""
    c = create_course(
        instructor_a,
        {
            "course_code": f"SEC-{uuid.uuid4().hex[:4].upper()}",
            "title": "Security Authorization Course",
            "category": "Security",
            "difficulty": "INTERMEDIATE",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


def test_foreign_instructor_cannot_upload_file(
    app: Flask, instructor_b: User, published_course: Course
) -> None:
    """Verify Instructor B cannot upload files to Course A (403 Forbidden)."""
    with pytest.raises(ForbiddenError):
        store_file_stream(
            actor=instructor_b,
            course_id=published_course.public_id,
            file_stream=io.BytesIO(b"Unauthorized upload"),
            filename="unauthorized.pdf",
            session=db.session,
        )


def test_foreign_instructor_cannot_trash_or_restore(
    app: Flask, instructor_a: User, instructor_b: User, published_course: Course
) -> None:
    """Verify Instructor B cannot trash or restore files owned by Instructor A."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Valid Course Asset"),
        filename="course_guide.pdf",
        session=db.session,
    )

    # Instructor B tries to trash
    with pytest.raises(ForbiddenError):
        trash_file_asset(actor=instructor_b, asset_id=asset.public_id, session=db.session)

    # Instructor A trashes it
    trash_file_asset(actor=instructor_a, asset_id=asset.public_id, session=db.session)

    # Instructor B tries to restore
    with pytest.raises(ForbiddenError):
        restore_file_asset(actor=instructor_b, asset_id=asset.public_id, session=db.session)


def test_foreign_instructor_cannot_add_revision(
    app: Flask, instructor_a: User, instructor_b: User, published_course: Course
) -> None:
    """Verify Instructor B cannot add revisions to files owned by Instructor A."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Revision 1"),
        filename="guide.pdf",
        session=db.session,
    )

    with pytest.raises(ForbiddenError):
        add_file_revision(
            actor=instructor_b,
            asset_id=asset.public_id,
            file_stream=io.BytesIO(b"Malicious Revision"),
            filename="guide_rev.pdf",
            session=db.session,
        )


def test_foreign_instructor_cannot_attach_or_detach_lesson_resource(
    app: Flask, instructor_a: User, instructor_b: User, published_course: Course
) -> None:
    """Verify Instructor B cannot attach or detach resources from lessons in Course A."""
    lesson = create_lesson(
        instructor_a,
        str(published_course.public_id),
        {"title": "Lesson 1", "position": 1, "markdown_content": "# Lesson 1 Content"},
        session=db.session,
    )
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Lesson Resource"),
        filename="lesson_resource.pdf",
        session=db.session,
    )

    # Instructor B cannot attach
    with pytest.raises(ForbiddenError):
        attach_resource_to_lesson(
            actor=instructor_b,
            lesson_id=lesson.public_id,
            asset_id=asset.public_id,
            session=db.session,
        )

    # Instructor A attaches
    lr = attach_resource_to_lesson(
        actor=instructor_a,
        lesson_id=lesson.public_id,
        asset_id=asset.public_id,
        session=db.session,
    )

    # Instructor B cannot detach
    with pytest.raises(ForbiddenError):
        detach_resource_from_lesson(
            actor=instructor_b,
            lesson_id=lesson.public_id,
            resource_id=lr.public_id,
            session=db.session,
        )


def test_unenrolled_student_cannot_download(
    app: Flask, instructor_a: User, student_unenrolled: User, published_course: Course
) -> None:
    """Verify unenrolled student receives 403 when attempting to download course file."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Enrolled Students Only"),
        filename="secret_lecture.pdf",
        session=db.session,
    )

    with pytest.raises(FileAccessDeniedError, match="not actively enrolled"):
        get_file_for_download(
            actor=student_unenrolled, asset_id=asset.public_id, session=db.session
        )


def test_enrolled_student_can_download_published_file(
    app: Flask, instructor_a: User, student_enrolled: User, published_course: Course
) -> None:
    """Verify actively enrolled student can download files from published course."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Public Learning Content"),
        filename="handout.pdf",
        session=db.session,
    )

    download_asset, blob, path = get_file_for_download(
        actor=student_enrolled, asset_id=asset.public_id, session=db.session
    )
    assert download_asset.id == asset.id
    assert path.exists()
    assert path.read_bytes() == b"Public Learning Content"


def test_student_cannot_download_from_draft_course(
    app: Flask, instructor_a: User, student_enrolled: User
) -> None:
    """Verify student cannot download files if course is still in DRAFT status."""
    draft_course = create_course(
        instructor_a,
        {
            "course_code": f"DRAFT-{uuid.uuid4().hex[:4].upper()}",
            "title": "Draft Course",
            "category": "Draft",
            "difficulty": "BEGINNER",
        },
    )
    # Manually create enrollment in draft course for test setup
    enrollment = Enrollment(
        course_id=draft_course.id,
        student_user_id=student_enrolled.id,
        status="ACTIVE",
    )
    db.session.add(enrollment)
    db.session.commit()

    asset = store_file_stream(
        actor=instructor_a,
        course_id=draft_course.public_id,
        file_stream=io.BytesIO(b"Draft Material"),
        filename="draft.pdf",
        session=db.session,
    )

    with pytest.raises(FileAccessDeniedError, match="unpublished course"):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)


def test_student_cannot_download_draft_lesson_resource(
    app: Flask, instructor_a: User, student_enrolled: User, published_course: Course
) -> None:
    """Verify student cannot access a resource attached exclusively to a DRAFT lesson."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    # Create DRAFT lesson
    draft_lesson = create_lesson(
        instructor_a,
        str(published_course.public_id),
        {
            "title": "Draft Upcoming Lesson",
            "position": 1,
            "markdown_content": "# Upcoming Content",
        },
        session=db.session,
    )
    assert draft_lesson.status == "DRAFT"

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Upcoming Unreleased Material"),
        filename="unreleased.pdf",
        session=db.session,
    )
    attach_resource_to_lesson(
        actor=instructor_a,
        lesson_id=draft_lesson.public_id,
        asset_id=asset.public_id,
        session=db.session,
    )

    # Student cannot download because attached lesson is DRAFT
    with pytest.raises(FileAccessDeniedError, match="not yet published"):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)

    # Once lesson is published, student can download
    draft_lesson.status = "PUBLISHED"
    db.session.commit()
    _, _, path = get_file_for_download(
        actor=student_enrolled, asset_id=asset.public_id, session=db.session
    )
    assert path.read_bytes() == b"Upcoming Unreleased Material"


def test_fail_closed_on_quarantined_or_infected_file(
    app: Flask, instructor_a: User, student_enrolled: User, published_course: Course
) -> None:
    """Verify files with failed scan checks or quarantined status are fail-closed."""
    enroll_student(
        actor=student_enrolled,
        course_id=str(published_course.public_id),
        session=db.session,
    )
    db.session.commit()

    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Infected payload simulation"),
        filename="infected.pdf",
        session=db.session,
    )

    # Simulate scan result failure (malware detected)
    rev = asset.current_revision
    scan = FileScanResult(
        file_revision_id=rev.id,
        scan_type="MALWARE",
        engine="ClamAV",
        engine_version="1.0",
        status="FAIL",
        details_json='{"threat": "EICAR-Test-Signature"}',
        started_at=utc_now(),
        completed_at=utc_now(),
    )
    db.session.add(scan)
    db.session.commit()

    with pytest.raises(FileSecurityQuarantineError):
        get_file_for_download(actor=student_enrolled, asset_id=asset.public_id, session=db.session)


def test_admin_can_download_any_file(
    app: Flask, instructor_a: User, admin_user: User, published_course: Course
) -> None:
    """Verify System Administrator has platform-wide access to download files."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"Administrative Oversight File"),
        filename="admin_test.pdf",
        session=db.session,
    )

    _, _, path = get_file_for_download(
        actor=admin_user, asset_id=asset.public_id, session=db.session
    )
    assert path.read_bytes() == b"Administrative Oversight File"


def test_adr002_zero_pk_leakage(app: Flask, instructor_a: User, published_course: Course) -> None:
    """Verify serializers do not leak internal BIGINT PKs or storage paths."""
    asset = store_file_stream(
        actor=instructor_a,
        course_id=published_course.public_id,
        file_stream=io.BytesIO(b"ADR-002 Zero Leakage Payload"),
        filename="zero_leak.pdf",
        session=db.session,
    )

    serialized = _serialize_file_asset(asset)
    assert "asset_id" in serialized
    assert "course_id" in serialized
    # Check no numeric IDs or storage paths
    forbidden_keys = {"id", "blob_id", "file_asset_id", "storage_key", "storage_path"}
    for key in forbidden_keys:
        assert key not in serialized

    # Attach to lesson and verify lesson resource serialization
    lesson = create_lesson(
        instructor_a,
        str(published_course.public_id),
        {
            "title": "Lesson Test ADR-002",
            "position": 1,
            "markdown_content": "# ADR-002 Content",
        },
        session=db.session,
    )
    lr = attach_resource_to_lesson(
        actor=instructor_a,
        lesson_id=lesson.public_id,
        asset_id=asset.public_id,
        session=db.session,
    )

    lr_serialized = _serialize_lesson_resource(lr)
    assert "resource_id" in lr_serialized
    assert uuid.UUID(lr_serialized["resource_id"])  # Valid UUID
    assert "id" not in lr_serialized
    assert "file_asset_id" not in lr_serialized
    assert "lesson_id" in lr_serialized


def test_anti_path_traversal_via_api_download(
    client: FlaskClient, instructor_a: User, published_course: Course
) -> None:
    """Verify that uploading a path-traversal filename sanitizes it in the download header."""
    tokens = create_token_pair(instructor_a)
    token_str = tokens["access_token"] if isinstance(tokens, dict) else tokens.access_token
    headers = {"Authorization": f"Bearer {token_str}"}

    # Upload file with path traversal attempt in filename
    data = {
        "file": (io.BytesIO(b"Traversal Defense Content"), "../../../../etc/passwd.pdf"),
    }
    resp = client.post(
        f"/api/courses/{published_course.public_id}/files",
        data=data,
        content_type="multipart/form-data",
        headers=headers,
    )
    assert resp.status_code == 201
    payload = resp.get_json()
    asset_id = payload["asset_id"]

    # Download file and check Content-Disposition header
    dl_resp = client.get(f"/api/files/{asset_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.data == b"Traversal Defense Content"

    # Header must be clean and not contain ../
    disp = dl_resp.headers.get("Content-Disposition", "")
    assert "passwd.pdf" in disp
    assert ".." not in disp
    assert "/" not in disp
    assert "\\" not in disp
    assert dl_resp.headers.get("X-Content-Type-Options") == "nosniff"
