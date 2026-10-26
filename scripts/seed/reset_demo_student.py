# -*- coding: utf-8 -*-
"""Reset demo student progress for course on VPS database."""

import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"


def reset_student_course(course_id_or_code="VVIP", student_email=None):
    print("=" * 80)
    print(f"RESET TIẾN ĐỘ DEMO CHO KHÓA HỌC: {course_id_or_code}")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

    email_filter = f"AND u.email = '{student_email}'" if student_email else ""

    sql = f"""
    SET QUOTED_IDENTIFIER ON;
    SET ANSI_NULLS ON;
    USE pwd301;
    DECLARE @cid BIGINT;
    SELECT @cid = id FROM courses WHERE course_code = '{course_id_or_code}' OR (TRY_CAST('{course_id_or_code}' AS UNIQUEIDENTIFIER) IS NOT NULL AND public_id = TRY_CAST('{course_id_or_code}' AS UNIQUEIDENTIFIER));

    IF @cid IS NOT NULL
    BEGIN
        DELETE ccs FROM course_completion_summaries ccs JOIN users u ON ccs.student_user_id = u.id WHERE ccs.course_id = @cid {email_filter};
        DELETE lp FROM lesson_progress lp JOIN enrollment_periods ep ON lp.enrollment_period_id = ep.id JOIN enrollments e ON ep.enrollment_id = e.id JOIN users u ON e.student_user_id = u.id WHERE e.course_id = @cid {email_filter};
        DELETE lpr FROM lesson_progress_receipts lpr JOIN enrollment_periods ep ON lpr.enrollment_period_id = ep.id JOIN enrollments e ON ep.enrollment_id = e.id JOIN users u ON e.student_user_id = u.id WHERE e.course_id = @cid {email_filter};
        UPDATE e SET e.status = 'ACTIVE', e.current_progress_percent = 0.0, e.completed_at = NULL, e.updated_at = SYSUTCDATETIME() FROM enrollments e JOIN users u ON e.student_user_id = u.id WHERE e.course_id = @cid {email_filter};
        UPDATE ep SET ep.status = 'ACTIVE' FROM enrollment_periods ep JOIN enrollments e ON ep.enrollment_id = e.id JOIN users u ON e.student_user_id = u.id WHERE e.course_id = @cid {email_filter};
        SELECT 'RESET_SUCCESS' AS result;
    END
    ELSE
    BEGIN
        SELECT 'COURSE_NOT_FOUND' AS result;
    END
    """

    clean_sql = " ".join(line.strip() for line in sql.splitlines() if line.strip())
    cmd = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{clean_sql}\""

    _, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")

    print(out)
    if err:
        print("[ERR]:", err)

    ssh.close()
    print("✓ Đã hoàn tất lệnh reset trên CSDL VPS!")


if __name__ == "__main__":
    course_arg = sys.argv[1] if len(sys.argv) > 1 else "VVIP"
    email_arg = sys.argv[2] if len(sys.argv) > 2 else None
    reset_student_course(course_arg, email_arg)
