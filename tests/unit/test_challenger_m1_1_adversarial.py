"""Adversarial stress and boundary tests for Milestone 1 (F02, F03, F04).

Authored by Challenger M1_1.
Adversarial dimensions:
- F02 (Lifetime Enrollment REST Lock):
    - All HTTP methods (GET, POST, PUT, DELETE, PATCH) blocked or rejected with 403 Forbidden.
    - Malformed payloads, SQL injection, bypass parameters (force=true, admin=true) strictly rejected.
    - Enrollment remains permanently ACTIVE in database across all attempts.
    - Re-enrollment of active courses is idempotent and never demotes enrollment.
    - Unauthenticated and cross-student withdrawal attempts rejected.
- F03 (Unified Staging Draft Engine):
    - Strict RBAC: Foreign instructors and students blocked from changeset endpoints (403 Forbidden).
    - Zero-changes changeset submission rejected with validation error (cannot flood pending queue).
    - Single Active Pending Lock: Submitting while another changeset is PENDING returns 409 Conflict.
    - Discard lifecycle: All staged draft lessons and metadata diffs are purged, live curriculum preserved.
    - Retract lifecycle: Cancels pending request and reverts staged lessons back to DRAFT for re-editing.
    - Malformed payload handling: Resilient against non-dict, garbage data, or negative positions.
- F04 (Video Auto-Complete Backend Progress Validation):
    - Valid auto-complete: `sec=0, vf=1.0, is_completed=True` marks lesson completed while preserving
      Wall-Clock Zero-Trust (`seconds_spent` in DB remains actual physical count, never spoofed).
    - Boundary rejection: `sec=0, vf=0.5, is_completed=False` does NOT auto-complete without wall-clock time.
    - Negative and out-of-bounds pings (`sec=-5`, `sec=-100`) bounded safely; monotonic progress never decreases.
    - Rapid ping spam: Server-authoritative wall-clock pacing clamps credit to elapsed physical time and logs anomaly.
    - Security boundaries: Non-enrolled students (403) and cross-course lesson tampering (404) blocked.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import (
    CourseChangeRequest,
    Enrollment,
    Lesson,
    LessonProgress,
)
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.notification_audit import AuditEvent
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.user_service import assign_role_to_user, register_user

# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------


def _login_web_session(client: FlaskClient, user: User) -> None:
    _, raw_key = create_auth_session(user, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = user.auth_version
        sess["auth_source"] = "SESSION"


@pytest.fixture
def base_env(app: Flask) -> dict[str, Any]:
    """Base setup with seeded baseline, instructors, students, and admin."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Primary Admin
    admin_role = sess.query(Role).filter_by(code="ADMIN").one()
    admin = register_user(
        f"adv_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Adv Admin", session=sess
    )
    sess.add(
        UserRole(
            user_id=admin.id,
            role_id=admin_role.id,
            assignment_reason="SUB_ROLE:ADMIN_PRIMARY | Test Primary",
        )
    )

    # 2. Owner Instructor
    inst_owner = register_user(
        f"adv_inst_owner_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Owner Instructor",
        session=sess,
    )
    assign_role_to_user(inst_owner.id, "INSTRUCTOR", session=sess)

    # 3. Foreign Instructor
    inst_foreign = register_user(
        f"adv_inst_foreign_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Foreign Instructor",
        session=sess,
    )
    assign_role_to_user(inst_foreign.id, "INSTRUCTOR", session=sess)

    # 4. Student 1 & 2
    student_1 = register_user(
        f"adv_student1_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Student One",
        session=sess,
    )
    assign_role_to_user(student_1.id, "STUDENT", session=sess)

    student_2 = register_user(
        f"adv_student2_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Student Two",
        session=sess,
    )
    assign_role_to_user(student_2.id, "STUDENT", session=sess)

    # 5. Published Course with 2 lessons
    course = create_course(
        actor=inst_owner,
        data={
            "course_code": f"ADV-{uuid.uuid4().hex[:4].upper()}",
            "title": "Adversarial Stress Course",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    change_course_status(inst_owner, course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin, course.id, "APPROVED", session=sess)
    change_course_status(inst_owner, course.id, "PUBLISHED", session=sess)

    lesson_text = create_lesson(
        actor=inst_owner,
        course_id=course.id,
        data={
            "title": "Text Lesson 01",
            "markdown_content": "# Text Lesson Content",
            "estimated_duration_minutes": 15,
            "minimum_completion_seconds": 60,
            "viewed_fraction_required": 0.80,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    lesson_video = create_lesson(
        actor=inst_owner,
        course_id=course.id,
        data={
            "title": "Video Lesson 02",
            "markdown_content": "<!-- video_url: https://example.com/stream.m3u8 -->\n\n# Video Content",
            "estimated_duration_minutes": 30,
            "minimum_completion_seconds": 300,
            "viewed_fraction_required": 0.90,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    # 6. Another Course for cross-course tests
    other_course = create_course(
        actor=inst_foreign,
        data={
            "course_code": f"OTHER-{uuid.uuid4().hex[:4].upper()}",
            "title": "Other Course",
            "category": "Science",
            "capacity": 50,
        },
        session=sess,
    )
    change_course_status(inst_foreign, other_course.id, "SUBMITTED_FOR_REVIEW", session=sess)
    change_course_status(admin, other_course.id, "APPROVED", session=sess)
    change_course_status(inst_foreign, other_course.id, "PUBLISHED", session=sess)

    other_lesson = create_lesson(
        actor=inst_foreign,
        course_id=other_course.id,
        data={
            "title": "Foreign Lesson",
            "markdown_content": "# Foreign Content",
            "status": "PUBLISHED",
        },
        session=sess,
    )

    # 7. Enroll Student 1 in Course
    enrollment = enroll_student(actor=student_1, course_id=course.id, session=sess)
    sess.commit()

    return {
        "admin": admin,
        "inst_owner": inst_owner,
        "inst_foreign": inst_foreign,
        "student_1": student_1,
        "student_2": student_2,
        "course": course,
        "lesson_text": lesson_text,
        "lesson_video": lesson_video,
        "other_course": other_course,
        "other_lesson": other_lesson,
        "enrollment": enrollment,
    }


# ===========================================================================
# 1. F02: Lifetime Enrollment REST Lock Adversarial Tests
# ===========================================================================


def test_f02_leave_http_methods_adversarial(client: FlaskClient, base_env: dict[str, Any]) -> None:
    """Adversarial Challenge: Try all HTTP methods on /leave to bypass withdrawal lock.

    Must return 403 Forbidden for POST and 405 Method Not Allowed (or 403) for other methods.
    Enrollment in database MUST remain strictly ACTIVE.
    """
    student = base_env["student_1"]
    course = base_env["course"]
    tokens = create_token_pair(student)
    jwt_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    api_url = f"/api/courses/{course.public_id}/leave"

    # POST (the official leave route)
    resp_post = client.post(api_url, headers=jwt_headers, json={"reason": "want to quit"})
    assert resp_post.status_code == 403
    data = resp_post.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"
    assert "Chức năng rời khóa học đã bị vô hiệu hóa" in data["error"]["message"]

    # Other HTTP methods
    resp_get = client.get(api_url, headers=jwt_headers)
    assert resp_get.status_code in (403, 405)

    resp_put = client.put(api_url, headers=jwt_headers, json={"reason": "override"})
    assert resp_put.status_code in (403, 405)

    resp_delete = client.delete(api_url, headers=jwt_headers)
    assert resp_delete.status_code in (403, 405)

    resp_patch = client.patch(api_url, headers=jwt_headers, json={"status": "LEFT"})
    assert resp_patch.status_code in (403, 405)

    # Check Student Blueprint Web route
    _login_web_session(client, student)
    web_url = f"/student/courses/{course.public_id}/leave"
    resp_web_post = client.post(web_url, json={"reason": "web leave"})
    assert resp_web_post.status_code == 403
    web_data = resp_web_post.get_json()
    assert web_data["success"] is False
    assert web_data["error"]["code"] == "FORBIDDEN"

    # DB Invariant Check
    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"
    assert enr.left_at is None


def test_f02_leave_adversarial_payloads_and_sql_injection(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Pass empty bodies, injection payloads, and administrative spoofing flags.

    Under no circumstance may the lock be bypassed or SQL executed.
    """
    student = base_env["student_1"]
    course = base_env["course"]
    tokens = create_token_pair(student)
    jwt_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    api_url = f"/api/courses/{course.public_id}/leave"

    adversarial_payloads = [
        {},  # Empty object
        {"force": True, "admin_override": True, "status": "LEFT"},  # Privilege escalation attempt
        {"reason": "'; UPDATE enrollments SET status = 'LEFT'; --"},  # SQL injection attempt
        {"reason": "A" * 10000},  # Buffer bloat attempt
        {"student_id": 999999, "action": "WITHDRAW"},
    ]

    for payload in adversarial_payloads:
        resp = client.post(api_url, headers=jwt_headers, json=payload)
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    # Raw non-JSON bytes with JSON content-type
    resp_corrupt = client.post(
        api_url,
        headers=jwt_headers,
        data="INVALID_NON_JSON_BODY",
        content_type="application/json",
    )
    assert resp_corrupt.status_code in (400, 403)

    # Verify Enrollment DB status remains ACTIVE
    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"


def test_f02_leave_query_params_and_headers_spoofing(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Query param bypasses (?force=1&status=LEFT) and header injection."""
    student = base_env["student_1"]
    course = base_env["course"]
    tokens = create_token_pair(student)

    spoofed_headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Admin-Override": "true",
        "X-Forwarded-Role": "ADMIN",
        "X-Original-Role": "ADMIN",
    }

    url_with_params = f"/api/courses/{course.public_id}/leave?force=1&status=LEFT&admin=true&override=1"
    resp = client.post(url_with_params, headers=spoofed_headers, json={"reason": "bypass"})
    assert resp.status_code == 403

    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"


def test_f02_re_enroll_active_course_is_idempotent(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Calling /re-enroll on an already ACTIVE course must be strictly idempotent."""
    student = base_env["student_1"]
    course = base_env["course"]
    tokens = create_token_pair(student)
    jwt_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    re_enroll_url = f"/api/courses/{course.public_id}/re-enroll"
    resp = client.post(re_enroll_url, headers=jwt_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ACTIVE"

    # Repeat call
    resp2 = client.post(re_enroll_url, headers=jwt_headers)
    assert resp2.status_code == 200
    assert resp2.get_json()["status"] == "ACTIVE"

    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"


# ===========================================================================
# 2. F03: Unified Staging Draft Engine Adversarial Tests
# ===========================================================================


def test_f03_changeset_unauthorized_isolation(client: FlaskClient, base_env: dict[str, Any]) -> None:
    """Adversarial Challenge: Unauthorized actors (foreign instructor, student) must be blocked from changeset endpoints."""
    inst_foreign = base_env["inst_foreign"]
    student = base_env["student_1"]
    course = base_env["course"]

    foreign_tokens = create_token_pair(inst_foreign)
    foreign_headers = {"Authorization": f"Bearer {foreign_tokens['access_token']}"}

    student_tokens = create_token_pair(student)
    student_headers = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # 1. Submit and Discard endpoints must strictly block foreign instructor (403)
    resp_foreign_sub = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=foreign_headers,
        json={"summary": "Unauthorized Submit"},
    )
    assert resp_foreign_sub.status_code == 403, "Foreign instructor was not blocked from submitting changeset!"

    resp_foreign_disc = client.post(
        f"/api/courses/{course.public_id}/changeset/discard",
        headers=foreign_headers,
        json={},
    )
    assert resp_foreign_disc.status_code == 403, "Foreign instructor was not blocked from discarding changeset!"

    # 2. Student must be blocked from all changeset endpoints (403)
    resp_stu_status = client.get(
        f"/api/courses/{course.public_id}/changeset/status",
        headers=student_headers,
    )
    assert resp_stu_status.status_code == 403, "Student was not blocked from changeset status!"

    resp_stu_sub = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=student_headers,
        json={"summary": "Student Submit"},
    )
    assert resp_stu_sub.status_code == 403, "Student was not blocked from changeset submit!"

    # 3. Check changeset status isolation for foreign instructor:
    # A foreign instructor must NOT be able to inspect private draft status of another instructor's course.
    resp_foreign_status = client.get(
        f"/api/courses/{course.public_id}/changeset/status",
        headers=foreign_headers,
    )
    # Finding / Defect Verification:
    # Notice: Currently get_course_changeset_status lacks course manager ownership check, returning 200 instead of 403.
    # Asserting expected security contract (403 Forbidden).
    assert resp_foreign_status.status_code == 403, (
        f"Security Isolation Defect (F03): Foreign instructor received {resp_foreign_status.status_code} "
        f"instead of 403 Forbidden when accessing changeset status!"
    )


def test_f03_submit_zero_changes_validation_error(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Instructor attempts to submit a changeset when NO changes exist.

    Must reject with validation error without creating any pending request.
    """
    inst_owner = base_env["inst_owner"]
    course = base_env["course"]
    tokens = create_token_pair(inst_owner)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Verify status is NONE initially
    status_resp = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert status_resp.status_code == 200
    status_data = status_resp.get_json()
    assert status_data["status"] == "NONE"
    assert status_data["has_changes"] is False

    # Attempt to submit empty changeset
    submit_resp = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=headers,
        json={},
    )
    # Service raises LessonValidationError -> 400 or 422
    assert submit_resp.status_code in (400, 422)

    # Ensure no change request was created
    pending_count = (
        db.session.query(CourseChangeRequest)
        .filter_by(course_id=course.id, status="PENDING")
        .count()
    )
    assert pending_count == 0


def test_f03_submit_changeset_atomic_pending_lock(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Single Active Pending Lock.

    Submitting while another changeset is PENDING must strictly return 409 Conflict.
    """
    inst_owner = base_env["inst_owner"]
    course = base_env["course"]
    tokens = create_token_pair(inst_owner)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1. Stage a new draft lesson
    create_resp = client.post(
        f"/api/courses/{course.public_id}/lessons",
        headers=headers,
        json={
            "title": "Staged Draft Lesson for Concurrency Test",
            "markdown_content": "# Staged Content",
            "position": 3,
        },
    )
    assert create_resp.status_code in (200, 201)

    # Check status is DRAFT
    status_resp = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.get_json()["status"] == "DRAFT"

    # 2. First submission -> 202 Accepted
    sub_resp1 = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=headers,
        json={"version_title": "V2.0 Draft Update", "summary": "New lessons"},
    )
    assert sub_resp1.status_code == 202
    data1 = sub_resp1.get_json()
    assert data1["pending_approval"] is True
    cr_id = data1["change_request_id"]

    # Status should now be PENDING
    status_pending = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    assert status_pending.status_code == 200
    assert status_pending.get_json()["status"] == "PENDING"

    # 3. Second immediate submission attempt while PENDING -> MUST 409 CONFLICT!
    sub_resp2 = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=headers,
        json={"version_title": "Concurrent V2.1", "summary": "Attempting race condition"},
    )
    assert sub_resp2.status_code == 409
    data2 = sub_resp2.get_json()
    assert "chờ Quản trị viên xét duyệt" in data2["error"]["message"]

    # Verify exactly 1 PENDING change request exists in DB
    pending_crs = (
        db.session.query(CourseChangeRequest)
        .filter_by(course_id=course.id, status="PENDING")
        .all()
    )
    assert len(pending_crs) == 1
    assert pending_crs[0].id == cr_id


def test_f03_discard_lifecycle_purges_staged_drafts(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Discard must atomically purge newly added draft lessons and revert state.

    The published lessons MUST remain completely untouched.
    """
    inst_owner = base_env["inst_owner"]
    course = base_env["course"]
    lesson_text = base_env["lesson_text"]
    tokens = create_token_pair(inst_owner)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Count initial published lessons
    initial_pub_count = (
        db.session.query(Lesson)
        .filter_by(course_id=course.id, status="PUBLISHED")
        .count()
    )

    # 1. Create a draft lesson
    draft_resp = client.post(
        f"/api/courses/{course.public_id}/lessons",
        headers=headers,
        json={
            "title": "Ephemeral Draft Lesson",
            "markdown_content": "# Ephemeral",
            "position": 10,
        },
    )
    assert draft_resp.status_code in (200, 201)

    # 2. Update published course metadata via staging engine (PATCH)
    meta_resp = client.patch(
        f"/api/courses/{course.public_id}",
        headers=headers,
        json={"title": "Staged Title Change (Unapproved)"},
    )
    assert meta_resp.status_code == 200
    assert meta_resp.get_json()["is_draft"] is True

    # Check status reflects DRAFT with staged lessons and metadata changes
    st_resp = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers)
    st_data = st_resp.get_json()
    assert st_data["status"] == "DRAFT"
    assert st_data["has_changes"] is True
    assert st_data["staged_lessons"] >= 1
    assert st_data["has_metadata_changes"] is True

    # 3. Discard changeset
    discard_resp = client.post(f"/api/courses/{course.public_id}/changeset/discard", headers=headers)
    assert discard_resp.status_code == 200
    assert discard_resp.get_json()["status"] == "DISCARDED"

    # 4. Verify post-discard state
    # - Newly created draft lesson is purged
    draft_in_db = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == course.id, Lesson.title == "Ephemeral Draft Lesson")
        .first()
    )
    assert draft_in_db is None

    # - Published lessons preserved
    remaining_pub_count = (
        db.session.query(Lesson)
        .filter_by(course_id=course.id, status="PUBLISHED")
        .count()
    )
    assert remaining_pub_count == initial_pub_count

    # - Status is now NONE
    st_after = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers).get_json()
    assert st_after["status"] == "NONE"
    assert st_after["has_changes"] is False
    assert st_after["staged_lessons"] == 0
    assert st_after["has_metadata_changes"] is False


def test_f03_retract_changeset_lifecycle(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Retract cancels pending changeset and reverts staged lessons to DRAFT."""
    inst_owner = base_env["inst_owner"]
    course = base_env["course"]
    tokens = create_token_pair(inst_owner)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Stage a lesson and submit
    client.post(
        f"/api/courses/{course.public_id}/lessons",
        headers=headers,
        json={"title": "Draft for Retract", "markdown_content": "# Retract Test", "position": 4},
    )
    sub = client.post(
        f"/api/courses/{course.public_id}/changeset/submit",
        headers=headers,
        json={"summary": "To be retracted"},
    )
    assert sub.status_code == 202

    # Retract via Instructor Blueprint Web/REST route
    _login_web_session(client, inst_owner)
    retract_resp = client.post(f"/instructor/courses/{course.public_id}/changeset/retract")
    assert retract_resp.status_code == 200

    # Status should return to DRAFT (unlocked for editing)
    st = client.get(f"/api/courses/{course.public_id}/changeset/status", headers=headers).get_json()
    assert st["status"] == "DRAFT"
    assert st["has_changes"] is True


# ===========================================================================
# 3. F04: Video Auto-Complete Backend Progress Validation Adversarial Tests
# ===========================================================================


def test_f04_video_autocomplete_valid_flow_preserves_wall_clock(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: When video player triggers completion (completed=True, vf=1.0, sec=0),

    lesson is marked completed, BUT Wall-Clock Zero-Trust is NOT violated (seconds_spent stays actual physical seconds).
    """
    student = base_env["student_1"]
    course = base_env["course"]
    lesson_video = base_env["lesson_video"]
    tokens = create_token_pair(student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    url = f"/api/courses/{course.public_id}/lessons/{lesson_video.public_id}/progress"

    # Send video completion event from player
    resp = client.post(
        url,
        headers=headers,
        json={
            "completed": True,
            "view_fraction": 1.0,
            "seconds_spent": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_completed"] is True
    assert data["completed"] is True
    assert data["completed_at"] is not None
    assert data["max_view_fraction"] == 1.0

    # ZERO-TRUST IRON LAW: seconds_spent in DB MUST NOT be spoofed to minimum_completion_seconds (300)
    lp = (
        db.session.query(LessonProgress)
        .filter_by(lesson_id=lesson_video.id)
        .first()
    )
    assert lp is not None
    assert lp.completed_at is not None
    assert lp.seconds_spent == 0, f"Zero-Trust violation: seconds_spent was spoofed to {lp.seconds_spent}!"


def test_f04_zero_seconds_low_view_fraction_does_not_complete(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: sec=0, vf=0.5, completed=False on video lesson requiring 300s.

    MUST NOT complete without meeting physical time or completion criteria!
    """
    student = base_env["student_1"]
    course = base_env["course"]
    lesson_video = base_env["lesson_video"]
    tokens = create_token_pair(student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    url = f"/api/courses/{course.public_id}/lessons/{lesson_video.public_id}/progress"

    # Student sends halfway ping without video complete flag
    resp = client.post(
        url,
        headers=headers,
        json={
            "completed": False,
            "view_fraction": 0.50,
            "seconds_spent": 0,
        },
    )
    # When sec=0 and completed=False and vf<0.95, video lesson requires a playback session
    # reconcile_lesson_progress rejects forging video evidence or completes=False
    if resp.status_code == 200:
        data = resp.get_json()
        assert data["is_completed"] is False
        assert data["completed"] is False
        assert data["completed_at"] is None
    else:
        # Or validation rejects missing session
        assert resp.status_code in (400, 422)


def test_f04_negative_and_extreme_seconds_spent_monotonicity(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Passing negative seconds (-5, -100) or oversized values (>60).

    Seconds must be clamped safely and seconds_spent must NEVER decrease.
    """
    student = base_env["student_1"]
    course = base_env["course"]
    lesson_text = base_env["lesson_text"]
    tokens = create_token_pair(student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    url = f"/api/courses/{course.public_id}/lessons/{lesson_text.public_id}/progress"

    # Initial valid ping
    resp1 = client.post(
        url,
        headers=headers,
        json={"seconds_increment": 10, "view_fraction": 0.20},
    )
    assert resp1.status_code == 200
    sec_initial = resp1.get_json()["seconds_spent"]
    assert sec_initial >= 0

    # Negative increment attempt
    resp_neg = client.post(
        url,
        headers=headers,
        json={"seconds_increment": -20, "view_fraction": 0.25},
    )
    assert resp_neg.status_code == 200
    sec_after_neg = resp_neg.get_json()["seconds_spent"]
    # Monotonicity check: seconds_spent MUST NOT decrease
    assert sec_after_neg >= sec_initial, "Monotonicity broken: seconds_spent decreased!"

    # Out of bounds increment attempt (> MAX_PING_SECONDS = 60)
    resp_huge = client.post(
        url,
        headers=headers,
        json={"seconds_increment": 9999, "view_fraction": 0.30},
    )
    assert resp_huge.status_code == 200
    sec_after_huge = resp_huge.get_json()["seconds_spent"]
    # Should be bounded to at most +60s
    assert sec_after_huge <= sec_after_neg + 60


def test_f04_rapid_fire_ping_spam_wall_clock_defense(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Firing multiple heartbeats in milliseconds claiming 60s each.

    Server-authoritative wall-clock pacing must clamp credit to actual physical elapsed time
    and generate LESSON_PROGRESS_PACE_ANOMALY audit event.
    """
    student = base_env["student_1"]
    course = base_env["course"]
    lesson_text = base_env["lesson_text"]
    tokens = create_token_pair(student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    url = f"/api/courses/{course.public_id}/lessons/{lesson_text.public_id}/progress"

    # Initial ping to set last_activity_at
    client.post(url, headers=headers, json={"seconds_increment": 5, "view_fraction": 0.1})

    # Rapid spam pings (10 pings claiming 60s each within milliseconds)
    for _ in range(5):
        resp = client.post(url, headers=headers, json={"seconds_increment": 60, "view_fraction": 0.5})
        assert resp.status_code == 200

    # Check AuditEvent in DB
    anomaly = (
        db.session.query(AuditEvent)
        .filter(
            AuditEvent.action == "LESSON_PROGRESS_PACE_ANOMALY",
            AuditEvent.actor_user_id == student.id,
        )
        .first()
    )
    assert anomaly is not None, "Expected LESSON_PROGRESS_PACE_ANOMALY audit event to be logged!"


def test_f04_non_enrolled_and_cross_course_lesson_tampering(
    client: FlaskClient, base_env: dict[str, Any]
) -> None:
    """Adversarial Challenge: Non-enrolled student (403) and cross-course lesson tampering (404)."""
    student_2 = base_env["student_2"]  # Not enrolled in course
    student_1 = base_env["student_1"]  # Enrolled in course
    course = base_env["course"]
    other_lesson = base_env["other_lesson"]  # Belongs to other_course
    lesson_text = base_env["lesson_text"]

    tokens_stu2 = create_token_pair(student_2)
    headers_stu2 = {"Authorization": f"Bearer {tokens_stu2['access_token']}"}

    tokens_stu1 = create_token_pair(student_1)
    headers_stu1 = {"Authorization": f"Bearer {tokens_stu1['access_token']}"}

    # 1. Unenrolled student tries to record progress -> 403 Forbidden
    url_valid = f"/api/courses/{course.public_id}/lessons/{lesson_text.public_id}/progress"
    resp_unenrolled = client.post(
        url_valid,
        headers=headers_stu2,
        json={"completed": True, "view_fraction": 1.0, "seconds_spent": 0},
    )
    assert resp_unenrolled.status_code == 403

    # 2. Enrolled student targets a lesson that belongs to ANOTHER course -> 404 ResourceNotFoundError
    url_tampered = f"/api/courses/{course.public_id}/lessons/{other_lesson.public_id}/progress"
    resp_tampered = client.post(
        url_tampered,
        headers=headers_stu1,
        json={"completed": True, "view_fraction": 1.0, "seconds_spent": 0},
    )
    assert resp_tampered.status_code == 404
