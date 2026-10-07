"""Unit tests for Video DRM Service, AES-128 HLS Transcoding & Tokenized Key Exchange (TASK-085)."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pwd301.services.video_drm_service import (
    generate_key_token,
    transcode_to_encrypted_hls,
    verify_key_token,
)


def test_generate_and_verify_key_token() -> None:
    secret = "test-super-secret-drm-key"
    student_id = 42
    course_id = 101
    lesson_id = 999

    # 1. Valid token
    token = generate_key_token(student_id, course_id, lesson_id, secret, expires_in=10)
    assert token is not None
    assert isinstance(token, str)

    valid, reason = verify_key_token(token, student_id, course_id, lesson_id, secret)
    assert valid is True
    assert reason == "OK"

    # 2. Token for different lesson must fail
    valid_diff, reason_diff = verify_key_token(token, student_id, course_id, 888, secret)
    assert valid_diff is False
    assert "mismatch" in reason_diff.lower()

    # 3. Token for different student must fail
    valid_user, reason_user = verify_key_token(token, 99, course_id, lesson_id, secret)
    assert valid_user is False
    assert "mismatch" in reason_user.lower()

    # 4. Tampered token must fail
    tampered = token[:-4] + "abcd"
    valid_tamp, reason_tamp = verify_key_token(tampered, student_id, course_id, lesson_id, secret)
    assert valid_tamp is False
    assert any(w in reason_tamp.lower() for w in ("tampered", "signature", "decode", "invalid"))

    # 5. Expired token must fail
    expired_token = generate_key_token(student_id, course_id, lesson_id, secret, expires_in=-5)
    valid_exp, reason_exp = verify_key_token(
        expired_token, student_id, course_id, lesson_id, secret
    )
    assert valid_exp is False
    assert "expired" in reason_exp.lower()


def test_transcode_to_encrypted_hls() -> None:
    temp_dir = tempfile.mkdtemp(prefix="pwd301_drm_test_")
    try:
        input_mp4 = os.path.join(temp_dir, "input.mp4")
        output_dir = os.path.join(temp_dir, "hls_out")

        # Generate 1s test mp4 via ffmpeg
        gen_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x240:rate=1",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            input_mp4,
        ]
        subprocess.run(gen_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert os.path.exists(input_mp4)

        # Transcode to AES-128 HLS
        playlist_path = transcode_to_encrypted_hls(
            input_path=input_mp4,
            output_dir=output_dir,
            key_uri_relative="key",
            segment_duration_seconds=1,
        )

        assert os.path.exists(playlist_path)
        playlist_content = Path(playlist_path).read_text(encoding="utf-8")

        # Must enforce AES-128 in manifest
        assert "#EXT-X-KEY:METHOD=AES-128" in playlist_content
        assert 'URI="key"' in playlist_content

        # Must have generated enc.key file (16 bytes)
        key_file = os.path.join(output_dir, "enc.key")
        assert os.path.exists(key_file)
        assert os.path.getsize(key_file) == 16

        # Must have at least one segment file
        segments = [f for f in os.listdir(output_dir) if f.endswith(".ts")]
        assert len(segments) >= 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
