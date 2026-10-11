"""Rendered document contracts for the two academic reference layouts."""

import io

import pypdf
import pytest

from pwd301.services.result_pdf_service import (
    build_assessment_gradebook_pdf,
    build_attempt_result_pdf,
)


@pytest.mark.parametrize(
    ("builder", "headings"),
    [
        (build_attempt_result_pdf, ["THÔNG TIN HỌC VIÊN & BÀI KIỂM TRA", "TỔNG QUAN KẾT QUẢ"]),
        (
            build_assessment_gradebook_pdf,
            ["THÔNG TIN KHÓA HỌC", "THÔNG TIN BÀI KIỂM TRA", "TỔNG HỢP KẾT QUẢ KHẢO THÍ"],
        ),
    ],
)
def test_reference_sections_are_visible_in_export(builder, headings):
    reader = pypdf.PdfReader(io.BytesIO(builder({})))
    text = " ".join(" ".join(page.extract_text() for page in reader.pages).split())
    for heading in headings:
        assert heading in text
    assert len(reader.pages) == 1


def test_gradebook_repeats_roster_header_and_preserves_every_candidate():
    attempts = [
        {
            "student_code": f"SV-{i:04}",
            "student_name": f"Nguyễn Thị Học Viên {i}",
            "score": 85.5,
            "is_passed": True,
        }
        for i in range(1, 91)
    ]
    reader = pypdf.PdfReader(io.BytesIO(build_assessment_gradebook_pdf({"attempts": attempts})))
    assert len(reader.pages) > 2
    texts = [page.extract_text() for page in reader.pages]
    combined = " ".join(" ".join(texts).split())
    for i in range(1, 91):
        assert f"SV-{i:04}" in combined
    for text in texts:
        assert text.count("Họ và tên thí sinh") <= 1
        if "SV-" in text:
            assert "Họ và tên thí sinh" in text
        assert "Trang" in text


def test_two_question_transcript_fits_a4_without_separating_notice():
    data = {
        "candidate_name": "Lê Hoàng Long",
        "candidate_email": "student1@pwd301.local",
        "assessment_title": "Kiểm tra Giữa kỳ: Cấu trúc Dữ liệu & Giải thuật Nâng cao",
        "assessment_code": "DSA201",
        "instructor_name": "ThS. Trần Thị B",
        "raw_score": 0,
        "max_score": 100,
        "is_passed": False,
        "questions": [
            {
                "content": "Độ phức tạp thời gian trung bình của giải thuật QuickSort khi phân hoạch ngẫu nhiên là gì?",
                "student_answer_text": "O(n^2)",
                "is_correct": False,
                "awarded_points": 0,
                "points_assigned": 50,
            },
            {
                "content": "Để xây dựng một Binary Heap từ một mảng n phần tử cho trước, thời gian tối ưu đạt được là bao nhiêu?",
                "student_answer_text": "O(n log n)",
                "is_correct": False,
                "awarded_points": 0,
                "points_assigned": 50,
            },
        ],
    }
    reader = pypdf.PdfReader(io.BytesIO(build_attempt_result_pdf(data)))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Binary Heap" in text
    assert "phúc khảo" in text


def test_overheight_question_does_not_leave_empty_table_pages():
    reader = pypdf.PdfReader(
        io.BytesIO(
            build_attempt_result_pdf(
                {
                    "questions": [
                        {
                            "content": "Giải thích a < b & c > d. " * 180 + "KẾT THÚC CÂU HỎI",
                            "student_answer_text": "<b>Đáp án là văn bản nguyên gốc</b> " * 60
                            + "KẾT THÚC ĐÁP ÁN",
                        }
                    ],
                }
            )
        )
    )
    for page in reader.pages:
        text = page.extract_text()
        assert text.count("Nội dung câu hỏi") <= 1
        if "Nội dung câu hỏi" in text:
            assert "Giải thích" in text or "Đáp án" in text
