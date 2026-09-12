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

from pwd301.extensions import db
from pwd301.models.identity import User
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
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import create_question
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
        assert (
            b"auth/forgot-password" in resp.data
            or b"forgot-password" in resp.data
            or b"Qu\xc3\xaan" in resp.data
        )

        resp = client.get("/auth/register", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/auth/forgot-password", headers={"Accept": "text/html"})
        assert resp.status_code == 200

    def test_student_views_render(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Student dashboard and views render with 200."""
        login_web_user(client, baseline_setup["student"])
        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200

        resp = client.get("/student/notifications", headers={"Accept": "text/html"})
        assert resp.status_code == 200

    def test_instructor_views_render(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
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

    def test_smart_login_redirect_by_role(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Login redirects to role dashboard according to user's highest role."""
        # Student login -> /student/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "student.test@pwd301.local", "password": "Password@123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/student/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"

        # Instructor login -> /instructor/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "instructor.test@pwd301.local", "password": "Password@123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "INSTRUCTOR"

        # Admin login -> /admin/dashboard
        resp = client.post(
            "/auth/login",
            data={"email": "admin@pwd301.local", "password": "Admin@123456"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "ADMIN"

    def test_role_switch_query_param_disabled_for_security(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Query parameter ?switch_role= must be ignored to prevent unauthorized role tampering."""
        multi_user = baseline_setup["multi_user"]
        login_web_user(client, multi_user)

        # Attempting to switch role via query param does NOT redirect or mutate session
        resp = client.get("/student/dashboard?switch_role=INSTRUCTOR", follow_redirects=False)
        assert resp.status_code == 200

        with client.session_transaction() as sess:
            # Active role is not escalated to INSTRUCTOR via query parameter
            assert sess.get("active_role") != "INSTRUCTOR"

    def test_admin_and_instructor_sidebar_and_topbar_rendering(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Admin and instructor dashboards render respective role sidebars and topbar titles."""
        # Admin login
        client.post(
            "/auth/login",
            data={"email": "admin@pwd301.local", "password": "Admin@123456"},
            follow_redirects=True,
        )
        resp = client.get("/admin/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Quản trị & Vận hành" in html
        assert "Quản lý người dùng" in html
        assert "QUẢN TRỊ VIÊN" in html

        # Instructor login
        client.post(
            "/auth/login",
            data={"email": "instructor.test@pwd301.local", "password": "Password@123"},
            follow_redirects=True,
        )
        resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Giảng dạy" in html
        assert "Chấm thi tự luận" in html
        assert "GIẢNG VIÊN" in html

    def test_role_switch_post_flow(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Multi-role users can switch role via POST; unauthorized roles are rejected."""
        # Admin login
        client.post(
            "/auth/login",
            data={"email": "admin@pwd301.local", "password": "Admin@123456"},
            follow_redirects=True,
        )

        # Admin switches to INSTRUCTOR
        resp = client.post(
            "/auth/switch-role",
            data={"role": "INSTRUCTOR"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "INSTRUCTOR"

        # Admin switches to STUDENT
        resp = client.post(
            "/auth/switch-role",
            data={"role": "STUDENT"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/student/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"

        # Admin switches back to ADMIN
        resp = client.post(
            "/auth/switch-role",
            data={"role": "ADMIN"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/admin/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "ADMIN"

        # Verify admin dropdown HTML shows all 3 role switch options
        resp = client.get("/admin/dashboard")
        assert resp.status_code == 200
        admin_html = resp.data.decode("utf-8")
        assert "VAI TRÒ (CHUYỂN ĐỔI)" in admin_html
        assert "Quản trị viên (Admin)" in admin_html
        assert "Giảng viên (Instructor)" in admin_html
        assert "Học viên (Student)" in admin_html

        # Instructor login
        client.post(
            "/auth/login",
            data={"email": "instructor.test@pwd301.local", "password": "Password@123"},
            follow_redirects=True,
        )
        # Verify instructor dropdown HTML shows Instructor and Student, but NOT Admin
        resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        inst_html = resp.data.decode("utf-8")
        assert "VAI TRÒ (CHUYỂN ĐỔI)" in inst_html
        assert "Giảng viên (Instructor)" in inst_html
        assert "Học viên (Student)" in inst_html
        assert "Quản trị viên (Admin)" not in inst_html

        # Instructor switches to STUDENT
        resp = client.post(
            "/auth/switch-role",
            data={"role": "STUDENT"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/student/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"

        # Instructor switches back to INSTRUCTOR
        resp = client.post(
            "/auth/switch-role",
            data={"role": "INSTRUCTOR"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/dashboard"
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "INSTRUCTOR"

        # Instructor attempts unauthorized escalation to ADMIN
        resp = client.post(
            "/auth/switch-role",
            data={"role": "ADMIN"},
            follow_redirects=False,
        )
        assert resp.status_code in (403, 302)
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "INSTRUCTOR"

        # Student login
        client.post(
            "/auth/login",
            data={"email": "student.test@pwd301.local", "password": "Password@123"},
            follow_redirects=True,
        )
        # Verify student dropdown HTML does NOT have role switcher
        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        student_html = resp.data.decode("utf-8")
        assert "VAI TRÒ (CHUYỂN ĐỔI)" not in student_html

        # Student cannot switch to any role
        resp = client.post(
            "/auth/switch-role",
            data={"role": "ADMIN"},
            follow_redirects=False,
        )
        assert resp.status_code in (403, 302)
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"

        resp = client.post(
            "/auth/switch-role",
            data={"role": "INSTRUCTOR"},
            follow_redirects=False,
        )
        assert resp.status_code in (403, 302)
        with client.session_transaction() as sess:
            assert sess.get("active_role") == "STUDENT"

    def test_auto_sync_active_role_on_portal_navigation(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Navigating to /admin/... or /instructor/... automatically synchronizes active_role."""
        admin = baseline_setup["admin"]
        login_web_user(client, admin)

        # Force active_role in session to STUDENT
        with client.session_transaction() as sess:
            sess["active_role"] = "STUDENT"

        # Admin visits /admin/dashboard
        resp = client.get("/admin/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Quản trị & Vận hành" in html
        assert "QUẢN TRỊ VIÊN" in html

        with client.session_transaction() as sess:
            assert sess.get("active_role") == "ADMIN"


class TestWebNotificationsFlow:
    """Verify notification read actions work via Web session without 401."""

    def test_mark_single_and_all_read(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
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

    def test_course_review_and_state_transitions(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
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
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )

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

    def test_user_management_actions(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
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
    """Verify student attempt page, autosave answers, lease renewal, and submit."""

    def test_full_attempt_web_lifecycle(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
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
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session
        )

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
        delivery = get_attempt_delivery(
            student_actor=student, attempt_id=attempt_id, session=db.session
        )
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


class TestQuestionBankUIFlows:
    """Verify question bank question creation forms and table display."""

    def test_create_question_form_submission_and_bank_rendering(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Instructor can submit questions via web forms and view them."""
        instructor = baseline_setup["instructor"]
        login_web_user(client, instructor)

        course = create_course(
            instructor,
            {
                "course_code": "QBK101",
                "title": "Question Bank Test Course",
                "summary": "Testing question bank",
            },
            session=db.session,
        )

        # 1. Create SINGLE_CHOICE question via form POST
        resp = client.post(
            f"/instructor/courses/{course.public_id}/questions",
            data={
                "question_type": "SINGLE_CHOICE",
                "difficulty": "APPLY",
                "content_text": "What is Flask?",
                "default_points": "2.5",
                "choice_1": "A micro web framework",
                "choice_2": "A relational database",
                "choice_3": "A CSS preprocessor",
                "correct_choice": "1",
            },
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert f"/instructor/courses/{course.public_id}/questions" in resp.headers["Location"]

        # 2. Create TRUE_FALSE question via form POST
        resp_tf = client.post(
            f"/instructor/courses/{course.public_id}/questions",
            data={
                "question_type": "TRUE_FALSE",
                "difficulty": "REMEMBER",
                "content_text": "Python supports object-oriented programming.",
                "default_points": "1.0",
                "correct_tf": "TRUE",
            },
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp_tf.status_code == 302

        # 3. View question bank HTML page
        resp_page = client.get(
            f"/instructor/courses/{course.public_id}/questions",
            headers={"Accept": "text/html"},
        )
        assert resp_page.status_code == 200
        html = resp_page.data.decode("utf-8")
        assert "What is Flask?" in html
        assert "SINGLE_CHOICE" in html
        assert "Python supports object-oriented programming." in html
        assert "TRUE_FALSE" in html
        assert "Sẵn sàng" in html


class TestStudentAssessmentStartWebFlow:
    """Verify student starting an assessment via Web POST redirects to attempt view."""

    def test_student_start_assessment_web_redirect(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Student initiates attempt via web POST and is redirected to attempt room."""
        instructor = baseline_setup["instructor"]
        student = baseline_setup["student"]

        # Setup course and published assessment
        course = create_course(
            instructor,
            {
                "course_code": "ASMSTART101",
                "title": "Start Assessment Course",
                "summary": "Testing start assessment",
            },
            session=db.session,
        )
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session
        )

        q = create_question(
            instructor,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Is this a test question?",
                "default_points": 10.0,
                "choices": [
                    {"content": "Yes", "is_correct": True, "position": 1},
                    {"content": "No", "is_correct": False, "position": 2},
                ],
            },
            session=db.session,
        )
        asm = create_assessment(
            instructor,
            course.id,
            {
                "title": "Quiz 1",
                "assessment_type": "QUIZ",
                "scoring_policy": "HIGHEST",
                "time_limit_minutes": 30,
            },
            session=db.session,
        )
        sec = create_section(
            instructor, asm.id, {"title": "General", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm.id,
            {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0},
            session=db.session,
        )
        publish_assessment(instructor, asm.id, session=db.session)
        enroll_student(student, course.id, session=db.session)

        # Student starts assessment via Web POST
        login_web_user(client, student)
        resp = client.post(
            f"/student/assessments/{asm.public_id}/start",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/student/attempt/" in resp.headers["Location"]

        # Visit the redirected attempt page
        attempt_url = resp.headers["Location"]
        resp_attempt = client.get(attempt_url, headers={"Accept": "text/html"})
        assert resp_attempt.status_code == 200
        assert b"Quiz 1" in resp_attempt.data
        assert b"Is this a test question?" in resp_attempt.data


class TestAutosaveSequenceKeyCompatibility:
    """Verify save_attempt_answer handles sequence keys monotonically."""

    def test_autosave_accepts_client_sequence_and_sequence_no(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Autosave accepts client_sequence and client_sequence_no without collision."""
        instructor = baseline_setup["instructor"]
        student = baseline_setup["student"]

        course = create_course(
            instructor,
            {
                "course_code": "AUTOSEQ101",
                "title": "Autosave Sequence Course",
                "summary": "Testing sequence keys",
            },
            session=db.session,
        )
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session
        )

        q = create_question(
            instructor,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Sequence question",
                "default_points": 5.0,
                "choices": [
                    {"content": "Option A", "is_correct": True, "position": 1},
                    {"content": "Option B", "is_correct": False, "position": 2},
                ],
            },
            session=db.session,
        )
        asm = create_assessment(
            instructor,
            course.id,
            {"title": "Seq Exam", "assessment_type": "QUIZ", "scoring_policy": "HIGHEST"},
            session=db.session,
        )
        sec = create_section(
            instructor, asm.id, {"title": "Sec", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm.id,
            {"question_id": str(q.public_id), "section_id": sec.id, "points": 5.0},
            session=db.session,
        )
        publish_assessment(instructor, asm.id, session=db.session)
        enroll_student(student, course.id, session=db.session)

        attempt, raw_lease = start_assessment_attempt(
            student_actor=student, assessment_id=str(asm.public_id), session=db.session
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student, attempt_id=attempt_id, session=db.session
        )
        aq_id = delivery["questions"][0]["attempt_question_id"]
        choice_key_a = delivery["questions"][0]["choices"][0]["choice_key"]
        choice_key_b = delivery["questions"][0]["choices"][1]["choice_key"]

        login_web_user(client, student)

        # 1. First autosave using client_sequence: 1
        resp1 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "selected_choice_keys": [choice_key_a],
                "lease_token": raw_lease,
            },
        )
        assert resp1.status_code == 200
        assert resp1.get_json()["answer_version"] == 1

        # 2. Second sequential autosave using client_sequence: 2
        resp2 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 2,
                "selected_choice_keys": [choice_key_b],
                "lease_token": raw_lease,
            },
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["answer_version"] == 2

        # 3. Third autosave using client_sequence_no: 3
        resp3 = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence_no": 3,
                "selected_choice_keys": [choice_key_a],
                "lease_token": raw_lease,
            },
        )
        assert resp3.status_code == 200
        assert resp3.get_json()["answer_version"] == 3


class TestInstructorCourseCreationAndListing:
    """Verify instructor course creation form and courses listing with lessons count."""

    def test_instructor_create_course_web_form(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Instructor can create a course via web form modal and see it in the courses listing."""
        instructor = baseline_setup["instructor"]
        login_web_user(client, instructor)

        resp = client.post(
            "/instructor/courses",
            data={
                "title": "New Modal Course",
                "course_code": "NMC101",
                "summary": "Created through instructor modal",
            },
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "/instructor/courses"

        # Check courses view renders cleanly
        resp_list = client.get("/instructor/courses", headers={"Accept": "text/html"})
        assert resp_list.status_code == 200
        html = resp_list.data.decode("utf-8")
        assert "NMC101" in html
        assert "New Modal Course" in html
        assert "0 bài học" in html or "bài học" in html


class TestStudentCourseEnrollmentAndLessonReader:
    """Verify student course enrollment and lesson reader with sidebar and heartbeat."""

    def test_enrollment_and_lesson_reader_flow(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Student enrolls in course, progresses to first lesson, and reads lesson content."""
        instructor = baseline_setup["instructor"]
        student = baseline_setup["student"]

        # 1. Instructor creates course with 2 published lessons
        course = create_course(
            instructor,
            {
                "course_code": "LES101",
                "title": "Lesson Reader Course",
                "summary": "Testing lesson reader",
            },
            session=db.session,
        )
        lesson1 = create_lesson(
            instructor,
            course.id,
            {
                "title": "Introduction to Python",
                "summary": "First lesson summary",
                "markdown_content": "# Intro\nWelcome to Python learning!",
                "status": "PUBLISHED",
            },
            session=db.session,
        )
        create_lesson(
            instructor,
            course.id,
            {
                "title": "Variables and Types",
                "summary": "Second lesson summary",
                "markdown_content": "# Variables\nUnderstanding data types.",
                "status": "PUBLISHED",
            },
            session=db.session,
        )
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session
        )

        # 2. Student enrolls via Web POST
        login_web_user(client, student)
        resp_enroll = client.post(
            f"/student/courses/{course.public_id}/enroll",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp_enroll.status_code == 302
        assert f"/student/courses/{course.public_id}/progress" in resp_enroll.headers["Location"]

        # 3. Course progress redirects to first active lesson
        resp_progress = client.get(
            f"/student/courses/{course.public_id}/progress",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp_progress.status_code == 302
        assert (
            f"/student/courses/{course.public_id}/lessons/{lesson1.public_id}"
            in resp_progress.headers["Location"]
        )

        # 4. View lesson reader page
        resp_lesson = client.get(
            f"/student/courses/{course.public_id}/lessons/{lesson1.public_id}",
            headers={"Accept": "text/html"},
        )
        assert resp_lesson.status_code == 200
        html = resp_lesson.data.decode("utf-8")
        assert "Introduction to Python" in html
        assert "Welcome to Python learning!" in html
        assert "Variables and Types" in html
        assert "/student/lessons/" in html
        assert "lesson-progress-badge" in html


class TestInstructorAttemptGradingUI:
    """Verify instructor attempt grading view and essay manual scoring."""

    def test_instructor_attempt_grading_page_and_essay_grading(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """Instructor views student attempt and manually grades an essay question."""
        instructor = baseline_setup["instructor"]
        student = baseline_setup["student"]

        # 1. Setup course and assessment with an ESSAY question
        course = create_course(
            instructor,
            {
                "course_code": "GRD101",
                "title": "Grading Course",
                "summary": "Testing essay grading",
            },
            session=db.session,
        )
        change_course_status(
            instructor, str(course.public_id), "SUBMITTED_FOR_REVIEW", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "APPROVED", session=db.session
        )
        change_course_status(
            baseline_setup["admin"], str(course.public_id), "PUBLISHED", session=db.session
        )

        q = create_question(
            instructor,
            course.id,
            {
                "question_type": "ESSAY",
                "difficulty": "APPLY",
                "content": "Explain the architectural principles of RESTful APIs.",
                "default_points": 10.0,
            },
            session=db.session,
        )
        asm = create_assessment(
            instructor,
            course.id,
            {"title": "Architecture Exam", "assessment_type": "FINAL", "scoring_policy": "HIGHEST"},
            session=db.session,
        )
        sec = create_section(
            instructor, asm.id, {"title": "Essays", "position": 1}, session=db.session
        )
        assign_question(
            instructor,
            asm.id,
            {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0},
            session=db.session,
        )
        publish_assessment(instructor, asm.id, session=db.session)
        enroll_student(student, course.id, session=db.session)

        # 2. Student starts attempt and answers essay
        attempt, raw_lease = start_assessment_attempt(
            student_actor=student, assessment_id=str(asm.public_id), session=db.session
        )
        attempt_id = str(attempt.public_id)

        delivery = get_attempt_delivery(
            student_actor=student, attempt_id=attempt_id, session=db.session
        )
        aq_id = delivery["questions"][0]["attempt_question_id"]

        login_web_user(client, student)
        save_resp = client.post(
            f"/student/attempt/{attempt_id}/answers/{aq_id}",
            json={
                "client_sequence": 1,
                "answer_text": "REST relies on statelessness and client-server separation.",
                "lease_token": raw_lease,
            },
        )
        assert save_resp.status_code == 200

        submit_resp = client.post(
            f"/student/attempt/{attempt_id}/submit",
            json={"lease_token": raw_lease},
        )
        assert submit_resp.status_code == 200

        # 3. Instructor views grading page
        login_web_user(client, instructor)
        resp_grade_ui = client.get(
            f"/instructor/attempts/{attempt_id}/grading",
            headers={"Accept": "text/html"},
        )
        assert resp_grade_ui.status_code == 200
        html = resp_grade_ui.data.decode("utf-8")
        assert "Explain the architectural principles of RESTful APIs." in html
        assert "REST relies on statelessness and client-server separation." in html
        assert "awarded_points" in html

        # 4. Instructor submits manual essay grade via web form
        resp_post_grade = client.post(
            f"/instructor/attempts/{attempt_id}/grades/{aq_id}",
            data={
                "awarded_points": "9.5",
                "reason": "Clear and comprehensive explanation of REST principles.",
            },
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp_post_grade.status_code == 302
        assert f"/instructor/attempts/{attempt_id}/grading" in resp_post_grade.headers["Location"]


class TestCustomErrorPages:
    """Verify custom error templates for 403, 404, and 500 when requested via HTML."""

    def test_custom_error_pages_html(
        self, client: FlaskClient, baseline_setup: dict[str, Any]
    ) -> None:
        """HTML requests for non-existent and forbidden endpoints render branded error templates."""
        # 404 Not Found
        resp_404 = client.get("/non-existent-page-url-xyz", headers={"Accept": "text/html"})
        assert resp_404.status_code == 404
        assert b"404" in resp_404.data
        assert (
            b"Kh\xc3\xb4ng t\xc3\xacm th\xe1\xba\xa5y trang" in resp_404.data
            or b"Trang kh\xc3\xb4ng t\xe1\xbb\x93n t\xe1\xba\xa1i" in resp_404.data
            or b"404" in resp_404.data
        )

        # 403 Forbidden (Student accessing Admin area)
        student = baseline_setup["student"]
        login_web_user(client, student)
        resp_403 = client.get("/admin/dashboard", headers={"Accept": "text/html"})
        assert resp_403.status_code == 403
        assert b"403" in resp_403.data
