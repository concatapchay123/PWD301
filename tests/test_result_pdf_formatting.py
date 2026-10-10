"""Unit tests for PDF generation formatting and requirements (TASK-090)."""

import io

import pypdf

from pwd301.services.result_pdf_service import (
    _format_score,
    build_assessment_gradebook_pdf,
    build_attempt_result_pdf,
)


def test_format_score_integer_and_decimal():
    assert _format_score(100.0) == "100"
    assert _format_score(0.0) == "0"
    assert _format_score(50) == "50"
    assert _format_score(85.5) == "85.5"
    assert _format_score(33.3333) == "33.33"
    assert _format_score("100.00") == "100"
    assert _format_score("95.50") == "95.5"


def _pdf_text(data):
    reader = pypdf.PdfReader(io.BytesIO(data))
    return reader, " ".join("\n".join(page.extract_text() or "" for page in reader.pages).split())


def test_attempt_pdf_retains_long_plain_text_and_splits_overheight_rows():
    question = "Giải thích a < b & c > d. " * 180 + "KẾT THÚC CÂU HỎI"
    answer = "<b>Đáp án là văn bản nguyên gốc</b> " * 60 + "KẾT THÚC ĐÁP ÁN"
    reader, text = _pdf_text(
        build_attempt_result_pdf(
            {
                "candidate_name": "Nguyễn <Anh> & Bình",
                "course_title": "Lập trình & Cấu trúc dữ liệu",
                "assessment_code": "d8cb2d87-0596-40aa-bbc9-5593c83e6d97",
                "questions": [{"content": question, "student_answer_text": answer}],
            }
        )
    )
    assert len(reader.pages) > 1
    assert "KẾT THÚC CÂU HỎI" in text
    assert "KẾT THÚC ĐÁP ÁN" in text
    assert "<b>Đáp án" in text
    assert "Nguyễn <Anh> & Bình" in text
    assert "Lập trình & Cấu trúc dữ liệu" in text
    assert "d8cb2d87-0596-40aa-bbc9-5593c83e6d97" not in text


def test_attempt_pdf_missing_authorized_data_does_not_invent_grades_or_duration():
    _, text = _pdf_text(build_attempt_result_pdf({"questions": None}))
    assert "45 phút" not in text
    assert "ĐẠT CHUẨN" not in text
    assert "CHƯA ĐẠT YÊU CẦU" not in text
    assert "0 / 0" not in text
    assert "0%" not in text


def test_pdf_without_unicode_font_fails_explicitly(monkeypatch):
    from pwd301.services import result_pdf_service

    monkeypatch.setattr(result_pdf_service, "_FONTS_REGISTERED", False)
    monkeypatch.setattr(result_pdf_service.os.path, "exists", lambda path: False)
    import pytest

    with pytest.raises(RuntimeError, match="Unicode"):
        build_attempt_result_pdf({})


def test_gradebook_pdf_handles_missing_scores_pending_results_and_plain_names():
    _, text = _pdf_text(
        build_assessment_gradebook_pdf(
            {
                "duration_minutes": None,
                "attempts": [{"student_name": "Nguyễn <A> & Bình", "score_status": "PENDING"}],
            }
        )
    )
    assert "Nguyễn <A> & Bình" in text
    assert "CHƯA CÔNG BỐ" in text
    assert "HỎNG" not in text
    assert "45 phút" not in text


def test_format_score_rejects_non_finite_values():
    for value in (float("nan"), float("inf"), "-Infinity", None):
        assert _format_score(value) == "-"


