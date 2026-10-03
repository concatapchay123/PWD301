$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "== Repository contract =="
& $Python scripts/repo_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Python compile =="
& $Python -m compileall -q src tests scripts migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Lint / format / types =="
& $Python -m ruff check src tests scripts migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m ruff format --check src tests scripts migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "== Frontend Node tests =="
$Node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $Node) {
    Write-Host "SKIP: node executable is not available; frontend tests were not run." -ForegroundColor Yellow
} else {
    $FrontendTests = @(Get-ChildItem -Path "tests/frontend" -Filter "*.test.js" -File | Sort-Object FullName | Select-Object -ExpandProperty FullName)
    if ($FrontendTests.Count -eq 0) {
        Write-Host "SKIP: no frontend Node tests were found." -ForegroundColor Yellow
    } else {
        & $Node.Source --test $FrontendTests
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}
Write-Host "== Tests =="
& $Python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PWD301 verification PASS"
