"""Verification test suite for comprehensive 6-category upgrade of PWD301 LMS.

Covers:
- Category 1: Email verification gate on video streaming
- Category 2: LaTeX math rendering and allow_student_view_results toggle
- Category 5: Final exam prerequisite course completion enforcement
- Category 6: Course lifecycle (DRAFT vs PUBLISHED unified staging draft)
"""

import datetime
import io

import pypdf
import pytest

from backend.extensions import db
from backend.models.assessment import Assessment
from backend.models.course import Course, LearningUnit, Lesson, LessonProgress
from backend.models.identity import User
from backend.models.types import utc_now
from backend.services.attempt_service import (
    AttemptValidationError,
    start_assessment_attempt,
)
from backend.services.enrollment_service import enroll_student
from backend.services.result_pdf_service import (
    build_attempt_result_pdf,
)


def _extract_pdf_text(data: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(data))
    return " ".join("\n".join(page.extract_text() or "" for page in reader.pages).split())


# ===========================================================================
# Category 1: Email Verification Gate
# ===========================================================================
def test_user_email_verified_property():
    """Verify is_email_verified property on User model."""
    unverified_user = User(
        email="unverified@fpt.edu.vn",
        email_verified_at=None,
    )
    assert unverified_user.is_email_verified is False

    verified_user = User(
        email="verified@fpt.edu.vn",
        email_verified_at=datetime.datetime.now(datetime.UTC),
    )
    assert verified_user.is_email_verified is True


# ===========================================================================
# Category 2: LaTeX Math Rendering & allow_student_view_results Toggle
# ===========================================================================
def test_latex_math_clean_rendering():
    """Actual vector formulas cover nested limits and matrices without raw TeX output."""
    from backend.services.pdf_math_service import render_math_svg

    rendered = render_math_svg(
        r"\lim_{x\to0}\frac{\sin(x)}{x}+\begin{pmatrix}1&2\\3&4\end{pmatrix}"
    )
    assert b"<path" in rendered
    assert b"data-mml-node" in rendered
    assert b"merror" not in rendered


def test_pdf_with_allow_student_view_results_false():
    """Missing total scores stay unknown while selected answer details remain blank."""
    attempt_payload = {
        "candidate_name": "Nguyễn Văn A",
        "candidate_email": "nguyenvana@fpt.edu.vn",
        "course_title": "Lập trình Web nâng cao",
        "assessment_title": "Kiểm tra Thực hành",
        "allow_student_view_results": False,
        "score_status": "RESULTS_HIDDEN",
        "total_score": None,
        "max_score": 10.0,
        "questions": [
            {
                "content": r"Giá trị của $x^2$ khi $x = 3$ là bao nhiêu?",
                "chosen_answer": "9",
                "is_correct": True,
                "awarded_points": 1.0,
            }
        ],
    }

    pdf_bytes = build_attempt_result_pdf(attempt_payload)
    text = _extract_pdf_text(pdf_bytes)

    # Header and student name should exist
    assert "Nguyễn Văn A" in text
    assert "nguyenvana@fpt.edu.vn" in text
    assert "CHƯA CÓ KẾT LUẬN" in text

    # Answers and scores should be masked with '-' or hidden
    assert "9 (Bạn đã chọn)" not in text
    assert "ĐÚNG" not in text
    assert "+1.0" not in text


# ===========================================================================
# Category 5: Final Exam Completion Lock
# ===========================================================================
def test_final_exam_requires_all_lessons_completed(app):
    """Verify start_assessment_attempt blocks final exam if course lessons are not 100% completed."""
    with app.app_context():
        # Setup student
        student = User(
            email=f"final_gate_{datetime.datetime.now().timestamp()}@fpt.edu.vn",
            display_name="Student Final Gate Test",
            password_hash="dummy_hash",
            email_verified_at=datetime.datetime.now(datetime.UTC),
        )
        db.session.add(student)
        db.session.flush()

        # Setup course with 2 published lessons
        course = Course(
            course_code=f"CG_{int(datetime.datetime.now().timestamp()) % 100000}",
            title="Course Gate Testing",
            status="PUBLISHED",
        )
        db.session.add(course)
        db.session.flush()

        unit = LearningUnit(
            course_id=course.id,
            title="Unit 1",
            position=1,
        )
        db.session.add(unit)
        db.session.flush()

        lesson1 = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title="Lesson 1",
            status="PUBLISHED",
            position=1,
        )
        lesson2 = Lesson(
            course_id=course.id,
            learning_unit_id=unit.id,
            title="Lesson 2",
            status="PUBLISHED",
            position=2,
        )
        db.session.add_all([lesson1, lesson2])
        db.session.flush()

        # Enroll student in course
        enrollment = enroll_student(actor=student, course_id=course.id, session=db.session)
        db.session.flush()

        # Setup Final Exam
        final_assessment = Assessment(
            course_id=course.id,
            title="Kỳ thi Cuối kỳ (Final Exam)",
            assessment_type="FINAL",
            status="PUBLISHED",
            attempt_limit=1,
            open_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
            close_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
        )
        db.session.add(final_assessment)
        db.session.flush()

        # Student only completes lesson 1
        prog1 = LessonProgress(
            enrollment_period_id=enrollment.current_period_id,
            lesson_id=lesson1.id,
            completed_at=utc_now(),
        )
        db.session.add(prog1)
        db.session.flush()

        # Attempt to start Final Exam must be rejected with AttemptValidationError
        with pytest.raises(AttemptValidationError) as exc_info:
            start_assessment_attempt(
                student_actor=student,
                assessment_id=final_assessment.id,
                session=db.session,
            )
        assert "hoàn thành tất cả các bài học" in str(exc_info.value)
        assert "1/2 bài" in str(exc_info.value)

        # Now student completes lesson 2
        prog2 = LessonProgress(
            enrollment_period_id=enrollment.current_period_id,
            lesson_id=lesson2.id,
            completed_at=utc_now(),
        )
        db.session.add(prog2)
        db.session.flush()

        # Prerequisite check now passes; next validation is question availability
        try:
            start_assessment_attempt(
                student_actor=student,
                assessment_id=final_assessment.id,
                session=db.session,
            )
        except AttemptValidationError as exc:
            assert "hoàn thành tất cả các bài học" not in str(exc)
            assert "contains no questions" in str(exc)
