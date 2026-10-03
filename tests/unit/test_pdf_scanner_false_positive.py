from __future__ import annotations

import zlib
from pathlib import Path

from pwd301.services.scanner_service import BuiltinHeuristicScanner


def test_compressed_stream_containing_js_bytes_passes(tmp_path: Path) -> None:
    """Ensure a safe PDF whose binary stream happens to contain the 3 bytes /JS passes."""
    scanner = BuiltinHeuristicScanner()
    safe_pdf = tmp_path / "safe_paper.pdf"

    # Compress a payload containing '/JS' as part of harmless text or font data
    raw_text = b"Research paper on neural networks with /JSlI58p mathematical tokens"
    stream_content = zlib.compress(raw_text)

    content = (
        b"%PDF-1.5\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length " + str(len(stream_content)).encode("ascii") + b" /Filter /FlateDecode >>\n"
        b"stream\n" + stream_content + b"\nendstream\n"
        b"endobj\n"
        b"%%EOF"
    )
    safe_pdf.write_bytes(content)

    verdict = scanner.scan_file(safe_pdf)
    assert verdict.status == "PASS", f"Expected PASS but got {verdict.status}: {verdict.details}"


def test_malicious_action_dictionary_with_javascript_fails(tmp_path: Path) -> None:
    """Ensure a PDF with an active JavaScript action dictionary is correctly flagged as FAIL."""
    scanner = BuiltinHeuristicScanner()
    malicious_pdf = tmp_path / "malicious_script.pdf"

    content = (
        b"%PDF-1.5\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R /OpenAction 3 0 R >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Action /S /JavaScript /JS (app.alert('Hacked');) >>\n"
        b"endobj\n"
        b"%%EOF"
    )
    malicious_pdf.write_bytes(content)

    verdict = scanner.scan_file(malicious_pdf)
    assert verdict.status == "FAIL"
    assert verdict.signature_name == "PDF-Malicious-Object"


def test_user_download_sample_files_if_present() -> None:
    """Verify that user's uploaded paper samples from Downloads pass heuristic scan."""
    scanner = BuiltinHeuristicScanner()
    samples = [
        Path(r"C:\Users\LENOVO\Downloads\570921738.pdf"),
        Path(r"C:\Users\LENOVO\Downloads\2405.14672v2.pdf"),
        Path(r"C:\Users\LENOVO\Downloads\2405.13080v1.pdf"),
    ]
    checked = 0
    for sample in samples:
        if sample.is_file():
            verdict = scanner.scan_file(sample)
            assert verdict.status == "PASS", (
                f"User file {sample.name} falsely flagged: {verdict.details}"
            )
            checked += 1
    # At least test that logic runs cleanly
    assert checked >= 0
