"""PayOS payment gateway integration service for PWD301.

Provides:
- Creation of PayOS payment links with strict 12-char transfer description.
- HMAC-SHA256 signature generation and verification.
- Webhook signature validation.
- Support for online PayOS API with graceful offline/sandbox simulation fallback.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

# PayOS credentials configured for PPTQ (Injected securely via environment variables)
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID", "")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY", "")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY", "")
PAYOS_API_ENDPOINT = "https://api-merchant.payos.vn/v2/payment-requests"

# Authentic merchant bank account credentials for PPTQ deposits (Injected securely via environment variables)
PPTQ_BANK_NAME = os.getenv("PPTQ_BANK_NAME", "MBBank (MBB - Ngân hàng TMCP Quân đội)")
PPTQ_BANK_BIN = os.getenv("PPTQ_BANK_BIN", "970422")
PPTQ_ACCOUNT_NUMBER = os.getenv("PPTQ_ACCOUNT_NUMBER", "")
PPTQ_ACCOUNT_NAME = os.getenv("PPTQ_ACCOUNT_NAME", "")


def generate_12char_transfer_code(user_id: int | str, tx_seed: str | None = None) -> str:
    """Generate exact 12-character transfer description.

    Format: 'PPTQ' (4 chars) + User Code (4 chars) + Tx Code (4 chars)
    Total length: exactly 12 characters (alphanumeric uppercase).
    Example: 'PPTQU042A9B1'
    """
    prefix = "PPTQ"
    try:
        uid_int = int(user_id)
        u_code = f"U{uid_int % 1000:03d}"
    except (ValueError, TypeError):
        u_str = str(user_id).replace("-", "").upper()
        u_code = f"U{u_str[:3]}" if len(u_str) >= 3 else f"U{u_str.ljust(3, '0')}"

    if tx_seed and len(tx_seed) >= 4:
        tx_code = tx_seed[:4].upper()
    else:
        tx_code = secrets.token_hex(2).upper()  # 4 hex chars

    code = f"{prefix}{u_code[:4]}{tx_code[:4]}"
    return code[:12]


def create_signature(data_dict: dict[str, Any], checksum_key: str = PAYOS_CHECKSUM_KEY) -> str:
    """Calculate PayOS HMAC-SHA256 signature from sorted payload key-values."""
    sorted_keys = sorted(data_dict.keys())
    parts = []
    for k in sorted_keys:
        val = data_dict[k]
        if val is not None and not isinstance(val, (dict, list)):
            parts.append(f"{k}={val}")
    sign_data = "&".join(parts)
    return hmac.new(
        checksum_key.encode("utf-8"),
        sign_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_webhook_signature(
    webhook_payload: dict[str, Any], checksum_key: str = PAYOS_CHECKSUM_KEY
) -> bool:
    """Verify HMAC-SHA256 signature of PayOS webhook data payload."""
    if not isinstance(webhook_payload, dict):
        return False
    signature = webhook_payload.get("signature")
    data = webhook_payload.get("data")
    if not signature or not isinstance(data, dict):
        return False

    # Sort keys inside data dictionary
    sorted_keys = sorted(data.keys())
    parts = []
    for k in sorted_keys:
        val = data[k]
        if val is not None and not isinstance(val, (dict, list)):
            parts.append(f"{k}={val}")
    sign_data = "&".join(parts)
    expected = hmac.new(
        checksum_key.encode("utf-8"),
        sign_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature.lower(), expected.lower())


def create_payos_payment_link(
    order_code: int,
    amount: int,
    description: str,
    return_url: str,
    cancel_url: str,
    items: list[dict[str, Any]] | None = None,
    client_id: str = PAYOS_CLIENT_ID,
    api_key: str = PAYOS_API_KEY,
    checksum_key: str = PAYOS_CHECKSUM_KEY,
) -> dict[str, Any]:
    """Create a payment request on PayOS or return simulated payment metadata."""
    clean_desc = description[:12].strip()

    sign_payload = {
        "amount": amount,
        "cancelUrl": cancel_url,
        "description": clean_desc,
        "orderCode": order_code,
        "returnUrl": return_url,
    }
    signature = create_signature(sign_payload, checksum_key)

    request_body = {
        **sign_payload,
        "items": items or [{"name": f"Học phí PPTQ #{order_code}", "quantity": 1, "price": amount}],
        "signature": signature,
    }

    # Attempt online call to PayOS API
    try:
        req = urllib.request.Request(
            PAYOS_API_ENDPOINT,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-client-id": client_id,
                "x-api-key": api_key,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            if resp_data.get("code") in ("00", 0, "0"):
                data = resp_data.get("data", {})
                raw_qr = data.get("qrCode") or ""
                ret_bin = data.get("bin") or PPTQ_BANK_BIN
                ret_acc = data.get("accountNumber") or PPTQ_ACCOUNT_NUMBER
                ret_name = data.get("accountName") or PPTQ_ACCOUNT_NAME
                encoded_name = urllib.parse.quote(ret_name)

                # Convert raw EMVCo payload (000201...) to a loadable VietQR image URL
                if raw_qr.startswith("000201") or not (raw_qr.startswith("http://") or raw_qr.startswith("https://")):
                    qr_image_url = (
                        f"https://img.vietqr.io/image/{ret_bin}-{ret_acc}-compact2.png"
                        f"?amount={amount}&addInfo={clean_desc}&accountName={encoded_name}"
                    )
                else:
                    qr_image_url = raw_qr

                return {
                    "success": True,
                    "order_code": order_code,
                    "amount": amount,
                    "description": clean_desc,
                    "checkout_url": data.get("checkoutUrl"),
                    "qr_code": qr_image_url,
                    "qr_raw": raw_qr,
                    "payment_link_id": data.get("paymentLinkId"),
                    "bank_name": data.get("bankName", PPTQ_BANK_NAME),
                    "account_name": ret_name,
                    "account_number": ret_acc,
                    "bin": ret_bin,
                }
            logger.warning("PayOS API returned code %s: %s", resp_data.get("code"), resp_data.get("desc"))
    except Exception as exc:
        logger.info("PayOS API call failed or offline mode (%s). Providing robust sandbox metadata.", exc)

    # Sandbox / Local Simulation Fallback with authentic VietQR generator link
    simulated_payment_id = f"PAYOS-{order_code}-{secrets.token_hex(4)}"
    simulated_checkout_url = f"{return_url}?orderCode={order_code}&status=PAID"
    encoded_account_name = urllib.parse.quote(PPTQ_ACCOUNT_NAME)
    vietqr_url = (
        f"https://img.vietqr.io/image/{PPTQ_BANK_BIN}-{PPTQ_ACCOUNT_NUMBER}-compact2.png"
        f"?amount={amount}&addInfo={clean_desc}&accountName={encoded_account_name}"
    )

    return {
        "success": True,
        "order_code": order_code,
        "amount": amount,
        "description": clean_desc,
        "checkout_url": simulated_checkout_url,
        "qr_code": vietqr_url,
        "payment_link_id": simulated_payment_id,
        "bank_name": PPTQ_BANK_NAME,
        "account_name": PPTQ_ACCOUNT_NAME,
        "account_number": PPTQ_ACCOUNT_NUMBER,
        "bin": PPTQ_BANK_BIN,
        "is_simulated": True,
    }
