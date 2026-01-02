# View CaseStrainer monitoring logs safely

param(
    [string]$LogType = "daemon",  # daemon or events
    [int]$Lines = 50
)

Write-Host "=== CaseStrainer Log Viewer ===" -ForegroundColor Cyan

if ($LogType -eq "daemon") {
    $logPath = "logs\docker_daemon_monitor.log"
    Write-Host "Showing Docker Daemon Monitor Log (last $Lines lines):" -ForegroundColor Yellow
} elseif ($LogType -eq "events") {
    $logPath = "logs\docker_events.log"
    Write-Host "Showing Docker Events Log (last $Lines lines):" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] Invalid log type. Use 'daemon' or 'events'" -ForegroundColor Red
    exit 1
}

# Use Get-Content with -Wait to follow the log
try {
    Write-Host "`nPress Ctrl+C to stop watching`n" -ForegroundColor Gray
    Get-Content $logPath -Tail $Lines -Wait
} catch {
    Write-Host "[ERROR] Cannot read log file: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "The monitoring service might be writing to the file. Try again in a moment." -ForegroundColor Yellow
}
