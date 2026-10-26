"""Database Field-Level Encryption (FLE) service for PWD301.

Enforces cryptographic security at-rest for sensitive user fields (email, display_name)
stored in Microsoft SQL Server 2022.

Format specification:
    PPTQ LMS$aes256$v1$<iv_base64>$<ciphertext_base64>

This mirrors the personalized Argon2id password hash format:
    PPTQ LMS$argon2id$v1$<salt_base64>$<hash_base64>

Key derivation:
- System secret pepper is combined with purpose-specific salt to derive 256-bit AES keys.
- Deterministic HMAC-SHA256 IV derivation is used for email to ensure O(1) indexed lookups
  and preservation of the unique constraint on email_normalized.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator

PPTQ_FIELD_ENCRYPTION_PREFIX = "PPTQ LMS$aes256$v1$"
DEFAULT_SYSTEM_PEPPER = "PPTQ_LMS_PEPPER_2026_SECURE"


def _get_encryption_key() -> bytes:
    """Derive 32-byte AES-256 key from system pepper."""
    pepper = os.environ.get("PPTQ_DB_ENCRYPTION_KEY", os.environ.get("PPTQ_PASSWORD_PEPPER", DEFAULT_SYSTEM_PEPPER))
    return hashlib.sha256(b"PPTQ_LMS_DB_FIELD_KEY_2026_" + pepper.encode("utf-8")).digest()


def encrypt_field(plaintext: str | None, field_type: str = "general") -> str | None:
    """Encrypt a plaintext string using AES-256-CBC with PKCS7 padding.

    Produces standardized format:
        PPTQ LMS$aes256$v1$<iv_base64>$<ciphertext_base64>

    If value is already encrypted (starts with 'PPTQ LMS$'), returns as-is.
    """
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    if plaintext.startswith(PPTQ_FIELD_ENCRYPTION_PREFIX):
        return plaintext

    key = _get_encryption_key()
    pt_bytes = plaintext.encode("utf-8")

    # Use deterministic IV derived via HMAC-SHA256 for searchable/reproducible fields
    if field_type == "email":
        norm_pt = plaintext.strip().lower().encode("utf-8")
        iv = hmac.new(key, b"email:" + norm_pt, hashlib.sha256).digest()[:16]
    elif field_type == "name":
        norm_pt = plaintext.strip().encode("utf-8")
        iv = hmac.new(key, b"name:" + norm_pt, hashlib.sha256).digest()[:16]
    else:
        iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(pt_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    iv_b64 = base64.b64encode(iv).decode("utf-8")
    ct_b64 = base64.b64encode(ciphertext).decode("utf-8")

    return f"{PPTQ_FIELD_ENCRYPTION_PREFIX}{iv_b64}${ct_b64}"


def decrypt_field(ciphertext: str | None) -> str | None:
    """Decrypt an encrypted string formatted as:
        PPTQ LMS$aes256$v1$<iv_base64>$<ciphertext_base64>

    If value does not start with PPTQ_FIELD_ENCRYPTION_PREFIX, returns as-is (legacy fallback).
    """
    if ciphertext is None:
        return None
    if not isinstance(ciphertext, str):
        return str(ciphertext)
    if not ciphertext.startswith(PPTQ_FIELD_ENCRYPTION_PREFIX):
        return ciphertext

    try:
        parts = ciphertext.split("$")
        if len(parts) != 5:
            return ciphertext

        iv = base64.b64decode(parts[3])
        ct = base64.b64decode(parts[4])

        key = _get_encryption_key()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ct) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return plaintext.decode("utf-8")
    except Exception:
        # If decryption fails for any reason, return the raw value to avoid hard crashes
        return ciphertext


class EncryptedUnicode(TypeDecorator):
    """SQLAlchemy TypeDecorator providing transparent field-level encryption for Unicode columns."""

    impl = sa.Unicode
    cache_ok = True

    def __init__(self, length: int | None = None, field_type: str = "general", **kwargs: Any) -> None:
        super().__init__(length, **kwargs)
        self.field_type = field_type

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return encrypt_field(value, field_type=self.field_type)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return decrypt_field(value)
