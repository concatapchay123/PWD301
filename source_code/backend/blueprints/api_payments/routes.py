"""Routes for PayOS payment processing and student digital wallet."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from flask import Response, jsonify, request
from flask_login import current_user, login_required

from backend.blueprints.api_payments import api_payments_bp
from backend.extensions import db
from backend.models.types import utc_now
from backend.models.wallet import WalletTransaction
from backend.services.authorization_service import get_authenticated_actor, require_authenticated_actor
from backend.services.exceptions import (
    ForbiddenError,
    ResourceNotFoundError,
    ValidationError,
)
from backend.services.payos_service import fetch_payos_payment_link_info
from backend.services.wallet_service import (
    create_direct_course_qr,
    deposit_via_payos,
    expire_stale_pending_transactions,
    get_or_create_balance,
    handle_payos_webhook,
    list_transactions,
    list_transactions_paginated,
    purchase_course_with_wallet,
)

logger = logging.getLogger(__name__)


@api_payments_bp.route("/wallet/me", methods=["GET"])
def get_my_wallet() -> tuple[Response, int] | Response:
    """Retrieve current student wallet balance and transaction history with pagination."""
    actor = get_authenticated_actor()
    if not actor:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # Sweep stale pending deposits (> 5 minutes)
    expire_stale_pending_transactions(user_id=actor.id, timeout_seconds=300, session=db.session)

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.args.get("page_size", 5))
    except (ValueError, TypeError):
        page_size = 5

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 5

    balance_record = get_or_create_balance(actor.id, session=db.session)
    paginated = list_transactions_paginated(
        page=page,
        page_size=page_size,
        user_id=actor.id,
        session=db.session,
    )

    return jsonify({
        "success": True,
        "balance": int(balance_record.balance or 0),
        "currency": balance_record.currency,
        "updated_at": balance_record.updated_at.isoformat() if balance_record.updated_at else None,
        "recent_transactions": paginated["items"],
        "pagination": {
            "page": paginated["page"],
            "page_size": paginated["page_size"],
            "total_count": paginated["total_count"],
            "total_pages": paginated["total_pages"],
        },
    }), 200


@api_payments_bp.route("/deposit/create", methods=["POST"])
def create_deposit_request() -> tuple[Response, int] | Response:
    """Initiate a PayOS payment request to deposit money into wallet."""
    actor = get_authenticated_actor()
    if not actor:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    try:
        amount = int(payload.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Số tiền không hợp lệ"}), 400

    return_url = payload.get("return_url", "")
    cancel_url = payload.get("cancel_url", "")

    try:
        res = deposit_via_payos(
            user=actor,
            amount=amount,
            return_url=return_url,
            cancel_url=cancel_url,
            session=db.session,
        )
        return jsonify({"success": True, "data": res, **res}), 201
    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as exc:
        logger.exception("Failed to create deposit link: %s", exc)
        return jsonify({"success": False, "error": "Không thể tạo liên kết thanh toán. Vui lòng thử lại."}), 500


@api_payments_bp.route("/payos/webhook", methods=["GET", "POST", "HEAD"])
def payos_webhook() -> tuple[Response, int] | Response:
    """Public webhook receiver for PayOS payment confirmation."""
    if request.method in ("GET", "HEAD"):
        return jsonify({
            "success": True,
            "message": "PayOS Webhook endpoint is active and listening.",
            "endpoint": "/api/payments/payos/webhook",
        }), 200

    payload = request.get_json(silent=True) or {}
    try:
        result = handle_payos_webhook(payload, session=db.session)
        return jsonify({"success": True, **result}), 200
    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as exc:
        logger.exception("PayOS webhook processing error: %s", exc)
        return jsonify({"success": False, "error": "Webhook processing error"}), 500


@api_payments_bp.route("/payos/confirm-webhook", methods=["POST"])
def trigger_confirm_payos_webhook() -> tuple[Response, int] | Response:
    """Admin / system trigger to register and confirm webhook URL with PayOS."""
    actor = get_authenticated_actor()
    if not actor or actor.role not in ("ADMIN", "SYSADMIN"):
        return jsonify({"success": False, "error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    webhook_url = payload.get("webhook_url")

    try:
        from backend.services.payos_service import confirm_payos_webhook_url

        res = confirm_payos_webhook_url(webhook_url=webhook_url)
        return jsonify({"success": True, "data": res}), 200
    except Exception as exc:
        logger.exception("Failed to confirm PayOS webhook: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@api_payments_bp.route("/course/purchase", methods=["POST"])
def purchase_course_api() -> tuple[Response, int] | Response:
    """Purchase a course using internal digital wallet balance."""
    actor = get_authenticated_actor()
    if not actor:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    course_id = payload.get("course_id")
    if not course_id:
        return jsonify({"success": False, "error": "Thiếu mã khóa học (course_id)"}), 400

    try:
        res = purchase_course_with_wallet(user=actor, course_id=course_id, session=db.session)
        return jsonify({"success": True, "data": res, **res}), 200
    except (ValidationError, ResourceNotFoundError) as err:
        return jsonify({"success": False, "error": str(err)}), 400
    except Exception as exc:
        logger.exception("Failed to purchase course with wallet: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@api_payments_bp.route("/course/create-direct-qr", methods=["POST"])
def create_direct_course_qr_api() -> tuple[Response, int] | Response:
    """Create a PayOS QR code to purchase a specific course directly."""
    actor = get_authenticated_actor()
    if not actor:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    course_id = payload.get("course_id")
    if not course_id:
        return jsonify({"success": False, "error": "Thiếu mã khóa học (course_id)"}), 400

    return_url = payload.get("return_url", "")
    cancel_url = payload.get("cancel_url", "")

    try:
        res = create_direct_course_qr(
            user=actor,
            course_id=course_id,
            return_url=return_url,
            cancel_url=cancel_url,
            session=db.session,
        )
        return jsonify({"success": True, "data": res, **res}), 201
    except (ValidationError, ResourceNotFoundError) as err:
        return jsonify({"success": False, "error": str(err)}), 400
    except Exception as exc:
        logger.exception("Failed to create direct course QR: %s", exc)
        return jsonify({"success": False, "error": "Không thể tạo mã QR thanh toán khóa học"}), 500


@api_payments_bp.route("/check-status/<tx_id>", methods=["GET"])
def check_transaction_status(tx_id: str) -> tuple[Response, int] | Response:
    """Check payment transaction status for client polling."""
    actor = get_authenticated_actor()
    if not actor:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    tx = None
    if tx_id.isdigit():
        tx_int = int(tx_id)
        tx = db.session.query(WalletTransaction).filter(
            WalletTransaction.user_id == actor.id,
            (WalletTransaction.id == tx_int) | (WalletTransaction.order_code == tx_int),
        ).first()
    else:
        try:
            val_uuid = uuid.UUID(tx_id)
            tx = db.session.query(WalletTransaction).filter(
                WalletTransaction.user_id == actor.id,
                WalletTransaction.public_id == val_uuid,
            ).first()
        except (ValueError, TypeError):
            tx = db.session.query(WalletTransaction).filter(
                WalletTransaction.user_id == actor.id,
                WalletTransaction.transfer_code_12 == tx_id,
            ).first()

    if tx is None:
        return jsonify({"success": False, "error": "Transaction not found"}), 404

    # Active sync with PayOS if still pending
    if tx.status == "PENDING" and tx.order_code:
        try:
            payos_info = fetch_payos_payment_link_info(tx.order_code)
            if payos_info and str(payos_info.get("status", "")).upper() in ("PAID", "COMPLETED", "SUCCESS"):
                paid_amt = payos_info.get("amountPaid") or payos_info.get("amount", tx.amount)
                user_bal = get_or_create_balance(tx.user_id, session=db.session)
                bal_before = int(user_bal.balance or 0)
                user_bal.balance = bal_before + int(paid_amt)
                user_bal.updated_at = utc_now()
                tx.balance_before = bal_before
                tx.balance_after = int(user_bal.balance)
                tx.status = "COMPLETED"
                tx.updated_at = utc_now()
                db.session.commit()
        except Exception as sync_err:
            logger.debug("Failed active PayOS sync during polling: %s", sync_err)

    return jsonify({
        "success": True,
        "transaction_id": tx.id,
        "order_code": tx.order_code,
        "status": tx.status,
        "amount": tx.amount,
        "balance": tx.balance_after if tx.status == "COMPLETED" else 0,
        "tx_type": tx.tx_type,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
    }), 200
