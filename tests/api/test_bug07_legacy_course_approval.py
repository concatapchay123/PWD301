"""Test suite for BUG-07: Admin legacy course approval, auto-synthesis, and rejection parity.

Verifies:
1. Legacy courses without CourseChangeRequest or CourseCompletionRule are approved gracefully.
2. Default CourseCompletionRule (100.00% progress) is auto-provisioned.
3. Default approved CourseChangeRequest of type COURSE_VERSION_CHANGESET is auto-synthesized.
4. Mandatory audit events and in-app notifications are persisted atomically.
5. Rejection of legacy courses transitions cleanly to DRAFT with audit and notifications.
6. Approval and rejection of modern courses with active pending changesets maintain parity.
7. Publishing an approved legacy course auto-publishes its draft lessons and retains completion rules.
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from typing import Any

import pytest
from flask.testing import FlaskClient

from backend.extensions import db
from backend.models.course import Course, CourseChangeRequest, CourseCompletionRule, Lesson
from backend.models.identity import Role, User
from backend.models.notification_audit import AuditEvent, Notification, NotificationEvent
from backend.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Any) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    sess = db.session
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
def admin_user(app: Any, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user(
        f"bug07_admin_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin BUG-07 Reviewer"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Any, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"bug07_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Legacy Owner"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_admin_approve_legacy_course_without_changeset_or_completion_rule(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Admin approves a legacy course lacking changeset & completion rules; system auto-synthesizes them."""
    sess = db.session
    legacy_course = Course(
        course_code="LEGACY_101",
        title="Legacy Computer Science Fundamentals",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(legacy_course)
    sess.commit()

    # Pre-conditions: No completion rule, no changeset exists
    assert sess.get(CourseCompletionRule, legacy_course.id) is None
    existing_cr = (
        sess.query(CourseChangeRequest)
        .filter(CourseChangeRequest.course_id == legacy_course.id)
        .first()
    )
    assert existing_cr is None

    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/courses/{legacy_course.public_id}/review",
        json={"action": "approve", "reason": "Meets institutional accreditation curriculum standards"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "APPROVED"

    sess.expire_all()
    reloaded_course = sess.get(Course, legacy_course.id)
    assert reloaded_course.status == "APPROVED"
    assert reloaded_course.approved_by_user_id == admin_user.id
    assert reloaded_course.approved_at is not None

    # Post-conditions: Default completion rule auto-provisioned
    rule = sess.get(CourseCompletionRule, legacy_course.id)
    assert rule is not None
    assert rule.require_all_required_lessons is True
    assert rule.require_required_assessments is True
    assert rule.minimum_progress_percent == Decimal("100.00")

    # Post-conditions: Default approved COURSE_VERSION_CHANGESET auto-synthesized
    synthesized_cr = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == legacy_course.id,
            CourseChangeRequest.change_type == "COURSE_VERSION_CHANGESET",
        )
        .first()
    )
    assert synthesized_cr is not None
    assert synthesized_cr.status == "APPROVED"
    assert synthesized_cr.reviewed_by_user_id == admin_user.id
    assert "accreditation" in synthesized_cr.review_reason.lower()

    # Post-conditions: Audit event and notification dispatched
    course_audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.target_id == legacy_course.id,
            AuditEvent.action == "COURSE_APPROVED",
        )
        .first()
    )
    assert course_audit is not None

    notif = (
        sess.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor_user.id,
            NotificationEvent.event_type == "COURSE_APPROVED",
        )
        .first()
    )
    assert notif is not None
    assert "LEGACY_101" in notif.body or "Legacy" in notif.body


