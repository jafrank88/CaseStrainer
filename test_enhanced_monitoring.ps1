# test_enhanced_monitoring.ps1 - Simple test for enhanced monitoring system

param(
    [switch]$QuickTest
)

Write-Host "Testing Enhanced Monitoring System..." -ForegroundColor Cyan

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
        Write-Host "  ✓ $script" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $script (MISSING)" -ForegroundColor Red
        $missingScripts += $script
    }
}

if ($missingScripts.Count -eq 0) {
    Write-Host "[TEST 1] PASSED - All scripts found" -ForegroundColor Green
} else {
    Write-Host "[TEST 1] FAILED - Missing $($missingScripts.Count) scripts" -ForegroundColor Red
    if (-not $QuickTest) { return }
}

# Test 2: Test enhanced Docker monitor (quick syntax check)
Write-Host "`n[TEST 2] Testing enhanced Docker monitor syntax..." -ForegroundColor Yellow
try {
    $enhancedMonitor = Join-Path $scriptsDir "enhanced_docker_monitor.ps1"
    $syntaxCheck = powershell -NoProfile -Command "& { . '$enhancedMonitor'; exit 0 }" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Enhanced Docker monitor syntax OK" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Enhanced Docker monitor syntax error" -ForegroundColor Red
        Write-Host "    Error: $syntaxCheck" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Enhanced Docker monitor test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test self-health monitor syntax
Write-Host "`n[TEST 3] Testing self-health monitor syntax..." -ForegroundColor Yellow
try {
    $selfHealthScript = Join-Path $scriptsDir "monitor_self_health.ps1"
    $syntaxCheck = powershell -NoProfile -Command "& { . '$selfHealthScript'; exit 0 }" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Self-health monitor syntax OK" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Self-health monitor syntax error" -ForegroundColor Red
        Write-Host "    Error: $syntaxCheck" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Self-health monitor test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check logs directory
Write-Host "`n[TEST 4] Checking logs directory..." -ForegroundColor Yellow
$logsDir = Join-Path $PSScriptRoot "logs"
if (Test-Path $logsDir) {
    Write-Host "  ✓ Logs directory exists" -ForegroundColor Green
    Write-Host "  Location: $logsDir" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Logs directory missing - creating..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "  ✓ Logs directory created" -ForegroundColor Green
}

# Test 5: Test basic Docker connectivity
Write-Host "`n[TEST 5] Testing Docker connectivity..." -ForegroundColor Yellow
try {
    $dockerTest = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker is running and responsive" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Docker not responding" -ForegroundColor Red
        Write-Host "    Error: $dockerTest" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Show current monitoring status
Write-Host "`n[TEST 6] Current monitoring status..." -ForegroundColor Yellow
try {
    $jobs = Get-Job | Where-Object { $_.Name -match "Enhanced|Self-Health|System-Recovery|Escalation" }
    if ($jobs.Count -gt 0) {
        Write-Host "  Found $($jobs.Count) enhanced monitoring jobs:" -ForegroundColor Green
        foreach ($job in $jobs) {
            Write-Host "    - $($job.Name): $($job.State) (ID: $($job.Id))" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No enhanced monitoring jobs currently running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Failed to check job status: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Enhanced Monitoring Test Complete ===" -ForegroundColor Cyan

if ($missingScripts.Count -eq 0) {
    Write-Host "System is ready for enhanced monitoring deployment" -ForegroundColor Green
    Write-Host "`nTo start enhanced monitoring, run:" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -EnableEnhancedMonitoring -EnableSelfHealthMonitoring" -ForegroundColor White
} else {
    Write-Host "System needs missing scripts before deployment" -ForegroundColor Yellow
}

Write-Host "`nFor detailed usage, see: ENHANCED_MONITORING_GUIDE.md" -ForegroundColor Gray
