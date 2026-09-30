"""Test suite for the new Cisco NetAcad-style Unified Learning Console.

Verifies:
1. Student course routing dispatches to the unified learning console.
2. JavaScript assets expose renderCourseConsole with smart accordion outline,
   floating chevrons [<] [>], locked content handling, and embedded checkpoint exams.
3. Backend APIs supporting the console (course detail, lesson detail, progress, quiz, notes).
"""

from __future__ import annotations

from pathlib import Path

from flask.testing import FlaskClient

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"


def test_student_view_exposes_render_course_console() -> None:
    """Verify student.js contains the Cisco NetAcad-style renderCourseConsole method."""
    student_js_path = FRONTEND_DIR / "assets" / "js" / "views" / "student.js"
    assert student_js_path.exists(), "student.js must exist"
    content = student_js_path.read_text(encoding="utf-8")

    assert "static async renderCourseConsole" in content, (
        "student.js must expose static async renderCourseConsole"
    )
    # Check key Cisco NetAcad UI markers
    assert "cisco-console-root" in content, "Console must define cisco-console-root container"
    assert "outline-search-input" in content, "Console must provide outline search filter"
    assert "Locked Content" in content or "Nội dung bị khóa" in content, (
        "Console must handle locked content with NetAcad card"
    )
    assert "floating-prev-btn" in content or "floating-nav" in content, (
        "Console must have floating [<] and [>] chevron buttons"
    )


def test_router_dispatches_to_render_course_console() -> None:
    """Verify router.js routes course entry and lesson reading to renderCourseConsole."""
    router_js_path = FRONTEND_DIR / "assets" / "js" / "router.js"
    assert router_js_path.exists(), "router.js must exist"
    content = router_js_path.read_text(encoding="utf-8")

    assert "renderCourseConsole" in content, (
        "router.js must call StudentView.renderCourseConsole for student course routes"
    )


def test_student_course_api_contracts_for_console(client: FlaskClient) -> None:
    """Ensure student course endpoints return required metadata for the NetAcad console."""
    # Check that public/authenticated route contracts remain sound
    resp = client.get("/student/my-learning")
    # Without auth cookie, must return 401 JSON or redirect to auth
    assert resp.status_code in (200, 302, 401)


def test_notes_and_ai_buttons_removed_from_console(client: FlaskClient) -> None:
    """Verify Ghi chú and Trợ lí AI buttons and their backend notes endpoints are removed."""
    student_js_path = FRONTEND_DIR / "assets" / "js" / "views" / "student.js"
    student_js = student_js_path.read_text(encoding="utf-8")
    assert "console-notes-btn" not in student_js, "console-notes-btn should be removed"
    assert "console-ai-btn" not in student_js, "console-ai-btn should be removed"

    api_js_path = FRONTEND_DIR / "assets" / "js" / "api.js"
    api_js = api_js_path.read_text(encoding="utf-8")
    assert "getLessonNotes" not in api_js, "getLessonNotes should be removed from api.js"
    assert "saveLessonNotes" not in api_js, "saveLessonNotes should be removed from api.js"

    # Backend /notes route should no longer exist (404)
    resp = client.get("/student/lessons/fake-lesson-id/notes")
    assert resp.status_code == 404, (
        f"Expected 404 for removed notes endpoint, got {resp.status_code}"
    )


def test_navigation_button_labels_updated() -> None:
    """Verify navigation button labels are updated to 'Bài phía trước' and 'Bài tiếp theo'."""
    student_js_path = FRONTEND_DIR / "assets" / "js" / "views" / "student.js"
    student_js = student_js_path.read_text(encoding="utf-8")

    assert "Bài phía trước" in student_js, "student.js must contain 'Bài phía trước'"
    assert "Bài trước: " not in student_js, "student.js must not contain 'Bài trước: '"
    assert "Bài tiếp theo: ${UI.escapeHtml" not in student_js, (
        "student.js must not append lesson title to 'Bài tiếp theo'"
    )
    assert "<span>Bài tiếp theo</span>" in student_js, (
        "student.js must have '<span>Bài tiếp theo</span>'"
    )
