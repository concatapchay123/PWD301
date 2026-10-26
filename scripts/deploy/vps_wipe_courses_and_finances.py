# -*- coding: utf-8 -*-
"""Wipe courses, money, balances, and transaction history on VPS production server."""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import paramiko

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"

print("=" * 80)
print(f"BẮT ĐẦU DỌN SẠCH CSDL VÀ DỮ LIỆU TÀI CHÍNH TRÊN VPS: {VPS_HOST}")
print("=" * 80)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=30)
print("✓ Kết nối SSH thành công!")

remote_script = """
import os
import shutil
import sys
from pathlib import Path
import sqlalchemy as sa

from backend import create_app
from backend.extensions import db
from backend.models.course import Course, Enrollment, LearningUnit, Lesson
from backend.models.identity import User
from backend.models.wallet import UserBalance, WalletTransaction

app = create_app()
with app.app_context():
    print('--- ĐANG THỰC HIỆN WIPE TRÊN CONTAINER PRODUCTION ---')
    with db.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))

        conn.execute(sa.text("UPDATE courses SET thumbnail_file_asset_id = NULL"))

        conn.execute(sa.text("DELETE FROM wallet_transactions"))
        conn.execute(sa.text("DELETE FROM user_balances"))

        conn.execute(sa.text("DELETE FROM lesson_media_progress"))
        conn.execute(sa.text("DELETE FROM playback_receipts"))
        conn.execute(sa.text("DELETE FROM playback_sessions"))
        conn.execute(sa.text("DELETE FROM lesson_progress_receipts"))
        conn.execute(sa.text("DELETE FROM lesson_progress"))
        conn.execute(sa.text("DELETE FROM lesson_resources"))
        conn.execute(sa.text("DELETE FROM lessons"))
        conn.execute(sa.text("DELETE FROM learning_units"))

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
        conn.execute(sa.text("DELETE FROM assessment_appeals"))
        conn.execute(sa.text("DELETE FROM regrade_items"))
        conn.execute(sa.text("DELETE FROM regrade_jobs"))
        conn.execute(sa.text("DELETE FROM assessment_attempts"))

        conn.execute(sa.text("DELETE FROM assessment_question_assignments"))
        conn.execute(sa.text("DELETE FROM assessment_sections"))
        conn.execute(sa.text("DELETE FROM assessment_blueprint_rules"))
        conn.execute(sa.text("DELETE FROM assessment_blueprints"))
        conn.execute(sa.text("DELETE FROM assessment_question_pool"))
        conn.execute(sa.text("DELETE FROM assessments"))

        conn.execute(sa.text("DELETE FROM question_revision_choices"))
        conn.execute(sa.text("DELETE FROM question_revision_accepted_answers"))
        conn.execute(sa.text("DELETE FROM question_revision_resources"))
        conn.execute(sa.text("DELETE FROM question_corrections"))
        conn.execute(sa.text("DELETE FROM question_revisions"))
        conn.execute(sa.text("DELETE FROM question_provenance"))
        conn.execute(sa.text("DELETE FROM questions"))

        conn.execute(sa.text("DELETE FROM enrollment_events"))
        conn.execute(sa.text("DELETE FROM enrollment_periods"))
        conn.execute(sa.text("DELETE FROM enrollments"))
        conn.execute(sa.text("DELETE FROM course_prerequisites"))
        conn.execute(sa.text("DELETE FROM course_completion_summaries"))
        conn.execute(sa.text("DELETE FROM course_completion_rules"))
        conn.execute(sa.text("DELETE FROM course_change_requests"))
        conn.execute(sa.text("DELETE FROM document_import_jobs"))
        conn.execute(sa.text("DELETE FROM import_question_resources"))
        conn.execute(sa.text("DELETE FROM import_duplicate_candidates"))
        conn.execute(sa.text("DELETE FROM import_questions"))
        conn.execute(sa.text("DELETE FROM grade_exports"))

        conn.execute(sa.text("DELETE FROM ai_source_usages"))
        conn.execute(sa.text("DELETE FROM ai_requests"))
        conn.execute(sa.text("DELETE FROM ai_messages"))
        conn.execute(sa.text("DELETE FROM ai_conversations"))
        conn.execute(sa.text("DELETE FROM ai_generated_question_drafts"))
        conn.execute(sa.text("DELETE FROM knowledge_chunks"))
        conn.execute(sa.text("DELETE FROM knowledge_versions"))
        conn.execute(sa.text("DELETE FROM knowledge_documents"))

        conn.execute(sa.text("DELETE FROM file_scan_results"))
        conn.execute(sa.text("DELETE FROM file_revisions"))
        conn.execute(sa.text("DELETE FROM file_assets"))
        conn.execute(sa.text("DELETE FROM file_blobs"))

        conn.execute(sa.text("DELETE FROM courses"))

        conn.execute(sa.text("DELETE FROM email_deliveries"))
        conn.execute(sa.text("DELETE FROM notifications"))
        conn.execute(sa.text("DELETE FROM notification_events"))
        conn.execute(sa.text("DELETE FROM audit_events"))

        tables_to_reseed = [
            'courses', 'learning_units', 'lessons', 'lesson_resources', 'lesson_progress',
            'lesson_media_progress', 'playback_sessions', 'playback_receipts', 'assessments',
            'assessment_sections', 'assessment_blueprints', 'assessment_blueprint_rules',
            'assessment_question_assignments', 'assessment_attempts', 'attempt_questions',
            'attempt_answers', 'attempt_answer_choices', 'attempt_answer_events',
            'attempt_choice_snapshots', 'attempt_focus_events', 'attempt_question_grades',
            'attempt_question_grade_history', 'assessment_results', 'assessment_result_history',
            'assessment_appeals', 'regrade_jobs', 'regrade_items', 'questions',
            'question_revisions', 'question_revision_choices', 'question_revision_accepted_answers',
            'question_revision_resources', 'question_corrections', 'question_provenance',
            'enrollments', 'enrollment_periods', 'enrollment_events', 'course_prerequisites',
            'course_completion_summaries', 'course_completion_rules', 'course_change_requests',
            'document_import_jobs', 'file_assets', 'file_revisions', 'file_blobs',
            'file_scan_results', 'wallet_transactions', 'user_balances', 'notification_events',
            'notifications', 'email_deliveries', 'audit_events', 'ai_conversations',
            'ai_messages', 'ai_requests', 'ai_source_usages', 'knowledge_documents',
            'knowledge_versions', 'knowledge_chunks'
        ]
        for tbl in tables_to_reseed:
            try:
                conn.execute(sa.text(f"DBCC CHECKIDENT ('[{tbl}]', RESEED, 0)"))
            except Exception:
                pass

        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'"))

    # Re-initialize clean 0 VND balances for all users
    all_users = db.session.query(User).all()
    for u in all_users:
        b = UserBalance(user_id=u.id, balance=0, currency='VND')
        db.session.add(b)
    db.session.commit()
    print(f'✓ Đã thiết lập số dư 0 VNĐ cho {len(all_users)} tài khoản.')

    # Verification stats
    print('=== KẾT QUẢ XÁC MINH TRÊN VPS ===')
    print('Users:', db.session.query(User).count())
    print('Courses:', db.session.query(Course).count())
    print('LearningUnits:', db.session.query(LearningUnit).count())
    print('Lessons:', db.session.query(Lesson).count())
    print('Enrollments:', db.session.query(Enrollment).count())
    print('Transactions:', db.session.query(WalletTransaction).count())
    print('UserBalances:', db.session.query(UserBalance).count())
    total_bal = db.session.query(sa.func.sum(UserBalance.balance)).scalar() or 0
    print('Total System Balance (VND):', total_bal)
"""

cmd = f"docker exec -i pwd301-production-web-1 python << 'EOF'\n{remote_script}\nEOF\n"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err:
    print("[ERR]", err)

ssh.close()
print("✓ Đã hoàn tất đồng bộ xóa dữ liệu trên VPS!")
