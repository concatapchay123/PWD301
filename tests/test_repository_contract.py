from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_specifications_exist() -> None:
    assert (ROOT / "docs/system/PWD301_SYSTEM_SPECIFICATION/00_MASTER_SYSTEM_SPEC.md").is_file()
    assert (ROOT / "docs/database/PWD301_DATABASE_ARCHITECTURE/README.md").is_file()
    assert (ROOT / "AGENTS.md").is_file()


def test_database_is_not_duplicated_under_system_spec() -> None:
    base = ROOT / "docs/system/PWD301_SYSTEM_SPECIFICATION/database"
    assert not (base / "reference_architecture").exists()
    assert not (base / "sql").exists()


def test_canonical_ddl_has_expected_table_count() -> None:
    sql_dir = ROOT / "docs/database/PWD301_DATABASE_ARCHITECTURE/sql"
    ddl = "\n".join(p.read_text(encoding="utf-8") for p in sorted(sql_dir.glob("*.sql")))
    assert len(re.findall(r"\bCREATE\s+TABLE\b", ddl, flags=re.IGNORECASE)) == 71


def test_current_task_exists() -> None:
    text = (ROOT / "tasks/CURRENT.md").read_text(encoding="utf-8")
    assert "TASK-001" in text
