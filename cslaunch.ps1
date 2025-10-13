# cslaunch.ps1 - Quick restart wrapper for production environment
# This is optimized for fast Python code updates without rebuilding Docker images

param(
    [switch]$Build,
    [switch]$Force,
    [switch]$NoCache
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Quick Restart (./cslaunch)" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if containers are already running
$containers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })

if ($containers.Count -gt 0 -and -not $Build -and -not $Force) {
    Write-Host "[OK] Found $($containers.Count) running containers" -ForegroundColor Green
    Write-Host "[QUICK RESTART] Restarting containers (10-15 seconds)..." -ForegroundColor Yellow
    Write-Host ""
    
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart
    $sw.Stop()
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[SUCCESS] RESTART COMPLETE in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds!" -ForegroundColor Green
        Write-Host "  Your Python changes are now active (volume mounts)" -ForegroundColor DarkGray
        Write-Host "  Application: http://localhost" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "`n[ERROR] Restart failed, falling back to full deployment..." -ForegroundColor Red
    }
}

# Fall back to full deployment
Write-Host "[FULL DEPLOY] Running full deployment (containers not found or rebuild requested)..." -ForegroundColor Yellow
$fullScriptPath = Join-Path $PSScriptRoot 'scripts\cslaunch.ps1'

if (-not (Test-Path $fullScriptPath)) {
    Write-Host '[ERROR] Could not find scripts\cslaunch.ps1' -ForegroundColor Red
    exit 1
}

# Forward parameters
$params = @{ Command = 'prod' }
if ($Build) { $params.Build = $true }
if ($Force) { $params.Force = $true }
if ($NoCache) { $params.NoCache = $true }

& $fullScriptPath @params
exit $LASTEXITCODE
