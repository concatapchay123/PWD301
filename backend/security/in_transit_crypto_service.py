"""Hybrid In-Transit Encryption Service for PWD301 LMS.

Implements two-tier in-transit cryptographic protection:
1. Client generates ephemeral AES-GCM 256 key and encrypts request payload.
2. Ephemeral AES key is encrypted using Server's RSA-OAEP 2048 public key (SHA-256).
3. Payload is packaged with explicit "prefix": "PPTQ LMS" and 60-second anti-replay timestamp verification.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

logger = logging.getLogger(__name__)

PREFIX = "PPTQ LMS"
MAX_TIMESTAMP_DRIFT_MS = 60_000  # 60 seconds anti-replay tolerance

_lock = threading.Lock()
_private_key: rsa.RSAPrivateKey | None = None
_public_key_pem: str | None = None


def _get_key_path() -> str:
    key_dir = os.environ.get("FILE_STORAGE_ROOT", "storage")
    os.makedirs(key_dir, exist_ok=True)
    return os.path.join(key_dir, "server_rsa_security_key.pem")


def _ensure_rsa_keys() -> tuple[rsa.RSAPrivateKey, str]:
    """Generate or retrieve persistent server RSA 2048 keypair across multi-process workers."""
    global _private_key, _public_key_pem
    if _private_key is not None and _public_key_pem is not None:
        return _private_key, _public_key_pem

    with _lock:
        if _private_key is not None and _public_key_pem is not None:
            return _private_key, _public_key_pem

        key_path = _get_key_path()
        if os.path.exists(key_path):
            try:
                with open(key_path, "rb") as f:
                    _private_key = serialization.load_pem_private_key(f.read(), password=None)
                pub_key = _private_key.public_key()
                _public_key_pem = pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8")
                return _private_key, _public_key_pem
            except Exception as exc:
                logger.warning("[Crypto] Failed reading existing key file, regenerating: %s", exc)

        # Generate RSA 2048 keypair
        _private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        pub_key = _private_key.public_key()
        _public_key_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        # Persist private key to disk atomically
        try:
            priv_pem = _private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            temp_path = f"{key_path}.tmp.{os.getpid()}"
            with open(temp_path, "wb") as f:
                f.write(priv_pem)
            os.replace(temp_path, key_path)
            logger.info("[Crypto] Persistent server RSA key saved to %s", key_path)
        except Exception as exc:
            logger.warning("[Crypto] Could not save RSA key to disk: %s", exc)

        logger.info("[Crypto] Server RSA-OAEP 2048 keypair initialized successfully.")
        return _private_key, _public_key_pem


def get_server_rsa_public_key_pem() -> str:
    """Return the Server's RSA Public Key in SPKI PEM format."""
    _, pub_pem = _ensure_rsa_keys()
    return pub_pem


def decrypt_hybrid_payload(envelope: dict[str, Any]) -> dict[str, Any]:
    """Decrypt a hybrid encrypted request payload envelope.

    Expected envelope format:
    {
        "prefix": "PPTQ LMS",
        "key": "<base64 RSA-encrypted AES key>",
        "iv": "<base64 12-byte IV>",
        "ciphertext": "<base64 AES-GCM ciphertext + 16-byte tag>",
        "timestamp": 1730000000000
    }

    Raises:
        ValueError: If prefix is invalid, timestamp has drifted, or decryption fails.
    """
    if not isinstance(envelope, dict):
        raise ValueError("Invalid encrypted envelope: must be a dictionary.")

    prefix = envelope.get("prefix")
    if prefix != PREFIX:
        raise ValueError(f"Invalid envelope prefix. Expected '{PREFIX}', got '{prefix}'.")

    # Anti-replay timestamp verification (60 seconds)
    timestamp = envelope.get("timestamp")
    if timestamp is not None:
        try:
            ts_int = int(timestamp)
            now_ms = int(time.time() * 1000)
            drift = abs(now_ms - ts_int)
            if drift > MAX_TIMESTAMP_DRIFT_MS:
                logger.warning(
                    "[Crypto] Anti-replay timestamp drift exceeded: %d ms (limit: %d ms)",
                    drift,
                    MAX_TIMESTAMP_DRIFT_MS,
                )
                raise ValueError("Yêu cầu đã hết hạn bảo mật (Anti-replay timestamp expired). Vui lòng thử lại.")
        except (ValueError, TypeError) as exc:
            if "Anti-replay" in str(exc):
                raise
            # If timestamp parsing fails, raise error
            raise ValueError("Chữ ký thời gian bảo mật không hợp lệ.") from exc

    priv_key, _ = _ensure_rsa_keys()

    # 1. Decrypt ephemeral AES key using RSA-OAEP (SHA-256)
    try:
        enc_aes_key = base64.b64decode(envelope["key"])
        aes_key = priv_key.decrypt(
            enc_aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        logger.error("[Crypto] Failed to decrypt ephemeral AES key with RSA-OAEP: %s", exc)
        raise ValueError("Không thể giải mã khóa phiên AES bảo mật.") from exc

    # 2. Decrypt ciphertext using AES-GCM 256
    try:
        iv = base64.b64decode(envelope["iv"])
        raw_ct_tag = base64.b64decode(envelope["ciphertext"])
        if len(raw_ct_tag) < 16:
            raise ValueError("Ciphertext too short.")

        raw_ct = raw_ct_tag[:-16]
        raw_tag = raw_ct_tag[-16:]

        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, raw_tag))
        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(raw_ct) + decryptor.finalize()

        payload_dict = json.loads(decrypted_bytes.decode("utf-8"))
        if not isinstance(payload_dict, dict):
            raise ValueError("Decrypted payload is not a JSON dictionary.")
        return payload_dict
    except Exception as exc:
        logger.error("[Crypto] Failed to decrypt AES-GCM payload: %s", exc)
        raise ValueError("Không thể giải mã dữ liệu yêu cầu bảo mật.") from exc
