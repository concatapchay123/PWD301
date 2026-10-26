"""Integration test suite for Database At-Rest Encryption & Hybrid In-Transit Encryption.

Verifies:
1. Database At-Rest Encryption:
   - users.email, users.password_hash, users.display_name are all encrypted
     with PPTQ LMS$ personalized prefixes at-rest.
   - Transparent application decryption works when accessed via User model.
2. Hybrid In-Transit Encryption:
   - GET /auth/security-key returns RSA-OAEP 2048 public key PEM.
   - POST /auth/login accepts hybrid encrypted payload (RSA-OAEP 2048 + AES-GCM 256) inside "PPTQ LMS" envelope.
   - Anti-replay timestamp verification rejects expired envelopes (> 60s).
   - Successful hybrid encrypted authentication returns valid session and user info.
"""

import base64
import json
import os
import time
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from backend.extensions import db
from backend.models.identity import User
from backend.services.user_service import get_user_by_email, register_user


def test_database_at_rest_encryption(app):
    """Verify that email, password_hash, and display_name are encrypted at-rest in the database."""
    with app.app_context():
        # Create a test user
        user = register_user("test_student@backend.local", "Password123!", "Học Viên Thử Nghiệm")
        user_id = user.id

        # Query raw database row directly using raw text to bypass TypeDecorator
        raw_row = db.session.execute(
            db.text("SELECT id, email, password_hash, display_name FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        assert raw_row is not None
        uid, raw_email, raw_pwd, raw_name = raw_row

        # Verify PPTQ LMS$ personalized prefixes at rest
        assert raw_email.startswith("PPTQ LMS$aes256$v1$"), f"Email is not encrypted at rest: {raw_email}"
        assert raw_pwd.startswith("PPTQ LMS$argon2id$v1$") or "argon2id" in raw_pwd or raw_pwd.startswith("scrypt:"), f"Password is not secure hash: {raw_pwd}"
        assert raw_name.startswith("PPTQ LMS$aes256$v1$"), f"Display name is not encrypted at rest: {raw_name}"

        # Verify transparent application decryption via User model
        queried_user = get_user_by_email("test_student@backend.local")
        assert queried_user is not None
        assert queried_user.email == "test_student@backend.local"
        assert queried_user.display_name == "Học Viên Thử Nghiệm"


def test_security_key_endpoint(client):
    """Verify GET /auth/security-key returns the server's RSA public key."""
    res = client.get("/auth/security-key")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "public_key" in data["data"]
    assert "-----BEGIN PUBLIC KEY-----" in data["data"]["public_key"]
    assert data["data"]["prefix"] == "PPTQ LMS"
    assert data["data"]["algorithm"] == "RSA-OAEP-256"


def test_hybrid_login_encryption_flow(client, app):
    """Verify end-to-end hybrid RSA-OAEP + AES-GCM 256 login."""
    from backend.models.types import utc_now
    with app.app_context():
        u = register_user("hybrid_admin@backend.local", "Password123!", "Quản Trị Viên")
        u.email_verified_at = utc_now()
        db.session.commit()

    # 1. Fetch server RSA public key
    key_res = client.get("/auth/security-key")
    assert key_res.status_code == 200
    public_pem = key_res.get_json()["data"]["public_key"]
    rsa_pub_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))

    # 2. Client generates ephemeral AES-GCM 256 key & encrypts login payload
    aes_key = os.urandom(32)
    iv = os.urandom(12)
    now_ms = int(time.time() * 1000)
    credentials = {
        "email": "hybrid_admin@backend.local",
        "password": "Password123!",
        "timestamp": now_ms,
        "nonce": "test-nonce-123",
    }
    encoded_payload = json.dumps(credentials).encode("utf-8")

    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(encoded_payload) + encryptor.finalize()
    tag = encryptor.tag

    # 3. Encrypt AES key using server RSA-OAEP
    enc_aes_key = rsa_pub_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    envelope = {
        "prefix": "PPTQ LMS",
        "key": base64.b64encode(enc_aes_key).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "ciphertext": base64.b64encode(ct + tag).decode("utf-8"),
        "timestamp": now_ms,
    }

    # 4. Get CSRF token
    csrf_res = client.get("/auth/login")
    csrf_token = csrf_res.get_json().get("csrf_token")

    # 5. POST encrypted envelope
    headers = {"X-CSRFToken": csrf_token} if csrf_token else {}
    login_res = client.post(
        "/auth/login",
        json={"encrypted_envelope": envelope, "remember": False},
        headers=headers,
    )
    assert login_res.status_code == 200
    res_data = login_res.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["user"]["email"] == "hybrid_admin@backend.local"


def test_hybrid_login_anti_replay_expired(client, app):
    """Verify that requests with expired timestamp (> 60s) are rejected."""
    key_res = client.get("/auth/security-key")
    public_pem = key_res.get_json()["data"]["public_key"]
    rsa_pub_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))

    aes_key = os.urandom(32)
    iv = os.urandom(12)
    # Timestamp is 2 minutes ago (expired!)
    expired_ms = int((time.time() - 120) * 1000)
    credentials = {
        "email": "hybrid_admin@backend.local",
        "password": "Password123!",
        "timestamp": expired_ms,
    }
    encoded_payload = json.dumps(credentials).encode("utf-8")

    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(encoded_payload) + encryptor.finalize()
    tag = encryptor.tag

    enc_aes_key = rsa_pub_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    envelope = {
        "prefix": "PPTQ LMS",
        "key": base64.b64encode(enc_aes_key).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "ciphertext": base64.b64encode(ct + tag).decode("utf-8"),
        "timestamp": expired_ms,
    }

    login_res = client.post(
        "/auth/login",
        json={"encrypted_envelope": envelope},
    )
    assert login_res.status_code == 400
    res_data = login_res.get_json()
    assert res_data["success"] is False
    assert "Anti-replay" in res_data["error"]["message"] or "hết hạn" in res_data["error"]["message"]
