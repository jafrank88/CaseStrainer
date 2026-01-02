# Simple verification of Docker fixes

Write-Host "=== Verifying Docker Fixes ===" -ForegroundColor Cyan

# Load the script to get functions
. ".\cslaunch.ps1"

# Check functions
Write-Host "`nChecking functions:" -ForegroundColor Yellow

if (Get-Command Test-AdminPrivileges -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Test-AdminPrivileges exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Test-AdminPrivileges missing" -ForegroundColor Red
}

if (Get-Command Get-BackoffDelay -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Get-BackoffDelay exists" -ForegroundColor Green
    $delay = Get-BackoffDelay -AttemptNumber 3
    Write-Host "    Test: Attempt 3 = ${delay}s delay" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Get-BackoffDelay missing" -ForegroundColor Red
}

if (Get-Command Start-DockerEventMonitoring -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Start-DockerEventMonitoring exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Start-DockerEventMonitoring missing" -ForegroundColor Red
}

# Check logs
Write-Host "`nChecking logs:" -ForegroundColor Yellow

if (Test-Path "logs\docker_daemon_monitor.log") {
    $size = [math]::Round((Get-Item "logs\docker_daemon_monitor.log").Length/1KB, 2)
    Write-Host "  ✓ Daemon monitor log exists (${size} KB)" -ForegroundColor Green
}

if (Test-Path "logs\docker_events.log") {
    Write-Host "  ✓ Event log exists" -ForegroundColor Green
    $events = Get-Content "logs\docker_events.log" | Where-Object { $_ -match "DOCKER EVENT MONITORING" }
    if ($events) {
        Write-Host "    Event monitoring has been started" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Event log not created yet (starts when monitoring runs)" -ForegroundColor Yellow
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Green
Write-Host "`nTo start enhanced monitoring: .\cslaunch.ps1 -Monitor" -ForegroundColor Gray
