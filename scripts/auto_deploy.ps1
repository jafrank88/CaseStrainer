# CaseStrainer Automatic Deployment Script
# This script automatically detects changes and deploys them correctly

param(
    [switch]$Force,
    [switch]$SkipVerification
)

Write-Host "=== CASESTRAINER AUTO DEPLOYMENT ===" -ForegroundColor Green

# Check if there are uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus -and -not $Force) {
    Write-Host "❌ Uncommitted changes detected. Use -Force to deploy anyway." -ForegroundColor Red
    Write-Host $gitStatus
    exit 1
}

# Detect what changed
Write-Host "`n1. Detecting changes..." -ForegroundColor Yellow
$backendChanged = $false
$frontendChanged = $false

# Check backend files
$backendFiles = @("src/", "requirements.txt", "Dockerfile", "docker-compose.prod.yml")
foreach ($pattern in $backendFiles) {
    if (git diff --name-only HEAD~1 HEAD | Where-Object { $_ -like "$pattern*" }) {
        $backendChanged = $true
        break
    }
}

# Check frontend files
$frontendFiles = @("casestrainer-vue-new/", "nginx.conf")
foreach ($pattern in $frontendFiles) {
    if (git diff --name-only HEAD~1 HEAD | Where-Object { $_ -like "$pattern*" }) {
        $frontendChanged = $true
        break
    }
}

Write-Host "Backend changes detected: $backendChanged" -ForegroundColor $(if ($backendChanged) { "Green" } else { "Gray" })
Write-Host "Frontend changes detected: $frontendChanged" -ForegroundColor $(if ($frontendChanged) { "Green" } else { "Gray" })

# Deploy backend changes
if ($backendChanged) {
    Write-Host "`n2. Deploying backend changes..." -ForegroundColor Yellow
    docker compose -f docker-compose.prod.yml build backend
    docker compose -f docker-compose.prod.yml restart backend
    Start-Sleep -Seconds 5
}

# Deploy frontend changes
if ($frontendChanged) {
    Write-Host "`n3. Deploying frontend changes..." -ForegroundColor Yellow
    docker compose -f docker-compose.prod.yml build frontend-prod
    docker compose -f docker-compose.prod.yml restart frontend-prod
    Start-Sleep -Seconds 10
}

# Run verification
if (-not $SkipVerification) {
    Write-Host "`n4. Running verification..." -ForegroundColor Yellow
    & ".\scripts\verify_deployment.ps1" -SkipFrontendRebuild:(-not $frontendChanged) -SkipBackendRestart:(-not $backendChanged)
}

Write-Host "`n=== AUTO DEPLOYMENT COMPLETE ===" -ForegroundColor Green
