# -*- coding: utf-8 -*-
"""Switch system to VULNERABLE mode for live committee defense demonstration across ANY course."""

import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"


def set_vulnerable(course_code="ALL", student_email=None):
    print("=" * 80)
    print("PPTQ LMS — KÍCH HOẠT CHẾ ĐỘ DEMO LỖ HỔNG TOÀN DIỆN (VULNERABLE MODE)")
    print("=" * 80)
    print(f"[*] Mục tiêu: Khóa học [{course_code}] | Học viên: [{student_email or 'Tất cả'}]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

    # 1. Ghi cờ VULNERABLE vào storage
    cmd_flag = "docker exec $(docker ps -q -f name=web) sh -c 'echo VULNERABLE > /app/storage/defense_mode.txt && chmod 666 /app/storage/defense_mode.txt'"
    _, out, _ = ssh.exec_command(cmd_flag)
    out.read()
    print("[+] Đã gỡ bỏ chốt chặn bảo mật phía máy chủ (Lỗ hổng 1 & Lỗ hổng 2 đã mở).")

    # 2. Reset tiến độ học viên về 0%
    email_filter = f"AND u.email = '{student_email}'" if student_email else ""
    course_filter = "" if course_code.upper() == "ALL" else f"""
    AND (c.course_code = '{course_code}' OR (TRY_CAST('{course_code}' AS UNIQUEIDENTIFIER) IS NOT NULL AND c.public_id = TRY_CAST('{course_code}' AS UNIQUEIDENTIFIER)))
    """

    sql = f"""
    SET QUOTED_IDENTIFIER ON;
    SET ANSI_NULLS ON;
    USE pwd301;

    DELETE ccs FROM course_completion_summaries ccs
    JOIN users u ON ccs.student_user_id = u.id
    JOIN courses c ON ccs.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    DELETE ar FROM assessment_results ar
    JOIN assessment_attempts aa ON ar.attempt_id = aa.id
    JOIN assessments a ON aa.assessment_id = a.id
    JOIN users u ON aa.student_user_id = u.id
    JOIN courses c ON a.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    DELETE aa FROM assessment_attempts aa
    JOIN assessments a ON aa.assessment_id = a.id
    JOIN users u ON aa.student_user_id = u.id
    JOIN courses c ON a.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    DELETE lp FROM lesson_progress lp
    JOIN enrollment_periods ep ON lp.enrollment_period_id = ep.id
    JOIN enrollments e ON ep.enrollment_id = e.id
    JOIN users u ON e.student_user_id = u.id
    JOIN courses c ON e.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    DELETE lpr FROM lesson_progress_receipts lpr
    JOIN enrollment_periods ep ON lpr.enrollment_period_id = ep.id
    JOIN enrollments e ON ep.enrollment_id = e.id
    JOIN users u ON e.student_user_id = u.id
    JOIN courses c ON e.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    UPDATE e
    SET e.status = 'ACTIVE',
        e.current_progress_percent = 0.0,
        e.completed_at = NULL,
        e.updated_at = SYSUTCDATETIME()
    FROM enrollments e
    JOIN users u ON e.student_user_id = u.id
    JOIN courses c ON e.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};

    UPDATE ep
    SET ep.status = 'ACTIVE',
        ep.completed_at = NULL,
        ep.updated_at = SYSUTCDATETIME()
    FROM enrollment_periods ep
    JOIN enrollments e ON ep.enrollment_id = e.id
    JOIN users u ON e.student_user_id = u.id
    JOIN courses c ON e.course_id = c.id
    WHERE 1=1 {email_filter} {course_filter};
    """
    clean_sql = " ".join(line.strip() for line in sql.splitlines() if line.strip())
    cmd_sql = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{clean_sql}\""
    _, out_s, _ = ssh.exec_command(cmd_sql)
    out_s.read()
    print(f"[+] Đã reset tiến độ học viên về 0% cho [{course_code}] (Sẵn sàng để demo hack).")

    ssh.close()
    print("=" * 80)
    print("✓ HỆ THỐNG ĐÃ SẴN SÀNG Ở CHẾ ĐỘ CÓ LỖ HỔNG (VULNERABLE) TRÊN TOÀN BỘ KHÓA HỌC!")
    print("👉 Bây giờ bạn có thể mở bất kỳ khóa học nào (JPD113, VVIP, DSA) và chạy demo.")
    print("=" * 80)


if __name__ == "__main__":
    course = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    email = sys.argv[2] if len(sys.argv) > 2 else None
    set_vulnerable(course, email)
