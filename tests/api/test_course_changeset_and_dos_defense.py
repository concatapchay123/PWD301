"""Test suite for Course Version Changeset & Anti-DoS Queue Defense.

Tests:
1. Rate Limiter: Repeated rapid curriculum mutation requests (>15 req/60s) trigger HTTP 429.
2. Changeset Submission: Submitting a changeset creates 1 CourseChangeRequest in PENDING status.
3. Single Active Pending Lock: Submitting another changeset while one is PENDING triggers HTTP 409.
4. Retract Mechanism: Instructor can retract a PENDING changeset (transitions to CANCELLED).
5. Admin Atomic Approval: Admin approves changeset in 1 transaction; changes are committed.
6. Admin Rejection: Admin rejecting requires a reason (min 5 chars) and marks request REJECTED.
"""

from __future__ import annotations

import json
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, CourseChangeRequest, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification, NotificationEvent
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_learning_unit, create_lesson
from pwd301.services.rate_limit_service import reset_all_rate_limits
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture(autouse=True)
def clean_rate_limits():
    """Ensure clean rate limiting state before each test."""
    reset_all_rate_limits()
    yield
    reset_all_rate_limits()


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
    """Create an instructor user."""
    email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Defense Test")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create an administrator user with COURSE_REVIEW permissions."""
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Admin Defense Test")
    adm = assign_role_to_user(u.id, "ADMIN")
    adm.admin_permissions = "COURSE_REVIEW,INSTRUCTOR_REVIEW"
    db.session.commit()
    return adm


