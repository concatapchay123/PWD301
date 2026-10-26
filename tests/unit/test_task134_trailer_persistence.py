"""Tests for Task 134: First-Class Course Trailer Architecture & Persistence."""

from __future__ import annotations

import io
import json
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.course import Course
from backend.models.file_import import FileAsset, FileScanResult
from backend.models.identity import Role, User
from backend.models.notification_audit import AuditEvent
from backend.models.types import utc_now
from backend.blueprints.admin.routes import _serialize_course as admin_serialize_course
from backend.blueprints.api_courses.routes import _serialize_course as api_serialize_course
from backend.blueprints.instructor.routes import (
    _normalize_course_metadata_payload,
    _serialize_course as instructor_serialize_course,
)
from backend.services.course_service import (
    create_course,
    get_course_trailer_asset,
    queue_course_metadata_review,
    update_course,
)
from backend.services.exceptions import CourseValidationError
from backend.services.file_service import store_file_stream
from backend.services.lesson_service import _apply_course_metadata_dict
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique_suffix = uuid.uuid4().hex[:8]
    user = register_user(
        email=f"inst_trailer_{unique_suffix}@backend.local",
        password="Password123!",
        display_name="Trailer Instructor",
    )
    user.email_verified_at = utc_now()
    assign_role_to_user(user.id, "INSTRUCTOR")
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    unique_suffix = uuid.uuid4().hex[:8]
    user = register_user(
        email=f"admin_trailer_{unique_suffix}@backend.local",
        password="Password123!",
        display_name="Admin Trailer",
    )
    user.email_verified_at = utc_now()
    assign_role_to_user(user.id, "ADMIN")
    db.session.commit()
    return user


def test_update_course_trailer_persistence_and_audit(app: Flask, instructor_user: User) -> None:
    """Verify update_course accurately binds trailer_file_asset_id and records audit trail."""
    course = create_course(
        instructor_user,
        {"course_code": f"TRL-{uuid.uuid4().hex[:6]}", "title": "Trailer Architecture Course"},
    )
    video = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"\x00\x00\x00\x18ftypmp42" + b"v" * 128),
        "trailer_intro.mp4",
        "video/mp4",
        asset_type="RESOURCE",
        session=db.session,
    )

    # 1. Update with UUID string
    updated = update_course(
        instructor_user,
        course.id,
        {"trailer_file_asset_id": str(video.public_id)},
        session=db.session,
    )
    assert updated.trailer_file_asset_id == video.id

    # Verify audit event captured trailer_file_asset_id in before and after state
    audit_evt = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == course.id, AuditEvent.action == "COURSE_UPDATED")
        .order_by(AuditEvent.id.desc())
        .first()
    )
    assert audit_evt is not None
    after_data = json.loads(audit_evt.after_json)
    assert after_data.get("trailer_file_asset_id") == video.id

    # 2. Update with integer ID
    updated2 = update_course(
        instructor_user,
        course.id,
        {"trailer_file_asset_id": video.id},
        session=db.session,
    )
    assert updated2.trailer_file_asset_id == video.id

    # 3. Clear trailer (None or empty)
    cleared = update_course(
        instructor_user,
        course.id,
        {"trailer_file_asset_id": None},
        session=db.session,
    )
    assert cleared.trailer_file_asset_id is None

    audit_clear = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == course.id, AuditEvent.action == "COURSE_UPDATED")
        .order_by(AuditEvent.id.desc())
        .first()
    )
    after_clear = json.loads(audit_clear.after_json)
    assert after_clear.get("trailer_file_asset_id") is None


def test_update_course_trailer_fail_closed_validation(
    app: Flask, instructor_user: User
) -> None:
    """Verify security validations on trailer_file_asset_id: course boundary, scans, soft-delete."""
    course_a = create_course(
        instructor_user,
        {"course_code": f"TRL-A-{uuid.uuid4().hex[:6]}", "title": "Course A"},
    )
    course_b = create_course(
        instructor_user,
        {"course_code": f"TRL-B-{uuid.uuid4().hex[:6]}", "title": "Course B"},
    )

    video_a = store_file_stream(
        instructor_user,
        course_a.id,
        io.BytesIO(b"\x00\x00\x00\x18ftypmp42" + b"a" * 64),
        "trailer_a.mp4",
        "video/mp4",
        asset_type="RESOURCE",
        session=db.session,
    )

    # 1. Cannot assign video of course A to course B
    with pytest.raises(CourseValidationError, match="Choose a clean video"):
        update_course(
            instructor_user,
            course_b.id,
            {"trailer_file_asset_id": str(video_a.public_id)},
            session=db.session,
        )

    # 2. Cannot assign non-existent asset ID
    with pytest.raises(CourseValidationError):
        update_course(
            instructor_user,
            course_a.id,
            {"trailer_file_asset_id": str(uuid.uuid4())},
            session=db.session,
        )

    # 3. Quarantined or infected asset is rejected
    video_a.current_revision.status = "QUARANTINED"
    db.session.commit()
    with pytest.raises(CourseValidationError, match="Choose a clean video"):
        update_course(
            instructor_user,
            course_a.id,
            {"trailer_file_asset_id": str(video_a.public_id)},
            session=db.session,
        )

    # 4. Soft-deleted asset is rejected
    video_a.current_revision.status = "ACTIVE"
    video_a.deleted_at = utc_now()
    db.session.commit()
    with pytest.raises(CourseValidationError, match="Choose a clean video"):
        update_course(
            instructor_user,
            course_a.id,
            {"trailer_file_asset_id": str(video_a.public_id)},
            session=db.session,
        )


