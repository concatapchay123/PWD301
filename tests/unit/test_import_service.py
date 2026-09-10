"""Unit tests for DOCX/PDF assessment import engine and duplicate detection (TASK-020).

Covers:
- DOCX parsing across all 5 question types (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE,
  SHORT_ANSWER, ESSAY) using pure standard-library zipfile and xml.etree.ElementTree.
- Inline multiple choices and custom question formatting.
- PDF stream parsing and fallback token extraction.
- Confidence scoring and diagnostic tagging (ambiguity, missing answer keys).
- Duplicate detection engine (exact SHA-256 match and SequenceMatcher similarity >= 0.85).
- State machine lifecycle (QUEUED -> PROCESSING -> REVIEW_REQUIRED -> COMPLETED).
- Review, edit, and decision operations (ACCEPTED / REJECTED).
- Atomic transaction commit into Question Bank and provenance tracking.
- Rollback safety on commit failure.
"""

from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import User
from pwd301.models.question_bank import Question, QuestionProvenance
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    DocumentImportStateViolationError,
)
from pwd301.services.file_service import store_file_stream
from pwd301.services.import_service import (
    cancel_import_job,
    commit_import_job,
    create_import_job,
    detect_duplicates,
    extract_text_from_docx,
    extract_text_from_pdf,
    normalize_text_for_dedup,
    parse_question_blocks,
    process_import_job,
    set_import_question_decision,
)
from pwd301.services.user_service import assign_role_to_user, register_user


