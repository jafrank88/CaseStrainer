# test_enhanced_simple.ps1 - Simple test for enhanced monitoring without Unicode issues

param(
    [switch]$QuickTest
)

Write-Host "Testing Enhanced Monitoring System (Clean Version)..." -ForegroundColor Cyan

# Import the clean enhanced monitoring functions
$enhancedFunctionsPath = Join-Path $PSScriptRoot "scripts\enhanced_monitoring_functions.ps1"
if (Test-Path $enhancedFunctionsPath) {
    . $enhancedFunctionsPath
    Write-Host "[OK] Enhanced monitoring functions loaded successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Enhanced monitoring functions not found" -ForegroundColor Red
    exit 1
}

# Test 1: Check if all script files exist
Write-Host "`n[TEST 1] Checking script files..." -ForegroundColor Yellow
$scriptsDir = Join-Path $PSScriptRoot "scripts"
$requiredScripts = @(
    "enhanced_docker_monitor.ps1",
    "monitor_self_health.ps1", 
    "system_recovery_logger.ps1",
    "escalation_manager.ps1",
    "enhanced_docker_restart.ps1"
)

$missingScripts = @()
foreach ($script in $requiredScripts) {
    $scriptPath = Join-Path $scriptsDir $script
    if (Test-Path $scriptPath) {
        Write-Host "  [OK] $script" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $script" -ForegroundColor Red
        $missingScripts += $script
    }
}

if ($missingScripts.Count -eq 0) {
    Write-Host "[TEST 1] PASSED - All scripts found" -ForegroundColor Green
} else {
    Write-Host "[TEST 1] FAILED - Missing $($missingScripts.Count) scripts" -ForegroundColor Red
}

# Test 2: Test enhanced monitoring status function
Write-Host "`n[TEST 2] Testing enhanced monitoring status..." -ForegroundColor Yellow
try {
    Show-EnhancedMonitoringStatus
    Write-Host "[TEST 2] PASSED - Status function works" -ForegroundColor Green
} catch {
    Write-Host "[TEST 2] FAILED - Status function error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check logs directory
Write-Host "`n[TEST 3] Checking logs directory..." -ForegroundColor Yellow
$logsDir = Join-Path $PSScriptRoot "logs"
if (Test-Path $logsDir) {
    Write-Host "  [OK] Logs directory exists" -ForegroundColor Green
    Write-Host "  Location: $logsDir" -ForegroundColor Gray
} else {
    Write-Host "  [CREATING] Logs directory missing - creating..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "  [OK] Logs directory created" -ForegroundColor Green
}

# Test 4: Test basic Docker connectivity
Write-Host "`n[TEST 4] Testing Docker connectivity..." -ForegroundColor Yellow
try {
    $dockerTest = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker is running and responsive" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Docker not responding" -ForegroundColor Yellow
        Write-Host "    Error: $dockerTest" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [ERROR] Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Enhanced Monitoring Test Complete ===" -ForegroundColor Cyan

if ($missingScripts.Count -eq 0) {
    Write-Host "System is ready for enhanced monitoring deployment" -ForegroundColor Green
    Write-Host "`nTo start enhanced monitoring, run:" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -EnableEnhancedMonitoring -EnableSelfHealthMonitoring" -ForegroundColor White
    Write-Host "`nOr test the clean functions directly:" -ForegroundColor Cyan
    Write-Host "  .\test_enhanced_simple.ps1" -ForegroundColor White
} else {
    Write-Host "System needs missing scripts before deployment" -ForegroundColor Yellow
}

Write-Host "`nFor detailed usage, see: ENHANCED_MONITORING_GUIDE.md" -ForegroundColor Gray
