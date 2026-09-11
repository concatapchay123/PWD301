"""Regression and integration test suite for Web UI flows and bug fixes.

Covers:
- Template rendering integrity for all blueprints (core, auth, student, instructor, admin)
- Login smart redirect and forgot password link
- Role switching mechanism (?switch_role=...)
- Notification mark-as-read and mark-all-read via Web session
- Student attempt exam delivery, answer autosave, lease renewal/takeover, and submit
- Admin actions content-negotiation (form POST redirects with flash)
"""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import Notification
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    start_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.question_bank_service import create_question
from pwd301.services.session_auth_service import create_auth_session
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def baseline_setup(app: Flask) -> dict[str, Any]:
    """Seed baseline roles and create test users for each role."""
    seed_baseline(db.session)

    admin = db.session.query(User).filter(User.email == "admin@pwd301.local").first()
    assert admin is not None

    instructor = register_user(
        email="instructor.test@pwd301.local",
        password="Password@123",
        display_name="Instructor Test",
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR")

    student = register_user(
        email="student.test@pwd301.local",
        password="Password@123",
        display_name="Student Test",
    )
    assign_role_to_user(student.id, "STUDENT")

    multi_user = register_user(
        email="multi.role@pwd301.local",
        password="Password@123",
        display_name="Multi Role User",
    )
    assign_role_to_user(multi_user.id, "STUDENT")
    assign_role_to_user(multi_user.id, "INSTRUCTOR")

    db.session.commit()
    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "multi_user": multi_user,
    }


