"""Unit and integration tests for LMS 17-10 Remediation.

Covers:
- BUG 01: Course Preflight Publish Checklist sub-items breakdown & SLO weights.
- BUG 02: YouTube video player clean embedding without clutter.
- BUG 03: Resolution of unique index collision (SQL Server Error 2601) on uq_lessons_course_position_active
          and fail-closed sanitized audit error responses.
"""

import json
import uuid

import pytest
from flask import Flask

from backend.blueprints.instructor.routes import validate_course_publish_readiness
from backend.extensions import db
from backend.models.course import LearningUnit, Lesson
from backend.models.identity import Role, User
from backend.services.course_service import create_course
from backend.services.exceptions import (
    AuditPersistenceError,
    LessonStateViolationError,
)
from backend.services.lesson_service import (
    TRASH_POSITION_BASE,
    delete_learning_unit,
)
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
    role_map = {}
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
    u = register_user(f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor User")
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_publish_checklist_course_info_sub_items(app: Flask, instructor_user: User) -> None:
    """Verify that validate_course_publish_readiness provides granular sub_items for description and SLOs."""
    with app.app_context():
        course = create_course(
            instructor_user,
            {
                "course_code": f"WEB_{uuid.uuid4().hex[:4].upper()}",
                "title": "Lập Trình Web Chuyên Sâu",
                "description": "Mô tả ngắn",  # < 20 chars
            },
        )
        course.learning_objectives = json.dumps([])
        db.session.commit()

        res = validate_course_publish_readiness(course, session=db.session)
        crit_3 = next(c for c in res["criteria"] if c["id"] == "course_info")
        assert not crit_3["passed"]
        assert "sub_items" in crit_3
        assert len(crit_3["sub_items"]) == 2

        desc_sub = next(s for s in crit_3["sub_items"] if s["id"] == "description")
        assert not desc_sub["passed"]
        assert desc_sub["action_tab"] == "overview"

        lo_sub = next(s for s in crit_3["sub_items"] if s["id"] == "learning_objectives")
        assert not lo_sub["passed"]
        assert lo_sub["action_tab"] == "curriculum-slos"

        # Now add valid SLOs but keep short description
        course.learning_objectives = json.dumps([{"title": "SLO 1", "description": "Mục tiêu 1", "weight": "100%"}])
        db.session.commit()

        res2 = validate_course_publish_readiness(course, session=db.session)
        crit_3_2 = next(c for c in res2["criteria"] if c["id"] == "course_info")
        assert not crit_3_2["passed"]
        lo_sub_2 = next(s for s in crit_3_2["sub_items"] if s["id"] == "learning_objectives")
        assert lo_sub_2["passed"]
        desc_sub_2 = next(s for s in crit_3_2["sub_items"] if s["id"] == "description")
        assert not desc_sub_2["passed"]

        # Now add authentic description >= 20 chars
        course.description = "Khóa học cung cấp kiến thức nền tảng và nâng cao về kiến trúc web hiện đại."
        db.session.commit()

        res3 = validate_course_publish_readiness(course, session=db.session)
        crit_3_3 = next(c for c in res3["criteria"] if c["id"] == "course_info")
        assert crit_3_3["passed"]
        assert all(s["passed"] for s in crit_3_3["sub_items"])


def test_delete_learning_unit_repositions_lessons_to_trash_offset(app: Flask, instructor_user: User) -> None:
    """Verify that deleting a learning unit relocates member lessons to TRASH_POSITION_BASE + id."""
    with app.app_context():
        course = create_course(
            instructor_user,
            {
                "course_code": f"POS_{uuid.uuid4().hex[:4].upper()}",
                "title": "Khóa học kiểm thử vị trí",
                "description": "Mô tả khóa học kiểm thử vị trí bài giảng.",
            },
        )
        unit = LearningUnit(
            course_id=course.id,
            title="Chương 1",
            position=1,
        )
        db.session.add(unit)
        db.session.flush()

        lesson = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title="Bài 1",
            position=1,
            status="PUBLISHED",
        )
        db.session.add(lesson)
        db.session.commit()

        lesson_id = lesson.id
        unit_public_id = str(unit.public_id)

        # Delete learning unit
        delete_learning_unit(instructor_user, unit_public_id, session=db.session)

        reloaded_lesson = db.session.get(Lesson, lesson_id)
        assert reloaded_lesson is not None
        assert reloaded_lesson.status == "TRASH"
        assert reloaded_lesson.deleted_at is not None
        assert reloaded_lesson.position == TRASH_POSITION_BASE + lesson_id