@pytest.fixture
def published_course(app: Flask, instructor_user: User) -> Course:
    """Create a published course with learning units and lessons."""
    sess: Session = db.session
    c = create_course(
        instructor_user,
        {
            "course_code": f"DOS-{uuid.uuid4().hex[:6].upper()}",
            "title": f"Course Defense {uuid.uuid4().hex[:6]}",
            "description": "Test published course for DoS defense",
            "category": "Security",
            "difficulty": "INTERMEDIATE",
        },
        session=sess,
    )
    c.status = "PUBLISHED"
    sess.flush()

    u1 = create_learning_unit(instructor_user, c.id, {"title": "Chương 1"}, session=sess)
    create_lesson(
        instructor_user,
        c.id,
        {
            "learning_unit_id": str(u1.public_id),
            "title": "Bài 1",
            "markdown_content": "Nội dung bài 1",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    create_lesson(
        instructor_user,
        c.id,
        {
            "learning_unit_id": str(u1.public_id),
            "title": "Bài 2",
            "markdown_content": "Nội dung bài 2",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    create_lesson(
        instructor_user,
        c.id,
        {
            "learning_unit_id": str(u1.public_id),
            "title": "Bài 3",
            "markdown_content": "Nội dung bài 3",
            "status": "PUBLISHED",
        },
        session=sess,
    )
    sess.commit()
    return c


def test_rate_limit_exceeded_on_spam_reorder(
    client: FlaskClient,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Spamming reorder requests (>15 req/60s) must trigger HTTP 429 Too Many Requests."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons
    ordered_ids = [str(les.public_id) for les in lessons]

    # Send 15 valid requests within limits
    for i in range(15):
        resp = client.post(
            f"/instructor/courses/{cid}/lessons/reorder",
            json={"ordered_lesson_ids": ordered_ids},
        )
        assert resp.status_code in (200, 202), (
            f"Request {i + 1} failed with status {resp.status_code}"
        )

    # 16th request must trigger HTTP 429
    resp_overflow = client.post(
        f"/instructor/courses/{cid}/lessons/reorder",
        json={"ordered_lesson_ids": ordered_ids},
    )
    assert resp_overflow.status_code == 429
    assert resp_overflow.is_json
    err = resp_overflow.get_json()["error"]
    assert err["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp_overflow.headers


def test_submit_changeset_and_single_active_pending_lock(
    client: FlaskClient,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Submitting a changeset creates 1 PENDING request; submitting again returns HTTP 409."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons

    payload = {
        "version_title": "Đợt cập nhật Học kỳ I",
        "summary": "Đổi vị trí bài giảng",
        "reorder_plan": {
            "lessons_order": [
                {"lesson_id": str(lessons[1].public_id), "position": 1},
                {"lesson_id": str(lessons[0].public_id), "position": 2},
                {"lesson_id": str(lessons[2].public_id), "position": 3},
            ]
        },
        "added_lessons": [],
        "modified_lessons": [],
        "deleted_lessons": [],
    }

    # 1. First submission succeeds (HTTP 201 or 202)
    resp1 = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    assert resp1.status_code in (201, 202)
    res_data = resp1.get_json()
    assert res_data["status"] == "pending_approval"
    cr_id = res_data["change_request_id"]
    assert cr_id is not None

    # Check status endpoint returns PENDING
    status_resp = client.get(f"/instructor/courses/{cid}/changeset/status")
    assert status_resp.status_code == 200
    st_data = status_resp.get_json()
    assert st_data["status"] == "PENDING"
    assert st_data["change_request_id"] == cr_id

    # 2. Second submission while PENDING must fail with HTTP 409 Conflict
    resp2 = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    assert resp2.status_code == 409
    err = resp2.get_json()["error"]
    assert err["code"] == "CONFLICT"
    assert "chờ Quản trị viên" in err["message"]


def test_retract_changeset_allows_resubmit(
    client: FlaskClient,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Instructor can retract a PENDING changeset, unblocking subsequent submission."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons

    payload = {
        "version_title": "Bản nháp cần sửa",
        "reorder_plan": {
            "lessons_order": [
                {"lesson_id": str(lessons[1].public_id), "position": 1},
                {"lesson_id": str(lessons[0].public_id), "position": 2},
            ]
        },
    }

    # Submit
    client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)

    # Retract
    resp_retract = client.post(f"/instructor/courses/{cid}/changeset/retract")
    assert resp_retract.status_code == 200
    assert resp_retract.get_json()["status"] == "CANCELLED"

    # Status check confirms CANCELLED or NONE
    status_resp = client.get(f"/instructor/courses/{cid}/changeset/status")
    assert status_resp.status_code == 200
    assert status_resp.get_json()["status"] in ("CANCELLED", "NONE")

    # Now submitting new changeset succeeds without 409
    resp_resubmit = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    assert resp_resubmit.status_code in (201, 202)
    assert resp_resubmit.get_json()["status"] == "pending_approval"


def test_admin_approve_changeset_atomic_commit(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """Admin approves changeset in 1 atomic transaction applying reorder and added lessons."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons
    u1 = published_course.learning_units[0]

    payload = {
        "version_title": "Phiên bản Hoàn Chỉnh",
        "reorder_plan": {
            "lessons_order": [
                {"lesson_id": str(lessons[2].public_id), "position": 1},
                {"lesson_id": str(lessons[0].public_id), "position": 2},
                {"lesson_id": str(lessons[1].public_id), "position": 3},
            ]
        },
        "added_lessons": [
            {
                "learning_unit_id": str(u1.public_id),
                "title": "Bài 4 Mới Thêm",
                "markdown_content": "Nội dung bài 4 mới toanh",
                "estimated_duration_minutes": 20,
            }
        ],
        "modified_lessons": [
            {
                "lesson_id": str(lessons[0].public_id),
                "title": "Bài 1 (Đã Chỉnh Sửa)",
                "markdown_content": "Nội dung bài 1 cập nhật mới",
            }
        ],
        "deleted_lessons": [],
    }

    # Submit as instructor
    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    assert res_sub.status_code in (201, 202)
    cr_id = res_sub.get_json()["change_request_id"]
    submitted_key = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-change:{cr_id}:COURSE_CHANGE_REQUESTED:{admin_user.id}",
    )
    assert (
        db.session.query(NotificationEvent)
        .filter(NotificationEvent.event_key == submitted_key)
        .one()
        .event_type
        == "COURSE_CHANGE_REQUESTED"
    )

    # Login as Admin and Approve
    login_web_user(client, admin_user)
    resp_approve = client.post(
        f"/admin/change-requests/{cr_id}/review",
        json={"action": "approve", "reason": "Phê duyệt đợt cập nhật hoàn chỉnh"},
    )
    assert resp_approve.status_code == 200
    approved_key = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:course-change:{cr_id}:COURSE_CHANGE_APPROVED:{instructor_user.id}",
    )
    assert (
        db.session.query(NotificationEvent)
        .filter(NotificationEvent.event_key == approved_key)
        .one()
        .event_type
        == "COURSE_CHANGE_APPROVED"
    )

    # Verify changes applied to database
    db.session.expire_all()
    updated_lessons = (
        db.session.query(Lesson)
        .filter(Lesson.course_id == published_course.id, Lesson.deleted_at.is_(None))
        .order_by(Lesson.position.asc())
        .all()
    )
    # Total active lessons should be 4
    active_published = [les for les in updated_lessons if les.status == "PUBLISHED"]
    assert len(active_published) == 4
    # Check new positions
    pos_map = {les.title: les.position for les in active_published}
    assert pos_map["Bài 3"] == 1
    assert pos_map["Bài 1 (Đã Chỉnh Sửa)"] == 2
    assert pos_map["Bài 2"] == 3
    assert pos_map["Bài 4 Mới Thêm"] == 4


def test_admin_reject_changeset_requires_reason(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """Admin rejecting requires at least 5 chars reason; successfully marks REJECTED."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)

    payload = {"version_title": "Bản Nháp Thử Nghiệm"}
    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    cr_id = res_sub.get_json()["change_request_id"]

    login_web_user(client, admin_user)

    # 1. Reject without reason or <5 chars fails with 400
    resp_bad = client.post(
        f"/admin/change-requests/{cr_id}/review",
        json={"action": "reject", "reason": "Lỗi"},
    )
    assert resp_bad.status_code == 400

    # 2. Reject with valid reason succeeds
    resp_ok = client.post(
        f"/admin/change-requests/{cr_id}/review",
        json={"action": "reject", "reason": "Cần bổ sung thêm ví dụ thực tế cho bài học."},
    )
    assert resp_ok.status_code == 200

    # Check status is REJECTED
    cr = db.session.get(CourseChangeRequest, cr_id)
    assert cr.status == "REJECTED"
    assert cr.review_reason == "Cần bổ sung thêm ví dụ thực tế cho bài học."


def test_dedicated_reject_changeset_uses_public_course_identity(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """Dedicated rejection notifications must not expose the internal course PK."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    res_sub = client.post(
        f"/instructor/courses/{cid}/changeset/submit",
        json={"version_title": "Bản Nháp Không Lộ ID"},
    )
    assert res_sub.status_code in (201, 202)
    cr_id = res_sub.get_json()["change_request_id"]

    login_web_user(client, admin_user)
    response = client.post(
        f"/admin/course-changes/{cr_id}/reject",
        json={"reason": "Cần bổ sung ví dụ minh họa trước khi áp dụng."},
    )
    assert response.status_code == 200

    notification = (
        db.session.query(Notification)
        .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
        .filter(
            Notification.recipient_user_id == instructor_user.id,
            NotificationEvent.event_type == "COURSE_CHANGE_REJECTED",
        )
        .order_by(Notification.id.desc())
        .first()
    )
    assert notification is not None
    assert notification.title == (
        f"Đợt cập nhật khóa học {published_course.course_code} cần chỉnh sửa lại"
    )
    assert f"#{published_course.id}" not in notification.title

    payload = json.loads(notification.event.payload_json)
    assert payload["course_id"] == str(published_course.public_id)
    assert payload["action_url"] == (f"#/instructor/courses/manage?id={published_course.public_id}")
    assert payload["action_url"] != f"#/instructor/courses/manage?id={published_course.id}"


def test_discard_changeset_cancels_pending_request(
    client: FlaskClient,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Instructor can discard working draft/changeset, cancelling any pending request."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)

    payload = {"version_title": "Bản Nháp Sẽ Hủy"}
    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    assert res_sub.status_code in (201, 202)
    cr_id = res_sub.get_json()["change_request_id"]

    # Discard
    resp_disc = client.post(f"/instructor/courses/{cid}/changeset/discard")
    assert resp_disc.status_code == 200
    assert resp_disc.get_json()["status"] == "DISCARDED"

    cr = db.session.get(CourseChangeRequest, cr_id)
    assert cr.status == "CANCELLED"


def test_admin_course_changes_diff_and_dedicated_endpoints(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """Admin can inspect changeset diff and approve/reject via dedicated /admin/course-changes/... routes."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons

    payload = {
        "version_title": "Đợt Cập Nhật Tháng 10",
        "summary": "Tối ưu hóa thứ tự",
        "reorder_plan": {
            "lessons_order": [
                {"lesson_id": str(lessons[1].public_id), "position": 1},
                {"lesson_id": str(lessons[0].public_id), "position": 2},
            ]
        },
        "added_lessons": [
            {
                "title": "Bài Thực Hành Mới",
                "markdown_content": "# Thực hành...",
                "position": 3,
            }
        ],
        "modified_lessons": [],
        "deleted_lessons": [],
    }

    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    cr_id = res_sub.get_json()["change_request_id"]

    login_web_user(client, admin_user)

    # 1. Test GET /admin/course-changes/<id>/diff
    resp_diff = client.get(f"/admin/course-changes/{cr_id}/diff")
    assert resp_diff.status_code == 200
    diff_data = resp_diff.get_json()
    assert diff_data["change_request_id"] == cr_id
    assert diff_data["version_title"] == "Đợt Cập Nhật Tháng 10"
    assert "live_curriculum" in diff_data
    assert "proposed_curriculum" in diff_data
    assert diff_data["changeset_stats"]["added_lessons_count"] == 1

    # Also test alias /admin/courses/<cid>/changeset/diff
    resp_diff_alias = client.get(f"/admin/courses/{cid}/changeset/diff")
    assert resp_diff_alias.status_code == 200

    # 2. Test dedicated approve endpoint: POST /admin/course-changes/<id>/approve
    resp_appr = client.post(
        f"/admin/course-changes/{cr_id}/approve",
        json={"reason": "Phê duyệt thông qua dedicated endpoint."},
    )
    assert resp_appr.status_code == 200
    assert resp_appr.get_json()["status"] == "APPROVED"

    cr = db.session.get(CourseChangeRequest, cr_id)
    assert cr.status == "APPROVED"


def test_admin_course_changes_dedicated_reject_validation(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """Dedicated reject endpoint validates reason length >= 5 chars."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)

    payload = {"version_title": "Đợt Sửa Lỗi Nhỏ"}
    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    cr_id = res_sub.get_json()["change_request_id"]

    login_web_user(client, admin_user)

    # Short reason (<5 chars) must return 400
    resp_short = client.post(
        f"/admin/course-changes/{cr_id}/reject",
        json={"reason": "Ko"},
    )
    assert resp_short.status_code == 400

    # Valid reason
    resp_ok = client.post(
        f"/admin/course-changes/{cr_id}/reject",
        json={"reason": "Cần hoàn thiện thêm nội dung video hướng dẫn."},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["status"] == "REJECTED"


def test_learner_progress_preserved_after_changeset_approval(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    published_course: Course,
) -> None:
    """LESSON-001 Invariant: Enrolled student progress is preserved 100% when lessons are reordered."""
    from pwd301.models.course import EnrollmentPeriod, LessonProgress
    from pwd301.services.enrollment_service import enroll_student

    # Create and enroll a student
    sess = db.session
    student_user = register_user(
        f"student_{uuid.uuid4().hex[:8]}@example.com",
        "Password@123",
        "Student Progress Test",
    )
    assign_role_to_user(student_user.id, "STUDENT")

    enrollment = enroll_student(student_user, published_course.id, session=sess)
    period = (
        sess.query(EnrollmentPeriod).filter(EnrollmentPeriod.enrollment_id == enrollment.id).first()
    )
    assert period is not None
    first_lesson = published_course.lessons[0]

    # Mark first lesson completed
    prog = LessonProgress(
        enrollment_period_id=period.id,
        lesson_id=first_lesson.id,
        completed_at=db.func.now(),
        last_activity_at=db.func.now(),
        seconds_spent=100,
    )
    sess.add(prog)
    sess.commit()

    # Instructor submits changeset reordering first lesson from pos 1 to pos 3
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    lessons = published_course.lessons

    payload = {
        "version_title": "Đổi vị trí nhưng giữ tiến độ học viên",
        "reorder_plan": {
            "lessons_order": [
                {"lesson_id": str(lessons[1].public_id), "position": 1},
                {"lesson_id": str(lessons[2].public_id), "position": 2},
                {"lesson_id": str(lessons[0].public_id), "position": 3},
            ]
        },
    }
    res_sub = client.post(f"/instructor/courses/{cid}/changeset/submit", json=payload)
    cr_id = res_sub.get_json()["change_request_id"]

    # Admin approves
    login_web_user(client, admin_user)
    resp_appr = client.post(
        f"/admin/course-changes/{cr_id}/approve",
        json={"reason": "Phê duyệt thay đổi thứ tự."},
    )
    assert resp_appr.status_code == 200

    # Verify student progress is intact!
    sess.expire_all()
    check_prog = (
        sess.query(LessonProgress)
        .filter(
            LessonProgress.enrollment_period_id == period.id,
            LessonProgress.lesson_id == first_lesson.id,
        )
        .first()
    )
    assert check_prog is not None
    assert check_prog.completed_at is not None


def test_rate_limit_on_learning_units_reorder_and_lessons_creation(
    client: FlaskClient,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Rapid curriculum mutations (>15 req/60s) on learning units and lessons trigger 429."""
    login_web_user(client, instructor_user)
    cid = str(published_course.public_id)
    u1 = published_course.learning_units[0]
    unit_ids = [str(u1.public_id)]

    # 15 requests succeed
    for i in range(15):
        resp = client.post(
            f"/instructor/courses/{cid}/learning-units/reorder",
            json={"unit_ids": unit_ids},
        )
        assert resp.status_code in (200, 202)

    # 16th request triggers 429
    resp_overflow = client.post(
        f"/instructor/courses/{cid}/learning-units/reorder",
        json={"unit_ids": unit_ids},
    )
    assert resp_overflow.status_code == 429
    assert resp_overflow.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_draft_curriculum_creates_no_admin_change_requests_or_notifications(
    client: FlaskClient,
    instructor_user: User,
    admin_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """TC-DOS-02: Editing a DRAFT course reorders directly and creates ZERO admin requests or notifications."""
    from pwd301.models.notification_audit import Notification

    sess = db.session
    # Count admin notifications before
    admin_notif_count_before = (
        sess.query(Notification).filter(Notification.recipient_user_id == admin_user.id).count()
    )
    cr_count_before = sess.query(CourseChangeRequest).count()

    # Create a draft course
    c_draft = create_course(
        instructor_user,
        {
            "course_code": f"DRAFT-{uuid.uuid4().hex[:6].upper()}",
            "title": "Bản Nháp Thử Nghiệm",
            "category": "Technology",
            "difficulty": "BEGINNER",
        },
        session=sess,
    )
    u = create_learning_unit(instructor_user, c_draft.id, {"title": "Chương Nháp"}, session=sess)
    l1 = create_lesson(
        instructor_user,
        c_draft.id,
        {"learning_unit_id": str(u.public_id), "title": "Bài 1", "markdown_content": "A"},
        session=sess,
    )
    l2 = create_lesson(
        instructor_user,
        c_draft.id,
        {"learning_unit_id": str(u.public_id), "title": "Bài 2", "markdown_content": "B"},
        session=sess,
    )
    sess.commit()

    login_web_user(client, instructor_user)
    cid = str(c_draft.public_id)

    # Reorder lessons 5 times in draft mode
    for _ in range(5):
        resp = client.post(
            f"/instructor/courses/{cid}/lessons/reorder",
            json={"ordered_lesson_ids": [str(l2.public_id), str(l1.public_id)]},
        )
        assert resp.status_code == 200

    # Verify zero change requests created, zero admin notifications
    sess.expire_all()
    cr_count_after = sess.query(CourseChangeRequest).count()
    admin_notif_count_after = (
        sess.query(Notification).filter(Notification.recipient_user_id == admin_user.id).count()
    )

    assert cr_count_after == cr_count_before
    assert admin_notif_count_after == admin_notif_count_before
