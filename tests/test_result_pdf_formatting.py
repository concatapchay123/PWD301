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
    normalized_full_text = " ".join(full_text.split())
    assert "Kiến trúc Backend" in normalized_full_text
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


def test_attempt_pdf_renders_latex_math_cleanly():
    sample_data = {
        "candidate_name": "Trần Văn Toán",
        "candidate_email": "toan.tv@pwd301.local",
        "assessment_title": "Toán Giải Tích Nâng Cao",
        "assessment_code": "MATH201",
        "duration_minutes": 60,
        "raw_score": 10.0,
        "max_score": 10.0,
        "percent_score": 100.0,
        "is_passed": True,
        "allow_student_view_results": True,
        "questions": [
            {
                "content": r"Tính tích phân $I = \int_{0}^{\pi} \frac{\sin(x)}{\sqrt{1 + x^2}} dx$",
                "selected_choice_keys": ["k1"],
                "choices": [
                    {
                        "choice_key": "k1",
                        "content": r"Kết quả là $\frac{\pi}{2} \pm \epsilon$ với $\alpha \le \beta$",
                        "is_selected": True,
                    }
                ],
                "is_correct": True,
                "awarded_points": 10.0,
                "points_assigned": 10.0,
            }
        ],
    }
    pdf_bytes = build_attempt_result_pdf(sample_data)
    assert len(pdf_bytes) > 0

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "".join(page.extract_text() for page in reader.pages)

    # Math glyphs are actual vector outlines; prose remains extractable.
    normalized_text = " ".join(full_text.split())
    assert "Tính tích phân" in normalized_text
    assert "Kết quả là" in normalized_text
    assert b" c" in reader.pages[-1].get_contents().get_data()
    # Ensure raw LaTeX tokens were converted
    assert r"\frac" not in full_text
    assert r"\sqrt" not in full_text
    assert r"\int" not in full_text


def test_attempt_pdf_hides_results_when_allow_student_view_results_is_false():
    sample_data = {
        "candidate_name": "Lê Thị Bảo Mật",
        "candidate_email": "secret@pwd301.local",
        "assessment_title": "Khảo Thí Cuối Kỳ",
        "assessment_code": "SEC301",
        "duration_minutes": 90,
        "raw_score": 8.5,
        "max_score": 10.0,
        "percent_score": 85.0,
        "is_passed": True,
        "allow_student_view_results": False,
        "questions": [
            {
                "content": "Giao thức nào cung cấp mã hóa đầu cuối?",
                "selected_choice_keys": ["c1"],
                "choices": [
                    {"choice_key": "c1", "content": "TLS 1.3", "is_selected": True},
                    {"choice_key": "c2", "content": "HTTP", "is_selected": False},
                ],
                "is_correct": True,
                "awarded_points": 8.5,
                "points_assigned": 10.0,
            }
        ],
    }
    pdf_bytes = build_attempt_result_pdf(sample_data)
    assert len(pdf_bytes) > 0

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = "".join(page.extract_text() for page in reader.pages)

    # Hiding question details preserves the released total and pass/fail result.
    assert "ĐẠT CHUẨN MÔN HỌC" in full_text

    # Student selected choice text, correctness and awarded score are masked
    assert "TLS 1.3" not in full_text
    assert "8.5 / 10" in full_text
    assert "85%" in full_text
    # Question text remains visible
    assert "Giao thức nào cung cấp mã hóa đầu cuối?" in full_text


def test_disabled_pdf_has_three_truly_empty_question_cells(monkeypatch):
    from pwd301.services import result_pdf_service

    tables = []
    table_type = result_pdf_service.Table

    def capture_table(rows, *args, **kwargs):
        table = table_type(rows, *args, **kwargs)
        tables.append(rows)
        return table

    monkeypatch.setattr(result_pdf_service, "Table", capture_table)
    result_pdf_service.build_attempt_result_pdf(
        {
            "allow_student_view_results": False,
            "score_status": "RELEASED",
            "raw_score": 8,
            "max_score": 10,
            "passed": True,
            "questions": [
                {
                    "content": "VISIBLE QUESTION",
                    "student_answer_text": "SECRET",
                    "awarded_points": 8,
                }
            ],
        }
    )
    rows = next(rows for rows in tables if len(rows) > 1 and len(rows[0]) == 5)
    assert [
        cell.getPlainText() if hasattr(cell, "getPlainText") else cell for cell in rows[1][-3:]
    ] == ["", "", ""]


def test_pdf_math_is_true_offline_vector_and_mixed_text_wraps():
    from reportlab.lib.styles import ParagraphStyle

    from pwd301.services.pdf_math_service import math_paragraph, render_math_svg

    expression = r"\lim_{x\to0}\frac{\sin x}{x}+\begin{pmatrix}1&2\\3&4\end{pmatrix}"
    svg = render_math_svg(expression)
    assert b"<path" in svg
    assert b"<script" not in svg
    assert b"http://" not in svg.replace(b"http://www.w3.org/2000/svg", b"")
    flowable = math_paragraph(
        "Dẫn giải " + f"${expression}$" + " kết thúc " * 20,
        ParagraphStyle("MathTest", fontName="Helvetica", fontSize=9, leading=12),
    )
    assert flowable.wrap(150, 800)[1] > 24
    assert len(flowable.split(150, 35)) == 2


def test_offline_math_rejects_external_content_and_oversized_input():
    import pytest

    from pwd301.services.pdf_math_service import render_math_svg

    for expression in (r"\href{https://example.org}{x}", r"\require{html}", "x" * 5000):
        with pytest.raises(ValueError):
            render_math_svg(expression)


def test_offline_math_preserves_vietnamese_text_inside_formula():
    from pwd301.services.pdf_math_service import render_math_svg

    assert b"<text" in render_math_svg(r"\text{nếu }x>0")
    _, text = _pdf_text(
        build_attempt_result_pdf(
            {
                "raw_score": 1,
                "max_score": 1,
                "passed": True,
                "questions": [
                    {
                        "content": r"Xét $f(x)=x^2\text{ nếu }x>0$.",
                        "student_answer_text": r"$1\text{ nếu }x=1$",
                    }
                ],
            }
        )
    )
    assert "ế" in text
