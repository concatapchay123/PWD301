"""Wallet and Payment service for PWD301.

Implements:
- Digital wallet balance management for registered users.
- PayOS deposit link generation and webhook processing with HMAC-SHA256 verification.
- Course purchase with wallet balance or direct PayOS QR.
- Admin Financial management: cashflow stats, manual verification, and balance revocation
  with automated enrollment cancellation and fail-closed audit logging.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import time
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentEvent
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.models.wallet import UserBalance, WalletTransaction
from pwd301.services.audit_service import record_audit_event
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    ForbiddenError,
    ResourceNotFoundError,
    ValidationError,
)
from pwd301.services.payos_service import (
    create_payos_payment_link,
    generate_12char_transfer_code,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)


def get_or_create_balance(user_id: int, session: Session | scoped_session[Any] | None = None) -> UserBalance:
    """Retrieve or initialize a user's digital wallet balance."""
    sess = session if session is not None else db.session
    record = sess.query(UserBalance).filter(UserBalance.user_id == user_id).first()
    if record is None:
        record = UserBalance(user_id=user_id, balance=0, currency="VND")
        sess.add(record)
        sess.flush()
    return record


def deposit_via_payos(
    user: User,
    amount: int,
    return_url: str = "",
    cancel_url: str = "",
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Create a PayOS payment request to deposit funds into student wallet."""
    sess = session if session is not None else db.session

    if amount < 10000:
        raise ValidationError("Số tiền nạp tối thiểu là 10.000 VNĐ.")
    if amount > 500_000_000:
        raise ValidationError("Số tiền nạp tối đa mỗi lần là 500.000.000 VNĐ.")

    user_balance = get_or_create_balance(user.id, session=sess)
    balance_before = int(user_balance.balance or 0)

    # Generate unique numeric order_code (e.g., timestamp in milliseconds truncated to 15 digits)
    order_code = int(time.time() * 1000) % 9007199254740991

    # Generate strict 12-char transfer code: PPTQ + [User 4 chars] + [Tx 4 chars]
    transfer_code = generate_12char_transfer_code(user.id)

    # Create PENDING transaction ledger entry
    tx = WalletTransaction(
        user_id=user.id,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_before,
        tx_type="DEPOSIT",
        status="PENDING",
        order_code=order_code,
        transfer_code_12=transfer_code,
        description=f"Nạp tiền ví #{order_code}",
        meta_data=json.dumps({"channel": "PAYOS_VIETQR", "user_id": user.id}),
    )
    sess.add(tx)
    sess.flush()

    # Call PayOS integration service
    pay_meta = create_payos_payment_link(
        order_code=order_code,
        amount=amount,
        description=transfer_code,
        return_url=return_url or "http://localhost:5000/#/student/wallet?status=success",
        cancel_url=cancel_url or "http://localhost:5000/#/student/wallet?status=cancelled",
        items=[{"name": "Nạp số dư tài khoản PPTQ", "quantity": 1, "price": amount}],
    )

    tx.payment_ref = pay_meta.get("payment_link_id")
    sess.commit()

    return {
        "transaction_id": tx.id,
        "public_id": str(tx.public_id),
        "order_code": order_code,
        "amount": amount,
        "transfer_code_12": transfer_code,
        "checkout_url": pay_meta.get("checkout_url"),
        "qr_code": pay_meta.get("qr_code"),
        "bank_name": pay_meta.get("bank_name"),
        "account_name": pay_meta.get("account_name"),
        "account_number": pay_meta.get("account_number"),
        "bin": pay_meta.get("bin"),
        "status": "PENDING",
    }


def handle_payos_webhook(
    webhook_payload: dict[str, Any], session: Session | scoped_session[Any] | None = None
) -> dict[str, Any]:
    """Process incoming PayOS webhook notification."""
    sess = session if session is not None else db.session

    # Verify signature
    if not verify_webhook_signature(webhook_payload):
        logger.warning("PayOS Webhook rejected: Invalid HMAC signature")
        raise ValidationError("Invalid PayOS webhook signature.")

    data = webhook_payload.get("data", {})
    order_code = data.get("orderCode")
    amount = data.get("amount")
    transfer_desc = data.get("description", "").strip()

    if not order_code:
        logger.info("PayOS Webhook: Test ping or empty orderCode acknowledged.")
        return {"success": True, "message": "PayOS webhook test ping received successfully"}

    # Locate transaction
    tx = sess.query(WalletTransaction).filter(WalletTransaction.order_code == order_code).first()
    if tx is None and transfer_desc:
        tx = sess.query(WalletTransaction).filter(WalletTransaction.transfer_code_12 == transfer_desc).first()

    if tx is None:
        logger.warning("PayOS Webhook: Transaction not found for orderCode %s (possible test webhook).", order_code)
        return {"success": True, "message": "Transaction not found or test webhook received"}

    # Idempotency guard: If already completed, skip duplicate processing
    if tx.status == "COMPLETED":
        return {"success": True, "message": "Transaction already processed"}

    # Process based on transaction type
    if tx.tx_type == "DEPOSIT":
        user_balance = get_or_create_balance(tx.user_id, session=sess)
        bal_before = int(user_balance.balance or 0)
        user_balance.balance = bal_before + int(tx.amount)
        user_balance.updated_at = utc_now()

        tx.balance_before = bal_before
        tx.balance_after = int(user_balance.balance)
        tx.status = "COMPLETED"
        tx.updated_at = utc_now()
        tx.meta_data = json.dumps({"webhook_received": data})

        sess.flush()

        record_audit_event(
            actor=tx.user,
            action="WALLET_DEPOSIT_SUCCESS",
            target_type="USER_BALANCE",
            target_id=tx.user_id,
            details={"order_code": order_code, "amount": tx.amount, "new_balance": tx.balance_after},
            session=sess,
        )
        sess.commit()
        return {"success": True, "message": "Deposit credited successfully", "balance": tx.balance_after}

    elif tx.tx_type == "COURSE_PURCHASE":
        # Direct QR payment for a course
        tx.status = "COMPLETED"
        tx.updated_at = utc_now()
        tx.meta_data = json.dumps({"webhook_received": data})

        if tx.target_course_id:
            try:
                enroll_student(actor=tx.user, course_id=tx.target_course_id, session=sess)
            except Exception as e:
                logger.info("Enrollment on direct QR purchase note: %s", e)

        record_audit_event(
            actor=tx.user,
            action="WALLET_DIRECT_PURCHASE_SUCCESS",
            target_type="COURSE",
            target_id=tx.target_course_id,
            details={"order_code": order_code, "amount": tx.amount},
            session=sess,
        )
        sess.commit()
        return {"success": True, "message": "Course purchase via QR completed successfully"}

    sess.commit()
    return {"success": True, "message": "Webhook received"}


def purchase_course_with_wallet(
    user: User,
    course_id: int | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Enroll student into course by deducting course price from wallet balance."""
    sess = session if session is not None else db.session

    from pwd301.services.authorization_service import _resolve_course

    course = _resolve_course(course_id, session=sess)
    if course is None or course.status == "TRASH" or course.deleted_at is not None:
        raise ResourceNotFoundError("Khóa học không tồn tại hoặc đã bị xóa.")

    course_price = int(course.price or 0)

    # 1. If course is free (0đ), enroll directly
    if course_price <= 0:
        enrollment = enroll_student(actor=user, course_id=course.id, session=sess)
        sess.commit()
        return {
            "success": True,
            "enrolled": True,
            "message": "Đăng ký khóa học miễn phí thành công!",
            "price": 0,
            "course_id": str(course.public_id),
        }

    # 2. Check and deduct wallet balance
    user_balance = get_or_create_balance(user.id, session=sess)
    current_bal = int(user_balance.balance or 0)

    if current_bal < course_price:
        raise ValidationError(
            f"Số dư tài khoản không đủ. Khóa học có giá {course_price:,.0f} VNĐ, số dư hiện tại là {current_bal:,.0f} VNĐ. Vui lòng nạp thêm {course_price - current_bal:,.0f} VNĐ."
        )

    bal_before = current_bal
    bal_after = current_bal - course_price
    user_balance.balance = bal_after
    user_balance.updated_at = utc_now()

    # Record purchase transaction
    tx = WalletTransaction(
        user_id=user.id,
        amount=course_price,
        balance_before=bal_before,
        balance_after=bal_after,
        tx_type="COURSE_PURCHASE",
        status="COMPLETED",
        target_course_id=course.id,
        description=f"Mua khóa học: {course.title[:100]}",
    )
    sess.add(tx)
    sess.flush()

    # Enroll student
    enrollment = enroll_student(actor=user, course_id=course.id, session=sess)

    record_audit_event(
        actor=user,
        action="WALLET_COURSE_PURCHASE",
        target_type="COURSE",
        target_id=course.id,
        details={"course_title": course.title, "price": course_price, "new_balance": bal_after},
        session=sess,
    )
    sess.commit()

    return {
        "success": True,
        "enrolled": True,
        "message": f"Mua khóa học thành công! Số dư còn lại: {bal_after:,.0f} VNĐ.",
        "price": course_price,
        "balance": bal_after,
        "course_id": str(course.public_id),
        "enrollment_id": str(enrollment.public_id) if enrollment else None,
    }


def create_direct_course_qr(
    user: User,
    course_id: int | str,
    return_url: str = "",
    cancel_url: str = "",
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Create a PayOS QR payment link to purchase a course directly."""
    sess = session if session is not None else db.session

    from pwd301.services.authorization_service import _resolve_course

    course = _resolve_course(course_id, session=sess)
    if course is None or course.status == "TRASH" or course.deleted_at is not None:
        raise ResourceNotFoundError("Khóa học không tồn tại hoặc đã bị xóa.")

    course_price = int(course.price or 0)
    if course_price <= 0:
        return purchase_course_with_wallet(user, course.id, session=sess)

    order_code = int(time.time() * 1000) % 9007199254740991
    transfer_code = generate_12char_transfer_code(user.id)

    user_balance = get_or_create_balance(user.id, session=sess)
    cur_bal = int(user_balance.balance or 0)

    tx = WalletTransaction(
        user_id=user.id,
        amount=course_price,
        balance_before=cur_bal,
        balance_after=cur_bal,
        tx_type="COURSE_PURCHASE",
        status="PENDING",
        order_code=order_code,
        transfer_code_12=transfer_code,
        target_course_id=course.id,
        description=f"Mua #{course.course_code}: {transfer_code}",
        meta_data=json.dumps({"course_id": str(course.public_id), "course_title": course.title}),
    )
    sess.add(tx)
    sess.flush()

    pay_meta = create_payos_payment_link(
        order_code=order_code,
        amount=course_price,
        description=transfer_code,
        return_url=return_url or f"http://localhost:5000/#/student/courses/intro?id={course.public_id}&payment=success",
        cancel_url=cancel_url or f"http://localhost:5000/#/student/courses/intro?id={course.public_id}&payment=cancelled",
        items=[{"name": f"Khóa học {course.course_code}", "quantity": 1, "price": course_price}],
    )

    tx.payment_ref = pay_meta.get("payment_link_id")
    sess.commit()

    return {
        "transaction_id": tx.id,
        "public_id": str(tx.public_id),
        "order_code": order_code,
        "course_id": str(course.public_id),
        "course_title": course.title,
        "amount": course_price,
        "transfer_code_12": transfer_code,
        "checkout_url": pay_meta.get("checkout_url"),
        "qr_code": pay_meta.get("qr_code"),
        "bank_name": pay_meta.get("bank_name"),
        "account_name": pay_meta.get("account_name"),
        "account_number": pay_meta.get("account_number"),
        "bin": pay_meta.get("bin"),
        "status": "PENDING",
    }


def revoke_transaction(
    admin_user: User,
    tx_id: int | str,
    reason: str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Revoke an abnormal deposit transaction, deduct wallet balance, and cancel associated course enrollments."""
    sess = session if session is not None else db.session

    if not admin_user.is_admin:
        raise ForbiddenError("Chỉ Quản trị viên mới có quyền thu hồi giao dịch.")

    tx = None
    try:
        tx_int = int(tx_id)
        tx = sess.query(WalletTransaction).filter(WalletTransaction.id == tx_int).first()
    except (ValueError, TypeError):
        pass

    if tx is None:
        import uuid
        try:
            val_uuid = uuid.UUID(str(tx_id))
            tx = sess.query(WalletTransaction).filter(WalletTransaction.public_id == val_uuid).first()
        except (ValueError, TypeError):
            pass

    if tx is None:
        raise ResourceNotFoundError("Giao dịch không tồn tại.")

    if tx.status == "REVOKED":
        raise ValidationError("Giao dịch này đã bị thu hồi trước đó.")

    # Deduct balance
    user_balance = get_or_create_balance(tx.user_id, session=sess)
    bal_before = int(user_balance.balance or 0)
    revoked_amount = int(tx.amount)
    bal_after = max(0, bal_before - revoked_amount)
    user_balance.balance = bal_after
    user_balance.updated_at = utc_now()

    # Identify and cancel course enrollments purchased with abnormal funds
    cancelled_courses = []
    # If the transaction itself was a course purchase
    if tx.target_course_id:
        enr = (
            sess.query(Enrollment)
            .filter(
                Enrollment.student_user_id == tx.user_id,
                Enrollment.course_id == tx.target_course_id,
            )
            .first()
        )
        if enr:
            enr.status = "LEFT"
            cancelled_courses.append(enr.course.title if enr.course else str(tx.target_course_id))
    else:
        # If user spent more than remaining balance, cancel recent enrolled courses
        if bal_before < revoked_amount:
            recent_purchases = (
                sess.query(WalletTransaction)
                .filter(
                    WalletTransaction.user_id == tx.user_id,
                    WalletTransaction.tx_type == "COURSE_PURCHASE",
                    WalletTransaction.status == "COMPLETED",
                )
                .order_by(WalletTransaction.id.desc())
                .all()
            )
            for p in recent_purchases:
                if p.target_course_id:
                    enr = (
                        sess.query(Enrollment)
                        .filter(
                            Enrollment.student_user_id == tx.user_id,
                            Enrollment.course_id == p.target_course_id,
                        )
                        .first()
                    )
                    if enr and enr.status == "ACTIVE":
                        enr.status = "LEFT"
                        cancelled_courses.append(enr.course.title if enr.course else str(p.target_course_id))

    tx.status = "REVOKED"
    tx.updated_at = utc_now()
    tx.created_by_user_id = admin_user.id
    meta = json.loads(tx.meta_data) if tx.meta_data else {}
    meta["revoke_reason"] = reason
    meta["revoked_by"] = admin_user.email
    meta["revoked_at"] = utc_now().isoformat()
    meta["cancelled_courses"] = cancelled_courses
    tx.meta_data = json.dumps(meta)

    # Mandatory Fail-Closed Audit Logging
    record_audit_event(
        actor=admin_user,
        action="WALLET_BALANCE_REVOKE",
        target_type="WALLET_TRANSACTION",
        target_id=tx.id,
        reason=reason,
        details={
            "user_id": tx.user_id,
            "revoked_amount": revoked_amount,
            "balance_before": bal_before,
            "balance_after": bal_after,
            "cancelled_courses": cancelled_courses,
        },
        session=sess,
    )
    sess.commit()

    return {
        "success": True,
        "message": f"Đã thu hồi thành công {revoked_amount:,.0f} VNĐ.",
        "transaction_id": tx.id,
        "revoked_amount": revoked_amount,
        "new_balance": bal_after,
        "cancelled_courses": cancelled_courses,
    }


def verify_deposit_manually(
    admin_user: User,
    tx_id: int | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Admin manual confirmation of a pending deposit transaction."""
    sess = session if session is not None else db.session

    if not admin_user.is_admin:
        raise ForbiddenError("Chỉ Quản trị viên mới có quyền xác thực giao dịch.")

    tx = None
    try:
        tx_int = int(tx_id)
        tx = sess.query(WalletTransaction).filter(WalletTransaction.id == tx_int).first()
    except (ValueError, TypeError):
        pass

    if tx is None:
        import uuid
        try:
            val_uuid = uuid.UUID(str(tx_id))
            tx = sess.query(WalletTransaction).filter(WalletTransaction.public_id == val_uuid).first()
        except (ValueError, TypeError):
            pass

    if tx is None:
        raise ResourceNotFoundError("Giao dịch không tồn tại.")

    if tx.status == "COMPLETED":
        return {"success": True, "message": "Giao dịch đã được ghi nhận trước đó."}

    user_balance = get_or_create_balance(tx.user_id, session=sess)
    bal_before = int(user_balance.balance or 0)
    bal_after = bal_before + int(tx.amount)
    user_balance.balance = bal_after
    user_balance.updated_at = utc_now()

    tx.balance_before = bal_before
    tx.balance_after = bal_after
    tx.status = "COMPLETED"
    tx.updated_at = utc_now()
    tx.created_by_user_id = admin_user.id

    record_audit_event(
        actor=admin_user,
        action="WALLET_MANUAL_VERIFY",
        target_type="WALLET_TRANSACTION",
        target_id=tx.id,
        details={"user_id": tx.user_id, "amount": tx.amount, "new_balance": bal_after},
        session=sess,
    )
    sess.commit()

    return {
        "success": True,
        "message": f"Đã xác thực nạp tiền thành công {tx.amount:,.0f} VNĐ cho học viên.",
        "transaction_id": tx.id,
        "balance": bal_after,
    }


def get_cashflow_stats(session: Session | scoped_session[Any] | None = None) -> dict[str, Any]:
    """Calculate aggregated cashflow statistics for dashboard."""
    sess = session if session is not None else db.session

    total_deposited = (
        sess.query(sa.func.sum(WalletTransaction.amount))
        .filter(
            WalletTransaction.tx_type == "DEPOSIT",
            WalletTransaction.status == "COMPLETED",
        )
        .scalar()
        or 0
    )

    total_revenue = (
        sess.query(sa.func.sum(WalletTransaction.amount))
        .filter(
            WalletTransaction.tx_type == "COURSE_PURCHASE",
            WalletTransaction.status == "COMPLETED",
        )
        .scalar()
        or 0
    )

    total_revoked = (
        sess.query(sa.func.sum(WalletTransaction.amount))
        .filter(
            WalletTransaction.status == "REVOKED",
        )
        .scalar()
        or 0
    )

    total_system_balance = (
        sess.query(sa.func.sum(UserBalance.balance)).scalar() or 0
    )

    tx_count_completed = (
        sess.query(sa.func.count(WalletTransaction.id))
        .filter(WalletTransaction.status == "COMPLETED")
        .scalar()
        or 0
    )

    tx_count_pending = (
        sess.query(sa.func.count(WalletTransaction.id))
        .filter(WalletTransaction.status == "PENDING")
        .scalar()
        or 0
    )

    return {
        "total_deposited": int(total_deposited),
        "total_revenue": int(total_revenue),
        "total_revoked": int(total_revoked),
        "total_system_balance": int(total_system_balance),
        "transactions_completed_count": int(tx_count_completed),
        "transactions_pending_count": int(tx_count_pending),
        "currency": "VND",
    }


def expire_stale_pending_transactions(
    user_id: int | None = None,
    timeout_seconds: int = 300,
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Auto-transition PENDING deposit transactions older than timeout_seconds (default 5m/300s) to FAILED."""
    sess = session if session is not None else db.session
    now = utc_now()
    threshold = now - timedelta(seconds=timeout_seconds)

    q = sess.query(WalletTransaction).filter(
        WalletTransaction.status == "PENDING",
        WalletTransaction.created_at <= threshold,
    )
    if user_id is not None:
        q = q.filter(WalletTransaction.user_id == user_id)

    stale_txs = q.all()
    if not stale_txs:
        return 0

    count = 0
    for tx in stale_txs:
        tx.status = "FAILED"
        tx.updated_at = now
        meta = {}
        if tx.meta_data:
            try:
                meta = json.loads(tx.meta_data) if isinstance(tx.meta_data, str) else dict(tx.meta_data)
            except Exception:
                meta = {"raw": str(tx.meta_data)}
        meta["expire_reason"] = "timeout_5m_expired"
        tx.meta_data = json.dumps(meta)
        count += 1

    try:
        sess.commit()
    except Exception as exc:
        sess.rollback()
        logger.warning("Failed to commit stale transaction expiration: %s", exc)

    return count


def list_transactions_paginated(
    page: int = 1,
    page_size: int = 5,
    user_id: int | None = None,
    tx_type: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """List transactions with pagination for user history or admin view."""
    sess = session if session is not None else db.session

    # Automatically sweep stale transactions before returning results
    expire_stale_pending_transactions(user_id=user_id, timeout_seconds=300, session=sess)

    q = sess.query(WalletTransaction)
    if user_id is not None:
        q = q.filter(WalletTransaction.user_id == user_id)
    if tx_type:
        q = q.filter(WalletTransaction.tx_type == tx_type)

    total_count = q.count()
    safe_page_size = max(1, page_size)
    total_pages = max(1, (total_count + safe_page_size - 1) // safe_page_size) if total_count > 0 else 1
    safe_page = max(1, min(page, total_pages))
    offset = (safe_page - 1) * safe_page_size

    txs = q.order_by(WalletTransaction.id.desc()).offset(offset).limit(safe_page_size).all()
    return {
        "items": [t.to_dict() for t in txs],
        "total_count": total_count,
        "page": safe_page,
        "page_size": safe_page_size,
        "total_pages": total_pages,
    }


def list_transactions(
    limit: int = 50,
    offset: int = 0,
    user_id: int | None = None,
    tx_type: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """List transactions with optional filters for audit/history view."""
    sess = session if session is not None else db.session

    # Automatically sweep stale transactions before returning results
    expire_stale_pending_transactions(user_id=user_id, timeout_seconds=300, session=sess)

    q = sess.query(WalletTransaction)
    if user_id is not None:
        q = q.filter(WalletTransaction.user_id == user_id)
    if tx_type:
        q = q.filter(WalletTransaction.tx_type == tx_type)

    txs = q.order_by(WalletTransaction.id.desc()).offset(offset).limit(limit).all()
    return [t.to_dict() for t in txs]
