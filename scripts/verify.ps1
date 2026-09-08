$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "== Repository contract =="
& $Python scripts/repo_check.py
Write-Host "== Python compile =="
& $Python -m compileall -q src tests scripts
Write-Host "== Lint / format / types =="
& $Python -m ruff check src tests scripts
& $Python -m ruff format --check src tests scripts
& $Python -m mypy src
Write-Host "== Tests =="
& $Python -m pytest
Write-Host "PWD301 verification PASS"
