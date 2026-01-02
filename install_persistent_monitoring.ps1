# Alternative: Persistent monitoring using scheduled tasks (no admin rights required for basic setup)

Write-Host "=== Setting Up Persistent Monitoring ===" -ForegroundColor Cyan

# Create a persistent monitoring script
$persistentScript = @'
# Persistent monitoring script
$daemonLog = "D:\dev\casestrainer\logs\docker_daemon_monitor.log"
$eventLog = "D:\dev\casestrainer\logs\docker_events.log"

# Ensure logs directory exists
New-Item -Path (Split-Path $daemonLog) -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -Path (Split-Path $eventLog) -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $daemonLog -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-EventLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $eventLog -Value $logEntry -ErrorAction SilentlyContinue
}

# Start event monitoring
$eventScript = {
    $eventLog = "D:\dev\casestrainer\logs\docker_events.log"
    function Write-EventLog {
        param([string]$Message)
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] $Message"
        Add-Content -Path $eventLog -Value $logEntry -ErrorAction SilentlyContinue
    }
    try {
        Write-EventLog "=== DOCKER EVENT MONITORING STARTED ==="
        docker events 2>&1 | ForEach-Object {
            if ($_ -and $_.ToString() -and $_.ToString().Trim()) {
                Write-EventLog $_.ToString()
            }
        }
    } catch {
        Write-EventLog "ERROR: $($_.Exception.Message)"
    }
}

# Start event job
Start-Job -Name "Docker-Events-Persistent" -ScriptBlock $eventScript | Out-Null

# Main monitoring loop
Write-Log "=== PERSISTENT MONITORING STARTED ===" "SUCCESS"

$checkCount = 0
while ($true) {
    try {
        # Check Docker daemon
        $null = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker daemon is healthy" "SUCCESS"
        } else {
            Write-Log "Docker daemon health check FAILED" "ERROR"
        }
        
        # Check containers every 5 minutes (every 10 checks)
        if ($checkCount % 10 -eq 0) {
            $containers = docker ps --filter name=casestrainer --format "{{.Names}}" 2>$null
            if ($containers) {
                $containerCount = ($containers | Measure-Object).Count
                Write-Log "Found $containerCount CaseStrainer containers running" "INFO"
            } else {
                Write-Log "No CaseStrainer containers found" "WARN"
            }
        }
        
        $checkCount++
        
    } catch {
        Write-Log "Error in monitoring: $($_.Exception.Message)" "ERROR"
    }
    
    # Wait 60 seconds
    Start-Sleep -Seconds 60
}
'@

# Save the persistent script
$persistentScriptPath = "D:\dev\casestrainer\persistent_monitor.ps1"
$persistentScript | Out-File -FilePath $persistentScriptPath -Encoding UTF8 -Force
Write-Host "[OK] Created persistent monitoring script" -ForegroundColor Green

# Create scheduled task for persistence
Write-Host "`n[INFO] Creating scheduled task for persistent monitoring..." -ForegroundColor Yellow

# Remove existing task if it exists
Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Create new task
$taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$persistentScriptPath`""
$taskTrigger = New-ScheduledTaskTrigger -AtLogOn
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -RunLevel Highest -Force | Out-Null

Write-Host "[OK] Scheduled task created" -ForegroundColor Green

# Start the task immediately
Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null

Write-Host "`n[SUCCESS] Persistent monitoring configured!" -ForegroundColor Green
Write-Host "The monitoring will:" -ForegroundColor Gray
Write-Host "  - Start automatically when you log in" -ForegroundColor Gray
Write-Host "  - Run in the background (hidden window)" -ForegroundColor Gray
Write-Host "  - Survive reboots and log offs" -ForegroundColor Gray
Write-Host "  - Monitor Docker daemon and containers" -ForegroundColor Gray

Write-Host "`n=== Management Commands ===" -ForegroundColor Cyan
Write-Host "Check status: Get-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray
Write-Host "Start manually: Start-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray
Write-Host "Stop: Stop-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray
Write-Host "Disable: Disable-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray
Write-Host "Remove: Unregister-ScheduledTask CaseStrainer-PersistentMonitor" -ForegroundColor Gray

Write-Host "`nLogs:" -ForegroundColor Cyan
Write-Host "  Daemon: logs\docker_daemon_monitor.log" -ForegroundColor Gray
Write-Host "  Events: logs\docker_events.log" -ForegroundColor Gray