def test_build_attempt_result_pdf_decodes_selected_choice_text():
    sample_data = {
        "candidate_name": "Lê Hoàng Long",
        "candidate_email": "student1@pwd301.local",
        "assessment_title": "Kiểm tra Giữa kỳ: Cấu trúc Dữ liệu & Giải thuật Nâng cao",
        "assessment_code": "DSA201",
        "instructor_name": "ThS. Trần Thị B",
        "duration_minutes": 45,
        "started_at": "2026-10-02T03:07:36Z",
        "submitted_at": "2026-10-02T03:08:01Z",
        "raw_score": 0.0,
        "max_score": 100.0,
        "percent_score": 0.0,
        "is_passed": False,
        "questions": [
            {
                "content": "Độ phức tạp thời gian trung bình của giải thuật QuickSort khi phân hoạch ngẫu nhiên là gì?",
                "points_assigned": 50.0,
                "awarded_points": 0.0,
                "is_correct": False,
                "selected_choice_keys": ["56a7d14f-7102-4ec4-ad5b-ff983f7827b"],
                "choices": [
                    {
                        "choice_key": "56a7d14f-7102-4ec4-ad5b-ff983f7827b",
                        "content": "O(n^2)",
                        "is_selected": True,
                    },
                    {
                        "choice_key": "89b7d14f-7102-4ec4-ad5b-ff983f7827c",
                        "content": "O(n log n)",
                        "is_selected": False,
                    },
                ],
            }
        ],
    }

    pdf_bytes = build_attempt_result_pdf(sample_data)
    assert len(pdf_bytes) > 0

    # Read with pypdf and verify text
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "".join(page.extract_text() for page in reader.pages)

    assert "Lê Hoàng Long" in full_text
    assert "DSA201" in full_text
    # Ensure choice text 'O(n^2)' appears and NOT raw UUID key
    assert "O(n^2)" in full_text
    assert "56a7d14f-7102-4ec4-ad5b-ff983f7827b" not in full_text
    # Ensure scores format as 0 / 100 instead of 0.00 / 100.00
    assert "0 / 100" in full_text
    assert "0%" in full_text


def test_build_assessment_gradebook_pdf_invariants():
    gradebook_data = {
        "assessment_title": "Kiến trúc Backend & RESTful API",
        "assessment_code": "d8cb2d87-0596-40aa-bbc9-5593c83e6d97",
        "assessment_type": "MIDTERM",
        "course_title": "Lập trình Web Chuyên sâu",
        "course_code": "PY301",
        "instructor_name": "TS. Nguyễn Văn A",
        "duration_minutes": 45,
        "total_candidates": 1,
        "submitted_count": 1,
        "passed_count": 1,
        "failed_count": 0,
        "pass_rate_pct": 100.0,
        "average_score": 100.0,
        "highest_score": 100.0,
        "lowest_score": 100.0,
        "attempts": [
            {
                "student_code": "67c934d6-977f-4dbb-8490-2142768d1d63",
                "student_name": "Lê Hoàng Long",
                "submitted_at": "2026-09-29T05:53:04Z",
                "violation_count": 0,
                "score": 100.0,
                "is_passed": True,
            }
        ],
    }

    pdf_bytes = build_assessment_gradebook_pdf(gradebook_data)
    assert len(pdf_bytes) > 0

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "".join(page.extract_text() for page in reader.pages)

    # 1. Course title: only course title, no PY301 prefix
    assert "Lập trình Web Chuyên sâu" in full_text
    assert "PY301 - Lập trình Web Chuyên sâu" not in full_text

    # 2. Assessment: Type + Title, without UUID in parentheses
    assert "Kiểm tra Giữa kỳ" in full_text
    assert "Kiến trúc Backend" in full_text
    assert "d8cb2d87-0596-40aa-bbc9-5593c83e6d97" not in full_text

    # 3. Proctoring standard: Always "Có giám sát nâng cao"
    assert "Có giám sát nâng cao" in full_text

    # 4. Signature location: Thành phố Hồ Chí Minh
    assert "Thành phố Hồ Chí Minh" in full_text
    assert "Hà Nội" not in full_text

    # 5. Score formatting: 100 / 100, 100% (1/1)
    assert "100 / 100" in full_text
    assert "100% (1/1)" in full_text

    # 6. Student code: Clean formatted SV-67C934D6 instead of raw 36-char UUID
    assert "SV-67C934D6" in full_text
    assert "67c934d6-977f-4dbb-8490-2142768d1d63" not in full_text
