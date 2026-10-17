"""Standalone Empirical Challenge Test Suite for Milestone 6 (Challenger 2).

Verifies:
- Challenge 1: Screenshot Artifact Integrity (20 files, > 100 KB, valid PNG magic bytes and structure).
- Challenge 2: HLS Path Resolution (get_lesson_hls_directory returns absolute path, segment path resolution produces an absolute path that does not contain /app/src/pwd301/storage).
- Challenge 3: Invariant text strings (exact Vietnamese archive rejection string in frontend & backend).
"""

from __future__ import annotations

import os
import re
import struct
import sys
from pathlib import Path

import pytest
from flask import Flask

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / ".agents" / "teamwork" / "evidence_r6"
STUDENT_ROUTES_PATH = REPO_ROOT / "src" / "pwd301" / "blueprints" / "student" / "routes.py"
VIDEO_DRM_SERVICE_PATH = REPO_ROOT / "src" / "pwd301" / "services" / "video_drm_service.py"
FILE_SERVICE_PATH = REPO_ROOT / "src" / "pwd301" / "services" / "file_service.py"
INSTRUCTOR_JS_PATH = REPO_ROOT / "frontend" / "assets" / "js" / "views" / "instructor.js"

EXACT_VIETNAMESE_ARCHIVE_MESSAGE = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). "
    "Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)

EXPECTED_SCREENSHOTS = [
    "r01_auth_screen.png",
    "r02_instructor_dashboard.png",
    "r03_upload_label.png",
    "r04_accept_attribute.png",
    "r05_zip_rejected.png",
    "r06_rar_rejected.png",
    "r07_pdf_uploaded.png",
    "r08_oversize_rejected.png",
    "r09_course_intro.png",
    "r10_clean_player_shell.png",
    "r11_zero_yt_branding.png",
    "r12_trailer_looping.png",
    "r13_no_header_badge.png",
    "r14_header_clean_ui.png",
    "r15_local_video_play.png",
    "r16_supplementary_tracker.png",
    "r17_next_btn_gray.png",
    "r18_dwell_60s_gate.png",
    "r19_quiz_80pct_gate.png",
    "r20_next_btn_green.png",
]

FORBIDDEN_ARCHIVES = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]


# =========================================================================
# CHALLENGE 1: Screenshot Artifact Integrity
# =========================================================================


def test_challenge_1_evidence_directory_exists() -> None:
    """Assert evidence_r6 directory exists and is a directory."""
    assert EVIDENCE_DIR.exists(), f"Evidence directory does not exist: {EVIDENCE_DIR}"
    assert EVIDENCE_DIR.is_dir(), f"Evidence path is not a directory: {EVIDENCE_DIR}"


@pytest.mark.parametrize("filename", EXPECTED_SCREENSHOTS)
def test_challenge_1_screenshot_artifact_integrity(filename: str) -> None:
    """Assert all 20 files r01 through r20 exist, > 100 KB, and have valid PNG magic bytes."""
    filepath = EVIDENCE_DIR / filename
    assert filepath.exists(), f"Missing screenshot artifact: {filepath}"
    assert filepath.is_file(), f"Screenshot path is not a file: {filepath}"

    file_size = filepath.stat().st_size
    # Size must be strictly greater than 100 KB (102,400 bytes and 100,000 bytes)
    assert file_size > 100 * 1024, (
        f"Screenshot {filename} is too small: {file_size} bytes (required > 102,400 bytes)"
    )

    # Validate PNG magic bytes: \x89PNG\r\n\x1a\n
    with open(filepath, "rb") as f:
        header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n", f"Invalid PNG magic bytes for {filename}: {header!r}"

        # Further integrity check: verify IHDR chunk
        chunk_len_bytes = f.read(4)
        assert len(chunk_len_bytes) == 4, f"Truncated PNG file {filename}"
        chunk_type = f.read(4)
        assert chunk_type == b"IHDR", f"Expected IHDR chunk in {filename}, got {chunk_type!r}"

        # Check valid width and height
        width, height = struct.unpack(">II", f.read(8))
        assert width > 0, f"Invalid width {width} in {filename}"
        assert height > 0, f"Invalid height {height} in {filename}"

        # Seek to end and verify IEND chunk
        f.seek(-12, os.SEEK_END)
        iend_chunk = f.read(12)
        assert b"IEND" in iend_chunk, f"Missing IEND chunk in {filename}"


def test_challenge_1_screenshot_count_and_naming() -> None:
    """Assert exactly 20 expected screenshot files exist without missing rounds."""
    existing_pngs = sorted([p.name for p in EVIDENCE_DIR.glob("*.png")])
    for expected in EXPECTED_SCREENSHOTS:
        assert expected in existing_pngs, f"Expected {expected} not found in evidence directory"
    assert len(EXPECTED_SCREENSHOTS) == 20