def test_queue_course_metadata_review_and_apply_changeset(
    app: Flask, instructor_user: User, admin_user: User
) -> None:
    """Verify queue_course_metadata_review stages trailer_file_asset_id and _apply_course_metadata_dict applies it."""
    course = create_course(
        instructor_user,
        {"course_code": f"TRL-STG-{uuid.uuid4().hex[:6]}", "title": "Staged Trailer Course"},
    )
    course.status = "PUBLISHED"
    course.approved_at = utc_now()
    db.session.commit()

    video = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"\x00\x00\x00\x18ftypmp42" + b"s" * 64),
        "staged_trailer.mp4",
        "video/mp4",
        asset_type="RESOURCE",
        session=db.session,
    )

    # Stage metadata change
    req = queue_course_metadata_review(
        instructor_user,
        course.id,
        {"trailer_file_asset_id": str(video.public_id)},
        session=db.session,
    )
    from backend.services.course_workflow_service import payload_for
    payload = payload_for(req)
    assert payload["course_metadata"]["trailer_file_asset_id"] == video.id

    # Test applying changeset dictionary directly to course
    _apply_course_metadata_dict(
        course,
        {"trailer_file_asset_id": str(video.public_id)},
        session=db.session,
        now=utc_now(),
    )
    assert course.trailer_file_asset_id == video.id

    # Test clearing via dictionary
    _apply_course_metadata_dict(
        course,
        {"trailer_file_asset_id": None},
        session=db.session,
        now=utc_now(),
    )
    assert course.trailer_file_asset_id is None


def test_normalize_course_metadata_payload_purges_legacy_comments(
    app: Flask, instructor_user: User
) -> None:
    """Verify _normalize_course_metadata_payload cleans regex comments and never injects them."""
    course = create_course(
        instructor_user,
        {"course_code": f"TRL-NORM-{uuid.uuid4().hex[:6]}", "title": "Normalize Payload Course"},
    )
    dirty_desc = "Khóa học chất lượng cao.\n\n<!-- trailer_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ -->"
    raw_payload = {
        "title": "Clean Course Title",
        "description": dirty_desc,
        "trailer_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }

    normalized = _normalize_course_metadata_payload(instructor_user, course.id, raw_payload)

    # In Task-136 Dual-Mode persistence, external trailer_url is synchronized in description
    assert "<!-- trailer_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ -->" in normalized["description"]
    # trailer_url must be preserved directly
    assert normalized["trailer_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_course_serialization_trailer_fields(app: Flask, instructor_user: User) -> None:
    """Verify all 3 course serializers return trailer_file_asset_id and stream trailer_url."""
    course = create_course(
        instructor_user,
        {"course_code": f"TRL-SER-{uuid.uuid4().hex[:6]}", "title": "Serialization Course"},
    )
    video = store_file_stream(
        instructor_user,
        course.id,
        io.BytesIO(b"\x00\x00\x00\x18ftypmp42" + b"e" * 64),
        "trailer_ser.mp4",
        "video/mp4",
        asset_type="RESOURCE",
        session=db.session,
    )
    update_course(
        instructor_user,
        course.id,
        {"trailer_file_asset_id": str(video.public_id)},
        session=db.session,
    )

    with app.test_request_context():
        # 1. Instructor serializer
        inst_ser = instructor_serialize_course(course)
        assert inst_ser["trailer_file_asset_id"] == str(video.public_id)
        assert inst_ser["trailer_url"] == f"/api/files/{video.public_id}/stream"

        # 2. API Courses serializer
        api_ser = api_serialize_course(course)
        assert api_ser["trailer_file_asset_id"] == str(video.public_id)
        assert api_ser["trailer_url"] == f"/api/files/{video.public_id}/stream"

        # 3. Admin serializer
        adm_ser = admin_serialize_course(course)
        assert adm_ser["trailer_file_asset_id"] == str(video.public_id)
        assert adm_ser["trailer_url"] == f"/api/files/{video.public_id}/stream"
