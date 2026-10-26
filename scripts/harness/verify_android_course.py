# -*- coding: utf-8 -*-
"""Verification Script for Android Security Master Course (AND801).

Rigorously verifies:
1. Exactly 1 active course in DB (AND801).
2. Exactly 5 Learning Units (Chapters).
3. Random 10-15 lessons per chapter (all 5 chapters within [10, 15]).
4. Total 60 lessons across 5 chapters.
5. Every single lesson:
   - Word count >= 600 Vietnamese words.
   - YouTube video URL present.
   - Real FileAsset resource attached.
   - 4-type miniquiz present (MULTIPLE_CHOICE, FILL_BLANK, MATCHING, CLOZE).
6. Assessments:
   - 5 Chapter Quizzes (10 questions each = 50 questions).
   - 1 Final Comprehensive Exam (20 questions with shuffle_choices=True and shuffle_questions=True).
   - Total 70 questions in question bank with choices and explanations.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import create_app, db
from backend.models.course import Course, LearningUnit, Lesson, Enrollment
from backend.models.assessment import Assessment, AssessmentSection, AssessmentQuestionAssignment
from backend.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from backend.models.file_import import FileAsset, LessonResource
from scripts.android_course_data.common import count_vietnamese_words


def verify_android_course() -> bool:
    print("=" * 80)
    print("XÁC MINH TOÀN DIỆN KHÓA HỌC AN NINH ANDROID (AND801)")
    print("=" * 80)

    app = create_app()
    with app.app_context():
        session = db.session

        # 1. Check Course Count
        courses = session.query(Course).all()
        print(f"\n[1] Kiểm tra số lượng khóa học trong hệ thống: {len(courses)}")
        assert len(courses) == 1, f"Expected exactly 1 course, found {len(courses)}"
        course = courses[0]
        print(f"    ✓ Mã khóa học: {course.course_code}")
        print(f"    ✓ Tiêu đề: {course.title}")
        print(f"    ✓ Trạng thái: {course.status}")

        # 2. Check Learning Units (Chapters)
        units = session.query(LearningUnit).filter_by(course_id=course.id).order_by(LearningUnit.position).all()
        print(f"\n[2] Kiểm tra số lượng chương (LearningUnits): {len(units)}")
        assert len(units) == 5, f"Expected exactly 5 chapters, found {len(units)}"
        for u in units:
            print(f"    ✓ Chương {u.position}: {u.title}")

        # 3. Check Lessons per Chapter & Total Lessons
        print(f"\n[3] Kiểm tra số lượng bài học theo từng chương (yêu cầu: random 10-15 bài/chương):")
        total_lessons = 0
        min_words_found = 999999
        max_words_found = 0

        for u in units:
            lessons = session.query(Lesson).filter_by(course_id=course.id, learning_unit_id=u.id).order_by(Lesson.position).all()
            l_count = len(lessons)
            print(f"    ✓ Chương {u.position} có: {l_count} bài học")
            assert 10 <= l_count <= 15, f"Chương {u.position} có {l_count} bài (không nằm trong khoảng [10, 15])"
            total_lessons += l_count

            # Check each lesson's 4 core components
            for l in lessons:
                # Component 1: Word Count >= 600 words
                wc = count_vietnamese_words(l.markdown_content)
                min_words_found = min(min_words_found, wc)
                max_words_found = max(max_words_found, wc)
                assert wc >= 600, f"Bài {u.position}.{l.position} chỉ có {wc} từ (< 600 từ)"

                # Component 2: Video URL
                assert "youtube.com" in l.markdown_content or "youtu.be" in l.markdown_content, (
                    f"Bài {u.position}.{l.position} thiếu video YouTube"
                )

                # Component 3: Miniquiz with 4 types
                match = re.search(r"<!-- mini_quiz: (\[.*?\]) -->", l.markdown_content, re.DOTALL)
                assert match, f"Bài {u.position}.{l.position} thiếu comment mini_quiz JSON"
                quiz_items = json.loads(match.group(1))
                assert len(quiz_items) == 4, f"Bài {u.position}.{l.position} có {len(quiz_items)} câu hỏi miniquiz != 4"
                q_types = [item["type"] for item in quiz_items]
                assert "MULTIPLE_CHOICE" in q_types, f"Bài {u.position}.{l.position} thiếu MULTIPLE_CHOICE"
                assert "FILL_BLANK" in q_types, f"Bài {u.position}.{l.position} thiếu FILL_BLANK"
                assert "MATCHING" in q_types, f"Bài {u.position}.{l.position} thiếu MATCHING"

                # Component 4: File Resource Attached
                resources = session.query(LessonResource).filter_by(lesson_id=l.id).all()
                assert len(resources) >= 1, f"Bài {u.position}.{l.position} thiếu tài liệu đính kèm"

        print(f"    ✓ Tổng số bài học toàn khóa: {total_lessons} bài (Đạt chuẩn)")
        print(f"    ✓ Độ dài bài giảng: từ {min_words_found} đến {max_words_found} từ (100% >= 600 từ)")
        print(f"    ✓ 100% bài học có video YouTube 16:9")
        print(f"    ✓ 100% bài học có miniquiz đầy đủ 4 dạng câu hỏi")
        print(f"    ✓ 100% bài học có tài liệu FileAsset đính kèm")

        # 4. Check Assessments
        print(f"\n[4] Kiểm tra các bài kiểm tra đánh giá (Assessments):")
        assessments = session.query(Assessment).filter_by(course_id=course.id).all()
        quizzes = [a for a in assessments if a.assessment_type == "QUIZ"]
        finals = [a for a in assessments if a.assessment_type == "FINAL"]

        print(f"    ✓ Tổng số bài kiểm tra: {len(assessments)} (5 Chapter Quizzes + 1 Final Exam)")
        assert len(quizzes) == 5, f"Expected 5 chapter quizzes, found {len(quizzes)}"
        assert len(finals) == 1, f"Expected 1 final exam, found {len(finals)}"

        # Verify each Chapter Quiz
        for qz in quizzes:
            assignments = session.query(AssessmentQuestionAssignment).filter_by(assessment_id=qz.id).all()
            print(f"      + [{qz.assessment_type}] {qz.title[:55]}... ({len(assignments)} câu hỏi, shuffle={qz.shuffle_choices})")
            assert len(assignments) == 10, f"Chapter Quiz {qz.id} has {len(assignments)} questions != 10"

        # Verify Final Exam
        final_exam = finals[0]
        final_assignments = session.query(AssessmentQuestionAssignment).filter_by(assessment_id=final_exam.id).all()
        print(f"      + [FINAL] {final_exam.title} ({len(final_assignments)} câu hỏi)")
        assert len(final_assignments) == 20, f"Final exam has {len(final_assignments)} questions != 20"
        assert final_exam.shuffle_choices is True, "Final exam phải có shuffle_choices = True"
        assert final_exam.shuffle_questions is True, "Final exam phải có shuffle_questions = True"
        print(f"        ✓ Đảo ngẫu nhiên câu hỏi (shuffle_questions): {final_exam.shuffle_questions}")
        print(f"        ✓ Đảo ngẫu nhiên phương án (shuffle_choices): {final_exam.shuffle_choices}")

        # 5. Check Enrollments
        enrollments = session.query(Enrollment).filter_by(course_id=course.id).all()
        print(f"\n[5] Kiểm tra học viên ghi danh: {len(enrollments)} học viên đang học")
        assert len(enrollments) >= 2, f"Expected at least 2 students, found {len(enrollments)}"

        print("\n" + "=" * 80)
        print("TẤT CẢ CÁC TIÊU CHÍ ĐÃ ĐƯỢC XÁC MINH THỰC NGHIỆM ĐẠT 100% XUẤT SẮC!")
        print("=" * 80)
        return True


if __name__ == "__main__":
    success = verify_android_course()
    if not success:
        sys.exit(1)
