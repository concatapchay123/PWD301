"""Video DRM, AES-128 HLS Transcoding & Tokenized Key Exchange Engine for PWD301 (TASK-085).

Implements:
- FFmpeg automated HLS transcoding with AES-128 encryption.
- Short-lived HMAC tokenized key exchange for student sessions.
- Wall-clock forensic zero-trust streaming security.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import subprocess
import time
from pathlib import Path

from flask import current_app

from pwd301.services.exceptions import ServiceError

logger = logging.getLogger(__name__)


class VideoDRMError(ServiceError):
    """Base exception for video DRM and transcoding errors."""


class VideoDRMTranscodeError(VideoDRMError):
    """Raised when FFmpeg transcoding fails."""


class VideoDRMKeyAuthError(VideoDRMError):
    """Raised when a DRM key request fails verification."""


def _get_app_secret() -> str:
    """Retrieve app secret key for HMAC token signing."""
    try:
        secret = current_app.config.get("SECRET_KEY", "pwd301-default-drm-secret")
        return str(secret)
    except RuntimeError:
        return "pwd301-default-drm-secret"


def generate_key_token(
    student_user_id: int,
    course_id: int,
    lesson_id: int,
    secret_key: str | None = None,
    expires_in: int = 60,
) -> str:
    """Generate a short-lived HMAC-signed token for DRM key acquisition.

    Args:
        student_user_id: BigInt ID of enrolled student.
        course_id: BigInt ID of the course.
        lesson_id: BigInt ID of the lesson.
        secret_key: Optional override for signing key.
        expires_in: Validity window in seconds (default: 60s).

    Returns:
        URL-safe base64 string containing token components and signature.
    """
    secret = secret_key or _get_app_secret()
    exp_ts = int(time.time()) + expires_in
    data_str = f"{student_user_id}:{course_id}:{lesson_id}:{exp_ts}"
    sig = hmac.new(
        secret.encode("utf-8"),
        data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{data_str}:{sig}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def verify_key_token(
    token: str,
    student_user_id: int,
    course_id: int,
    lesson_id: int,
    secret_key: str | None = None,
) -> tuple[bool, str]:
    """Verify validity, expiration, and authorization of a DRM key token.

    Returns:
        (is_valid: bool, reason: str)
    """
    if not token or not isinstance(token, str):
        return False, "Token missing or invalid"

    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        parts = raw.split(":")
        if len(parts) != 5:
            return False, "Invalid token format"

        u_id_str, c_id_str, l_id_str, exp_str, sig = parts
        u_id = int(u_id_str)
        c_id = int(c_id_str)
        l_id = int(l_id_str)
        exp_ts = int(exp_str)
    except Exception:
        return False, "Failed to decode token"

    secret = secret_key or _get_app_secret()
    data_str = f"{u_id}:{c_id}:{l_id}:{exp_ts}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        return False, "Token signature tampered or invalid"

    curr_ts = int(time.time())
    if curr_ts > exp_ts:
        return False, "Token expired"

    if u_id != student_user_id:
        return False, "User mismatch"

    if c_id != course_id:
        return False, "Course mismatch"

    if l_id != lesson_id:
        return False, "Lesson mismatch"

    return True, "OK"


def transcode_to_encrypted_hls(
    input_path: str,
    output_dir: str,
    key_uri_relative: str = "key",
    segment_duration_seconds: int = 4,
) -> str:
    """Transcode source video to AES-128 encrypted HLS playlist and segments using FFmpeg.

    Args:
        input_path: Path to source MP4/WebM video.
        output_dir: Destination folder for .m3u8, enc.key, and .ts segments.
        key_uri_relative: Relative URI in playlist for key fetching (e.g. 'key').
        segment_duration_seconds: Duration of each chunk (default 4 seconds).

    Returns:
        Path to output 'playlist.m3u8'.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    key_file = out_path / "enc.key"
    keyinfo_file = out_path / "enc.keyinfo"
    playlist_file = out_path / "playlist.m3u8"

    # Generate or retain 16-byte random key
    if not key_file.exists() or key_file.stat().st_size != 16:
        aes_key = os.urandom(16)
        key_file.write_bytes(aes_key)

    # Generate random 16-byte initialization vector (IV) in hex
    iv_hex = secrets.token_hex(16)

    # Write FFmpeg keyinfo file:
    # Line 1: Key URI
    # Line 2: Path to key file
    # Line 3: IV in hex
    keyinfo_content = f"{key_uri_relative}\n{key_file.resolve()}\n{iv_hex}\n"
    keyinfo_file.write_text(keyinfo_content, encoding="utf-8")

    segment_pattern = str(out_path / "segment_%03d.ts")

    # Fast stream copy attempt first
    cmd_copy = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-hls_time",
        str(segment_duration_seconds),
        "-hls_playlist_type",
        "vod",
        "-hls_key_info_file",
        str(keyinfo_file.resolve()),
        "-hls_segment_filename",
        segment_pattern,
        str(playlist_file.resolve()),
    ]

    try:
        subprocess.run(cmd_copy, capture_output=True, text=True, check=True)
        logger.info(f"Successfully transcoded HLS (copy): {playlist_file}")
        return str(playlist_file)
    except subprocess.CalledProcessError:
        logger.warning("Stream copy failed; falling back to re-encoding libx264/aac...")

    # Re-encode fallback if stream copy failed
    cmd_encode = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-c:a",
        "aac",
        "-hls_time",
        str(segment_duration_seconds),
        "-hls_playlist_type",
        "vod",
        "-hls_key_info_file",
        str(keyinfo_file.resolve()),
        "-hls_segment_filename",
        segment_pattern,
        str(playlist_file.resolve()),
    ]

    try:
        subprocess.run(cmd_encode, capture_output=True, text=True, check=True)
        logger.info(f"Successfully transcoded HLS (re-encode): {playlist_file}")
        return str(playlist_file)
    except subprocess.CalledProcessError as err:
        logger.error(f"FFmpeg transcode error: {err.stderr}")
        raise VideoDRMTranscodeError(
            f"Failed to transcode video to encrypted HLS: {err.stderr}"
        ) from err


def get_lesson_hls_directory(course_id: int, lesson_id: int) -> Path:
    """Return canonical directory for a lesson's encrypted HLS files."""
    try:
        storage_base = Path(current_app.config.get("STORAGE_DIR", "storage"))
    except RuntimeError:
        storage_base = Path("storage")
    hls_dir = storage_base / "drm_hls" / f"course_{course_id}" / f"lesson_{lesson_id}"
    hls_dir.mkdir(parents=True, exist_ok=True)
    return hls_dir
