from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUPERSEDED_WORKFLOW_PLANS = (
    "2026-10-07-curriculum-authoring-approval-and-quiz-remediation.md",
    "2026-10-07-curriculum-tree-exams-and-coursera-quizzes.md",
    "2026-10-09-admin-review-diff-and-pdf-export.md",
    "2026-10-09-comprehensive-assessment-review-pdf-and-course-approval-system.md",
    "2026-10-14-course-changeset-and-ui-remediation.md",
    "2026-10-14-system-enhancements-and-remediation.md",
)

REQUIRED = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "tasks" / "CURRENT.md",
    ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "00_MASTER_SYSTEM_SPEC.md",
    ROOT / "docs" / "database" / "PWD301_DATABASE_ARCHITECTURE" / "README.md",
    ROOT / "docs" / "database" / "PWD301_DATABASE_ARCHITECTURE" / "sql" / "001_identity.sql",
]

FORBIDDEN_DUPLICATES = [
    ROOT
    / "docs"
    / "system"
    / "PWD301_SYSTEM_SPECIFICATION"
    / "database"
    / "reference_architecture",
    ROOT / "docs" / "system" / "PWD301_SYSTEM_SPECIFICATION" / "database" / "sql",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_required() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        fail("Missing required repository files: " + ", ".join(missing))
    print("[PASS] Required repository contract files exist")


def check_no_duplicate_db() -> None:
    present = [str(p.relative_to(ROOT)) for p in FORBIDDEN_DUPLICATES if p.exists()]
    if present:
        fail("Duplicate database source reintroduced: " + ", ".join(present))
    print("[PASS] No duplicate database architecture/SQL copy under System Specification")


def check_sql_tables() -> None:
    sql_dir = ROOT / "docs" / "database" / "PWD301_DATABASE_ARCHITECTURE" / "sql"
    files = sorted(sql_dir.glob("*.sql"))
    ddl = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in files)
    count = len(re.findall(r"\bCREATE\s+TABLE\b", ddl, flags=re.IGNORECASE))
    if count != 77:
        fail(f"Canonical DDL CREATE TABLE count is {count}, expected 77")
    print("[PASS] Canonical SQL Server DDL contains 77 CREATE TABLE statements")


def check_markdown_fences() -> None:
    bad: list[str] = []
    for p in ROOT.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if text.count("```") % 2:
            bad.append(str(p.relative_to(ROOT)))
    if bad:
        fail("Unbalanced Markdown fences: " + ", ".join(bad[:20]))
    print("[PASS] Markdown code fences are balanced")


def check_secrets() -> None:
    # Lightweight guard against committing the local .env;
    # deeper secret scanning belongs in CI/security tasks.
    if (ROOT / ".env").exists():
        print("[NOTE] .env exists locally; ensure it remains ignored by Git")
    if not (ROOT / ".env.example").exists():
        fail(".env.example is missing")
    print("[PASS] Environment template exists")


def check_workflow_authority() -> None:
    specification = ROOT / "docs/system/PWD301_SYSTEM_SPECIFICATION"
    authority = specification / "implementation/WORKFLOW_SUPERSESSION.md"
    entrypoints = (
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / "tasks/CURRENT.md",
        specification / "CODING_AGENT_START_HERE.md",
    )
    for entry in entrypoints:
        if not entry.exists() or "WORKFLOW_SUPERSESSION.md" not in entry.read_text(
            encoding="utf-8"
        ):
            fail(f"Missing workflow authority pointer: {entry.relative_to(ROOT)}")
    if not authority.exists():
        fail("Workflow authority is missing")
    contract = authority.read_text(encoding="utf-8")
    if not all(f"WF{number:02d}" in contract for number in range(1, 11)):
        fail("Workflow replacement register is incomplete")
    for name in SUPERSEDED_WORKFLOW_PLANS:
        path = ROOT / "docs/superpowers/plans" / name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if (
            "SUPERSEDED" not in text
            or "WORKFLOW_SUPERSESSION.md" not in text
            or "### Task" in text
            or "Step 1:" in text
        ):
            fail(f"Retired workflow plan is actionable or unlinked: {name}")
    print("[PASS] Workflow authority and retired-plan supersession gates")


def main() -> int:
    print(f"PWD301 repository check: {ROOT}")
    check_required()
    check_no_duplicate_db()
    check_sql_tables()
    check_markdown_fences()
    check_secrets()
    check_workflow_authority()
    print("[PASS] Repository contract check complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
