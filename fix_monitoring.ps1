# Fix the monitoring issues

Write-Host "=== Fixing CaseStrainer Monitoring ===" -ForegroundColor Cyan

# 1. Stop all existing jobs
Write-Host "`n[1] Stopping existing jobs..." -ForegroundColor Yellow
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue

# 2. Clear old logs
Write-Host "`n[2] Clearing old logs..." -ForegroundColor Yellow
Clear-Content "logs\docker_daemon_monitor.log" -ErrorAction SilentlyContinue
Clear-Content "logs\docker_events.log" -ErrorAction SilentlyContinue
Clear-Content "logs\monitoring_watchdog.log" -ErrorAction SilentlyContinue

# 3. Create a simple monitoring script
Write-Host "`n[3] Creating persistent monitoring script..." -ForegroundColor Yellow

$monitorScript = @'
# Simple monitoring script
$daemonLog = "D:\dev\casestrainer\logs\docker_daemon_monitor.log"
$eventLog = "D:\dev\casestrainer\logs\docker_events.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $daemonLog -Value $logEntry
}

# Start event monitoring
$eventScript = {
    $logPath = "D:\dev\casestrainer\logs\docker_events.log"
    function Write-EventLog {
        param([string]$Message)
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] $Message"
        Add-Content -Path $logPath -Value $logEntry
    }
    try {
        Write-EventLog "=== DOCKER EVENT MONITORING STARTED ==="
        docker events --format 'Type={{.Type}} Action={{.Action}} Object={{.Object}} Time={{.Time}} Status={{.Status}}' 2>&1 | ForEach-Object {
            if ($_ -and $_.ToString() -and $_.ToString().Trim()) {
                Write-EventLog $_.ToString()
            }
        }
    } catch {
        Write-EventLog "ERROR: $($_.Exception.Message)"
    }
}

Start-Job -Name "Docker-Events" -ScriptBlock $eventScript

# Main monitoring loop
Write-Log "=== MONITORING STARTED ===" "SUCCESS"
while ($true) {
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker daemon is healthy" "SUCCESS"
        } else {
            Write-Log "Docker daemon health check FAILED" "ERROR"
        }
    } catch {
        Write-Log "Error checking Docker: $($_.Exception.Message)" "ERROR"
    }
    
    Start-Sleep -Seconds 60
}
'@

# Save the monitoring script
$monitorScript | Out-File -FilePath "D:\dev\casestrainer\simple_monitor.ps1" -Encoding UTF8 -Force

# 4. Create scheduled task for persistence
Write-Host "`n[4] Creating scheduled task for persistence..." -ForegroundColor Yellow

$taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File D:\dev\casestrainer\simple_monitor.ps1"
$taskTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "CaseStrainer-Monitor" -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -RunLevel Highest -Force | Out-Null

# 5. Start the monitoring
Write-Host "`n[5] Starting monitoring..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName "CaseStrainer-Monitor" | Out-Null

Write-Host "`n[SUCCESS] Monitoring fixed and started!" -ForegroundColor Green
Write-Host "  - Simple monitor script created" -ForegroundColor Gray
Write-Host "  - Scheduled task created (runs every minute)" -ForegroundColor Gray
Write-Host "  - Logs: docker_daemon_monitor.log, docker_events.log" -ForegroundColor Gray
Write-Host "`nTo stop: Unregister-ScheduledTask -TaskName 'CaseStrainer-Monitor'" -ForegroundColor Gray
