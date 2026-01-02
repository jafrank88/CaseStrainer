# Integrate persistent monitoring into cslaunch

Write-Host "=== Integrating Persistent Monitoring into cslaunch ===" -ForegroundColor Cyan

# Read cslaunch.ps1
$scriptPath = ".\cslaunch.ps1"
$content = Get-Content $scriptPath -Raw

# Add persistent monitoring check at the end
$persistentCheck = @'

# Check and ensure persistent monitoring is enabled
function Ensure-PersistentMonitoring {
    $task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue
    
    if (-not $task) {
        Write-Host "[SETUP] Configuring persistent monitoring..." -ForegroundColor Yellow
        & (Join-Path $PSScriptRoot "install_persistent_monitoring.ps1")
    } elseif ($task.State -ne "Running") {
        Write-Host "[MONITOR] Starting persistent monitoring..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null
        Start-Sleep -Seconds 2
        $task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
        if ($task.State -eq "Running") {
            Write-Host "[OK] Persistent monitoring is running" -ForegroundColor Green
        }
    } else {
        Write-Host "[OK] Persistent monitoring is already active" -ForegroundColor Green
    }
    
    Write-Host "  - Logs: logs\docker_daemon_monitor.log" -ForegroundColor Gray
    Write-Host "  - Events: logs\docker_events.log" -ForegroundColor Gray
    Write-Host "  - Status: Get-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray
}

# Call persistent monitoring setup
Ensure-PersistentMonitoring
'@

# Find the end of the script (before exit)
$insertPoint = $content.LastIndexOf("exit $deployExitCode")
if ($insertPoint -gt 0) {
    # Insert before the exit command
    $content = $content.Substring(0, $insertPoint) + $persistentCheck + "`n" + $content.Substring($insertPoint)
    
    # Write the updated script
    Set-Content -Path $scriptPath -Value $content -Encoding UTF8
    
    Write-Host "[SUCCESS] Persistent monitoring integrated into cslaunch!" -ForegroundColor Green
    Write-Host "`nNow when you run .\cslaunch, it will:" -ForegroundColor Gray
    Write-Host "  1. Start/stop containers as needed" -ForegroundColor Gray
    Write-Host "  2. Ensure persistent monitoring is configured" -ForegroundColor Gray
    Write-Host "  3. Start monitoring if not running" -ForegroundColor Gray
    Write-Host "`nThe monitoring will survive reboots and session changes!" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Could not find insertion point in cslaunch.ps1" -ForegroundColor Red
}
