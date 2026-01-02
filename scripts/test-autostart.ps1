<#
.SYNOPSIS
    Tests the Docker autostart configuration without rebooting.

.DESCRIPTION
    This script simulates what happens on boot by:
    1. Checking if Docker is running
    2. Running the autostart script
    3. Verifying containers are running

.EXAMPLE
    .\scripts\test-autostart.ps1
#>

param(
    [string]$ProjectPath = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Docker Auto-Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get the project root
if ($ProjectPath -eq $PSScriptRoot) {
    $ProjectPath = Split-Path -Parent $ProjectPath
}

$autostartScript = Join-Path $ProjectPath "scripts\docker-autostart.ps1"

if (-not (Test-Path $autostartScript)) {
    Write-Host "[ERROR] Autostart script not found: $autostartScript" -ForegroundColor Red
    Write-Host "        Run: .\scripts\install-docker-autostart.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/3] Checking Docker status..." -ForegroundColor Yellow
$DockerInfo = docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Docker is running" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Docker is not running" -ForegroundColor Red
    Write-Host "          Please start Docker Desktop first" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[2/3] Running autostart script..." -ForegroundColor Yellow
& $autostartScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Autostart script failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/3] Verifying containers..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$containers = docker ps --format "{{.Names}}" | Select-String -Pattern "casestrainer"
$expectedContainers = @(
    "casestrainer-redis-prod",
    "casestrainer-backend-prod",
    "casestrainer-rqworker1-prod",
    "casestrainer-rqworker2-prod",
    "casestrainer-rqworker3-prod",
    "casestrainer-frontend-prod",
    "casestrainer-nginx-prod"
)

$runningContainers = $containers | ForEach-Object { $_.ToString().Trim() }
$missingContainers = $expectedContainers | Where-Object { $_ -notin $runningContainers }

if ($missingContainers.Count -eq 0) {
    Write-Host "  [OK] All containers are running" -ForegroundColor Green
    Write-Host "`nRunning containers:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "casestrainer"
} else {
    Write-Host "  [WARN] Some containers are not running:" -ForegroundColor Yellow
    foreach ($container in $missingContainers) {
        Write-Host "    - $container" -ForegroundColor Yellow
    }
    Write-Host "`nRunning containers:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "casestrainer"
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan












