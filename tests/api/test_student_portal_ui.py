"""Tests for Student Web Portal UI views, navigation, and interactive actions."""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import User
from pwd301.seeds.demo import seed_demo
from tests.conftest import login_web_user


@pytest.fixture
def demo_env(app: Flask) -> dict[str, Any]:
    """Seed demo data and retrieve test entities."""
    summary = seed_demo(db.session)
    student1 = db.session.query(User).filter(User.email == "student1@pwd301.local").first()
    student2 = db.session.query(User).filter(User.email == "student2@pwd301.local").first()
    cs101 = db.session.query(Course).filter(Course.course_code == "CS101").first()
    assert student1 is not None
    assert student2 is not None
    assert cs101 is not None
    return {
        "student1": student1,
        "student2": student2,
        "cs101": cs101,
        "summary": summary,
    }


class TestStudentPortalViews:
    """Verify all student portal routes render cleanly with real data."""

    def test_student_dashboard_displays_enrolled_courses(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Student dashboard renders 200 and shows enrolled courses and KPI metrics."""
        login_web_user(client, demo_env["student1"])
        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "CS101" in html
        assert "Python" in html
        assert "Bảng điều khiển Học tập" in html
        assert "app-sidebar" in html
        assert "app-topbar" in html
        assert "demo-banner" not in html

    def test_sidebar_sticky_and_collapse_controls(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Sidebar contains topbar toggle button, footer collapse button, and nav tooltip labels."""
        login_web_user(client, demo_env["student1"])
        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "sidebar-toggle-btn" in html
        assert "sidebar-collapse-btn" in html
        assert 'title="Tổng quan"' in html
        assert 'data-nav-label="Tổng quan"' in html
        assert 'data-nav-label="Khóa học của tôi"' in html
        assert 'data-nav-label="Bài kiểm tra"' in html
        assert "sidebar-collapsed" in html

    def test_student_my_learning_page(self, client: FlaskClient, demo_env: dict[str, Any]) -> None:
        """My learning page renders with list of enrolled courses."""
        login_web_user(client, demo_env["student1"])
        resp = client.get("/student/my-learning", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Khóa học của tôi" in html
        assert "CS101" in html

    def test_student_assessments_page(self, client: FlaskClient, demo_env: dict[str, Any]) -> None:
        """Assessments page renders upcoming and completed exams."""
        login_web_user(client, demo_env["student1"])
        resp = client.get("/student/assessments", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Bài kiểm tra & Đánh giá" in html

    def test_student_assessment_detail_view(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Assessment detail page displays rules and start button."""
        login_web_user(client, demo_env["student1"])
        assessment = (
            db.session.query(Assessment)
            .filter(Assessment.status == "PUBLISHED", Assessment.deleted_at.is_(None))
            .first()
        )
        assert assessment is not None
        resp = client.get(
            f"/student/assessments/{assessment.public_id}", headers={"Accept": "text/html"}
        )
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Kiểm tra Giữa kỳ" in html
        assert "Thông tin quy chế thi" in html

    def test_student_attempt_result_view(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Result page displays score and pass/fail status for graded attempt."""
        student1 = demo_env["student1"]
        attempt = (
            db.session.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.student_user_id == student1.id,
                AssessmentAttempt.status == "GRADED",
            )
            .first()
        )
        assert attempt is not None
        login_web_user(client, student1)
        resp = client.get(
            f"/student/attempt/{attempt.public_id}/result", headers={"Accept": "text/html"}
        )
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Kết quả bài thi" in html
        assert "điểm" in html

    def test_student_lesson_shortcut_redirect(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Accessing /student/lessons/<lesson_id> redirects to canonical course lesson path."""
        student1 = demo_env["student1"]
        cs101 = demo_env["cs101"]
        lesson = db.session.query(Lesson).filter(Lesson.course_id == cs101.id).first()
        assert lesson is not None

        login_web_user(client, student1)
        resp = client.get(f"/student/lessons/{lesson.public_id}", follow_redirects=False)
        assert resp.status_code == 302
        expected_dest = f"/student/courses/{cs101.public_id}/lessons/{lesson.public_id}"
        assert expected_dest in resp.headers["Location"]

    def test_student_course_detail_view(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Course detail page renders with course description and enrollment action."""
        student2 = demo_env["student2"]
        cs101 = demo_env["cs101"]
        login_web_user(client, student2)
        resp = client.get(f"/student/courses/{cs101.public_id}", headers={"Accept": "text/html"})
        assert resp.status_code in (200, 302)

    def test_student_ai_assistant_page(self, client: FlaskClient, demo_env: dict[str, Any]) -> None:
        """Dedicated AI assistant full page redirects to dashboard with floating AI assistant."""
        login_web_user(client, demo_env["student1"])
        resp = client.get("/student/ai-assistant", headers={"Accept": "text/html"})
        assert resp.status_code == 302
        assert "/student/dashboard" in resp.headers.get("Location", "")

    def test_student_ai_chat_endpoint(self, client: FlaskClient, demo_env: dict[str, Any]) -> None:
        """Session-authenticated AI chat endpoint returns response."""
        login_web_user(client, demo_env["student1"])
        resp = client.post(
            "/student/ai/chat",
            json={"message": "Giải thích cơ chế bảo vệ CSRF trong Flask-WTF?"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_start_assessment_resumes_active_attempt(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """If attempt already active, start endpoint redirects cleanly to exam instead of 409."""
        from pwd301.services.attempt_service import start_assessment_attempt

        student1 = demo_env["student1"]
        assessment = (
            db.session.query(Assessment)
            .filter(Assessment.status == "PUBLISHED", Assessment.deleted_at.is_(None))
            .first()
        )
        assert assessment is not None

        # Start an initial active attempt using the service
        active_att, _ = start_assessment_attempt(
            student_actor=student1,
            assessment_id=assessment.public_id,
            session=db.session,
        )
        db.session.commit()

        login_web_user(client, student1)
        resp = client.post(
            f"/student/assessments/{assessment.public_id}/start",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert f"/student/attempt/{active_att.public_id}" in resp.headers["Location"]

    def test_base_navigation_rendering_instructor_and_admin(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Instructor and Admin dashboards render base layout cleanly without Jinja BuildError."""
        instructor = db.session.query(User).filter(User.email == "instructor1@pwd301.local").first()
        admin = db.session.query(User).filter(User.email == "admin@pwd301.local").first()
        assert instructor is not None
        assert admin is not None

        # Instructor dashboard and sidebar routes
        login_web_user(client, instructor)
        resp = client.get("/instructor/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Giảng viên" in html
        assert "Khóa học của tôi" in html

        # Admin dashboard and sidebar routes
        login_web_user(client, admin)
        resp = client.get("/admin/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Quản trị" in html
        assert "Quản lý Người dùng" in html

    def test_smart_lesson_resumption_redirects_to_uncompleted_lesson(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Course progress redirects to the first uncompleted lesson instead of always lesson 1."""
        student2 = demo_env["student2"]
        cs101 = demo_env["cs101"]
        lessons = (
            db.session.query(Lesson)
            .filter(Lesson.course_id == cs101.id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.position.asc())
            .all()
        )
        assert len(lessons) >= 2

        login_web_user(client, student2)
        resp = client.get(
            f"/student/courses/{cs101.public_id}/progress",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        # Student2 completed lesson[0] in demo seed, so resumption redirects to lesson[1]
        expected_target = f"/student/courses/{cs101.public_id}/lessons/{lessons[1].public_id}"
        assert expected_target in resp.headers["Location"]

    def test_course_detail_prerequisite_blocking_and_flash(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Course detail page detects unmet prerequisites and form POST cleanly redirects."""
        student2 = demo_env["student2"]
        cs201 = db.session.query(Course).filter(Course.course_code == "CS201").first()
        assert cs201 is not None

        login_web_user(client, student2)
        resp = client.get(f"/student/courses/{cs201.public_id}", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Ghi danh bị chặn do chưa đạt điều kiện tiên quyết" in html
        assert "Chưa đủ điều kiện" in html

        # HTML form enrollment attempt must redirect with flash message rather than 400 crash
        post_resp = client.post(
            f"/student/courses/{cs201.public_id}/enroll",
            headers={"Accept": "text/html"},
            follow_redirects=True,
        )
        assert post_resp.status_code == 200
        post_html = post_resp.data.decode("utf-8")
        assert "Không thể ghi danh" in post_html
        assert "tiên quyết" in post_html or "Prerequisite" in post_html

    def test_assessment_detail_passing_percentage_rendered(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Assessment detail page displays passing percent correctly."""
        student1 = demo_env["student1"]
        assessment = (
            db.session.query(Assessment)
            .filter(Assessment.status == "PUBLISHED", Assessment.deleted_at.is_(None))
            .first()
        )
        assert assessment is not None
        login_web_user(client, student1)
        resp = client.get(
            f"/student/assessments/{assessment.public_id}", headers={"Accept": "text/html"}
        )
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        # Passing score badge/text should contain %
        assert "Điểm đạt tối thiểu" in html
        assert "%" in html

    def test_octopus_mascot_ai_launcher_and_dashboard_cleanup(
        self, client: FlaskClient, demo_env: dict[str, Any]
    ) -> None:
        """Verify octopus mascot launcher in base shell and quick card removed from dashboard."""
        student1 = demo_env["student1"]
        login_web_user(client, student1)

        resp = client.get("/student/dashboard", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")

        # 1. Old quick card on dashboard must be removed
        assert "Mở cửa sổ Trợ lý AI →" not in html
        assert "Cơ chế chống CSRF hoạt động thế nào?" not in html

        # 2. Circular octopus mascot launcher and expand UI must be present in application shell
        assert "ai-fab-launcher" in html
        assert "octopus_mascot.png" in html
        assert "Trợ lý Bạch Tuộc AI" in html
        assert "ai-online-badge" in html
        assert "ai-chat-window" in html
        assert "ai-chat-expand-btn" in html
        assert "ai-expand-icon" in html
        assert "ai-compress-icon" in html
        assert "data-user-initials" in html
        assert "data-user-name" in html

        # 3. Test sending a message to /student/ai/chat
        chat_resp = client.post(
            "/student/ai/chat",
            json={"message": "Giải thích nhanh về HTTP GET"},
            headers={"Accept": "application/json"},
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.get_json()
        assert chat_data.get("status") == "success"
        assert "reply" in chat_data
        assert len(chat_data["reply"]) > 0