class TestTemplateRenderingIntegrity:
    """Verify that all main Web UI views render with 200 and no Jinja BuildErrors."""

    def test_public_pages_render(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Core public pages render without crash."""
        resp = client.get("/", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        assert b"PWD301" in resp.data

        resp = client.get("/auth/login", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        assert b"auth/forgot-password" in resp.data or b"forgot-password" in resp.data or b"Qu\xc3\xaan" in resp.data

        resp = client.get("/auth/register", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/auth/forgot-password", headers={"Accept": "text/html"})
        assert resp.status_code == 200

    def test_student_views_render(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Student dashboard and views render with 200."""
        login_web_user(client, baseline_setup["student"])
        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/student/notifications", headers={"Accept": "text/html"})
        assert resp.status_code == 200

    def test_instructor_views_render(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Instructor dashboard, courses, and grading render with 200."""
        login_web_user(client, baseline_setup["instructor"])
        resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/instructor/courses", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/instructor/grading", headers={"Accept": "text/html"})
        assert resp.status_code == 200

    def test_admin_views_render(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Admin dashboard, courses, users, backups, audit logs render with 200."""
        login_web_user(client, baseline_setup["admin"])

        resp = client.get("/admin/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/admin/courses", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/admin/users", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/admin/backups", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/admin/audit-logs", headers={"Accept": "text/html"})
        assert resp.status_code == 200


class TestLoginAndRoleSwitching:
    """Verify smart login redirects and ?switch_role= functionality."""

    def test_smart_login_redirect_by_role(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Login redirects to role dashboard according to user's highest role."""
        # Student login -> /student/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "student.test@pwd301.local", "password": "Password@123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/student/dashboard"

        # Instructor login -> /instructor/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "instructor.test@pwd301.local", "password": "Password@123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/dashboard"

        # Admin login -> /admin/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "admin@pwd301.local", "password": "Admin@123456"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/dashboard"

    def test_role_switch_hook(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Multi-role user can switch active role via ?switch_role=."""
        multi_user = baseline_setup["multi_user"]
        login_web_user(client, multi_user)

        # Start on student dashboard, switch to INSTRUCTOR
        resp = client.get("/student/dashboard?switch_role=INSTRUCTOR", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/dashboard"

        with client.session_transaction() as sess:
            assert sess.get("active_role") == "INSTRUCTOR"

        # On instructor dashboard, switch to STUDENT
        resp = client.get("/instructor/dashboard?switch_role=STUDENT", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/student/dashboard"

        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"


class TestWebNotificationsFlow:
    """Verify notification read actions work via Web session without 401."""

    def test_mark_single_and_all_read(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Student can mark individual and all notifications as read via web forms."""
        from pwd301.services.notification_service import dispatch_notification

        student = baseline_setup["student"]
        login_web_user(client, student)

        # Seed 2 notifications via dispatch_notification
        notif1, _ = dispatch_notification(
            recipient_user=student,
            event_type="SYSTEM_ALERT",
            title="Notification 1",
            body="Body 1",
            session=db.session,
        )
        notif2, _ = dispatch_notification(
            recipient_user=student,
            event_type="SYSTEM_ALERT",
            title="Notification 2",
            body="Body 2",
            session=db.session,
        )
        db.session.commit()

        # Mark single read
        resp = client.post(
            f"/student/notifications/{notif1.public_id}/read",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/student/notifications" in resp.headers["Location"]

        db.session.refresh(notif1)
        assert notif1.read_at is not None

        # Mark all read
        resp = client.post(
            "/student/notifications/mark-all-read",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/student/notifications" in resp.headers["Location"]

        db.session.refresh(notif2)
        assert notif2.read_at is not None


class TestAdminWebFormResponses:
    """Verify that Admin form submissions return 302 redirects with flash instead of raw JSON."""

    def test_course_review_and_state_transitions(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Course review, publish, trash, restore return redirects to /admin/courses."""
        admin = baseline_setup["admin"]
        instructor = baseline_setup["instructor"]
        login_web_user(client, admin)

        # Create and submit course
        course = create_course(
            instructor,
            {
                "course_code": "ADM101",
                "title": "Admin Test Course",
                "summary": "Course for admin tests",
            },
            session=db.session,
        )
        change_course_status(instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session)

        # Approve course
        resp = client.post(
            f"/admin/courses/{course.public_id}/review",
            data={"action": "approve", "reason": "Approved by admin"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/courses"

        # Publish course
        resp = client.post(
            f"/admin/courses/{course.public_id}/publish",
            data={"reason": "Published publicly"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/courses"

        # Create a separate draft course to test Trash & Restore
        trash_course = create_course(
            instructor,
            {
                "course_code": "TRASH101",
                "title": "Course to Trash",
                "summary": "Draft course to test trash",
            },
            session=db.session,
        )

        # Trash course
        resp = client.post(
            f"/admin/courses/{trash_course.public_id}/trash",
            data={"reason": "Moving to trash"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/courses"

        # Restore course
        resp = client.post(
            f"/admin/courses/{trash_course.public_id}/restore",
            data={"reason": "Restoring to archived"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/courses"

    def test_user_management_actions(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Admin suspend, unsuspend, and revoke sessions return redirects to /admin/users."""
        admin = baseline_setup["admin"]
        student = baseline_setup["student"]
        login_web_user(client, admin)

        # Suspend
        resp = client.post(
            f"/admin/users/{student.public_id}/suspend",
            data={"reason": "Test suspension"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/users"

        # Unsuspend
        resp = client.post(
            f"/admin/users/{student.public_id}/unsuspend",
            data={"reason": "Test reactivate"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/users"

        # Revoke sessions
        resp = client.post(
            f"/admin/users/{student.public_id}/revoke-sessions",
            data={"reason": "Test revocation"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/users"

    def test_backup_actions(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """Admin backup creation returns redirect to /admin/backups."""
        admin = baseline_setup["admin"]
        login_web_user(client, admin)

        # Create backup
        resp = client.post(
            "/admin/backups",
            data={"backup_type": "MANUAL", "notes": "Test backup"},
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/backups"


class TestStudentAttemptWebFlow:
    """Verify the student attempt page, autosave answers, lease renewal, and submission via Web session."""

    def test_full_attempt_web_lifecycle(self, client: FlaskClient, baseline_setup: dict[str, Any]) -> None:
        """End-to-end attempt delivery via Web UI."""
        instructor = baseline_setup["instructor"]
        student = baseline_setup["student"]

        # 1. Create course & publish
        course = create_course(
            instructor,
            {
                "course_code": "EXAM101",
                "title": "Exam Course",
                "summary": "Testing exam attempt delivery",
            },
            session=db.session,
        )
        change_course_status(instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session)
        change_course_status(baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session)
        change_course_status(baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session)

        # 2. Create question in question bank
        q = create_question(
            instructor,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "APPLY",
                "content": "What is Python?",
                "default_points": 5.0,
                "choices": [
                    {"content": "A programming language", "is_correct": True, "position": 1},
                    {"content": "A snake only", "is_correct": False, "position": 2},
                ],
                "provenance": {"source_type": "MANUAL"},
            },
            session=db.session,
        )

        # 3. Create assessment with section and question
        asm = create_assessment(
            instructor,
            course.id,
            {
                "title": "Final Exam",
                "assessment_type": "MIDTERM",
                "scoring_policy": "HIGHEST",
                "time_limit_minutes": 60,
                "attempt_limit": 2,
            },
            session=db.session,
        )
        sec = create_section(
            instructor,
            asm.id,
            {"title": "Section 1", "position": 1},
            session=db.session,
        )
        assign_question(
            instructor,
            asm.id,
            {"question_id": str(q.public_id), "section_id": sec.id, "points": 5.0},
            session=db.session,
        )
        publish_assessment(instructor, asm.id, session=db.session)

        # 4. Enroll student and start attempt
        enroll_student(student, course.id, session=db.session)
        attempt, raw_lease = start_assessment_attempt(
            student_actor=student,
            assessment_id=str(asm.public_id),
            session=db.session,
        )
        attempt_id = str(attempt.public_id)

        # 5. Web student visits attempt page
        login_web_user(client, student)
        resp = client.get(f"/student/attempt/{attempt_id}", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        # Check that question text and choice text are rendered properly
        assert b"What is Python?" in resp.data
        assert b"A programming language" in resp.data

        # 6. Fetch attempt delivery to obtain attempt_question_id and choice_key
        delivery = get_attempt_delivery(student_actor=student, attempt_id=attempt_id, session=db.session)
        q_item = delivery["questions"][0]
        aq_id = q_item["attempt_question_id"]
        choice_key = q_item["choices"][0]["choice_key"]

        import re
        m = re.search(r'leaseToken = "(.*?)"', resp.data.decode("utf-8"))
        assert m is not None and len(m.group(1)) > 0
        lease_token = m.group(1)

        # 7. Student autosaves answer via Web session
        save_resp = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "selected_choice_keys": [choice_key],
                "lease_token": lease_token,
            },
        )
        assert save_resp.status_code == 200
        save_json = save_resp.get_json()
        assert "answer_version" in save_json

        # 8. Student renews / takes over lease via Web session
        lease_resp = client.post(
            f"/student/attempt/{attempt_id}/lease/takeover",
            json={"force": False},
        )
        assert lease_resp.status_code == 200
        new_lease_token = lease_resp.get_json()["lease_token"]

        # 9. Student submits attempt via Web session
        submit_resp = client.post(
            f"/student/attempt/{attempt_id}/submit",
            json={"lease_token": new_lease_token},
        )
        assert submit_resp.status_code == 200
        sub_json = submit_resp.get_json()
        assert sub_json["status"] in ("SUBMITTED", "GRADED")
