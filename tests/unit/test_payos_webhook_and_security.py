"""Unit and integration tests for PayOS Webhook processing and financial security.

Verifies:
- Canonical HMAC-SHA256 signature verification matching PayOS SDK specifications (handling nulls).
- Tamper-proofing: rejecting forged or malformed signatures.
- Robust bank memo resolution (exact and regex extraction of 12-char code PPTQ[A-Z0-9]{8}).
- Double-credit race condition and idempotency prevention.
- Underpayment financial exploit defense.
- Recovery of prematurely failed transactions.
- Active synchronization with PayOS gateway in check_transaction_status.
"""

from __future__ import annotations

import json
from unittest.mock import patch
import pytest
from werkzeug.security import generate_password_hash

from backend.extensions import db
from backend.models.identity import User
from backend.models.types import utc_now
from backend.models.wallet import UserBalance, WalletTransaction
from backend.services.jwt_auth_service import create_token_pair
from backend.services.exceptions import ValidationError
from backend.services.payos_service import (
    PAYOS_CHECKSUM_KEY,
    convert_obj_to_query_str,
    create_signature,
    generate_12char_transfer_code,
    verify_webhook_signature,
)
from backend.services.wallet_service import (
    get_or_create_balance,
    handle_payos_webhook,
)


def test_payos_signature_canonical_with_null_fields():
    """Verify signature algorithm handles nulls per official PayOS canonical specs."""
    checksum_key = "70416e4bea731fa6887e4d175e4503aae1e49b938d0d9a9f6463b0e568ed6d4d"
    sample_data = {
        "orderCode": 99887766,
        "amount": 50000,
        "description": "PPTQU001A801",
        "accountNumber": "0908667141",
        "reference": "FT2401",
        "transactionDateTime": "2026-10-24 10:00:00",
        "currency": "VND",
        "paymentLinkId": "test-link-123",
        "code": "00",
        "desc": "success",
        "counterAccountBankId": None,
        "counterAccountBankName": None,
        "counterAccountName": None,
        "counterAccountNumber": None,
        "virtualAccountName": None,
        "virtualAccountNumber": None,
    }

    # Query string must include counterAccount* as empty string key=
    query_str = convert_obj_to_query_str(sample_data)
    assert "counterAccountBankId=&" in query_str
    assert "virtualAccountName=&" in query_str

    sig = create_signature(sample_data, checksum_key)
    payload = {
        "code": "00",
        "desc": "success",
        "data": sample_data,
        "signature": sig,
    }

    assert verify_webhook_signature(payload, checksum_key) is True

    # Tampered signature must fail
    tampered_payload = {
        "code": "00",
        "desc": "success",
        "data": sample_data,
        "signature": "bad_signature_123456",
    }
    assert verify_webhook_signature(tampered_payload, checksum_key) is False