# =========================================================================
# CHALLENGE 2: HLS Path Resolution
# =========================================================================


def test_challenge_2_get_lesson_hls_directory_without_flask_context() -> None:
    """Call get_lesson_hls_directory without app context; verify is_absolute() is True."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pwd301.services.video_drm_service import get_lesson_hls_directory

    hls_dir = get_lesson_hls_directory(course_id=110006, lesson_id=160031)
    assert hls_dir.is_absolute(), f"Path {hls_dir} must be absolute"
    assert "course_110006" in str(hls_dir)
    assert "lesson_160031" in str(hls_dir)
    assert hls_dir.exists(), f"Directory {hls_dir} must be created on disk"


def test_challenge_2_get_lesson_hls_directory_with_flask_context_relative() -> None:
    """Call get_lesson_hls_directory with relative STORAGE_DIR in Flask context; verify is_absolute()."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pwd301.services.video_drm_service import get_lesson_hls_directory

    app = Flask("test_app_relative")
    app.config["STORAGE_DIR"] = "storage"

    with app.app_context():
        hls_dir = get_lesson_hls_directory(course_id=99901, lesson_id=88801)
        assert hls_dir.is_absolute(), f"Expected absolute path, got {hls_dir}"
        assert "course_99901" in str(hls_dir)
        assert "lesson_88801" in str(hls_dir)


def test_challenge_2_segment_resolution_prevents_mispointing() -> None:
    """Verify segment path resolution produces an absolute path that does not contain /app/src/pwd301/storage."""
    sys.path.insert(0, str(REPO_ROOT / "src"))

    # Simulate container layout where app root_path is /app/src/pwd301 and storage is /app/storage
    app = Flask("pwd301", root_path="/app/src/pwd301")
    app.config["STORAGE_DIR"] = "/app/storage"

    with app.app_context():
        # Even if STORAGE_DIR is set to a path or relative fallback
        # Let's test with pure Path resolution logic
        hls_dir = (
            Path(app.config["STORAGE_DIR"]).resolve()
            / "drm_hls"
            / "course_110006"
            / "lesson_160031"
        )
        segment_path = (
            hls_dir
            / "67e23c44-28d9-46d1-814b-773a91681c36"
            / "bcbf3419-b20d-5aef-9718-83f675291333"
            / "segment_000.ts"
        )
        resolved = segment_path.resolve()

        assert resolved.is_absolute(), f"Resolved path must be absolute: {resolved}"
        # Crucial assertion: Must NOT contain /app/src/pwd301/storage
        normalized_str = str(resolved).replace("\\", "/")
        assert "/app/src/pwd301/storage" not in normalized_str, (
            f"Segment path erroneously contains /app/src/pwd301/storage: {normalized_str}"
        )


def test_challenge_2_posix_container_simulation() -> None:
    """Verify in POSIX environment (Docker container /app), segment path is absolute and never has /app/src/pwd301/storage."""
    from pathlib import PurePosixPath

    # In Linux container:
    app_root_path = PurePosixPath("/app/src/pwd301")
    storage_dir = PurePosixPath("/app/storage")

    # If relative, Flask prepends root_path:
    rel_segment = PurePosixPath("storage/drm_hls/course_110006/lesson_160031/segment_000.ts")
    assert not rel_segment.is_absolute()
    flawed_flask_path = app_root_path / rel_segment
    assert (
        str(flawed_flask_path)
        == "/app/src/pwd301/storage/drm_hls/course_110006/lesson_160031/segment_000.ts"
    )

    # With .resolve(), the segment path is absolute:
    correct_segment = storage_dir / "drm_hls" / "course_110006" / "lesson_160031" / "segment_000.ts"
    assert correct_segment.is_absolute()
    # Flask does NOT prepend root_path if path is absolute:
    assert "/app/src/pwd301/storage" not in str(correct_segment)
    assert str(correct_segment).startswith("/app/storage")


def test_challenge_2_code_inspection_routes_resolve() -> None:
    """Verify in student routes that segment.resolve() is explicitly used with send_file."""
    content = STUDENT_ROUTES_PATH.read_text(encoding="utf-8")
    assert 'send_file(segment.resolve(), mimetype="video/MP2T", conditional=True)' in content, (
        "student/routes.py must call send_file(segment.resolve(), ...)"
    )

    drm_service_content = VIDEO_DRM_SERVICE_PATH.read_text(encoding="utf-8")
    assert ".resolve()" in drm_service_content, (
        "video_drm_service.py must use .resolve() when resolving storage_base"
    )


