"""Integration test suite verifying fixes discovered during comprehensive browser audit."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course, Enrollment
from pwd301.models.identity import Role, User
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


def _ensure_roles() -> None:
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        if not db.session.query(Role).filter(Role.code == code).first():
            db.session.add(Role(code=code, name=name))
    db.session.commit()


def _get_csrf_token(client: FlaskClient) -> str:
    res = client.get("/auth/csrf-token")
    data = res.get_json() or {}
    return str(data.get("csrf_token", ""))


def _create_user(
    email: str = "testuser@pwd301.local",
    role: str = "STUDENT",
) -> User:
    _ensure_roles()
    u = register_user(email, "Password@123", "Test User", session=db.session)
    u.email_verified_at = u.created_at
    if role != "STUDENT":
        assign_role_to_user(u.id, role, session=db.session)
    db.session.commit()
    return u


def _create_course(instructor: User, status: str = "PUBLISHED") -> Course:
    course = Course(
        course_code="AUDIT101",
        title="Software Testing & Verification",
        description="Comprehensive audit verification course",
        owner_instructor_id=instructor.id,
        status=status,
    )
    db.session.add(course)
    db.session.commit()
    return course


def test_student_course_detail_max_points(client: FlaskClient, app: Flask) -> None:
    """Verify GET /student/courses/<id> handles assessments without AttributeError."""
    with app.app_context():
        instructor = _create_user("inst_audit@pwd301.local", "INSTRUCTOR")
        student = _create_user("stud_audit@pwd301.local", "STUDENT")
        course = _create_course(instructor, status="PUBLISHED")

        # Enroll student
        enrollment = Enrollment(
            student_user_id=student.id,
            course_id=course.id,
            status="ACTIVE",
        )
        db.session.add(enrollment)

        # Create an assessment under this course
        asm = Assessment(
            course_id=course.id,
            creator_user_id=instructor.id,
            title="Kiểm tra giữa kỳ ABET",
            assessment_type="MIDTERM",
            status="PUBLISHED",
            time_limit_minutes=45,
            passing_percent=50.0,
        )
        db.session.add(asm)
        db.session.commit()

        login_web_user(client, student)
        resp = client.get(f"/student/courses/{course.public_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["course"]["course_code"] == "AUDIT101"
        assert len(data["assessments"]) == 1
        assert data["assessments"][0]["max_points"] == 10.0
        assert data["assessments"][0]["title"] == "Kiểm tra giữa kỳ ABET"


def test_student_become_instructor_adaptation(client: FlaskClient, app: Flask) -> None:
    """Verify POST /student/become-instructor adaptively maps alternate form fields."""
    with app.app_context():
        student = _create_user("stud_nominate@pwd301.local", "STUDENT")
        login_web_user(client, student)
        csrf = _get_csrf_token(client)

        payload = {
            "teaching_experience": "Lập trình Web & AI tại Đại học Bách Khoa TP.HCM",
            "certificate_url": "https://drive.google.com/drive/folders/audit-proof",
            "statement": "Tôi muốn chia sẻ kiến thức kiểm thử phần mềm cho sinh viên.",
        }

        resp = client.post(
            "/student/become-instructor",
            json=payload,
            headers={"X-CSRFToken": csrf},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "PENDING"
        assert "application_id" in data


def test_operations_telemetry_host_object(client: FlaskClient, app: Flask) -> None:
    """Verify /admin/telemetry returns node_label, network, and host for complete UI."""
    with app.app_context():
        admin = _create_user("admin_telem@pwd301.local", "ADMIN")
        login_web_user(client, admin)

        resp = client.get("/admin/telemetry")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data
        assert "node_label" in data
        assert "host" in data
        assert "node_label" in data["host"]
        assert "network" in data
        assert "traffic_label" in data["network"]


def test_instructor_ai_draft_route(client: FlaskClient, app: Flask) -> None:
    """Verify POST /instructor/ai/questions/draft accepts session authentication."""
    with app.app_context():
        instructor = _create_user("inst_ai_draft@pwd301.local", "INSTRUCTOR")
        course = _create_course(instructor, status="DRAFT")
        login_web_user(client, instructor)
        with client.session_transaction() as sess:
            sess["active_role"] = "INSTRUCTOR"
        csrf = _get_csrf_token(client)

        mock_draft = MagicMock()
        mock_draft.to_dict.return_value = {
            "draft_id": "mock-draft-uuid",
            "topic": "CSS Flexbox",
            "stem": "Flexbox CSS property...",
        }

        with (
            patch("pwd301.services.rate_limit_service.check_ai_rate_limit"),
            patch(
                "pwd301.services.ai_service.draft_course_questions",
                return_value=[mock_draft],
            ),
        ):
            resp = client.post(
                "/instructor/ai/questions/draft",
                json={
                    "course_id": str(course.public_id),
                    "topic": "CSS Flexbox",
                    "difficulty": "UNDERSTAND",
                    "count": 1,
                },
                headers={"X-CSRFToken": csrf},
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["count"] == 1
            assert data["drafts"][0]["draft_id"] == "mock-draft-uuid"
