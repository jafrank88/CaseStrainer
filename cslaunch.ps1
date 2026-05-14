# cslaunch.ps1 — DEPRECATED
# This script is no longer maintained. Use cslauncher.ps1 instead.
#
# Usage:
#   .\cslauncher.ps1 [same arguments]
#
Write-Warning "[DEPRECATED] cslaunch.ps1 is deprecated. Use cslauncher.ps1 instead."
Write-Host "Redirecting to cslauncher.ps1..." -ForegroundColor Yellow
Write-Host ""

$script = Join-Path $PSScriptRoot "cslauncher.ps1"
& $script @args
exit $LASTEXITCODE
