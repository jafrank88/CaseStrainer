# Test script to verify Docker monitoring fixes

Write-Host "=== Testing Docker Monitoring Fixes ===" -ForegroundColor Cyan

# Test 1: Check if helper functions exist
Write-Host "`n[Test 1] Checking helper functions..." -ForegroundColor Yellow

# Load the script to test functions
try {
    . ".\cslaunch.ps1" -ErrorAction Stop
    
    if (Get-Command Test-AdminPrivileges -ErrorAction SilentlyContinue) {
        Write-Host "  ✓ Test-AdminPrivileges function exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Test-AdminPrivileges function missing" -ForegroundColor Red
    }
    
    if (Get-Command Get-BackoffDelay -ErrorAction SilentlyContinue) {
        Write-Host "  ✓ Get-BackoffDelay function exists" -ForegroundColor Green
        # Test the function
        $delay = Get-BackoffDelay -AttemptNumber 3
        Write-Host "    Test: Attempt 3 delay = ${delay}s" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Get-BackoffDelay function missing" -ForegroundColor Red
    }
    
    if (Get-Command Start-DockerEventMonitoring -ErrorAction SilentlyContinue) {
        Write-Host "  ✓ Start-DockerEventMonitoring function exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Start-DockerEventMonitoring function missing" -ForegroundColor Red
    }
    
} catch {
    Write-Host "  ✗ Error loading script: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Check if event monitoring can start
Write-Host "`n[Test 2] Testing Docker event monitoring..." -ForegroundColor Yellow

try {
    # Check if Docker is running
    $null = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Docker is running, testing event monitoring..." -ForegroundColor Gray
        
        # Start event monitoring for a short time
        $eventJob = Start-DockerEventMonitoring
        Write-Host "  ✓ Event monitoring started (Job ID: $($eventJob.Id))" -ForegroundColor Green
        
        # Wait a moment
        Start-Sleep -Seconds 3
        
        # Check if event log is being written
        if (Test-Path "logs\docker_events.log") {
            $logContent = Get-Content "logs\docker_events.log"
            if ($logContent -match "DOCKER EVENT MONITORING STARTED") {
                Write-Host "  ✓ Event log is being written" -ForegroundColor Green
            }
        }
        
        # Stop the monitoring
        Stop-Job -Job $eventJob -ErrorAction SilentlyContinue
        Remove-Job -Job $eventJob -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Event monitoring stopped" -ForegroundColor Green
        
    } else {
        Write-Host "  ⚠ Docker is not running, cannot test event monitoring" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error testing event monitoring: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check daemon monitor log
Write-Host "`n[Test 3] Checking daemon monitor log..." -ForegroundColor Yellow

if (Test-Path "logs\docker_daemon_monitor.log") {
    $logSize = (Get-Item "logs\docker_daemon_monitor.log").Length
    $logLines = (Get-Content "logs\docker_daemon_monitor.log").Count
    Write-Host "  ✓ Daemon monitor log exists" -ForegroundColor Green
    Write-Host "    Size: $([math]::Round($logSize/1KB, 2)) KB, Lines: $logLines" -ForegroundColor Gray
    
    # Check for recent entries
    $recentEntries = Get-Content "logs\docker_daemon_monitor.log" | Select-Object -Last 5
    if ($recentEntries -match "enhanced") {
        Write-Host "  ✓ Enhanced monitoring entries found" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ Daemon monitor log not found" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "`nTo run the enhanced monitoring:" -ForegroundColor Gray
Write-Host "  .\cslaunch.ps1 -Monitor" -ForegroundColor White
Write-Host "`nTo check logs:" -ForegroundColor Gray
Write-Host "  Get-Content logs\docker_events.log -Tail 20" -ForegroundColor White
Write-Host "  Get-Content logs\docker_daemon_monitor.log -Tail 20" -ForegroundColor White
