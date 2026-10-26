# -*- coding: utf-8 -*-
"""Wipe all courses, financial ledgers, transaction history, and reset all account balances to 0.

Strictly preserves:
- User accounts (Admin, Instructor, Student)
- Roles and permissions
- Authentication sessions and security tokens
- Alembic database migration state
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

import sqlalchemy as sa
from backend import create_app, db
from backend.models.course import Course, Enrollment, LearningUnit, Lesson
from backend.models.identity import User
from backend.models.wallet import UserBalance, WalletTransaction


def clean_storage_directories(base_dir: Path) -> dict[str, int]:
    """Remove orphaned physical storage files while keeping folder structures."""
    storage_root = base_dir / "storage"
    quarantine_root = base_dir / "quarantine"
    exports_root = base_dir / "exports"

    stats = {"blobs": 0, "appeals": 0, "samples": 0, "quarantine": 0, "exports": 0}

    # Blobs
    blobs_dir = storage_root / "blobs"
    if blobs_dir.exists():
        for f in blobs_dir.rglob("*"):
            if f.is_file():
                stats["blobs"] += 1
        shutil.rmtree(blobs_dir, ignore_errors=True)
    blobs_dir.mkdir(parents=True, exist_ok=True)

    # Appeals
    appeals_dir = storage_root / "appeals"
    if appeals_dir.exists():
        for f in appeals_dir.rglob("*"):
            if f.is_file():
                stats["appeals"] += 1
        shutil.rmtree(appeals_dir, ignore_errors=True)
    appeals_dir.mkdir(parents=True, exist_ok=True)

    # DRM HLS
    drm_dir = storage_root / "drm_hls"
    if drm_dir.exists():
        shutil.rmtree(drm_dir, ignore_errors=True)
    drm_dir.mkdir(parents=True, exist_ok=True)

    # Sample MP4s
    if storage_root.exists():
        for s in storage_root.glob("sample_*.mp4"):
            try:
                s.unlink()
                stats["samples"] += 1
            except OSError:
                pass

    # Quarantine
    if quarantine_root.exists():
        for q in quarantine_root.rglob("*"):
            if q.is_file() and q.name != ".gitkeep":
                stats["quarantine"] += 1
        shutil.rmtree(quarantine_root, ignore_errors=True)
    quarantine_root.mkdir(parents=True, exist_ok=True)

    # Exports
    if exports_root.exists():
        for e in exports_root.rglob("*"):
            if e.is_file() and e.name != ".gitkeep":
                stats["exports"] += 1
        shutil.rmtree(exports_root, ignore_errors=True)
    exports_root.mkdir(parents=True, exist_ok=True)

    return stats


def wipe_courses_and_finances(app_env: str = "development") -> dict[str, int]:
    print("=" * 80)
    print("PWD301: XÓA SẠCH DỮ LIỆU KHÓA HỌC, TIỀN, SỐ DƯ TÀI KHOẢN VÀ LỊCH SỬ GIAO DỊCH")
    print("=" * 80)

    app = create_app(app_env)
    with app.app_context():
        # Pre-wipe inspection
        user_count_before = db.session.query(User).count()
        course_count_before = db.session.query(Course).count()
        enrollment_count_before = db.session.query(Enrollment).count()
        tx_count_before = db.session.query(WalletTransaction).count()
        balance_sum_before = (
            db.session.query(sa.func.sum(UserBalance.balance)).scalar() or 0
        )

        print("\n[1/4] THỐNG KÊ TRƯỚC KHI XÓA:")
        print(f"  - Tổng số người dùng (Users):        {user_count_before} (SẼ BẢO TỒN NGUYÊN VẸN)")
        print(f"  - Tổng số khóa học (Courses):        {course_count_before}")
        print(f"  - Tổng số lượt đăng ký (Enrollments): {enrollment_count_before}")
        print(f"  - Tổng số giao dịch (Transactions):  {tx_count_before}")
        print(f"  - Tổng số dư toàn hệ thống (VND):    {balance_sum_before:,.0f} đ")

        # Execute SQL Server hard wipe
        print("\n[2/4] Đang thực thi dọn sạch CSDL...")
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # A. Tắt ràng buộc toàn bảng và triggers
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))

            # B. Gỡ liên kết khóa ngoại thumbnail file asset
            conn.execute(sa.text("UPDATE courses SET thumbnail_file_asset_id = NULL"))

            # C. Xóa toàn bộ lịch sử giao dịch và ví tiền
            conn.execute(sa.text("DELETE FROM wallet_transactions"))
            conn.execute(sa.text("DELETE FROM user_balances"))

            # D. Xóa tiến trình bài học và đa phương tiện
            conn.execute(sa.text("DELETE FROM lesson_media_progress"))
            conn.execute(sa.text("DELETE FROM playback_receipts"))
            conn.execute(sa.text("DELETE FROM playback_sessions"))
            conn.execute(sa.text("DELETE FROM lesson_progress_receipts"))
            conn.execute(sa.text("DELETE FROM lesson_progress"))
            conn.execute(sa.text("DELETE FROM lesson_resources"))
            conn.execute(sa.text("DELETE FROM lessons"))
            conn.execute(sa.text("DELETE FROM learning_units"))

            # E. Xóa kết quả thi, bài nộp, phúc khảo
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

            # F. Xóa bài kiểm tra & ma trận đề
            conn.execute(sa.text("DELETE FROM assessment_question_assignments"))
            conn.execute(sa.text("DELETE FROM assessment_sections"))
            conn.execute(sa.text("DELETE FROM assessment_blueprint_rules"))
            conn.execute(sa.text("DELETE FROM assessment_blueprints"))
            conn.execute(sa.text("DELETE FROM assessment_question_pool"))
            conn.execute(sa.text("DELETE FROM assessments"))

            # G. Xóa ngân hàng câu hỏi
            conn.execute(sa.text("DELETE FROM question_revision_choices"))
            conn.execute(sa.text("DELETE FROM question_revision_accepted_answers"))
            conn.execute(sa.text("DELETE FROM question_revision_resources"))
            conn.execute(sa.text("DELETE FROM question_corrections"))
            conn.execute(sa.text("DELETE FROM question_revisions"))
            conn.execute(sa.text("DELETE FROM question_provenance"))
            conn.execute(sa.text("DELETE FROM questions"))

            # H. Xóa đăng ký học & tiến trình khóa học
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

            # I. Xóa AI & tài liệu tri thức
            conn.execute(sa.text("DELETE FROM ai_source_usages"))
            conn.execute(sa.text("DELETE FROM ai_requests"))
            conn.execute(sa.text("DELETE FROM ai_messages"))
            conn.execute(sa.text("DELETE FROM ai_conversations"))
            conn.execute(sa.text("DELETE FROM ai_generated_question_drafts"))
            conn.execute(sa.text("DELETE FROM knowledge_chunks"))
            conn.execute(sa.text("DELETE FROM knowledge_versions"))
            conn.execute(sa.text("DELETE FROM knowledge_documents"))

            # J. Xóa tệp đính kèm và tài nguyên bài giảng
            conn.execute(sa.text("DELETE FROM file_scan_results"))
            conn.execute(sa.text("DELETE FROM file_revisions"))
            conn.execute(sa.text("DELETE FROM file_assets"))
            conn.execute(sa.text("DELETE FROM file_blobs"))

            # K. Xóa toàn bộ khóa học
            conn.execute(sa.text("DELETE FROM courses"))

            # L. Xóa thông báo và nhật ký kiểm toán liên quan
            conn.execute(sa.text("DELETE FROM email_deliveries"))
            conn.execute(sa.text("DELETE FROM notifications"))
            conn.execute(sa.text("DELETE FROM notification_events"))
            conn.execute(sa.text("DELETE FROM audit_events"))

            # M. Reseed identity sequences cho tất cả các bảng đã xóa
            tables_to_reseed = [
                "courses",
                "learning_units",
                "lessons",
                "lesson_resources",
                "lesson_progress",
                "lesson_media_progress",
                "playback_sessions",
                "playback_receipts",
                "assessments",
                "assessment_sections",
                "assessment_blueprints",
                "assessment_blueprint_rules",
                "assessment_question_assignments",
                "assessment_attempts",
                "attempt_questions",
                "attempt_answers",
                "attempt_answer_choices",
                "attempt_answer_events",
                "attempt_choice_snapshots",
                "attempt_focus_events",
                "attempt_question_grades",
                "attempt_question_grade_history",
                "assessment_results",
                "assessment_result_history",
                "assessment_appeals",
                "regrade_jobs",
                "regrade_items",
                "questions",
                "question_revisions",
                "question_revision_choices",
                "question_revision_accepted_answers",
                "question_revision_resources",
                "question_corrections",
                "question_provenance",
                "enrollments",
                "enrollment_periods",
                "enrollment_events",
                "course_prerequisites",
                "course_completion_summaries",
                "course_completion_rules",
                "course_change_requests",
                "document_import_jobs",
                "file_assets",
                "file_revisions",
                "file_blobs",
                "file_scan_results",
                "wallet_transactions",
                "user_balances",
                "notification_events",
                "notifications",
                "email_deliveries",
                "audit_events",
                "ai_conversations",
                "ai_messages",
                "ai_requests",
                "ai_source_usages",
                "knowledge_documents",
                "knowledge_versions",
                "knowledge_chunks",
            ]
            for tbl in tables_to_reseed:
                try:
                    conn.execute(sa.text(f"DBCC CHECKIDENT ('[{tbl}]', RESEED, 0)"))
                except Exception:
                    pass

            # N. Bật lại triggers và kiểm tra toàn vẹn ràng buộc
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
            conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'"))

        # Initialize clean 0 VND balance for all existing users
        print("\n[3/4] Khởi tạo số dư 0 VNĐ sạch cho toàn bộ tài khoản...")
        all_users = db.session.query(User).all()
        for u in all_users:
            b = UserBalance(user_id=u.id, balance=0, currency="VND")
            db.session.add(b)
        db.session.commit()
        print(f"  ✓ Đã thiết lập số dư 0 VNĐ thành công cho {len(all_users)} tài khoản.")

        # Clean storage files
        storage_stats = clean_storage_directories(BASE_DIR)
        print(f"  ✓ Đã dọn sạch tệp đính kèm: {storage_stats}")

        # Post-wipe verification
        user_count_after = db.session.query(User).count()
        course_count_after = db.session.query(Course).count()
        unit_count_after = db.session.query(LearningUnit).count()
        lesson_count_after = db.session.query(Lesson).count()
        enrollment_count_after = db.session.query(Enrollment).count()
        tx_count_after = db.session.query(WalletTransaction).count()
        balance_count_after = db.session.query(UserBalance).count()
        balance_sum_after = (
            db.session.query(sa.func.sum(UserBalance.balance)).scalar() or 0
        )
        non_zero_balances = (
            db.session.query(UserBalance).filter(UserBalance.balance > 0).count()
        )

        print("\n[4/4] BÁO CÁO XÁC MINH KẾT QUẢ THỰC TẾ:")
        print(f"  - Người dùng (Users):                {user_count_after} (100% tài khoản được giữ lại)")
        print(f"  - Khóa học (Courses):                {course_count_after} (Mục tiêu: 0)")
        print(f"  - Chương học (LearningUnits):        {unit_count_after} (Mục tiêu: 0)")
        print(f"  - Bài học (Lessons):                 {lesson_count_after} (Mục tiêu: 0)")
        print(f"  - Lượt đăng ký (Enrollments):        {enrollment_count_after} (Mục tiêu: 0)")
        print(f"  - Lịch sử giao dịch (Transactions):  {tx_count_after} (Mục tiêu: 0)")
        print(f"  - Bản ghi số dư (UserBalances):      {balance_count_after} (Mỗi tài khoản có 1 ví)")
        print(f"  - Tổng số tiền toàn hệ thống:        {balance_sum_after:,.0f} đ (Mục tiêu: 0 đ)")
        print(f"  - Số tài khoản có số dư > 0:         {non_zero_balances} (Mục tiêu: 0)")

        assert course_count_after == 0, f"Vẫn còn {course_count_after} khóa học!"
        assert enrollment_count_after == 0, f"Vẫn còn {enrollment_count_after} đăng ký!"
        assert tx_count_after == 0, f"Vẫn còn {tx_count_after} giao dịch!"
        assert balance_sum_after == 0, f"Tổng số dư khác 0: {balance_sum_after} đ!"
        assert non_zero_balances == 0, f"Vẫn còn {non_zero_balances} tài khoản có số dư > 0!"
        assert user_count_after == user_count_before, "Số lượng tài khoản bị thay đổi!"

        print("\n" + "=" * 80)
        print("✓ HOÀN TẤT 100%: TOÀN BỘ KHÓA HỌC, TIỀN, SỐ DƯ VÀ LỊCH SỬ GIAO DỊCH ĐÃ ĐƯỢC XÓA SẠCH!")
        print("=" * 80)

        return {
            "users": user_count_after,
            "courses": course_count_after,
            "transactions": tx_count_after,
            "balance_sum": balance_sum_after,
        }


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "development"
    wipe_courses_and_finances(env)
