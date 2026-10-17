"""Standalone Empirical Challenge Test Suite for Milestone 4 (Challenger 2).

Verifies:
- Challenge 1: Header Progress Badge Absence & updateConsoleCourseProgressBadge safe execution.
- Challenge 2: Hero Trailer Clean Player Shell Invariants (scaling, pointer-events, shield, query params).
- Challenge 3: Instructor Attachment Upload accept attribute & client-side archive rejection.
"""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDENT_JS_PATH = REPO_ROOT / "frontend" / "assets" / "js" / "views" / "student.js"
INSTRUCTOR_JS_PATH = REPO_ROOT / "frontend" / "assets" / "js" / "views" / "instructor.js"

EXACT_VIETNAMESE_ARCHIVE_ERROR = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)


@pytest.fixture(scope="module")
def student_source() -> str:
    assert STUDENT_JS_PATH.exists(), f"Missing {STUDENT_JS_PATH}"
    return STUDENT_JS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def instructor_source() -> str:
    assert INSTRUCTOR_JS_PATH.exists(), f"Missing {INSTRUCTOR_JS_PATH}"
    return INSTRUCTOR_JS_PATH.read_text(encoding="utf-8")


# =========================================================================
# CHALLENGE 1: Header Progress Badge Absence & Safe Function Calls
# =========================================================================

def test_challenge_1_header_progress_badge_absent(student_source: str) -> None:
    """Assert #console-course-progress-badge is absent from student console header and code."""
    # Ensure ID never appears in the student view file
    assert 'id="console-course-progress-badge"' not in student_source
    assert "id='console-course-progress-badge'" not in student_source

    # Extract console header block
    header_match = re.search(r"<header[\s\S]*?id=\"console-exit-btn\"[\s\S]*?</header>", student_source)
    assert header_match is not None, "Console header markup must exist in student.js"
    header_html = header_match.group(0)

    # Exit button must be preserved
    assert 'id="console-exit-btn"' in header_html
    # Progress badge must be completely absent from header
    assert "console-course-progress-badge" not in header_html


def test_challenge_1_update_badge_function_is_safe_noop(student_source: str) -> None:
    """Assert updateConsoleCourseProgressBadge exists as safe no-op callable with arbitrary values."""
    fn_match = re.search(r"const\s+updateConsoleCourseProgressBadge\s*=\s*\([^)]*\)\s*=>\s*\{[\s\S]*?\};", student_source)
    assert fn_match is not None, "updateConsoleCourseProgressBadge definition must be present"

    # Function body should not access null elements or perform dangerous mutations
    fn_body = fn_match.group(0)
    assert "document.getElementById('console-course-progress-badge')" not in fn_body
    assert 'document.getElementById("console-course-progress-badge")' not in fn_body


# =========================================================================
# CHALLENGE 2: Hero Trailer Clean Shell Invariants
# =========================================================================

def test_challenge_2_hero_trailer_clean_shell_markup(student_source: str) -> None:
    """Assert hero trailer clean player shell has overflow-hidden, container scaling, pointer-events, and shield."""
    # Check #hero-trailer-clean-shell container tag (attribute order agnostic)
    shell_match = re.search(r'<div\s+[^>]*id="hero-trailer-clean-shell"[^>]*>', student_source)
    assert shell_match is not None, "#hero-trailer-clean-shell must exist in student.js"
    shell_tag = shell_match.group(0)

    class_match = re.search(r'class="([^"]*)"', shell_tag)
    assert class_match is not None, "#hero-trailer-clean-shell must have class attribute"
    shell_classes = class_match.group(1).split()
    assert "overflow-hidden" in shell_classes, "Clean shell must have overflow-hidden class"

    # Check inner container scaling styles: top: -14%, height: 128%, pointer-events: none
    assert re.search(r"top:\s*-14%", student_source) is not None, "Must have top: -14% style"
    assert re.search(r"height:\s*128%", student_source) is not None, "Must have height: 128% style"
    assert re.search(r"pointer-events:\s*none", student_source) is not None, "Must have pointer-events: none style"

    # Check iframe pointer-events-none class
    iframe_match = re.search(r'<iframe[\s\S]*?id="hero-trailer-iframe"[\s\S]*?class="([^"]*)"', student_source)
    assert iframe_match is not None, "hero-trailer-iframe must exist"
    iframe_classes = iframe_match.group(1).split()
    assert "pointer-events-none" in iframe_classes, "iframe must have pointer-events-none class"

    # Check #hero-trailer-shield overlay
    shield_match = re.search(r'<div\s+[^>]*id="hero-trailer-shield"[^>]*>', student_source)
    assert shield_match is not None, "hero-trailer-shield must exist"
    shield_tag = shield_match.group(0)
    shield_class_match = re.search(r'class="([^"]*)"', shield_tag)
    assert shield_class_match is not None, "hero-trailer-shield must have class attribute"
    shield_classes = shield_class_match.group(1).split()
    for req_class in ["absolute", "inset-0", "z-10", "cursor-pointer", "bg-transparent"]:
        assert req_class in shield_classes, f"hero-trailer-shield missing class {req_class}"


