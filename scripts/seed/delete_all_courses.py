# -*- coding: utf-8 -*-
"""Hard delete all existing courses in PWD301 database.
Ensures zero existing courses remain before building the fresh Android course.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import create_app, db
from backend.models.course import Course
import sqlalchemy as sa

def hard_delete_all_courses():
    print("=" * 80)
    print("XÓA CỨNG TOÀN BỘ KHÓA HỌC HIỆN HÀNH TRONG HỆ THỐNG")
    print("=" * 80)
    
    app = create_app()
    with app.app_context():
        courses = db.session.query(Course).all()
        print(f"Số lượng khóa học hiện tại: {len(courses)}")
        for c in courses:
            print(f"  - [ID: {c.id}] Mã: {c.course_code} | Tiêu đề: {c.title}")
            
        print("\nTiến hành xóa cứng toàn bộ khóa học và các bảng liên quan...")
        
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Disable constraints and triggers
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))
            
            # 2. Reset thumbnail FKs
            conn.execute(sa.text("UPDATE courses SET thumbnail_file_asset_id = NULL"))
            
            # 3. Delete lessons & units
            conn.execute(sa.text("DELETE FROM lesson_media_progress"))
            conn.execute(sa.text("DELETE FROM playback_receipts"))
            conn.execute(sa.text("DELETE FROM playback_sessions"))
            conn.execute(sa.text("DELETE FROM lesson_progress_receipts"))
            conn.execute(sa.text("DELETE FROM lesson_progress"))
            conn.execute(sa.text("DELETE FROM lesson_resources"))
            conn.execute(sa.text("DELETE FROM lessons"))
            conn.execute(sa.text("DELETE FROM learning_units"))
            
            # 4. Delete assessment attempts
            conn.execute(sa.text("DELETE FROM attempt_answer_choices"))
            conn.execute(sa.text("DELETE FROM attempt_answers"))
            conn.execute(sa.text("DELETE FROM attempt_answer_events"))
            conn.execute(sa.text("DELETE FROM attempt_choice_snapshots"))
            conn.execute(sa.text("DELETE FROM attempt_focus_events"))
            conn.execute(sa.text("DELETE FROM attempt_question_grade_history"))
            conn.execute(sa.text("DELETE FROM attempt_question_grades"))
            conn.execute(sa.text("DELETE FROM attempt_questions"))
            conn.execute(sa.text("DELETE FROM assessment_result_history"))
            conn.execute(sa.text("DELETE FROM assessment_results"))
            conn.execute(sa.text("DELETE FROM regrade_items"))
            conn.execute(sa.text("DELETE FROM regrade_jobs"))
            conn.execute(sa.text("DELETE FROM assessment_attempts"))
            
            # 5. Delete assessments
            conn.execute(sa.text("DELETE FROM assessment_question_assignments"))
            conn.execute(sa.text("DELETE FROM assessment_sections"))
            conn.execute(sa.text("DELETE FROM assessment_blueprint_rules"))
            conn.execute(sa.text("DELETE FROM assessment_blueprints"))
            conn.execute(sa.text("DELETE FROM assessment_question_pool"))
            conn.execute(sa.text("DELETE FROM assessments"))
            
            # 6. Delete question bank
            conn.execute(sa.text("DELETE FROM question_revision_choices"))
            conn.execute(sa.text("DELETE FROM question_revision_accepted_answers"))
            conn.execute(sa.text("DELETE FROM question_revision_resources"))
            conn.execute(sa.text("DELETE FROM question_corrections"))
            conn.execute(sa.text("DELETE FROM question_revisions"))
            conn.execute(sa.text("DELETE FROM question_provenance"))
            conn.execute(sa.text("DELETE FROM questions"))
            
            # 7. Delete enrollments
            conn.execute(sa.text("DELETE FROM enrollment_events"))
            conn.execute(sa.text("DELETE FROM enrollment_periods"))
            conn.execute(sa.text("DELETE FROM enrollments"))
            
            # 8. Delete course metadata
            conn.execute(sa.text("DELETE FROM course_prerequisites"))
            conn.execute(sa.text("DELETE FROM course_completion_summaries"))
            conn.execute(sa.text("DELETE FROM course_completion_rules"))
            conn.execute(sa.text("DELETE FROM course_change_requests"))
            conn.execute(sa.text("DELETE FROM document_import_jobs"))
            conn.execute(sa.text("DELETE FROM grade_exports"))
            
            # 9. Delete AI / RAG
            conn.execute(sa.text("DELETE FROM ai_source_usages"))
            conn.execute(sa.text("DELETE FROM ai_requests"))
            conn.execute(sa.text("DELETE FROM ai_messages"))
            conn.execute(sa.text("DELETE FROM ai_conversations WHERE course_id IS NOT NULL"))
            conn.execute(sa.text("DELETE FROM ai_generated_question_drafts WHERE course_id IS NOT NULL"))
            conn.execute(sa.text("DELETE FROM knowledge_chunks"))
            conn.execute(sa.text("DELETE FROM knowledge_versions"))
            conn.execute(sa.text("DELETE FROM knowledge_documents WHERE course_id IS NOT NULL"))
            
            # 10. Delete course files
            conn.execute(sa.text("DELETE FROM file_scan_results WHERE file_revision_id IN (SELECT fr.id FROM file_revisions fr JOIN file_assets fa ON fr.file_asset_id = fa.id WHERE fa.course_id IS NOT NULL)"))
            conn.execute(sa.text("DELETE FROM file_revisions WHERE file_asset_id IN (SELECT id FROM file_assets WHERE course_id IS NOT NULL)"))
            conn.execute(sa.text("DELETE FROM file_assets WHERE course_id IS NOT NULL"))
            
            # 11. Delete courses
            conn.execute(sa.text("DELETE FROM courses"))
            
            # 12. Re-enable constraints and triggers with verification
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'"))
            
        remaining = db.session.query(Course).count()
        print(f"\n✓ Đã xóa xong! Số lượng khóa học còn lại: {remaining}")
        if remaining != 0:
            raise RuntimeError(f"Lỗi: Vẫn còn {remaining} khóa học chưa xóa!")
        print("✓ XÁC NHẬN: Toàn bộ khóa học đã được XÓA CỨNG (hard delete) 100% thành công!")

if __name__ == "__main__":
    hard_delete_all_courses()
