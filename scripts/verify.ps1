$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "== Repository contract =="
& $Python scripts/repo_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Python compile =="
& $Python -m compileall -q src tests scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Lint / format / types =="
& $Python -m ruff check src tests scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m ruff format --check src tests scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Tests =="
& $Python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PWD301 verification PASS"
