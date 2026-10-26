"""Direct Database Query Utility for PWD301 LMS.

Allows developers and operators to directly query the local Docker SQL Server database,
inspect digital wallets, trace cashflow transactions, and execute raw SQL safely.

Usage:
    python scripts/query_db.py                   # Run interactive overview
    python scripts/query_db.py --stats           # Cashflow summary statistics
    python scripts/query_db.py --wallets         # List all user balances
    python scripts/query_db.py --tx              # List recent wallet transactions
    python scripts/query_db.py --users           # List user accounts
    python scripts/query_db.py --sql "SELECT TOP 5 id, amount, status FROM wallet_transactions"
"""

from __future__ import annotations

import argparse
import io
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure src is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from backend import create_app
from backend.extensions import db
from backend.models.course import Course, Enrollment
from backend.models.identity import User
from backend.models.notification_audit import AuditEvent
from backend.models.wallet import UserBalance, WalletTransaction
from backend.services.wallet_service import get_cashflow_stats


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def show_stats() -> None:
    print_header("Thống Kê Dòng Tiền Toàn Hệ Thống (Cashflow Stats)")
    stats = get_cashflow_stats(session=db.session)
    print(f"  * Tổng tiền đã nạp thành công:    {stats['total_deposited']:>15,d} {stats['currency']}")
    print(f"  * Tổng doanh thu bán khóa học:    {stats['total_revenue']:>15,d} {stats['currency']}")
    print(f"  * Tổng tiền bị thu hồi/gian lận:  {stats['total_revoked']:>15,d} {stats['currency']}")
    print(f"  * Tổng số dư ví đang lưu ký:     {stats['total_system_balance']:>15,d} {stats['currency']}")
    print(f"  * Giao dịch thành công (Count):   {stats['transactions_completed_count']:>15,d}")
    print(f"  * Giao dịch đang chờ (Pending):   {stats['transactions_pending_count']:>15,d}")


def show_wallets(limit: int = 20) -> None:
    print_header("Danh Sách Số Dư Ví Học Viên (User Balances)")
    balances = (
        db.session.query(UserBalance)
        .order_by(UserBalance.balance.desc())
        .limit(limit)
        .all()
    )
    if not balances:
        print("  (Chưa có số dư ví nào trong hệ thống)")
        return

    print(f"  {'UID':<6} | {'Email':<30} | {'Tên hiển thị':<22} | {'Số dư (VNĐ)':>15}")
    print("  " + "-" * 80)
    for b in balances:
        email = b.user.email if b.user else f"UID {b.user_id}"
        name = b.user.display_name if b.user else "Unknown"
        # Truncate if too long
        email_str = (email[:28] + "..") if len(email) > 30 else email
        name_str = (name[:20] + "..") if len(name) > 22 else name
        print(f"  {b.user_id:<6} | {email_str:<30} | {name_str:<22} | {int(b.balance):>15,d} {b.currency}")


def show_transactions(limit: int = 15) -> None:
    print_header(f"{limit} Giao Dịch Dòng Tiền Gần Nhất (Recent Wallet Transactions)")
    txs = (
        db.session.query(WalletTransaction)
        .order_by(WalletTransaction.id.desc())
        .limit(limit)
        .all()
    )
    if not txs:
        print("  (Chưa có giao dịch nào trong sổ cái)")
        return

    print(f"  {'ID':<5} | {'Loại':<15} | {'Số tiền (VNĐ)':>13} | {'Trạng thái':<10} | {'Mã chuyển khoản':<14} | {'Mô tả'}")
    print("  " + "-" * 90)
    for t in txs:
        amt = f"{int(t.amount):,d}"
        status_colored = t.status
        code = t.transfer_code_12 or (str(t.order_code) if t.order_code else "-")
        desc = (t.description[:25] + "..") if t.description and len(t.description) > 27 else (t.description or "-")
        print(f"  {t.id:<5} | {t.tx_type:<15} | {amt:>13} | {status_colored:<10} | {code:<14} | {desc}")


