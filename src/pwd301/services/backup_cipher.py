"""Streaming authenticated backup encryption; never release unverified plaintext."""

from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAGIC = b"PWD301BK1"
CHUNK = 1024 * 1024


def _key(value: str) -> bytes:
    try:
        decoded = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeError):
        raise ValueError("Backup encryption requires a base64-encoded 32-byte key.") from None
    if len(decoded) != 32:
        raise ValueError("Backup encryption requires a base64-encoded 32-byte key.")
    return decoded


def encrypt_backup(source: Path, destination: Path, key: str) -> None:
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(_key(key)), modes.GCM(nonce)).encryptor()
    cipher.authenticate_additional_data(MAGIC)
    temporary = destination.with_suffix(destination.suffix + "." + uuid.uuid4().hex + ".tmp")
    try:
        with source.open("rb") as incoming, temporary.open("xb") as outgoing:
            os.chmod(temporary, 0o600)
            outgoing.write(MAGIC + nonce)
            while chunk := incoming.read(CHUNK):
                outgoing.write(cipher.update(chunk))
            outgoing.write(cipher.finalize())
            outgoing.write(cipher.tag)
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def decrypt_backup(source: Path, destination: Path, key: str) -> None:
    size = source.stat().st_size
    header_size = len(MAGIC) + 12
    if size < header_size + 16 or destination.exists():
        raise ValueError("Invalid encrypted backup or destination already exists.")
    temporary = destination.with_suffix(destination.suffix + "." + uuid.uuid4().hex + ".tmp")
    try:
        with source.open("rb") as incoming:
            if incoming.read(len(MAGIC)) != MAGIC:
                raise ValueError("Unrecognized backup format.")
            nonce = incoming.read(12)
            incoming.seek(-16, 2)
            tag = incoming.read(16)
            incoming.seek(header_size)
            cipher = Cipher(algorithms.AES(_key(key)), modes.GCM(nonce, tag)).decryptor()
            cipher.authenticate_additional_data(MAGIC)
            remaining = size - header_size - 16
            with temporary.open("xb") as outgoing:
                os.chmod(temporary, 0o600)
                while remaining:
                    chunk = incoming.read(min(CHUNK, remaining))
                    if not chunk:
                        raise ValueError("Truncated encrypted backup.")
                    remaining -= len(chunk)
                    outgoing.write(cipher.update(chunk))
                outgoing.write(cipher.finalize())
        os.link(temporary, destination)
    except InvalidTag:
        raise ValueError("Backup authentication failed.") from None
    finally:
        temporary.unlink(missing_ok=True)
