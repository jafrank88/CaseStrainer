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
