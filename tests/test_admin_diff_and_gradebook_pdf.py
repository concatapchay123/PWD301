"""
Tests for Admin granular diff summary and gradebook PDF generation (TASK-089).
"""

from unittest.mock import MagicMock

from pwd301.blueprints.admin.routes import build_change_request_diff_summary
from pwd301.services.result_pdf_service import build_assessment_gradebook_pdf


def test_partial_lesson_diff_keeps_resources_unless_explicitly_changed():
    request = MagicMock(change_type="LESSON_CONTENT", target_type="LESSON")
    original = {
        "title": "Before",
        "resources": [{"resource_id": 1, "asset_id": "old", "title": "old.pdf"}],
    }
    diff = build_change_request_diff_summary(request, original, {"title": "After"})
    assert diff["changed_fields"] == ["title"]
    removed = build_change_request_diff_summary(request, original, {"resources": []})
    assert removed["changed_fields"] == ["resources"]


def test_resource_diff_applies_attach_detach_proposal_without_mutating_original():
    request = MagicMock(change_type="LESSON_CONTENT", target_type="LESSON")
    original = {"resources": [{"resource_id": 1, "asset_id": "old", "title": "old.pdf"}]}
    proposal = {
        "action": "RESOURCE_CHANGES",
        "changes": [
            {"action": "DETACH", "resource_id": 1},
            {"action": "ATTACH", "asset_id": "new", "title": "new.pdf"},
        ],
    }
    diff = build_change_request_diff_summary(request, original, proposal)
    resource_change = next(item for item in diff["changes"] if item["field"] == "resources")
    assert [item["title"] for item in resource_change["new_value"]] == ["new.pdf"]
    assert [item["title"] for item in original["resources"]] == ["old.pdf"]


def test_build_assessment_gradebook_pdf_generates_valid_pdf():
    """Verify build_assessment_gradebook_pdf produces a valid, non-empty PDF binary."""
    sample_data = {
        "assessment_id": 101,
        "title": "Kiểm tra Cuối kỳ Lập trình Web",
        "course_code": "PWD301",
        "course_title": "Lập trình Web Nâng Cao",
        "instructor_name": "TS. Nguyễn Văn A",
        "duration_minutes": 60,
        "pass_score": 5.0,
        "max_score": 10.0,
        "total_attempts": 3,
        "pass_count": 2,
        "fail_count": 1,
        "pass_rate": 66.7,
        "avg_score": 7.2,
        "highest_score": 9.5,
        "lowest_score": 4.0,
        "attempts": [
            {
                "student_name": "Lê Văn C",
                "student_email": "levanc@example.com",
                "score": 9.5,
                "percentage": 95.0,
                "is_passed": True,
                "duration_minutes": 45,
                "proctoring_flags": 0,
                "score_status": "RELEASED",
                "submitted_at": "2026-10-09 14:30:00",
            },
            {
                "student_name": "Trần Thị B",
                "student_email": "tranthib@example.com",
                "score": 8.0,
                "percentage": 80.0,
                "is_passed": True,
                "duration_minutes": 55,
                "proctoring_flags": 1,
                "score_status": "RELEASED",
                "submitted_at": "2026-10-09 14:45:00",
            },
            {
                "student_name": "Phạm Văn D",
                "student_email": "phamvand@example.com",
                "score": 4.0,
                "percentage": 40.0,
                "is_passed": False,
                "duration_minutes": 60,
                "proctoring_flags": 3,
                "score_status": "RELEASED",
                "submitted_at": "2026-10-09 15:00:00",
            },
        ],
    }

    pdf_bytes = build_assessment_gradebook_pdf(sample_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_build_change_request_diff_summary_course_metadata():
    """Verify build_change_request_diff_summary categorizes changed vs unchanged fields."""
    mock_request = MagicMock()
    mock_request.change_type = "COURSE_METADATA"
    mock_request.target_type = "COURSE"

    original_data = {
        "title": "Lập trình Căn bản",
        "category": "Công nghệ thông tin",
        "description": "Mô tả cũ",
        "difficulty": "BEGINNER",
        "learning_objectives": "SLO cũ",
    }
    payload_data = {
        "title": "Lập trình Web Hiện đại (Cập nhật)",
        "description": "Mô tả mới chi tiết hơn",
        # category & difficulty are untouched
    }

    diff = build_change_request_diff_summary(mock_request, original_data, payload_data)
    assert diff["category"] == "COURSE_METADATA"
    assert "title" in diff["changed_fields"]
    assert "description" in diff["changed_fields"]
    assert "category" not in diff["changed_fields"]
    assert "difficulty" not in diff["changed_fields"]

    # Check changed list
    change_fields = [c["field"] for c in diff["changes"]]
    assert "title" in change_fields
    assert "description" in change_fields

    # Check unchanged list
    unchanged_fields = [u["field"] for u in diff["unchanged_fields"]]
    assert "category" in unchanged_fields
    assert "difficulty" in unchanged_fields
