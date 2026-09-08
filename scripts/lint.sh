#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="python3"; [ -x .venv/bin/python ] && PY=".venv/bin/python"
"$PY" -m ruff check src tests scripts
"$PY" -m ruff format --check src tests scripts
"$PY" -m mypy src
