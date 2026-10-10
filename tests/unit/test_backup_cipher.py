"""Streaming backup encryption must authenticate every byte before publication."""

import base64
import os

import pytest

from pwd301.services.backup_cipher import decrypt_backup, encrypt_backup


def test_streaming_backup_round_trip(tmp_path):
    source = tmp_path / "source.bak"
    source.write_bytes(os.urandom(200000))
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    encrypted = tmp_path / "backup.encrypted"
    restored = tmp_path / "restored.bak"
    encrypt_backup(source, encrypted, key)
    decrypt_backup(encrypted, restored, key)
    assert restored.read_bytes() == source.read_bytes()
    assert source.read_bytes()[:32] not in encrypted.read_bytes()


def test_tampered_backup_never_publishes_plaintext(tmp_path):
    source = tmp_path / "source.bak"
    source.write_bytes(b"database backup")
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    encrypted = tmp_path / "backup.encrypted"
    encrypt_backup(source, encrypted, key)
    damaged = bytearray(encrypted.read_bytes())
    damaged[-1] ^= 1
    encrypted.write_bytes(damaged)
    restored = tmp_path / "restored.bak"
    with pytest.raises(ValueError):
        decrypt_backup(encrypted, restored, key)
    assert not restored.exists()


def test_existing_backup_destination_is_never_overwritten(tmp_path):
    source = tmp_path / "source.bak"
    source.write_bytes(b"database backup")
    destination = tmp_path / "existing.encrypted"
    destination.write_bytes(b"existing recovery copy")
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    with pytest.raises((ValueError, FileExistsError)):
        encrypt_backup(source, destination, key)
    assert destination.read_bytes() == b"existing recovery copy"
