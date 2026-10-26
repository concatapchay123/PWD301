#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ is required" >&2; exit 1; }
[ -d .venv ] || python3 -m venv .venv
PY="$ROOT/.venv/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt -r requirements-dev.txt
"$PY" -m pip install -e .
[ -f .env ] || { cp .env.example .env; echo "Created .env; replace local secrets before running the app."; }

if command -v npm >/dev/null 2>&1 && [ -f tools/pdf-math/package.json ]; then
    echo "Installing tools/pdf-math Node dependencies..."
    npm --prefix tools/pdf-math install --silent || true
fi

"$PY" scripts/repo_check.py
echo "PWD301 development environment bootstrap completed."
