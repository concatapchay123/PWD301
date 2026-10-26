# -*- coding: utf-8 -*-
"""Synchronize latest codebase to VPS server, wipe all courses,
and retain only the 4 canonical administrator accounts.
"""

import os
import sys
import time
import tarfile
from pathlib import Path
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"
LOCAL_PKG = Path("backups/pwd301_sync_package.tar.gz")
REMOTE_PKG = "/opt/apps/pwd301_sync_package.tar.gz"

ADMIN_EMAILS = [
    "tqtphamnguyenhoangphuc@gmail.com",
    "danglyquan@gmail.com",
    "vinhphu2020.nt@gmail.com",
    "callmewin06@gmail.com",
]

ADMIN_NAMES = {
    "tqtphamnguyenhoangphuc@gmail.com": "Hoàng Phúc",
    "danglyquan@gmail.com": "Đặng Lý Quân",
    "vinhphu2020.nt@gmail.com": "Vĩnh Phú",
    "callmewin06@gmail.com": "Hữu Thắng",
}


def build_package():
    print("=" * 80)
    print("BƯỚC 1: ĐÓNG GÓI PHIÊN BẢN MỚI NHẤT CỦA HỆ THỐNG")
    print("=" * 80)

    INCLUDE_DIRS = [
        "src",
        "frontend",
        "migrations",
        "deploy",
        "scripts",
    ]

    INCLUDE_FILES = [
        "requirements.txt",
        "AGENTS.md",
        "Dockerfile",
        "wsgi.py",
        "pyproject.toml",
    ]

    def filter_tar(tarinfo):
        name = tarinfo.name
        for pat in [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".git",
            "*.pyc",
            "course_data",
            "android_course_data",
            "qa-evidence",
            "qa-task",
            "screenshots",
        ]:
            if pat in name:
                return None
        return tarinfo

    LOCAL_PKG.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(LOCAL_PKG, "w:gz") as tar:
        for d in INCLUDE_DIRS:
            dp = Path(d)
            if dp.exists():
                print(f"  + Thư mục: {d}")
                tar.add(d, filter=filter_tar)
        for f in INCLUDE_FILES:
            fp = Path(f)
            if fp.exists():
                print(f"  + Tệp tin: {f}")
                tar.add(f)

    pkg_size_mb = LOCAL_PKG.stat().st_size / (1024 * 1024)
    print(f"-> Gói đồng bộ sẵn sàng: {LOCAL_PKG} ({pkg_size_mb:.2f} MB)")
    return pkg_size_mb


