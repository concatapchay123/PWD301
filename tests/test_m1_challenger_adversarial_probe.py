"""Adversarial challenger test harness for Milestone 1: Spec & Outdated Documentation Cleansing.

Empirically tests:
1. Complete neutralization of docs/intent/copyright-protection.md
2. Absence of contradictory or obsolete YouTube terms across active documentation
3. Exact presence and consistency of Clean Player Shell v2 rules across AGENTS.md,
   04_LESSON_AND_PROGRESS.md, 06_NON_NEGOTIABLE_INVARIANTS.md, and tasks/CURRENT.md
4. Absence of unshielded iframe, red play button, or visible branding requirements
5. Verification of 4 universal touchpoints and 3-tier resilient fallback in canonical specs
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_active_docs():
    """Retrieve all active markdown documentation excluding docs/archive/."""
    active = [
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "PROJECT.md",
        PROJECT_ROOT / "tasks" / "CURRENT.md",
    ]
    docs_dir = PROJECT_ROOT / "docs"
    for path in docs_dir.rglob("*.md"):
        # Skip archive directories
        if "archive" in path.parts:
            continue
        active.append(path)
    return [p for p in active if p.exists()]


def test_copyright_protection_neutralization():
    """Ensure docs/intent/copyright-protection.md cannot be mistaken for active policy."""
    target = PROJECT_ROOT / "docs" / "intent" / "copyright-protection.md"
    assert target.exists(), "docs/intent/copyright-protection.md must exist"
    content = target.read_text(encoding="utf-8")

    # 1. Must have explicit SUPERSEDED NOTICE at the top
    assert "SUPERSEDED NOTICE" in content
    assert "Clean Player Shell v2" in content
    assert "STRICTLY SUPERSEDED" in content

    # 2. Historical section must be clearly tagged
    assert "(Historical / Superseded)" in content

    # 3. Must reference AGENTS.md §10.8 and Invariant 25
    assert "AGENTS.md" in content
    assert "Invariant 25" in content


def test_no_unshielded_youtube_claims_in_active_docs():
    """Probe all active documentation for active claims that YouTube branding or navigation must be visible."""
    active_docs = get_active_docs()
    violations = []
    
    # Phrases that indicate active policy to keep YouTube native branding/controls
    bad_phrases = [
        "keeps branding and navigation visible",
        "keeps branding visible",
        "no obscuring shields or watermark",
        "unshielded iframe",
    ]

    for doc in active_docs:
        content = doc.read_text(encoding="utf-8")
        rel_path = doc.relative_to(PROJECT_ROOT)
        for line_no, line in enumerate(content.splitlines(), start=1):
            for phrase in bad_phrases:
                if phrase in line.lower():
                    # If in copyright-protection.md, ensure it is within the quote of what was superseded
                    if str(rel_path) == os.path.join("docs", "intent", "copyright-protection.md"):
                        if "STRICTLY SUPERSEDED" in line or "Historical statements below" in line:
                            continue
                    # If describing superseding historical unshielded iframe statements in changelogs/task tracking
                    if "historical unshielded" in line.lower() or "supersed" in line.lower():
                        continue
                    violations.append(f"{rel_path}:{line_no} -> {line.strip()}")

    assert not violations, "Found obsolete unshielded YouTube claims:\n" + "\n".join(violations)


def test_agents_md_clean_player_shell_v2_comprehensive():
    """Verify AGENTS.md codifies Clean Player Shell v2 in both Section 4 and Section 10.8."""
    agents_file = PROJECT_ROOT / "AGENTS.md"
    assert agents_file.exists()
    content = agents_file.read_text(encoding="utf-8")

    required_keywords_section_4 = [
        "Clean Player Shell v2",
        "Cover Poster/Backdrop Shield",
        "concealing 100% of YouTube red play button",
        "zero YouTube branding",
        "youtube-nocookie.com",
        "Resilient Playback Fallback",
        "safe default (1800s, min 300s)",
    ]
    for kw in required_keywords_section_4:
        assert kw in content, f"AGENTS.md missing Section 4 keyword: '{kw}'"

    required_keywords_section_10_8 = [
        "10.8. Bất biến Bản quyền Video & YouTube Clean Player Shell v2",
        "Cover Poster Shield",
        "nút play đỏ",
        "youtube-nocookie.com",
        "Error 153",
        "Hero Trailer",
        "autoplay",
        "mute",
        "loop",
        "Universal Touchpoints",
        "Resilient Playback Fallback",
        "LessonValidationError",
    ]
    for kw in required_keywords_section_10_8:
        assert kw in content, f"AGENTS.md missing Section 10.8 keyword: '{kw}'"


def test_system_specification_invariant_25_alignment():
    """Verify 04_LESSON_AND_PROGRESS.md and 06_NON_NEGOTIABLE_INVARIANTS.md reflect Clean Player Shell v2."""
    inv_file = PROJECT_ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md"
    lesson_file = PROJECT_ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "business" / "04_LESSON_AND_PROGRESS.md"

    for f in [inv_file, lesson_file]:
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "Clean Player Shell v2" in content
        assert "Cover Poster" in content
        assert "youtube-nocookie.com" in content
        assert "Resilient Playback Fallback" in content
        assert "1800s" in content
        assert "4 universal touchpoints" in content or "4 touchpoints" in content


def test_current_task_alignment():
    """Verify tasks/CURRENT.md properly tracks TASK-098 and links to authority."""
    current_file = PROJECT_ROOT / "tasks" / "CURRENT.md"
    assert current_file.exists()
    content = current_file.read_text(encoding="utf-8")

    assert "TASK-098" in content
    assert "WORKFLOW_SUPERSESSION.md" in content
    assert "Clean Player Shell v2" in content
    assert "Resilient Fallback" in content


def test_no_archive_policy_preserved():
    """Verify that attachment invariants remain strict and unaltered."""
    agents_file = PROJECT_ROOT / "AGENTS.md"
    content = agents_file.read_text(encoding="utf-8")

    assert "50,000,000 bytes" in content
    assert "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)" in content