def test_handle_payos_webhook_success_and_idempotency(app):
    """Verify webhook auto-credits wallet balance and prevents double-crediting."""
    with app.app_context():
        user = User(
            email="test_webhook_user@backend.local",
            display_name="Webhook Student",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        tx = WalletTransaction(
            user_id=user.id,
            amount=100000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=777001,
            transfer_code_12="PPTQU001TX01",
            description="Nạp ví #777001",
        )
        db.session.add(tx)
        db.session.commit()

        webhook_data = {
            "orderCode": 777001,
            "amount": 100000,
            "description": "PPTQU001TX01",
            "accountNumber": "0908667141",
            "reference": "FT998877",
            "transactionDateTime": "2026-10-24 10:30:00",
            "currency": "VND",
            "paymentLinkId": "pl-777001",
            "code": "00",
            "desc": "success",
            "counterAccountBankId": None,
            "counterAccountBankName": None,
            "counterAccountName": None,
            "counterAccountNumber": None,
            "virtualAccountName": None,
            "virtualAccountNumber": None,
        }
        sig = create_signature(webhook_data, PAYOS_CHECKSUM_KEY)
        payload = {
            "code": "00",
            "desc": "success",
            "data": webhook_data,
            "signature": sig,
        }

        # First call: Credits the balance
        res1 = handle_payos_webhook(payload, session=db.session)
        assert res1["success"] is True
        assert res1["balance"] == 100000

        db.session.refresh(tx)
        assert tx.status == "COMPLETED"
        assert tx.balance_after == 100000

        user_bal = get_or_create_balance(user.id, session=db.session)
        assert int(user_bal.balance) == 100000

        # Second call (Idempotency check): Must NOT double credit
        res2 = handle_payos_webhook(payload, session=db.session)
        assert res2["success"] is True
        assert res2.get("already_completed") is True

        db.session.refresh(user_bal)
        assert int(user_bal.balance) == 100000  # Still 100000, not 200000!


def test_handle_payos_webhook_bank_memo_variance(app):
    """Verify bank transfer memo with prefix/suffix still resolves via regex."""
    with app.app_context():
        user = User(
            email="test_memo_user@backend.local",
            display_name="Memo Student",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        tx = WalletTransaction(
            user_id=user.id,
            amount=50000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=888002,
            transfer_code_12="PPTQU042TX99",
            description="Nạp ví #888002",
        )
        db.session.add(tx)
        db.session.commit()

        # Bank transfers often add bank prefixes / suffixes
        noisy_memo = "MBVCB.9876543210.PPTQU042TX99.CHUYEN TIEN HOC PHI PPTQ"
        webhook_data = {
            "orderCode": 99999999,  # Even if bank sends arbitrary or unlinked orderCode
            "amount": 50000,
            "description": noisy_memo,
            "accountNumber": "0908667141",
            "reference": "FT554433",
            "code": "00",
            "desc": "success",
            "counterAccountBankId": None,
            "counterAccountBankName": None,
            "counterAccountName": None,
            "counterAccountNumber": None,
            "virtualAccountName": None,
            "virtualAccountNumber": None,
        }
        sig = create_signature(webhook_data, PAYOS_CHECKSUM_KEY)
        payload = {"data": webhook_data, "signature": sig}

        res = handle_payos_webhook(payload, session=db.session)
        assert res["success"] is True
        assert res["balance"] == 50000

        db.session.refresh(tx)
        assert tx.status == "COMPLETED"


def test_handle_payos_webhook_underpayment_protection(app):
    """Verify underpayment safety: if user transfers less than order amount, credit only received amount."""
    with app.app_context():
        user = User(
            email="test_underpay_user@backend.local",
            display_name="Underpay Student",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        tx = WalletTransaction(
            user_id=user.id,
            amount=500000,  # Expected 500k
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=777003,
            transfer_code_12="PPTQU003TX03",
            description="Nạp ví #777003",
        )
        db.session.add(tx)
        db.session.commit()

        # Attacker transfers only 20,000 VND
        webhook_data = {
            "orderCode": 777003,
            "amount": 20000,
            "description": "PPTQU003TX03",
            "accountNumber": "0908667141",
            "reference": "FT112233",
            "code": "00",
            "desc": "success",
            "counterAccountBankId": None,
            "counterAccountBankName": None,
            "counterAccountName": None,
            "counterAccountNumber": None,
            "virtualAccountName": None,
            "virtualAccountNumber": None,
        }
        sig = create_signature(webhook_data, PAYOS_CHECKSUM_KEY)
        payload = {"data": webhook_data, "signature": sig}

        res = handle_payos_webhook(payload, session=db.session)
        assert res["success"] is True
        assert res["amount"] == 20000  # Credited only 20,000!
        assert res["is_underpaid"] is True

        user_bal = get_or_create_balance(user.id, session=db.session)
        assert int(user_bal.balance) == 20000


def test_handle_payos_webhook_recovers_stale_failed_tx(app):
    """Verify that a transaction marked FAILED due to timeout is gracefully revived upon valid webhook."""
    with app.app_context():
        user = User(
            email="test_stale_revive@backend.local",
            display_name="Stale Revive Student",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        tx = WalletTransaction(
            user_id=user.id,
            amount=200000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="FAILED",  # Prematurely timed out
            order_code=777004,
            transfer_code_12="PPTQU004TX04",
            description="Nạp ví #777004",
        )
        db.session.add(tx)
        db.session.commit()

        webhook_data = {
            "orderCode": 777004,
            "amount": 200000,
            "description": "PPTQU004TX04",
            "accountNumber": "0908667141",
            "reference": "FT990011",
            "code": "00",
            "desc": "success",
            "counterAccountBankId": None,
            "counterAccountBankName": None,
            "counterAccountName": None,
            "counterAccountNumber": None,
            "virtualAccountName": None,
            "virtualAccountNumber": None,
        }
        sig = create_signature(webhook_data, PAYOS_CHECKSUM_KEY)
        payload = {"data": webhook_data, "signature": sig}

        res = handle_payos_webhook(payload, session=db.session)
        assert res["success"] is True
        assert res["balance"] == 200000

        db.session.refresh(tx)
        assert tx.status == "COMPLETED"


def test_check_transaction_status_active_payos_sync(client, app):
    """Verify polling /api/payments/check-status/<id> actively syncs with PayOS API and credits wallet."""
    with app.app_context():
        user = User(
            email="test_active_sync@backend.local",
            display_name="Active Sync Student",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        tx = WalletTransaction(
            user_id=user.id,
            amount=150000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=777005,
            transfer_code_12="PPTQU005TX05",
            description="Nạp ví #777005",
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id
        user_id = user.id

        tokens = create_token_pair(user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Mock fetch_payos_payment_link_info returning PAID
    mock_payos_info = {
        "orderCode": 777005,
        "amount": 150000,
        "amountPaid": 150000,
        "status": "PAID",
        "description": "PPTQU005TX05",
    }

    with patch("backend.blueprints.api_payments.routes.fetch_payos_payment_link_info", return_value=mock_payos_info):
        resp = client.get(f"/api/payments/check-status/{tx_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["status"] == "COMPLETED"
        assert data["balance"] == 150000

    # Verify database was committed
    with app.app_context():
        reloaded_tx = db.session.query(WalletTransaction).filter(WalletTransaction.id == tx_id).first()
        assert reloaded_tx.status == "COMPLETED"
        user_bal = get_or_create_balance(user_id, session=db.session)
        assert int(user_bal.balance) == 150000


def test_payos_qr_base64_data_uri_and_fail_safe_output():
    """Verify create_payos_payment_link produces fail-safe Base64 data URI as primary qr_code."""
    from backend.services.payos_service import create_payos_payment_link

    res = create_payos_payment_link(
        order_code=888999,
        amount=50000,
        description="PPTQU001TX99",
        return_url="http://localhost:5000/#/student/wallet",
        cancel_url="http://localhost:5000/#/student/wallet",
    )

    assert res["success"] is True
    assert res["order_code"] == 888999
    assert res["amount"] == 50000
    assert "qr_code" in res
    assert "qr_data_uri" in res
    assert "qr_raw" in res
    assert "vietqr_url" in res

    # Primary qr_code must be the local data URI if generated, or vietqr_url
    if res.get("qr_data_uri"):
        assert res["qr_data_uri"].startswith("data:image/png;base64,")
        assert res["qr_code"].startswith("data:image/png;base64,")
    assert res["vietqr_url"].startswith("https://img.vietqr.io/image/")


def test_payos_webhook_listening_endpoints(client):
    """Verify PayOS webhook endpoint responds to GET, HEAD, and test pings."""
    get_resp = client.get("/api/payments/payos/webhook")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["success"] is True
    assert get_data["endpoint"] == "/api/payments/payos/webhook"

    head_resp = client.head("/api/payments/payos/webhook")
    assert head_resp.status_code == 200
