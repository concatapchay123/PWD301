import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from pwd301.services import video_drm_service as drm


def test_concurrent_hls_requests_publish_one_complete_generation(tmp_path, monkeypatch):
    calls = []

    def generate(command, **kwargs):
        calls.append(command)
        time.sleep(0.05)
        directory = Path(command[-1]).parent
        (directory / "segment_000.ts").write_bytes(b"fixture-encrypted-segment")
        Path(command[-1]).write_text(
            '#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key"\n#EXTINF:1,\nsegment_000.ts\n#EXT-X-ENDLIST\n'
        )

    monkeypatch.setattr(drm.subprocess, "run", generate)
    output = tmp_path / "hls"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(drm.transcode_to_encrypted_hls, "input.mp4", str(output)) for _ in range(2)
        ]
        results = [future.result() for future in futures]
    assert results[0] == results[1]
    assert len(calls) == 1
    assert (output / "enc.key").stat().st_size == 16


def test_failed_generation_never_publishes_key_or_playlist(tmp_path, monkeypatch):
    def expired(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 90)

    monkeypatch.setattr(drm.subprocess, "run", expired)
    with pytest.raises(drm.VideoDRMTranscodeError):
        drm.transcode_to_encrypted_hls("input.mp4", str(tmp_path / "hls"))
    assert not (tmp_path / "hls" / "enc.key").exists()
    assert not (tmp_path / "hls" / "playlist.m3u8").exists()