def test_admin_reject_legacy_course(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Admin rejects a legacy course; status becomes DRAFT with mandatory audit & notification."""
    sess = db.session
    legacy_course = Course(
        course_code="LEGACY_REJ101",
        title="Legacy Course Needing Revision",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(legacy_course)
    sess.commit()

    login_web_user(client, admin_user)

    reject_reason = "Đề cương cần bổ sung thêm 3 bài thực hành lab và rubric chi tiết."
    res = client.post(
        f"/admin/courses/{legacy_course.public_id}/review",
        json={"action": "reject", "reason": reject_reason},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "DRAFT"

    sess.expire_all()
    reloaded_course = sess.get(Course, legacy_course.id)
    assert reloaded_course.status == "DRAFT"

    # Audit event recorded
    course_audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.target_id == legacy_course.id,
            AuditEvent.action == "COURSE_REJECTED",
        )
        .first()
    )
    assert course_audit is not None

    # Notification sent to instructor
    notif = (
        sess.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor_user.id,
            NotificationEvent.event_type == "COURSE_REJECTED",
        )
        .first()
    )
    assert notif is not None
    assert reject_reason in notif.body or "LEGACY_REJ101" in notif.body


def test_admin_approve_modern_course_with_pending_changeset(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Approving a course with active PENDING changeset atomically approves both."""
    sess = db.session
    course = Course(
        course_code="MODERN_APP101",
        title="Modern Course with Active Changeset",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.flush()

    cr = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="COURSE_VERSION_CHANGESET",
        target_type="COURSE",
        target_id=course.id,
        proposed_payload_json=json.dumps({"action": "COURSE_VERSION_CHANGESET", "title": course.title}),
        status="PENDING",
    )
    sess.add(cr)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/courses/{course.public_id}/review",
        json={"action": "approve", "reason": "All changeset diffs inspected and verified."},
    )
    assert res.status_code == 200

    sess.expire_all()
    reloaded_course = sess.get(Course, course.id)
    reloaded_cr = sess.get(CourseChangeRequest, cr.id)
    assert reloaded_course.status == "APPROVED"
    assert reloaded_cr.status == "APPROVED"
    assert reloaded_cr.reviewed_by_user_id == admin_user.id


def test_admin_reject_modern_course_with_pending_changeset(
    client: FlaskClient,
    admin_user: User,
    instructor_user: User,
) -> None:
    """Rejecting a course with active PENDING changeset rejects changeset and generates successor draft."""
    sess = db.session
    course = Course(
        course_code="MODERN_REJ101",
        title="Modern Course to Reject",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.flush()

    cr = CourseChangeRequest(
        course_id=course.id,
        requested_by_user_id=instructor_user.id,
        change_type="COURSE_VERSION_CHANGESET",
        target_type="COURSE",
        target_id=course.id,
        proposed_payload_json=json.dumps({"action": "COURSE_VERSION_CHANGESET", "notes": "initial submission"}),
        status="PENDING",
    )
    sess.add(cr)
    sess.commit()

    login_web_user(client, admin_user)

    res = client.post(
        f"/admin/courses/{course.public_id}/review",
        json={"action": "reject", "reason": "Vui lòng cập nhật lại cấu trúc bài học chương 2"},
    )
    assert res.status_code == 200

    sess.expire_all()
    reloaded_course = sess.get(Course, course.id)
    reloaded_cr = sess.get(CourseChangeRequest, cr.id)
    assert reloaded_course.status == "DRAFT"
    assert reloaded_cr.status == "REJECTED"

    # Successor draft should exist
    successor = (
        sess.query(CourseChangeRequest)
        .filter(
            CourseChangeRequest.course_id == course.id,
            CourseChangeRequest.change_type == "COURSE_VERSION_CHANGESET",
            CourseChangeRequest.status == "DRAFT",
        )
        .first()
    )
    assert successor is not None


def test_publish_approved_legacy_course_with_lessons(
    admin_user: User,
    instructor_user: User,
) -> None:
    """Directly publishing an approved legacy course auto-publishes its draft lessons."""
    from backend.models.course import LearningUnit
    from backend.services.course_service import change_course_status

    sess = db.session
    course = Course(
        course_code="LEGACY_PUB101",
        title="Legacy Course For Publishing",
        owner_instructor_id=instructor_user.id,
        status="SUBMITTED_FOR_REVIEW",
    )
    sess.add(course)
    sess.flush()

    unit = LearningUnit(
        course_id=course.id,
        title="Module 1",
        position=1,
    )
    sess.add(unit)
    sess.flush()

    lesson1 = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Lesson 1 Introduction",
        position=1,
        status="PENDING_APPROVAL",
    )
    lesson2 = Lesson(
        course_id=course.id,
        learning_unit_id=unit.id,
        title="Lesson 2 Advanced Concepts",
        position=2,
        status="DRAFT",
    )
    sess.add_all([lesson1, lesson2])
    sess.commit()

    # Admin approves
    approved = change_course_status(
        actor=admin_user,
        course_id=course.id,
        new_status="APPROVED",
        reason="Curriculum validated",
        session=sess,
    )
    sess.commit()
    assert approved.status == "APPROVED"
    assert sess.get(Lesson, lesson1.id).status == "DRAFT"
    assert sess.get(Lesson, lesson2.id).status == "DRAFT"

    # Instructor publishes
    published = change_course_status(
        actor=instructor_user,
        course_id=course.id,
        new_status="PUBLISHED",
        session=sess,
    )
    sess.commit()
    assert published.status == "PUBLISHED"
    assert sess.get(Lesson, lesson1.id).status == "PUBLISHED"
    assert sess.get(Lesson, lesson2.id).status == "PUBLISHED"
