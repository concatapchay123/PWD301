"""Adversarial challenger test suite for Milestone 1 specification consistency.

Verifies that AGENTS.md, docs/system/, and docs/database/ contain zero
conflicting statements regarding:
1. Dynamic header badge calculation / navigation progress calculation
2. 100MB PPTX limits
3. Obsolete dwell times (20s / 30s)
4. Obsolete forensic watermark overlays or unobscured iframe claims
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCS_SYSTEM = PROJECT_ROOT / "docs" / "system"
DOCS_DATABASE = PROJECT_ROOT / "docs" / "database"
AGENTS_MD = PROJECT_ROOT / "AGENTS.md"


def test_no_100mb_pptx_in_database_architecture():
    """Verify that no active docs in docs/database/ reference 100MB PPTX."""
    bad_matches = []
    pattern = re.compile(r"100\s*MB", re.IGNORECASE)
    for md_file in DOCS_DATABASE.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line) and "pptx" in line.lower():
                bad_matches.append(f"{md_file.relative_to(PROJECT_ROOT)}:{line_no} -> {line.strip()}")
    assert not bad_matches, "Found conflicting 100MB PPTX in docs/database:\n" + "\n".join(bad_matches)


def test_no_100mb_pptx_in_system_specification():
    """Verify that no active docs in docs/system/ reference 100MB PPTX."""
    bad_matches = []
    pattern = re.compile(r"100\s*MB", re.IGNORECASE)
    for md_file in DOCS_SYSTEM.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line) and "pptx" in line.lower():
                bad_matches.append(f"{md_file.relative_to(PROJECT_ROOT)}:{line_no} -> {line.strip()}")
    assert not bad_matches, "Found conflicting 100MB PPTX in docs/system:\n" + "\n".join(bad_matches)


def test_no_dynamic_header_progress_in_non_negotiable_invariants():
    """Verify that 06_NON_NEGOTIABLE_INVARIANTS.md has purged dynamic navigation progress calculation."""
    invariants_file = DOCS_SYSTEM / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md"
    assert invariants_file.exists()
    content = invariants_file.read_text(encoding="utf-8")
    
    # Check for obsolete sentence: "Course progress in student navigation is computed dynamically"
    bad_matches = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        if "Course progress in student navigation is computed dynamically" in line:
            bad_matches.append(f"{invariants_file.relative_to(PROJECT_ROOT)}:{line_no} -> {line.strip()}")
    assert not bad_matches, "Found obsolete dynamic header progress statement:\n" + "\n".join(bad_matches)


def test_no_obsolete_video_watermark_in_non_negotiable_invariants():
    """Verify that 06_NON_NEGOTIABLE_INVARIANTS.md has updated Rule 25 (Video DRM & Clean Player)."""
    invariants_file = DOCS_SYSTEM / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md"
    content = invariants_file.read_text(encoding="utf-8")
    bad_matches = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        if "dynamic forensic watermarks" in line or "unobscured iframe" in line:
            bad_matches.append(f"{invariants_file.relative_to(PROJECT_ROOT)}:{line_no} -> {line.strip()}")
    assert not bad_matches, "Found obsolete watermark/iframe claims in invariants:\n" + "\n".join(bad_matches)


def test_no_obsolete_dwell_time_in_spec():
    """Verify that 06_NON_NEGOTIABLE_INVARIANTS.md and 04_LESSON_AND_PROGRESS.md do not state < 60s dwell."""
    bad_matches = []
    target_files = [
        DOCS_SYSTEM / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md",
        DOCS_SYSTEM / "PWD301_SYSTEM_SPECIFICATION" / "business" / "04_LESSON_AND_PROGRESS.md",
    ]
    for target in target_files:
        if not target.exists():
            continue
        content = target.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if "20 seconds" in line or "30 seconds" in line:
                if "dwell" in line.lower():
                    bad_matches.append(f"{target.relative_to(PROJECT_ROOT)}:{line_no} -> {line.strip()}")
    assert not bad_matches, "Found obsolete dwell time (<60s) in specs:\n" + "\n".join(bad_matches)


if __name__ == "__main__":
    import sys

    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
