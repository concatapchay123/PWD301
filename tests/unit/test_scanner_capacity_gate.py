from pwd301.services.scanner_service import ClamAVScanner


def test_unscannable_size_never_becomes_clean(tmp_path):
    path = tmp_path / "beyond-capacity.txt"
    path.write_bytes(b"a" * 11)
    verdict = ClamAVScanner(max_stream_bytes=10).scan_file(path)
    assert verdict.status == "ERROR"
    assert "exceeds ClamAV stream limit" in verdict.details