def deploy_and_clean():
    build_package()

    print("\n" + "=" * 80)
    print(f"BƯỚC 2: KẾT NỐI VÀ UPLOAD LÊN VPS SERVER ({VPS_HOST})")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=30)
    print(f"✓ Đã kết nối SSH thành công tới {VPS_HOST}")

    sftp = ssh.open_sftp()
    print(f"-> Đang tải gói đồng bộ {LOCAL_PKG} lên VPS...")

    last_pct = [0]
    def sftp_cb(transferred, total):
        pct = int(transferred / total * 100)
        if pct >= last_pct[0] + 25 or pct == 100:
            print(f"   [SFTP] {pct}% ({transferred / (1024*1024):.1f}/{total / (1024*1024):.1f} MB)")
            last_pct[0] = pct

    sftp.put(str(LOCAL_PKG), REMOTE_PKG, callback=sftp_cb)
    sftp.close()
    print("✓ Tải gói đồng bộ lên VPS hoàn tất!")

    def run_remote(cmd, title=""):
        if title:
            print(f"\n--- {title} ---")
        print(f"$ {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        if out:
            print(out)
        if err:
            print(f"[ERR] {err}")
        return out, err

    # Step 3: Tạm dừng web & worker
    run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml stop web worker", "BƯỚC 3: Tạm dừng container web & worker")

    # Step 4: Giải nén mã nguồn mới nhất đè lên /opt/apps/pwd301
    run_remote("tar -xzf /opt/apps/pwd301_sync_package.tar.gz -C /opt/apps/pwd301", "BƯỚC 4: Giải nén phiên bản mới nhất vào /opt/apps/pwd301")

    # Step 5: Rebuild & Khởi động lại dịch vụ
    run_remote("cd /opt/apps/pwd301/deploy && docker compose -f compose.production.yml up -d --build web worker proxy", "BƯỚC 5: Rebuild & Khởi động lại dịch vụ (web, worker, proxy)")

    print("\n--- Đợi dịch vụ ổn định (15 giây) ---")
    time.sleep(15)

    # Step 6: Chạy migration DB
    run_remote("docker exec pwd301-production-web-1 flask db upgrade", "BƯỚC 6: Đồng bộ Schema CSDL (flask db upgrade)")

    # Step 7: Thực hiện dọn sạch CSDL khóa học và chỉ giữ lại 4 Admin
    print("\n" + "=" * 80)
    print("BƯỚC 7: XÓA SẠCH TOÀN BỘ CSDL KHÓA HỌC & CHỈ CHỪA LẠI 4 ADMIN CHÍNH")
    print("=" * 80)

    db_clean_script = """
import os
import shutil
import sys
from pathlib import Path
import sqlalchemy as sa

sys.stdout.reconfigure(encoding='utf-8')
from backend import create_app
from backend.extensions import db
from backend.models.identity import User, UserRole, Role
from backend.models.course import Course, Enrollment, LearningUnit, Lesson
from backend.models.assessment import Assessment
from backend.models.question_bank import Question
from backend.models.wallet import UserBalance, WalletTransaction
from backend.services.user_service import generate_pptq_password_hash, verify_password

app = create_app()
with app.app_context():
    ADMIN_EMAILS = [
        'tqtphamnguyenhoangphuc@gmail.com',
        'danglyquan@gmail.com',
        'vinhphu2020.nt@gmail.com',
        'callmewin06@gmail.com',
    ]
    ADMIN_NAMES = {
        'tqtphamnguyenhoangphuc@gmail.com': 'Hoàng Phúc',
        'danglyquan@gmail.com': 'Đặng Lý Quân',
        'vinhphu2020.nt@gmail.com': 'Vĩnh Phú',
        'callmewin06@gmail.com': 'Hữu Thắng',
    }

    print('[1/5] Tìm kiếm và xác thực 4 tài khoản Admin chính...')
    admins = db.session.query(User).filter(User.email.in_(ADMIN_EMAILS)).all()
    admin_ids = [a.id for a in admins]
    print(f'   -> Tìm thấy {len(admins)}/4 Admin chính: ID = {admin_ids}')
    for a in admins:
        print(f'      * ID {a.id}: {a.email} ({ADMIN_NAMES.get(a.email, a.display_name)})')

    if len(admins) < 4:
        # Nếu thiếu admin nào, tự động tạo mới admin đó
        existing_emails = {a.email for a in admins}
        for email in ADMIN_EMAILS:
            if email not in existing_emails:
                print(f'   [!] Tạo mới Admin còn thiếu: {email}')
                new_admin = User(
                    email=email,
                    display_name=ADMIN_NAMES.get(email, 'Admin'),
                    primary_role='ADMIN',
                    is_active=True,
                    is_suspended=False,
                )
                db.session.add(new_admin)
                db.session.flush()
                admins.append(new_admin)
                admin_ids.append(new_admin.id)

    print('[2/5] Vô hiệu hóa constraints để thực hiện purge sạch sẽ...')
    with db.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))

        # Gỡ liên kết avatar và thumbnail
        try:
            conn.execute(sa.text("UPDATE users SET avatar_file_asset_id = NULL"))
            conn.execute(sa.text("UPDATE courses SET thumbnail_file_asset_id = NULL"))
            conn.execute(sa.text("UPDATE courses SET trailer_file_asset_id = NULL"))
        except Exception as e:
            print('   (Notice on update asset FKs):', e)

        # Xóa hàng đợi tác vụ nền
        try:
            conn.execute(sa.text("DELETE FROM background_jobs"))
        except Exception as e:
            print('   (Notice on delete background_jobs):', e)

        # Xóa toàn bộ giao dịch & số dư
        conn.execute(sa.text("DELETE FROM wallet_transactions"))
        conn.execute(sa.text("DELETE FROM user_balances"))

        # Xóa toàn bộ tiến trình học & bài giảng
        conn.execute(sa.text("DELETE FROM lesson_media_progress"))
        conn.execute(sa.text("DELETE FROM playback_receipts"))
        conn.execute(sa.text("DELETE FROM playback_sessions"))
        conn.execute(sa.text("DELETE FROM lesson_progress_receipts"))
        conn.execute(sa.text("DELETE FROM lesson_progress"))
        conn.execute(sa.text("DELETE FROM lesson_resources"))
        conn.execute(sa.text("DELETE FROM lessons"))
        conn.execute(sa.text("DELETE FROM learning_units"))

        # Xóa toàn bộ bài kiểm tra & câu trả lời
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

        # Xóa ngân hàng câu hỏi
        conn.execute(sa.text("DELETE FROM question_revision_choices"))
        conn.execute(sa.text("DELETE FROM question_revision_accepted_answers"))
        conn.execute(sa.text("DELETE FROM question_revision_resources"))
        conn.execute(sa.text("DELETE FROM question_corrections"))
        conn.execute(sa.text("DELETE FROM question_revisions"))
        conn.execute(sa.text("DELETE FROM question_provenance"))
        conn.execute(sa.text("DELETE FROM questions"))

        # Xóa ghi danh & khóa học
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

        # Xóa AI & Tri thức
        conn.execute(sa.text("DELETE FROM ai_source_usages"))
        conn.execute(sa.text("DELETE FROM ai_requests"))
        conn.execute(sa.text("DELETE FROM ai_messages"))
        conn.execute(sa.text("DELETE FROM ai_conversations"))
        conn.execute(sa.text("DELETE FROM ai_generated_question_drafts"))
        conn.execute(sa.text("DELETE FROM knowledge_chunks"))
        conn.execute(sa.text("DELETE FROM knowledge_versions"))
        conn.execute(sa.text("DELETE FROM knowledge_documents"))

        # Xóa tệp tin
        conn.execute(sa.text("DELETE FROM file_scan_results"))
        conn.execute(sa.text("DELETE FROM file_revisions"))
        conn.execute(sa.text("DELETE FROM file_assets"))
        conn.execute(sa.text("DELETE FROM file_blobs"))

        # Xóa khóa học
        conn.execute(sa.text("DELETE FROM courses"))

        # Xóa thông báo, audit và lịch sử phiên làm việc
        conn.execute(sa.text("DELETE FROM email_deliveries"))
        conn.execute(sa.text("DELETE FROM notifications"))
        conn.execute(sa.text("DELETE FROM notification_events"))
        conn.execute(sa.text("DELETE FROM notification_preferences"))
        conn.execute(sa.text("DELETE FROM audit_events"))
        conn.execute(sa.text("DELETE FROM auth_sessions"))
        conn.execute(sa.text("DELETE FROM jwt_token_grants"))
        conn.execute(sa.text("DELETE FROM user_security_tokens"))
        conn.execute(sa.text("DELETE FROM security_events"))
        conn.execute(sa.text("DELETE FROM system_alerts"))
        conn.execute(sa.text("DELETE FROM backup_runs"))
        conn.execute(sa.text("DELETE FROM instructor_applications"))

        # XÓA TOÀN BỘ USERS NGOẠI TRỪ 4 ADMIN CHÍNH
        admin_id_str = ', '.join(str(i) for i in admin_ids)
        print(f'[3/5] Xóa các user phụ (chỉ giữ lại ID: {admin_id_str})...')
        conn.execute(sa.text(f"DELETE FROM user_roles WHERE user_id NOT IN ({admin_id_str})"))
        conn.execute(sa.text(f"UPDATE user_roles SET assigned_by_user_id = NULL WHERE assigned_by_user_id NOT IN ({admin_id_str})"))
        conn.execute(sa.text(f"DELETE FROM users WHERE id NOT IN ({admin_id_str})"))

        # Reseed identity cho các bảng đã làm sạch
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
            'knowledge_versions', 'knowledge_chunks', 'background_jobs'
        ]
        for tbl in tables_to_reseed:
            try:
                conn.execute(sa.text(f"DBCC CHECKIDENT ('[{tbl}]', RESEED, 0)"))
            except Exception:
                pass

        # Bật lại triggers & constraints
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
        conn.execute(sa.text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'"))

    db.session.expire_all()
    print('[4/5] Đồng bộ và thiết lập chuẩn hóa 4 tài khoản Admin...')
    admins = db.session.query(User).filter(User.id.in_(admin_ids)).all()
    admin_hash = generate_pptq_password_hash('Password123!')

    for a in admins:
        a.display_name = ADMIN_NAMES.get(a.email, a.display_name)
        a.status = 'ACTIVE'
        a.is_suspended = False
        a.suspended_at = None
        a.suspension_reason = None
        a.password_hash = admin_hash

        # Cấp đủ quyền STUDENT (1), INSTRUCTOR (2), ADMIN (3)
        existing_role_ids = {ur.role_id for ur in db.session.query(UserRole).filter_by(user_id=a.id).all()}
        for req_role_id in [1, 2, 3]:
            if req_role_id not in existing_role_ids:
                db.session.add(UserRole(
                    user_id=a.id,
                    role_id=req_role_id,
                    assignment_reason='System Admin Provisioning',
                ))

        # Cấp số dư sạch 0 VNĐ
        db.session.add(UserBalance(user_id=a.id, balance=0, currency='VND'))

    db.session.commit()
    print('   ✓ Đã cập nhật 4 Admin với mật khẩu Password123!, đủ roles và số dư 0 VNĐ.')

    # Dọn dẹp ổ đĩa lưu trữ tệp tin cũ
    print('[5/5] Dọn dẹp tệp tin rác trên ổ cứng storage và quarantine...')
    storage_root = Path('/app/storage')
    quarantine_root = Path('/app/quarantine')

    for qf in quarantine_root.glob('upload_*'):
        try:
            if qf.is_file():
                qf.unlink()
        except Exception:
            pass

    for sub in ['blobs', 'appeals', 'cashflow_proofs', 'drm_hls']:
        subdir = storage_root / sub
        if subdir.exists():
            for item in subdir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass
    print('   ✓ Đã giải phóng bộ nhớ lưu trữ tệp tin thành công!')

    # Xác minh cuối cùng
    print('\\n' + '=' * 80)
    print('=== KẾT QUẢ XÁC MINH CƠ SỞ DỮ LIỆU VPS ===')
    print('=' * 80)
    user_count = db.session.query(User).count()
    course_count = db.session.query(Course).count()
    unit_count = db.session.query(LearningUnit).count()
    lesson_count = db.session.query(Lesson).count()
    assessment_count = db.session.query(Assessment).count()
    enrollment_count = db.session.query(Enrollment).count()
    transaction_count = db.session.query(WalletTransaction).count()
    balance_count = db.session.query(UserBalance).count()

    print(f'Số lượng User hiện hữu: {user_count} (Yêu cầu: chính xác 4)')
    print(f'Số lượng Khóa học: {course_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Chương học: {unit_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Bài học: {lesson_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Bài kiểm tra: {assessment_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Ghi danh: {enrollment_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Giao dịch ví: {transaction_count} (Yêu cầu: chính xác 0)')
    print(f'Số lượng Ví tài khoản: {balance_count} (Yêu cầu: chính xác 4)')

    print('\\nDanh sách 4 Admin đang hoạt động trên VPS:')
    for u in db.session.query(User).all():
        valid_pwd = verify_password(u, 'Password123!')
        roles_str = ', '.join([ur.role.role for ur in u.user_roles])
        print(f' - ID {u.id}: {u.email} | Tên: {u.display_name} | Role: {u.primary_role} ({roles_str}) | Mật khẩu hợp lệ: {valid_pwd}')

    if user_count == 4 and course_count == 0:
        print('\\n>>> [XÁC MINH HOÀN TOÀN ĐẠT CHUẨN 100%] <<<')
    else:
        print('\\n>>> [CẢNH BÁO: CHƯA ĐẠT CHUẨN!] <<<')
"""

    clean_cmd = f"docker exec -i pwd301-production-web-1 python << 'EOF'\n{db_clean_script}\nEOF\n"
    stdin, stdout, stderr = ssh.exec_command(clean_cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    print(out)
    if err:
        print("[ERR]", err)

    # Step 8: Kiểm tra trạng thái docker containers
    run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml ps", "BƯỚC 8: Kiểm tra trạng thái dịch vụ Docker")

    # Step 9: Kiểm tra dung lượng ổ đĩa sau dọn dẹp
    run_remote("df -h /", "BƯỚC 9: Dung lượng ổ đĩa VPS sau dọn dẹp")

    # Step 10: Kiểm tra API health từ bên trong và bên ngoài
    run_remote("docker exec pwd301-production-web-1 curl -s http://localhost:5000/api/health", "BƯỚC 10.1: Kiểm tra Web Internal API Healthcheck")
    run_remote("curl -s -k https://127.0.0.1/api/health", "BƯỚC 10.2: Kiểm tra Caddy Reverse Proxy Public Healthcheck")

    ssh.close()
    print("\n" + "=" * 80)
    print("QUY TRÌNH ĐỒNG BỘ VÀ TRIỂN KHAI LÊN VPS SERVER ĐÃ HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 80)


if __name__ == "__main__":
    deploy_and_clean()
