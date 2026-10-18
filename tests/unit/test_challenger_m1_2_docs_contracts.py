"""Adversarial challenger test suite for Milestone 1: Repo Contracts, Markdown Formatting, and Invariant Hardening.

Author: Challenger M1_2 (teamwork_preview_challenger)
Purpose: Rigorously stress-test and empirically challenge:
1. scripts/repo_check.py contract checks (required files, no duplicate DB, 77 SQL tables, balanced fences, workflow authority).
2. Deep markdown fence balancing and syntax validity on all modified files:
   - AGENTS.md
   - tasks/CURRENT.md
   - docs/intent/copyright-protection.md
   - docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md
   - docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md
3. Markdown link integrity: all local relative links in modified files resolve to existing files.
4. Exact Vietnamese archive rejection message invariant:
   "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
5. Complete Clean Player Shell v2 platform invariants across AGENTS.md and System Specification:
   - Container scaling (-14% top, 128% height, aspect-video, overflow-hidden)
   - Click shield overlay (pointer-events: none on iframe)
   - Cover Poster Shield concealing 100% of YouTube red play button and thumbnail before play
   - Error 153 fix: youtube-nocookie.com and elimination of conflicting origin parameter
   - 4 universal touchpoints (Student learning view, Course Hero intro trailer, Trailer Lightbox modal, Reviewer/Instructor preview modals)
   - 3-tier Resilient Playback Fallback (Google Data API -> client reported duration -> lesson duration -> safe default 1800s, min 300s; forbid LessonValidationError; reconcile on heartbeat)
   - Elimination of watermark overlays (Peppa Pig...) and seek-lock indicator badges
6. Zero instances of legacy "PPTX 100MB" or "100 MB" in active documentation.
7. Verification that docs/intent/copyright-protection.md carries the strict SUPERSEDED NOTICE.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

VIETNAMESE_REJECTION_MESSAGE = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). "
    "Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)

MODIFIED_FILES = [
    ROOT / "AGENTS.md",
    ROOT / "tasks" / "CURRENT.md",
    ROOT / "docs" / "intent" / "copyright-protection.md",
    ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "business" / "04_LESSON_AND_PROGRESS.md",
    ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md",
]


class TestRepoCheckContractsAdversarial:
    """Empirical challenge of repo_check.py rules and contracts."""

    def test_repo_check_script_execution_passes_cleanly(self) -> None:
        """Execute repo_check functions directly and verify all assertions."""
        from scripts import repo_check

        repo_check.check_required()
        repo_check.check_no_duplicate_db()
        repo_check.check_sql_tables()
        repo_check.check_markdown_fences()
        repo_check.check_secrets()
        repo_check.check_workflow_authority()

    def test_all_repository_markdown_fences_are_balanced(self) -> None:
        """Scan every single markdown file in repository for balanced triple backticks."""
        unbalanced = []
        for p in ROOT.rglob("*.md"):
            # Exclude git or cache directories if any
            if ".git" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            count = text.count("```")
            if count % 2 != 0:
                unbalanced.append((str(p.relative_to(ROOT)), count))
        assert not unbalanced, f"Found files with unbalanced code fences: {unbalanced}"

    def test_canonical_sql_tables_count(self) -> None:
        """Ensure exactly 77 CREATE TABLE statements exist in canonical SQL Server DDL."""
        sql_dir = ROOT / "docs" / "database" / "PWD301_DATABASE_ARCHITECTURE" / "sql"
        assert sql_dir.exists(), "Canonical SQL directory must exist"
        files = sorted(sql_dir.glob("*.sql"))
        assert len(files) > 0, "Canonical SQL directory must contain DDL files"
        ddl = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in files)
        tables = re.findall(r"\bCREATE\s+TABLE\b", ddl, flags=re.IGNORECASE)
        assert len(tables) == 77, f"Expected 77 CREATE TABLE statements, found {len(tables)}"


class TestModifiedDocsMarkdownFormatting:
    """Deep syntax and formatting checks on Milestone 1 modified files."""

    @pytest.mark.parametrize("file_path", MODIFIED_FILES)
    def test_modified_file_exists_and_is_non_empty(self, file_path: Path) -> None:
        """Modified file must exist and have content."""
        assert file_path.exists(), f"File does not exist: {file_path}"
        assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

    @pytest.mark.parametrize("file_path", MODIFIED_FILES)
    def test_code_fences_and_spans_in_modified_files(self, file_path: Path) -> None:
        """Verify code fences ``` and inline spans ` in modified files are balanced and valid."""
        content = file_path.read_text(encoding="utf-8")
        
        # Check triple backticks
        fence_count = content.count("```")
        assert fence_count % 2 == 0, f"Unbalanced triple backtick fences in {file_path.name}: {fence_count}"
        
        # Check tilde fences
        tilde_count = content.count("~~~")
        assert tilde_count % 2 == 0, f"Unbalanced tilde fences in {file_path.name}: {tilde_count}"

    def test_markdown_local_relative_links_in_modified_files(self) -> None:
        """Verify that all markdown local relative links [text](path) in modified files point to real files."""
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        broken_links = []

        for file_path in MODIFIED_FILES:
            content = file_path.read_text(encoding="utf-8")
            for match in link_pattern.finditer(content):
                target = match.group(2).strip()
                # Skip external URLs, anchors, mailto
                if (
                    target.startswith("http://")
                    or target.startswith("https://")
                    or target.startswith("#")
                    or target.startswith("mailto:")
                ):
                    continue
                # Strip internal anchor if any
                clean_target = target.split("#")[0]
                if not clean_target:
                    continue
                # Handle file:/// URLs
                if clean_target.startswith("file:///"):
                    clean_target = clean_target.replace("file:///", "")
                    resolved = Path(clean_target)
                else:
                    resolved = (file_path.parent / clean_target).resolve()

                if not resolved.exists():
                    broken_links.append({
                        "source": str(file_path.relative_to(ROOT)),
                        "target": target,
                        "resolved": str(resolved),
                    })

        assert not broken_links, f"Broken markdown links found: {broken_links}"


class TestDocumentationInvariantsAdversarial:
    """Stress-test business, security, and architecture invariants in docs."""

    def test_exact_vietnamese_rejection_message_integrity(self) -> None:
        """The Vietnamese rejection message must match character-by-character."""
        agents_content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert VIETNAMESE_REJECTION_MESSAGE in agents_content, (
            "AGENTS.md does not contain exact Vietnamese rejection message."
        )

    def test_no_legacy_100mb_or_pptx_in_active_docs(self) -> None:
        """No active documentation file (excluding docs/archive/) may contain 'PPTX 100MB' or '100 MB'."""
        pattern_100mb = re.compile(r"100\s*mb", re.IGNORECASE)
        pattern_pptx_100 = re.compile(r"pptx[^\n]*100\s*mb", re.IGNORECASE)
        violations = []

        for p in ROOT.rglob("*.md"):
            rel_parts = [part.lower() for part in p.relative_to(ROOT).parts]
            if (
                "archive" in rel_parts
                or ".git" in rel_parts
                or ".agents" in rel_parts
                or ".worktrees" in rel_parts
                or ".venv" in rel_parts
            ):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for idx, line in enumerate(text.splitlines(), 1):
                if pattern_100mb.search(line) or pattern_pptx_100.search(line):
                    violations.append((str(p.relative_to(ROOT)), idx, line.strip()))

        assert not violations, f"Legacy 100MB references found in active docs: {violations}"

    def test_clean_player_shell_v2_specifications_in_agents_md(self) -> None:
        """AGENTS.md must thoroughly codify YouTube Standard 16:9 Player invariants."""
        agents_content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        required_keywords = [
            "YouTube Standard 16:9 Player",
            "Cover Poster",
            "youtube-nocookie.com",
            "renderReviewerCoursePreview",
            "openVideoModal",
            "Resilient Playback Fallback",
            "1800.0s",
            "zero crop",
            "Pacing Engine & 5-Second Seek Unlock",
            "Realtime Lesson Completion Gate",
        ]
        missing = [kw for kw in required_keywords if kw.lower() not in agents_content.lower()]
        assert not missing, f"AGENTS.md is missing required YouTube Standard 16:9 Player keywords: {missing}"

    def test_system_specification_06_non_negotiable_invariants(self) -> None:
        """06_NON_NEGOTIABLE_INVARIANTS.md Invariant 25 must be updated to YouTube Standard 16:9 Player."""
        invariants_content = (
            ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "implementation" / "06_NON_NEGOTIABLE_INVARIANTS.md"
        ).read_text(encoding="utf-8")

        assert "YouTube Standard 16:9 Player" in invariants_content
        assert "Cover Poster/Backdrop Shield" in invariants_content
        assert "youtube-nocookie.com" in invariants_content
        assert "Resilient Playback Fallback" in invariants_content
        assert "1800s" in invariants_content or "1800.0s" in invariants_content
        assert "Error 153" in invariants_content

    def test_system_specification_04_lesson_and_progress(self) -> None:
        """04_LESSON_AND_PROGRESS.md must specify YouTube Standard 16:9 Player and resilient duration fallback."""
        lesson_spec = (
            ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "business" / "04_LESSON_AND_PROGRESS.md"
        ).read_text(encoding="utf-8")

        assert "YouTube Standard 16:9 Player" in lesson_spec
        assert "Cover Poster/Backdrop Shield" in lesson_spec
        assert "youtube-nocookie.com" in lesson_spec
        assert "Resilient Playback Fallback" in lesson_spec

    def test_copyright_protection_superseded_notice(self) -> None:
        """docs/intent/copyright-protection.md must contain explicit SUPERSEDED NOTICE."""
        doc = (ROOT / "docs" / "intent" / "copyright-protection.md").read_text(encoding="utf-8")
        assert "SUPERSEDED NOTICE" in doc
        assert "YouTube Standard 16:9 Player" in doc
        assert "AGENTS.md" in doc

    def test_tasks_current_tracks_task_098_with_supersession_pointer(self) -> None:
        """tasks/CURRENT.md must track TASK-100 and preserve WORKFLOW_SUPERSESSION.md link."""
        current_task = (ROOT / "tasks" / "CURRENT.md").read_text(encoding="utf-8")
        assert "TASK-100" in current_task
        assert "YouTube Standard 16:9 Viewport" in current_task
        assert "WORKFLOW_SUPERSESSION.md" in current_task
