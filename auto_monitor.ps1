# Auto-monitor script - called by cslaunch
param($ScriptRoot)

# Start simple monitoring in background
Start-Job -Name "CaseStrainer-AutoMonitor" -ScriptBlock {
    $daemonLog = Join-Path $using:ScriptRoot "logs\docker_daemon_monitor.log"
    $eventLog = Join-Path $using:ScriptRoot "logs\docker_events.log"
    
    function Write-Log {
        param([string]$Message, [string]$Level = "INFO")
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$Level] $Message"
        Add-Content -Path $daemonLog -Value $logEntry
    }
    
    function Write-EventLog {
        param([string]$Message)
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] $Message"
        Add-Content -Path $eventLog -Value $logEntry
    }
    
    # Start event monitoring
    Start-Job -Name "Docker-Events" -ScriptBlock {
        $eventLog = $using:eventLog
        function Write-EventLog {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $eventLog -Value $logEntry
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
    
    # Main monitoring loop
    Write-Log "=== AUTO MONITORING STARTED ===" "SUCCESS"
    while ($true) {
        try {
            $null = docker info 2>$null
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
} | Out-Null

Write-Host "[AUTO] Monitoring started in background" -ForegroundColor Green