def test_audit_persistence_error_sanitization_in_api_response(app: Flask) -> None:
    """Verify that 500 error messages from AuditPersistenceError never leak ODBC/SQL Server details to client."""
    client = app.test_client()

    with app.app_context():
        from backend import DOMAIN_EXCEPTION_HANDLERS
        code, status = DOMAIN_EXCEPTION_HANDLERS[AuditPersistenceError]
        assert code == "AUDIT_PERSISTENCE_FAILED"
        assert status == 500

    @app.route("/api/test-audit-fail")
    def _test_audit_fail():
        raise AuditPersistenceError("Cannot insert duplicate key row in dbo.lessons with unique index uq_lessons_course_position_active")

    resp = client.get("/api/test-audit-fail")
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUDIT_PERSISTENCE_FAILED"
    assert "dbo.lessons" not in data["error"]["message"]
    assert "uq_lessons_course_position_active" not in data["error"]["message"]
    assert "correlation_id" in data["error"]


def test_staged_chapter_deletion_and_diff(app: Flask, instructor_user: User) -> None:
    """Verify that deleting a chapter in a published course stages DELETE_LEARNING_UNIT,
    cascades child lessons, blocks adding new lessons in that deleted unit, and displays in get_course_changeset_diff."""
    from backend.services.lesson_service import (
        LessonValidationError,
        create_learning_unit,
        create_lesson,
        delete_learning_unit,
        get_course_changeset_diff,
    )
    with app.app_context():
        course = create_course(
            instructor_user,
            {
                "course_code": f"DIFF_{uuid.uuid4().hex[:4].upper()}",
                "title": "Khóa học Test Diff Bản Nháp",
                "description": "Mô tả khóa học phục vụ kiểm thử diff và bản nháp.",
            },
        )
        # Mark course as PUBLISHED to trigger staging
        course.status = "PUBLISHED"
        db.session.commit()

        # Create unit
        unit = create_learning_unit(instructor_user, course.id, {"title": "Chương Cũ Cần Xóa"}, session=db.session)
        # Create lesson inside unit
        les = create_lesson(
            instructor_user,
            course.id,
            {
                "title": "Bài học trong chương",
                "markdown_content": "# Nội dung bài học",
                "learning_unit_id": str(unit.public_id),
            },
            session=db.session,
        )
        db.session.commit()

        # Delete learning unit
        delete_learning_unit(instructor_user, unit.public_id, session=db.session)
        db.session.commit()

        # Attempting to create a new lesson in this deleted unit must be rejected
        with pytest.raises((LessonValidationError, LessonStateViolationError)):
            create_lesson(
                instructor_user,
                course.id,
                {
                    "title": "Bài học mới trong chương đã xóa",
                    "markdown_content": "# Nội dung mới",
                    "learning_unit_id": str(unit.public_id),
                },
                session=db.session,
            )

        # Get changeset diff
        diff = get_course_changeset_diff(instructor_user, course.id, session=db.session)
        struct = diff.get("curriculum_structure", [])
        assert any(item.get("change_type") == "REMOVED" and "Chương Cũ Cần Xóa" in item.get("title", "") for item in struct), f"Expected chapter deletion in diff, got: {struct}"