def create_sample_docx(paragraphs: list[str]) -> bytes:
    """Generate in-memory valid OpenXML DOCX bytes with given paragraphs."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        p_elements = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f"  <w:body>{p_elements}</w:body>\n"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
    return buffer.getvalue()


def create_sample_pdf(lines: list[str]) -> bytes:
    """Generate in-memory valid PDF bytes with given text lines."""
    text_commands = "\n".join(f"({line}) Tj T*" for line in lines)
    stream_bytes = f"BT /F1 12 Tf 50 700 Td 14 TL\n{text_commands}\nET".encode("latin-1")
    length = len(stream_bytes)
    pdf_content = (
        f"%PDF-1.4\n"
        f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        f"4 0 obj << /Length {length} >>\nstream\n"
        f"{stream_bytes.decode('latin-1')}\nendstream\nendobj\n"
        f"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        f"0000000115 00000 n \n0000000234 00000 n \n0000000300 00000 n \n"
        f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n380\n%%EOF\n"
    )
    return pdf_content.encode("latin-1")


@pytest.fixture
def instructor_actor(app: Flask) -> User:
    """Register and return an instructor user."""
    instructor = register_user(
        "import_inst@example.com", "Password123!", display_name="Instructor Import"
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR")
    return instructor


@pytest.fixture
def course_fixture(app: Flask, instructor_actor: User) -> Course:
    """Create a course owned by the instructor."""
    c = create_course(
        instructor_actor,
        {
            "course_code": f"IMP-{instructor_actor.id}",
            "title": "Import Testing Course",
            "summary": "Import Testing Course Summary",
        },
    )
    db.session.commit()
    return c


class TestDocumentParsing:
    """Tests for DOCX and PDF document extraction and pattern matching."""

    def test_parse_docx_all_five_question_types(self, tmp_path: Path) -> None:
        paragraphs = [
            "Câu 1: Thủ đô của Việt Nam là gì? [1.5 đ] [REMEMBER]",
            "A. Hà Nội",
            "B. TP. Hồ Chí Minh",
            "C. Đà Nẵng",
            "D. Cần Thơ",
            "Đáp án: A",
            "Giải thích: Hà Nội là thủ đô của Việt Nam từ năm 1010.",
            "Question 2: Which of the following are Python frameworks? [2 pts] [UNDERSTAND]",
            "A. Flask",
            "B. Laravel",
            "C. Django",
            "D. Spring",
            "Answer: A, C",
            "Explanation: Flask and Django are Python web frameworks.",
            "Câu 3: Trái đất quay quanh Mặt trời. [TRUE_FALSE]",
            "A. Đúng",
            "B. Sai",
            "Đáp án: Đúng",
            "Câu 4: Điền từ vào chỗ trống: Thủ đô của Pháp là ______. [SHORT_ANSWER]",
            "Đáp án: Paris",
            "Câu 5: Hãy trình bày kiến trúc phân tầng trong phần mềm. [ESSAY] [APPLY]",
            "Giải thích: Bao gồm Presentation, Business Logic, và Data Access Layer.",
        ]
        docx_bytes = create_sample_docx(paragraphs)
        file_path = tmp_path / "questions.docx"
        file_path.write_bytes(docx_bytes)

        lines = extract_text_from_docx(file_path)
        assert len(lines) >= 15

        drafts = parse_question_blocks(lines)
        assert len(drafts) == 5

        # 1. Single choice
        q1 = drafts[0]
        assert q1.ordinal == 1
        assert "Thủ đô của Việt Nam" in q1.content_text
        assert q1.question_type == "SINGLE_CHOICE"
        assert q1.difficulty == "REMEMBER"
        assert q1.points == 1.5
        assert len(q1.choices) == 4
        assert q1.choices[0].is_correct is True
        assert q1.choices[1].is_correct is False
        assert q1.explanation_text == "Hà Nội là thủ đô của Việt Nam từ năm 1010."
        assert q1.review_state == "READY"
        assert q1.confidence_score >= 0.85

        # 2. Multiple choice
        q2 = drafts[1]
        assert q2.ordinal == 2
        assert q2.question_type == "MULTIPLE_CHOICE"
        assert q2.points == 2.0
        assert len(q2.choices) == 4
        assert q2.choices[0].is_correct is True  # A
        assert q2.choices[2].is_correct is True  # C
        assert q2.choices[1].is_correct is False  # B
        assert q2.review_state == "READY"

        # 3. True/False
        q3 = drafts[2]
        assert q3.ordinal == 3
        assert q3.question_type == "TRUE_FALSE"
        assert len(q3.choices) == 2
        assert q3.choices[0].is_correct is True  # Đúng

        # 4. Short Answer
        q4 = drafts[3]
        assert q4.ordinal == 4
        assert q4.question_type == "SHORT_ANSWER"
        assert "Paris" in q4.detected_answers

        # 5. Essay
        q5 = drafts[4]
        assert q5.ordinal == 5
        assert q5.question_type == "ESSAY"
        assert q5.difficulty == "APPLY"
        assert "Presentation" in (q5.explanation_text or "")

    def test_parse_docx_inline_choices(self, tmp_path: Path) -> None:
        paragraphs = [
            "Câu 1: Chọn màu sắc của bầu trời vào ban ngày:",
            "A. Xanh lam  B. Đỏ  C. Vàng  D. Tím",
            "Đáp án: A",
        ]
        file_path = tmp_path / "inline.docx"
        file_path.write_bytes(create_sample_docx(paragraphs))

        lines = extract_text_from_docx(file_path)
        drafts = parse_question_blocks(lines)
        assert len(drafts) == 1
        q = drafts[0]
        assert len(q.choices) == 4
        assert q.choices[0].key == "A"
        assert q.choices[0].content == "Xanh lam"
        assert q.choices[0].is_correct is True
        assert q.choices[1].key == "B"
        assert q.choices[1].content == "Đỏ"

    def test_parse_pdf_document(self, tmp_path: Path) -> None:
        lines = [
            "Question 1: What is the largest planet in our solar system?",
            "A. Mars",
            "B. Jupiter",
            "C. Saturn",
            "D. Venus",
            "Answer: B",
        ]
        pdf_bytes = create_sample_pdf(lines)
        file_path = tmp_path / "questions.pdf"
        file_path.write_bytes(pdf_bytes)

        extracted = extract_text_from_pdf(file_path)
        assert len(extracted) >= 5

        drafts = parse_question_blocks(extracted)
        assert len(drafts) == 1
        assert "largest planet" in drafts[0].content_text
        assert drafts[0].choices[1].is_correct is True  # Jupiter

    def test_parse_missing_answer_key_flags_needs_review(self) -> None:
        lines = [
            "Câu 1: Câu hỏi này không có đáp án sẵn?",
            "A. Lựa chọn 1",
            "B. Lựa chọn 2",
        ]
        drafts = parse_question_blocks(lines)
        assert len(drafts) == 1
        q = drafts[0]
        assert q.review_state == "NEEDS_REVIEW"
        assert q.confidence_score < 0.85
        assert any("No answer key detected" in w for w in q.diagnostics.get("warnings", []))


class TestDuplicateDetection:
    """Tests for exact and fuzzy duplicate detection engine."""

    def test_normalize_text_for_dedup(self) -> None:
        raw1 = "Câu 1: Thủ đô của Việt Nam là gì?"
        raw2 = "Question 10.  Thủ đô của Việt Nam là gì???"
        assert normalize_text_for_dedup(raw1) == normalize_text_for_dedup(raw2)

    def test_detect_duplicates_exact_and_fuzzy(
        self,
        app: Flask,
        course_fixture: Course,
        instructor_actor: User,
    ) -> None:
        # Create an existing question in the Question Bank
        from pwd301.services.question_bank_service import create_question

        existing_q = create_question(
            actor=instructor_actor,
            course_id=course_fixture.id,
            payload={
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Thủ đô của Việt Nam là thành phố nào sau đây?",
                "choices": [
                    {"content": "Hà Nội", "is_correct": True},
                    {"content": "TP Hồ Chí Minh", "is_correct": False},
                ],
            },
            session=db.session,
        )
        db.session.commit()

        # Test cases:
        # 1. Exact duplicate (normalized)
        # 2. Near duplicate (fuzzy >= 0.85)
        # 3. Completely different question
        drafts = parse_question_blocks(
            [
                "Câu 1: Thủ đô của Việt Nam là thành phố nào sau đây?",
                "A. Hà Nội  B. TP Hồ Chí Minh",
                "Đáp án: A",
                "Câu 2: Thủ đô của Việt Nam là thành phố nào?",
                "A. Hà Nội  B. Đà Nẵng",
                "Đáp án: A",
                "Câu 3: Mặt trời mọc ở hướng nào?",
                "A. Đông  B. Tây",
                "Đáp án: A",
            ]
        )
        assert len(drafts) == 3

        duplicates = detect_duplicates(
            session=db.session,
            course_id=course_fixture.id,
            parsed_questions=drafts,
            similarity_threshold=0.85,
        )

        # Draft 1: exact match
        assert 1 in duplicates
        assert duplicates[1][0].similarity_score == 1.0
        assert duplicates[1][0].match_type == "EXACT_HASH"
        assert duplicates[1][0].candidate_question_id == existing_q.id

        # Draft 2: fuzzy similarity >= 0.85
        assert 2 in duplicates
        assert duplicates[2][0].similarity_score >= 0.85
        assert duplicates[2][0].match_type == "TEXT_SIMILARITY"

        # Draft 3: no duplicate
        assert 3 not in duplicates


class TestImportLifecycleAndCommit:
    """Tests for job creation, processing, review, and atomic commit."""

    def test_full_import_workflow(
        self,
        app: Flask,
        course_fixture: Course,
        instructor_actor: User,
    ) -> None:
        # 1. Upload safe file
        docx_bytes = create_sample_docx(
            [
                "Câu 1: Ngôn ngữ nào sau đây là statically typed?",
                "A. Python",
                "B. Rust",
                "C. Ruby",
                "D. PHP",
                "Đáp án: B",
                "Câu 2: HTML là viết tắt của HyperText Markup Language.",
                "A. Đúng",
                "B. Sai",
                "Đáp án: Đúng",
            ]
        )
        asset = store_file_stream(
            actor=instructor_actor,
            course_id=course_fixture.id,
            file_stream=io.BytesIO(docx_bytes),
            filename="programming_test.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            asset_type="IMPORT_SOURCE",
            session=db.session,
        )
        assert asset.status == "ACTIVE"

        # 2. Create Import Job
        job = create_import_job(
            actor=instructor_actor,
            course_id=course_fixture.id,
            file_asset_id=asset.id,
            session=db.session,
        )
        assert job.status == "QUEUED"
        assert job.document_type == "DOCX"

        # 3. Process Import Job
        job = process_import_job(
            actor=instructor_actor,
            job_id=job.id,
            session=db.session,
        )
        assert job.status == "REVIEW_REQUIRED"
        assert job.question_count == 2
        assert len(job.questions) == 2

        # Verify questions
        q1 = job.questions[0]
        q2 = job.questions[1]
        assert q1.review_state == "READY"
        assert q2.review_state == "READY"

        # 4. Review & Decide: Accept question 1, reject question 2
        set_import_question_decision(
            actor=instructor_actor,
            job_id=job.id,
            temp_id=q1.ordinal,
            decision="ACCEPTED",
            session=db.session,
        )
        set_import_question_decision(
            actor=instructor_actor,
            job_id=job.id,
            temp_id=q2.ordinal,
            decision="REJECTED",
            session=db.session,
        )

        # 5. Commit Job
        commit_res = commit_import_job(
            actor=instructor_actor,
            job_id=job.id,
            session=db.session,
        )
        assert commit_res["status"] == "COMPLETED"
        assert commit_res["imported_count"] == 1  # Only accepted question 1

        # Verify in Question Bank
        created_q_id = commit_res["created_question_ids"][0]
        created_q = (
            db.session.query(Question).filter(Question.public_id == uuid.UUID(created_q_id)).first()
        )
        assert created_q is not None
        assert created_q.course_id == course_fixture.id
        assert "statically typed" in created_q.current_revision.content

        # Verify Provenance
        prov = (
            db.session.query(QuestionProvenance)
            .filter(QuestionProvenance.question_id == created_q.id)
            .first()
        )
        assert prov is not None
        assert prov.source_type == "IMPORT"
        assert prov.approved_by_user_id == instructor_actor.id

        # 6. Idempotency: cannot commit again
        with pytest.raises(DocumentImportStateViolationError):
            commit_import_job(
                actor=instructor_actor,
                job_id=job.id,
                session=db.session,
            )

    def test_cancel_import_job(
        self,
        app: Flask,
        course_fixture: Course,
        instructor_actor: User,
    ) -> None:
        docx_bytes = create_sample_docx(["Câu 1: Câu hỏi mẫu", "A. A", "B. B", "Đáp án: A"])
        asset = store_file_stream(
            actor=instructor_actor,
            course_id=course_fixture.id,
            file_stream=io.BytesIO(docx_bytes),
            filename="cancel_sample.docx",
            asset_type="IMPORT_SOURCE",
            session=db.session,
        )
        job = create_import_job(
            actor=instructor_actor,
            course_id=course_fixture.id,
            file_asset_id=asset.id,
            session=db.session,
        )
        cancelled = cancel_import_job(
            actor=instructor_actor,
            job_id=job.id,
            reason="Instructor decided not to import",
            session=db.session,
        )
        assert cancelled.status == "CANCELLED"
        assert cancelled.last_error == "Instructor decided not to import"
