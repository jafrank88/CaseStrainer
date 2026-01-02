# Auto-start monitoring when cslaunch runs

Write-Host "=== Setting up Auto-Start Monitoring ===" -ForegroundColor Cyan

# Create a startup script that will be called by cslaunch
$autoMonitorScript = @'
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
'@

# Save the auto-monitor script
$autoMonitorScript | Out-File -FilePath ".\auto_monitor.ps1" -Encoding UTF8 -Force

# Now add the call to cslaunch.ps1
$scriptPath = ".\cslaunch.ps1"
$content = Get-Content $scriptPath -Raw

# Find where to insert the auto-monitor call (after the main header)
$insertPoint = $content.IndexOf("Write-Host `"========================================`" -ForegroundColor Cyan")
if ($insertPoint -gt 0) {
    $insertPoint = $content.IndexOf("`n", $insertPoint) + 1
    $autoMonitorCall = @'

# Start auto-monitoring if no flags provided
if (-not $Build -and -not $Monitor -and -not $ConfigureAutostart -and -not $NoAutostart -and -not $ConfigurePeriodicHealthCheck -and -not $RemovePeriodicHealthCheck -and -not $DeepCleanRestart -and -not $MemoryOptimizeRestart -and -not $NoCache -and -not $Force) {
    Write-Host "[AUTO] Starting background monitoring..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "auto_monitor.ps1") -ScriptRoot $PSScriptRoot
}
'@
    $content = $content.Substring(0, $insertPoint) + $autoMonitorCall + $content.Substring($insertPoint)
    Set-Content -Path $scriptPath -Value $content -Encoding UTF8
    Write-Host "[OK] Added auto-monitor call to cslaunch.ps1" -ForegroundColor Green
}

Write-Host "`n[SUCCESS] Auto-start monitoring configured!" -ForegroundColor Green
Write-Host "Now when you run .\cslaunch without flags, monitoring will start automatically" -ForegroundColor Gray