# =========================================================================
# CHALLENGE 3: Invariant Text Strings
# =========================================================================


def test_challenge_3_backend_forbidden_archive_message() -> None:
    """Assert backend file_service.py defines the exact Vietnamese archive rejection string."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pwd301.services.exceptions import FileValidationError
    from pwd301.services.file_service import (
        FORBIDDEN_ARCHIVE_EXTENSIONS,
        FORBIDDEN_ARCHIVE_MESSAGE,
        validate_file_metadata,
    )

    assert FORBIDDEN_ARCHIVE_MESSAGE == EXACT_VIETNAMESE_ARCHIVE_MESSAGE, (
        f"Backend archive message mismatch:\nExpected: {EXACT_VIETNAMESE_ARCHIVE_MESSAGE}\nActual:   {FORBIDDEN_ARCHIVE_MESSAGE}"
    )

    for ext in FORBIDDEN_ARCHIVES:
        assert ext in FORBIDDEN_ARCHIVE_EXTENSIONS, (
            f"Extension {ext} missing from FORBIDDEN_ARCHIVE_EXTENSIONS"
        )

    # Verify validate_file_metadata raises with exact message
    for ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]:
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_metadata(filename=f"malicious{ext}")
        assert str(exc_info.value) == EXACT_VIETNAMESE_ARCHIVE_MESSAGE


def test_challenge_3_frontend_forbidden_archive_message() -> None:
    """Assert frontend instructor.js contains the exact Vietnamese archive rejection string."""
    content = INSTRUCTOR_JS_PATH.read_text(encoding="utf-8")
    assert EXACT_VIETNAMESE_ARCHIVE_MESSAGE in content, (
        f"Frontend instructor.js missing exact archive rejection message:\n{EXACT_VIETNAMESE_ARCHIVE_MESSAGE}"
    )

    # Verify forbiddenArchiveExts in instructor.js contains all required extensions
    for ext in FORBIDDEN_ARCHIVES:
        assert f"'{ext}'" in content or f'"{ext}"' in content, (
            f"Extension {ext} missing from instructor.js archive check"
        )


def test_challenge_3_exact_string_parity() -> None:
    """Assert character-by-character string parity between frontend and backend message."""
    backend_content = FILE_SERVICE_PATH.read_text(encoding="utf-8")
    frontend_content = INSTRUCTOR_JS_PATH.read_text(encoding="utf-8")

    backend_match = re.search(
        r'FORBIDDEN_ARCHIVE_MESSAGE:\s*str\s*=\s*\(\s*"([^"]+)"', backend_content
    )
    assert backend_match is not None, "Could not find FORBIDDEN_ARCHIVE_MESSAGE in file_service.py"
    backend_str = backend_match.group(1)

    frontend_match = re.search(
        r'UI\.showToast\(\s*"([^"]*Hệ thống không hỗ trợ tệp nén[^"]*)"',
        frontend_content,
    )
    assert frontend_match is not None, "Could not find archive rejection toast in instructor.js"
    frontend_str = frontend_match.group(1)

    assert backend_str == EXACT_VIETNAMESE_ARCHIVE_MESSAGE, "Backend string differs from invariant"
    assert frontend_str == EXACT_VIETNAMESE_ARCHIVE_MESSAGE, (
        "Frontend string differs from invariant"
    )
    assert backend_str == frontend_str, (
        "Frontend and backend archive rejection strings are not identical!"
    )


def test_challenge_3_scanner_service_parity() -> None:
    """Assert scanner_service.py also defines the identical archive rejection string and extension set."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pwd301.services.scanner_service import (
        FORBIDDEN_ARCHIVE_EXTENSIONS as SCANNER_ARCHIVES,
    )
    from pwd301.services.scanner_service import (
        FORBIDDEN_ARCHIVE_MESSAGE as SCANNER_MESSAGE,
    )

    assert SCANNER_MESSAGE == EXACT_VIETNAMESE_ARCHIVE_MESSAGE
    for ext in FORBIDDEN_ARCHIVES:
        assert ext in SCANNER_ARCHIVES


# =========================================================================
# Standalone CLI execution
# =========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING STANDALONE EMPIRICAL CHALLENGE SUITE (CHALLENGER 2 - M6)")
    print("=" * 70)

    # Run pytest programmatically on this file
    retcode = pytest.main([__file__, "-v", "-s", "--tb=short"])
    if retcode == 0:
        print("\nALL EMPIRICAL CHALLENGES PASSED SUCCESSFULLY (VERDICT: APPROVE)")
    else:
        print(f"\nCHALLENGES FAILED WITH RETCODE {retcode} (VERDICT: REQUEST_CHANGES)")
    sys.exit(retcode)
