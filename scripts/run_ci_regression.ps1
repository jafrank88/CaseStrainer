# CaseStrainer CI regression gate (parity with GitHub Actions).
# From repo root:  .\scripts\run_ci_regression.ps1 [extra pytest args...]
#
# Uses local Redis like the wolf script when running async/analyze tests.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$env:CASSTRAINER_USE_TEST_REDIS = "1"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:CACHE_REDIS_URL = "redis://127.0.0.1:6379/1"

$forward = [System.Collections.ArrayList]@()
foreach ($a in $args) {
    if ($a -ne '--') { [void]$forward.Add($a) }
}

python scripts/ci_regression.py @forward
exit $LASTEXITCODE