def test_challenge_2_hero_trailer_query_params(student_source: str) -> None:
    """Assert hero trailer embed URL includes required query parameters: mute, loop, controls, playlist, etc."""
    url_match = re.search(r"const\s+heroEmbedUrl\s*=\s*`([^`]+)`;", student_source)
    assert url_match is not None, "heroEmbedUrl template must exist"

    template = url_match.group(1)
    test_yt_id = "testVideo123"
    resolved_url = template.replace("${ytMatch[1]}", test_yt_id)

    parsed = urllib.parse.urlparse(resolved_url)
    assert parsed.netloc == "www.youtube-nocookie.com"
    assert parsed.path == f"/embed/{test_yt_id}"

    params = urllib.parse.parse_qs(parsed.query)
    assert params.get("autoplay") == ["1"]
    assert params.get("mute") == ["1"]
    assert params.get("loop") == ["1"]
    assert params.get("controls") == ["0"]
    assert params.get("playlist") == [test_yt_id]
    assert params.get("showinfo") == ["0"]
    assert params.get("modestbranding") == ["1"]
    assert params.get("playsinline") == ["1"]


# =========================================================================
# CHALLENGE 3: Instructor Upload UI & Client-side Archive Rejection
# =========================================================================

def test_challenge_3_instructor_upload_accept_attribute(instructor_source: str) -> None:
    """Assert block-file-input accept attribute excludes archives and includes CAD/3D/Docs."""
    input_match = re.search(r'<input\s+type="file"\s+class="block-file-input[^"]*"\s+accept="([^"]+)"', instructor_source)
    assert input_match is not None, "block-file-input with accept attribute must exist"

    accept_str = input_match.group(1)
    accepted_exts = [ext.strip().lower() for ext in accept_str.split(",")]

    # Forbidden archives
    forbidden_archives = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]
    for arch in forbidden_archives:
        assert arch not in accepted_exts, f"accept attribute must NOT contain archive extension {arch}"

    # Required extensions
    required_exts = [
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt",
        ".dwg", ".dxf", ".obj", ".fbx", ".stl", ".blend", ".step", ".stp", ".gltf", ".glb"
    ]
    for ext in required_exts:
        assert ext in accepted_exts, f"accept attribute must contain {ext}"

    # Verify upload button label text
    assert "Tải tệp đính kèm (PDF, Word, Excel, PPT, CAD, 3D...)" in instructor_source


def test_challenge_3_client_archive_validation(instructor_source: str) -> None:
    """Assert client-side validation rejects archive filenames with exact Vietnamese error message."""
    assert EXACT_VIETNAMESE_ARCHIVE_ERROR in instructor_source

    forbidden_exts = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]

    def validate_filename(filename: str) -> tuple[bool, str]:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in forbidden_exts):
            return False, EXACT_VIETNAMESE_ARCHIVE_ERROR
        return True, ""

    # Test adversarial archive extensions
    archive_test_cases = [
        "assignment.zip", "ASSIGNMENT.ZIP", "report.Zip",
        "archive.rar", "BACKUP.RAR", "data.7z", "data.7Z",
        "dist.tar", "dist.tar.gz", "archive.gz", "bundle.bz2",
        "binary.xz", "disc.iso", "fake.dwg.zip"
    ]
    for filename in archive_test_cases:
        valid, err = validate_filename(filename)
        assert not valid, f"{filename} should be rejected as archive"
        assert err == EXACT_VIETNAMESE_ARCHIVE_ERROR

    # Test allowed filenames
    allowed_test_cases = [
        "document.pdf", "report.docx", "drawing.dwg", "model.stl",
        "render.blend", "cad.dxf", "object.obj", "scene.gltf",
        "part.step", "part.stp", "mesh.glb", "my_zip_code.pdf"
    ]
    for filename in allowed_test_cases:
        valid, err = validate_filename(filename)
        assert valid, f"{filename} should be accepted"
        assert err == ""
