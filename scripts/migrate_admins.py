"""Script to migrate administrator accounts in PWD301.

Deletes legacy admin accounts and establishes 4 primary administrators:
1. vinhphu2020.nt@gmail.com - Vĩnh Phú
2. danglyquan@gmail.com - Đặng Lý Quân
3. tqtphamnguyenhoangphuc@gmail.com - Hoàng Phúc (Historical data recipient)
4. callmewin06@gmail.com - Hữu Thắng

All accounts have password: Password123! and full ADMIN_PRIMARY privileges.
"""

from __future__ import annotations

import os
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.models.types import utc_now

TARGET_ADMINS = [
    {
        "email": "vinhphu2020.nt@gmail.com",
        "display_name": "Vĩnh Phú",
        "password": "Password123!",
    },
    {
        "email": "danglyquan@gmail.com",
        "display_name": "Đặng Lý Quân",
        "password": "Password123!",
    },
    {
        "email": "tqtphamnguyenhoangphuc@gmail.com",
        "display_name": "Hoàng Phúc",
        "password": "Password123!",
    },
    {
        "email": "callmewin06@gmail.com",
        "display_name": "Hữu Thắng",
        "password": "Password123!",
    },
]

HISTORICAL_TRANSFER_EMAIL = "tqtphamnguyenhoangphuc@gmail.com"


