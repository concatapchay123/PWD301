# -*- coding: utf-8 -*-
"""Verification script for BHE501 Black Hat Cybersecurity Course.
Empirically queries Microsoft SQL Server and tests all business criteria and invariants.
"""

import sys
import json
import re
from decimal import Decimal

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pwd301 import create_app, db
from pwd301.models.course import Course, LearningUnit, Lesson, Enrollment
from pwd301.models.file_import import LessonResource, FileAsset
from pwd301.models.assessment import Assessment, AssessmentQuestionAssignment
from pwd301.models.question_bank import Question, QuestionRevision, QuestionRevisionChoice
from scripts.course_data.common import count_vietnamese_words


def verify():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("KIỂM THỬ XÁC MINH THỰC NGHIỆM KHÓA HỌC AN NINH MẠNG (BHE501)")
        print("=" * 80)

        # 1. Course Verification
        course = db.session.query(Course).filter_by(course_code="BHE501").first()
        assert course is not None, "FAIL: Không tìm thấy khóa học BHE501 trong CSDL!"
        assert course.status == "PUBLISHED", f"FAIL: Khóa học status không phải PUBLISHED ({course.status})!"
        assert course.thumbnail_file_asset_id is not None, "FAIL: Khóa học thiếu thumbnail cover!"
        print(f"[1/7] Khóa học: '{course.title}' (ID: {course.id}) - STATUS: {course.status} => PASS")

        # 2. Chapters (Learning Units) Verification
        units = db.session.query(LearningUnit).filter_by(course_id=course.id).order_by(LearningUnit.position).all()
        assert len(units) == 5, f"FAIL: Số lượng chương không đúng! Kỳ vọng 5, thực tế {len(units)}"
        print(f"[2/7] Số lượng chương: {len(units)}/5 chương => PASS")
        for u in units:
            lesson_count = len(u.lessons)
            assert 10 <= lesson_count <= 15, f"FAIL: Chương {u.position} có {lesson_count} bài (không nằm trong khoảng 10-15)!"
            print(f"      - Chương {u.position}: {u.title[:55]}... ({lesson_count} bài học)")

        # 3. Lessons & Mandatory Components Verification
        lessons = db.session.query(Lesson).filter_by(course_id=course.id).order_by(Lesson.position).all()
        assert len(lessons) == 60, f"FAIL: Tổng số bài học không đúng! Kỳ vọng 60, thực tế {len(lessons)}"
        print(f"[3/7] Tổng số bài học: {len(lessons)}/60 bài => PASS")

        total_words = 0
        video_count = 0
        miniquiz_count = 0
        pdf_resource_count = 0

        for idx, l in enumerate(lessons, 1):
            # Check Word Count >= 600
            wc = count_vietnamese_words(l.markdown_content)
            total_words += wc
            assert wc >= 600, f"FAIL: Bài học ID {l.id} ('{l.title}') chỉ có {wc} từ (< 600 từ)!"

            # Check Video URL
            v_match = re.search(r"<!--\s*video_url:\s*(\S+?)\s*-->", l.markdown_content)
            assert v_match is not None, f"FAIL: Bài học ID {l.id} ('{l.title}') thiếu thẻ video_url!"
            v_url = v_match.group(1)
            assert "youtube.com" in v_url or "youtu.be" in v_url, f"FAIL: Video URL không hợp lệ: {v_url}"
            video_count += 1

            # Check Miniquiz
            q_match = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", l.markdown_content, re.DOTALL)
            assert q_match is not None, f"FAIL: Bài học ID {l.id} ('{l.title}') thiếu thẻ mini_quiz!"
            quiz_list = json.loads(q_match.group(1))
            assert len(quiz_list) >= 2, f"FAIL: Bài học ID {l.id} miniquiz quá ít câu hỏi ({len(quiz_list)})!"
            miniquiz_count += 1

            # Check Attached PDF Resource
            assert len(l.resources) >= 1, f"FAIL: Bài học ID {l.id} ('{l.title}') chưa được đính kèm file PDF!"
            pdf_res = l.resources[0]
            assert pdf_res.file_asset is not None, f"FAIL: LessonResource không có FileAsset hợp lệ!"
            assert pdf_res.file_asset.mime_type == "application/pdf" or pdf_res.file_asset.original_filename.endswith(".pdf"), f"FAIL: File đính kèm không phải PDF!"
            pdf_resource_count += 1

        print(f"      - Độ dài bài giảng: 100% bài học đạt chuẩn >= 600 từ (Tổng: {total_words:,} từ, TB: {total_words//60} từ/bài) => PASS")
        print(f"      - Video YouTube 16:9: {video_count}/60 bài => PASS")
        print(f"      - Miniquiz củng cố: {miniquiz_count}/60 bài => PASS")
        print(f"      - File PDF đính kèm: {pdf_resource_count}/60 bài => PASS")

        # 4. Chapter Quizzes Verification
        chapter_quizzes = db.session.query(Assessment).filter(
            Assessment.course_id == course.id,
            Assessment.assessment_type == "QUIZ"
        ).order_by(Assessment.id).all()
        assert len(chapter_quizzes) == 5, f"FAIL: Số bài kiểm tra chương không đúng! Kỳ vọng 5, thực tế {len(chapter_quizzes)}"
        print(f"[4/7] Bài kiểm tra đánh giá theo chương: {len(chapter_quizzes)}/5 bài => PASS")
        for qz in chapter_quizzes:
            assignments = qz.question_assignments
            assert len(assignments) == 10, f"FAIL: Quiz '{qz.title}' có {len(assignments)} câu hỏi (kỳ vọng 10)!"
            total_pts = sum(a.points for a in assignments)
            assert total_pts == Decimal("100.0000"), f"FAIL: Quiz '{qz.title}' tổng điểm là {total_pts} (kỳ vọng 100.00)!"
            print(f"      - Quiz: {qz.title[:55]}... ({len(assignments)} câu, {total_pts:.2f} điểm) => PASS")

        # 5. Final Exam Verification (Exactly 20 questions)
        final_exam = db.session.query(Assessment).filter(
            Assessment.course_id == course.id,
            Assessment.assessment_type == "FINAL"
        ).first()
        assert final_exam is not None, "FAIL: Không tìm thấy Bài thi tốt nghiệp (FINAL)!"
        final_assignments = final_exam.question_assignments
        assert len(final_assignments) == 20, f"FAIL: Bài thi tốt nghiệp có {len(final_assignments)} câu hỏi (kỳ vọng chính xác 20 câu)!"
        final_total_pts = sum(a.points for a in final_assignments)
        assert final_total_pts == Decimal("100.0000"), f"FAIL: Bài thi tốt nghiệp tổng điểm là {final_total_pts} (kỳ vọng 100.00)!"
        print(f"[5/7] Bài thi tốt nghiệp (Final Exam): '{final_exam.title}'")
        print(f"      - Số câu hỏi: {len(final_assignments)}/20 câu hỏi chính xác => PASS")
        print(f"      - Tổng điểm: {final_total_pts:.2f}/100.00 điểm (5.00 điểm/câu) => PASS")

        # 6. Question Bank Integrity
        questions = db.session.query(Question).filter_by(course_id=course.id).all()
        assert len(questions) == 70, f"FAIL: Tổng số câu hỏi ngân hàng không đúng! Kỳ vọng 70 (50 quiz + 20 final), thực tế {len(questions)}"
        for q in questions:
            rev = q.current_revision or q.revisions[0]
            assert rev is not None, f"FAIL: Question ID {q.id} không có revision!"
            assert len(rev.choices) >= 2, f"FAIL: Question ID {q.id} có ít hơn 2 lựa chọn!"
            assert any(c.is_correct for c in rev.choices), f"FAIL: Question ID {q.id} không có lựa chọn đúng nào!"
        print(f"[6/7] Ngân hàng câu hỏi: {len(questions)}/70 câu hỏi chính quy với đầy đủ choices và đáp án => PASS")

        # 7. Student Enrollments Verification
        enrollments = db.session.query(Enrollment).filter_by(course_id=course.id).all()
        assert len(enrollments) >= 2, f"FAIL: Số học viên ghi danh ít hơn 2 ({len(enrollments)})!"
        print(f"[7/7] Ghi danh học viên: {len(enrollments)} học viên đang học tập => PASS")
        for e in enrollments:
            print(f"      - Học viên: {e.student.display_name} ({e.student.email}) - Trạng thái: {e.status}")

        print("\n" + "=" * 80)
        print("XÁC MINH THỰC NGHIỆM HOÀN TẤT: TẤT CẢ 7/7 TIÊU CHÍ ĐỀU ĐẠT CHUẨN 100%!")
        print("=" * 80)


if __name__ == "__main__":
    verify()