def show_users(limit: int = 20) -> None:
    print_header("Danh Sách Tài Khoản Người Dùng (Users)")
    users = db.session.query(User).order_by(User.id.asc()).limit(limit).all()
    print(f"  {'ID':<5} | {'Email':<30} | {'Tên hiển thị':<24} | {'Role':<12} | {'Trạng thái'}")
    print("  " + "-" * 85)
    for u in users:
        email = (u.email[:28] + "..") if len(u.email) > 30 else u.email
        name = (u.display_name[:22] + "..") if len(u.display_name) > 24 else u.display_name
        status = "ACTIVE" if u.is_active else "SUSPENDED"
        roles_str = ",".join(u.role_codes) if u.role_codes else (u.primary_role or "STUDENT")
        print(f"  {u.id:<5} | {email:<30} | {name:<24} | {roles_str:<12} | {status}")


def show_audit_logs(limit: int = 25) -> None:
    print_header(f"{limit} Nhật Ký Kiểm Toán An Ninh & Quản Trị Hệ Thống (Admin Audit Logs)")
    events = (
        db.session.query(AuditEvent)
        .order_by(AuditEvent.id.desc())
        .limit(limit)
        .all()
    )
    if not events:
        print("  (Chưa có sự kiện kiểm toán nào)")
        return

    for e in events:
        t_str = str(e.created_at)[:19] if e.created_at else "-"
        actor_name = e.actor.display_name if e.actor else "Hệ thống / Guest"
        actor_email = e.actor.email if e.actor else "-"
        role = e.actor_roles_snapshot or (e.actor.primary_role if e.actor else "SYSTEM")
        ip = e.ip_address or "Internal"
        
        print(f"\n  [ID #{e.id} | {t_str}] HÀNH ĐỘNG: {e.action}")
        print(f"  * Người thực hiện: {actor_name} ({actor_email}) | Role: {role} | IP: {ip}")
        target_info = f"{e.target_type} (ID: {e.target_id})" if e.target_type else "-"
        reason_info = f" | Lý do: {e.reason}" if e.reason else ""
        print(f"  * Mục tiêu tác động: {target_info}{reason_info}")
        if e.after_json and e.after_json != "{}":
            print(f"  * Dữ liệu chi tiết: {e.after_json}")
        print("  " + "-" * 80)


def execute_raw_sql(query: str) -> None:
    print_header(f"Thực Thi Lệnh SQL Tùy Biến")
    print(f"  SQL: {query}\n")
    try:
        result = db.session.execute(db.text(query))
        if result.returns_rows:
            rows = result.fetchall()
            keys = result.keys()
            if not rows:
                print("  (Kết quả rỗng: 0 dòng)")
                return
            # Print header
            header_str = " | ".join(f"{str(k):<15}" for k in keys)
            print(f"  {header_str}")
            print("  " + "-" * len(header_str))
            for row in rows[:50]:  # limit 50 rows
                row_str = " | ".join(f"{str(v):<15}" for v in row)
                print(f"  {row_str}")
            print(f"\n  (Tổng cộng: {len(rows)} dòng)")
        else:
            db.session.commit()
            print(f"  Lệnh đã được thực thi thành công! (Rows affected: {result.rowcount})")
    except Exception as exc:
        print(f"  [LỖI THỰC THI SQL]: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PWD301 Database Direct Query Tool")
    parser.add_argument("--stats", action="store_true", help="Hiển thị thống kê dòng tiền tổng thể")
    parser.add_argument("--wallets", action="store_true", help="Hiển thị danh sách số dư ví học viên")
    parser.add_argument("--tx", action="store_true", help="Hiển thị các giao dịch dòng tiền gần nhất")
    parser.add_argument("--users", action="store_true", help="Hiển thị danh sách tài khoản người dùng")
    parser.add_argument("--audit", action="store_true", help="Hiển thị nhật ký kiểm toán quản trị (Admin Audit Logs)")
    parser.add_argument("--sql", type=str, help="Chạy câu lệnh SQL Raw trực tiếp")

    args = parser.parse_args()

    app = create_app("development")
    with app.app_context():
        if args.sql:
            execute_raw_sql(args.sql)
        elif args.audit:
            show_audit_logs()
        elif args.stats:
            show_stats()
        elif args.wallets:
            show_wallets()
        elif args.tx:
            show_transactions()
        elif args.users:
            show_users()
        else:
            # Default: Show summary dashboard
            show_stats()
            show_wallets(limit=5)
            show_transactions(limit=8)
            print("\n  [Gợi ý]: Dùng các cờ để xem chi tiết: --wallets, --tx, --users, --stats, --sql \"SELECT...\"\n")


if __name__ == "__main__":
    main()
