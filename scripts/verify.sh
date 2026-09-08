#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="python3"; [ -x .venv/bin/python ] && PY=".venv/bin/python"

echo "== Repository contract =="
"$PY" scripts/repo_check.py
echo "== Python compile =="
"$PY" -m compileall -q src tests scripts
echo "== Lint / format / types =="
"$PY" -m ruff check src tests scripts
"$PY" -m ruff format --check src tests scripts
"$PY" -m mypy src
echo "== Tests =="
"$PY" -m pytest
echo "PWD301 verification PASS"
