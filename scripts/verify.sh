#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="python3"; [ -x .venv/bin/python ] && PY=".venv/bin/python"
"$PY" -c 'import os; from scripts.test_database_guard import require_disposable_database; require_disposable_database(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))'
command -v node >/dev/null || { echo "FAIL: Node is required for frontend verification."; exit 1; }

echo "== Repository contract =="
"$PY" scripts/repo_check.py
echo "== Python compile =="
"$PY" -m compileall -q src tests scripts migrations
echo "== Lint / format / types =="
"$PY" -m ruff check src tests scripts migrations
"$PY" -m ruff format --check src tests scripts migrations
"$PY" -m mypy src
echo "== Frontend Node tests =="
node --test tests/frontend/*.test.js
echo "== Tests =="
"$PY" -m pytest
echo "PWD301 verification PASS"