def run_migration() -> None:
    app = create_app()
    with app.app_context():
        session = db.session

        print("=== BƯỚC 1: KHỞI TẠO HOẶC CẬP NHẬT 4 TÀI KHOẢN ADMIN CHÍNH ===")
        # Ensure canonical roles exist
        roles = {}
        for code, name in [
            ("STUDENT", "Student"),
            ("INSTRUCTOR", "Instructor"),
            ("ADMIN", "System Administrator"),
        ]:
            role = session.query(Role).filter_by(code=code).first()
            if not role:
                role = Role(code=code, name=name)
                session.add(role)
                session.flush()
            roles[code] = role

        created_admin_map: dict[str, User] = {}
        for item in TARGET_ADMINS:
            email = item["email"].strip().lower()
            user = session.query(User).filter_by(email_normalized=email).first()
            if user is None:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(item["password"]),
                    display_name=item["display_name"],
                    status="ACTIVE",
                    auth_version=1,
                    email_verified_at=utc_now(),
                )
                session.add(user)
                session.flush()
                print(f" [+] Đã tạo mới user: {email} (ID: {user.id})")
            else:
                user.display_name = item["display_name"]
                user.password_hash = generate_password_hash(item["password"])
                user.status = "ACTIVE"
                if not user.email_verified_at:
                    user.email_verified_at = utc_now()
                session.flush()
                print(f" [*] Đã cập nhật user: {email} (ID: {user.id})")

            # Ensure cumulative roles: STUDENT, INSTRUCTOR, ADMIN
            for r_code in ["STUDENT", "INSTRUCTOR", "ADMIN"]:
                r_obj = roles[r_code]
                link = (
                    session.query(UserRole)
                    .filter_by(user_id=user.id, role_id=r_obj.id)
                    .first()
                )
                reason = (
                    "SUB_ROLE:ADMIN_PRIMARY | Baseline root administrator initialization"
                    if r_code == "ADMIN"
                    else "Baseline root administrator initialization"
                )
                if not link:
                    link = UserRole(
                        user_id=user.id,
                        role_id=r_obj.id,
                        assigned_by_user_id=user.id,
                        assignment_reason=reason,
                    )
                    session.add(link)
                else:
                    if r_code == "ADMIN" and "SUB_ROLE:ADMIN_PRIMARY" not in (
                        link.assignment_reason or ""
                    ):
                        link.assignment_reason = reason
            created_admin_map[email] = user

        session.commit()

        # Identify recipient of historical data
        phuc_user = created_admin_map[HISTORICAL_TRANSFER_EMAIL.lower()]
        print(f"\nTarget admin nhận dữ liệu lịch sử: {phuc_user.email} (ID: {phuc_user.id})")

        print("\n=== BƯỚC 2: TÌM KIẾM VÀ CHUYỂN GIAO TOÀN BỘ ADMIN CŨ KHỎI HỆ THỐNG ===")
        allowed_emails = {a["email"].lower() for a in TARGET_ADMINS}

        # Query all users with ADMIN role not in allowed_emails
        old_admins = (
            session.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .filter(Role.code == "ADMIN")
            .filter(User.email_normalized.not_in(allowed_emails))
            .distinct()
            .all()
        )

        print(f"Tìm thấy {len(old_admins)} tài khoản admin cũ cần gỡ bỏ:")
        for oa in old_admins:
            print(f" - ID: {oa.id} | Email: {oa.email} | Display Name: {oa.display_name}")

        for old_user in old_admins:
            old_id = old_user.id
            new_id = phuc_user.id

            print(f"\nĐang xử lý chuyển giao ID: {old_id} -> ID: {new_id}...")

            # Run transfer SQL in transaction
            transfer_sql = text("""
                -- Disable trigger on audit_events
                IF OBJECT_ID('trg_audit_events_append_only', 'TR') IS NOT NULL
                    ALTER TABLE audit_events DISABLE TRIGGER trg_audit_events_append_only;

                -- Dynamic update for all foreign keys pointing to users table
                DECLARE @sql NVARCHAR(MAX) = N'';
                SELECT @sql += N'UPDATE ' + QUOTENAME(OBJECT_SCHEMA_NAME(fk.parent_object_id)) + '.' + QUOTENAME(OBJECT_NAME(fk.parent_object_id)) 
                             + N' SET ' + QUOTENAME(c.name) + N' = @new_id WHERE ' + QUOTENAME(c.name) + N' = @old_id; '
                FROM sys.foreign_keys fk
                JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
                WHERE OBJECT_NAME(fk.referenced_object_id) = 'users'
                  AND OBJECT_NAME(fk.parent_object_id) NOT IN ('auth_sessions', 'jwt_token_grants', 'user_security_tokens', 'user_roles', 'notification_preferences');

                EXEC sp_executesql @sql, N'@old_id BIGINT, @new_id BIGINT', @old_id = :old_id, @new_id = :new_id;

                -- Re-enable trigger on audit_events
                IF OBJECT_ID('trg_audit_events_append_only', 'TR') IS NOT NULL
                    ALTER TABLE audit_events ENABLE TRIGGER trg_audit_events_append_only;

                -- Delete ephemeral records
                DELETE FROM auth_sessions WHERE user_id = :old_id;
                DELETE FROM jwt_token_grants WHERE user_id = :old_id;
                DELETE FROM user_security_tokens WHERE user_id = :old_id;
                DELETE FROM notification_preferences WHERE user_id = :old_id;
                DELETE FROM user_roles WHERE user_id = :old_id;

                -- Delete the user record
                DELETE FROM users WHERE id = :old_id;
            """)

            session.execute(transfer_sql, {"old_id": old_id, "new_id": new_id})
            session.commit()
            print(f" [+] Đã chuyển giao toàn bộ dữ liệu và xóa vĩnh viễn user ID {old_id}!")

        print("\n=== BƯỚC 3: KIỂM TRA XÁC MINH CƠ SỞ DỮ LIỆU SAU MIGRATION ===")
        current_admins = (
            session.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .filter(Role.code == "ADMIN")
            .distinct()
            .all()
        )

        print(f"Số lượng Admin hiện tại trong hệ thống: {len(current_admins)}")
        for ca in current_admins:
            print(
                f" - ID: {ca.id} | Email: {ca.email} | Tên: {ca.display_name} "
                f"| is_admin: {ca.is_admin} | is_primary_admin: {ca.is_primary_admin} "
                f"| roles: {sorted(ca.role_codes)}"
            )

        assert len(current_admins) == 4, f"Mong đợi 4 admins, thực tế có {len(current_admins)}"
        print("\n>>> MIGRATION HOÀN TẤT THÀNH CÔNG 100%! <<<")


if __name__ == "__main__":
    run_migration()
