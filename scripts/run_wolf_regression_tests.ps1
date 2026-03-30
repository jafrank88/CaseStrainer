# CaseStrainer regression suite: same Python code paths users hit on https://wolf.law.uw.edu
# Prerequisites: Redis listening on 127.0.0.1:6379 (e.g. docker compose up -d redis)
# Optional: matches CI by exporting REDIS_URL before pytest (conftest also forces local Redis by default).
#
# Invoke from repo root:  .\scripts\run_wolf_regression_tests.ps1 [extra pytest args...]
# Do not use `param()` here — PowerShell would treat pytest flags like -q as script parameters.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

# Ensure local Redis target even if parent shell loaded production .env
$env:CASSTRAINER_USE_TEST_REDIS = "1"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:CACHE_REDIS_URL = "redis://127.0.0.1:6379/1"

# $args = arguments after script name. Strip "--" (pytest does not accept it as an argument).
$forward = [System.Collections.ArrayList]@()
foreach ($a in $args) {
    if ($a -ne '--') { [void]$forward.Add($a) }
}
python -m pytest -c pytest-wolf.ini @forward
exit $LASTEXITCODE

