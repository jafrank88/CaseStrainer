# monitor_self_health.ps1 - Self-health monitoring for CaseStrainer monitoring system
# Ensures monitoring scripts stay alive and automatically recovers from crashes

param(
    [int]$CheckInterval = 300,        # Health check interval (5 minutes)
    [int]$MaxDowntime = 1800,         # Maximum allowed downtime (30 minutes)
    [string]$MonitorScript = "enhanced_docker_monitor.ps1",
    [string]$LogPath = "logs\self_health_monitor.log"
)

# Setup logging
$ErrorActionPreference = "Continue"
$script:LogPath = Join-Path $PSScriptRoot $LogPath
$script:StartTime = Get-Date
$script:LastMonitorRestart = $null
$script:RestartCount = 0
$script:MaxRestartsPerHour = 6

# Ensure logs directory exists
$logDir = Split-Path $script:LogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-SelfHealthLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $uptime = "{0:hh\:mm\:ss}" - (Get-Date - $script:StartTime)
    $logEntry = "[$timestamp] [Uptime: $uptime] [$Level] $Message"
    
    Add-Content -Path $script:LogPath -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "CRITICAL" { Write-Host $logEntry -ForegroundColor Magenta }
        default { Write-Host $logEntry }
    }
}

function Test-MonitorScriptHealth {
    <#
    .SYNOPSIS
    Check if the monitoring script is running and healthy
    #>
    
    $health = @{
        ProcessRunning = $false
        LogFileActive = $false
        LastLogEntry = $null
        DowntimeMinutes = 0
        Overall = $false
    }
    
    try {
        # Check if monitoring process is running
        $monitorProcesses = Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { 
            $_.CommandLine -and $_.CommandLine -match $MonitorScript 
        }
        
        $health.ProcessRunning = ($monitorProcesses.Count -gt 0)
        
        if ($health.ProcessRunning) {
            Write-SelfHealthLog "Found $($monitorProcesses.Count) monitoring process(es) running" "INFO"
        } else {
            Write-SelfHealthLog "No monitoring processes found" "WARN"
        }
        
        # Check if log file is being updated
        $monitorLogPath = Join-Path $PSScriptRoot "..\logs\enhanced_monitor.log"
        if (Test-Path $monitorLogPath) {
            $logFile = Get-Item $monitorLogPath
            $timeSinceLastWrite = (Get-Date) - $logFile.LastWriteTime
            $health.DowntimeMinutes = $timeSinceLastWrite.TotalMinutes
            $health.LogFileActive = ($timeSinceLastWrite.TotalMinutes -lt $MaxDowntime)
            
            # Get last log entry
            $lastLines = Get-Content $monitorLogPath -Tail 1
            $health.LastLogEntry = $lastLines
            
            if ($health.LogFileActive) {
                Write-SelfHealthLog "Log file active (last update: $($timeSinceLastWrite.TotalMinutes.ToString('F1')) minutes ago)" "INFO"
            } else {
                Write-SelfHealthLog "Log file inactive (last update: $($timeSinceLastWrite.TotalMinutes.ToString('F1')) minutes ago)" "WARN"
            }
        } else {
            Write-SelfHealthLog "Monitor log file not found at $monitorLogPath" "ERROR"
        }
        
        # Overall health
        $health.Overall = $health.ProcessRunning -and $health.LogFileActive
        
    } catch {
        Write-SelfHealthLog "Health check failed: $($_.Exception.Message)" "ERROR"
    }
    
    return $health
}

function Restart-MonitorScript {
    <#
    .SYNOPSIS
    Restart the monitoring script with proper error handling
    #>
    
    param([string]$Reason = "Auto-recovery")
    
    Write-SelfHealthLog "=== MONITOR SCRIPT RESTART INITIATED ===" "CRITICAL"
    Write-SelfHealthLog "Reason: $Reason" "CRITICAL"
    
    try {
        # Check restart rate limit
        $now = Get-Date
        if ($script:LastMonitorRestart -and ($now - $script:LastMonitorRestart).TotalHours -lt 1) {
            $script:RestartCount++
            if ($script:RestartCount -gt $script:MaxRestartsPerHour) {
                Write-SelfHealthLog "Restart rate limit exceeded ($script:RestartCount restarts in last hour)" "ERROR"
                Write-SelfHealthLog "Manual intervention required" "CRITICAL"
                return $false
            }
        } else {
            # Reset counter if more than an hour has passed
            $script:RestartCount = 0
        }
        
        # Kill existing monitoring processes
        Write-SelfHealthLog "Stopping existing monitoring processes..." "INFO"
        $monitorProcesses = Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { 
            $_.CommandLine -and $_.CommandLine -match $MonitorScript 
        }
        
        foreach ($process in $monitorProcesses) {
            try {
                Write-SelfHealthLog "Stopping process $($process.Id) ($($process.ProcessName))" "INFO"
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            } catch {
                Write-SelfHealthLog "Failed to stop process $($process.Id): $($_.Exception.Message)" "WARN"
            }
        }
        
        # Wait a moment for processes to fully stop
        Start-Sleep -Seconds 5
        
        # Start new monitoring process
        $monitorScriptPath = Join-Path $PSScriptRoot $MonitorScript
        if (Test-Path $monitorScriptPath) {
            Write-SelfHealthLog "Starting new monitoring process..." "INFO"
            
            $startArgs = @(
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", "`"$monitorScriptPath`"",
                "-EnableAutoRecovery",
                "-EnableResourceMonitoring"
            )
            
            Start-Process powershell.exe -ArgumentList $startArgs -WindowStyle Hidden -ErrorAction Stop
            
            $script:LastMonitorRestart = $now
            Write-SelfHealthLog "=== MONITOR SCRIPT RESTART SUCCESSFUL ===" "SUCCESS"
            
            # Wait a moment and verify it started
            Start-Sleep -Seconds 10
            $health = Test-MonitorScriptHealth
            
            if ($health.Overall) {
                Write-SelfHealthLog "New monitoring process verified and healthy" "SUCCESS"
                return $true
            } else {
                Write-SelfHealthLog "New monitoring process failed to start properly" "ERROR"
                return $false
            }
        } else {
            Write-SelfHealthLog "Monitor script not found at $monitorScriptPath" "ERROR"
            return $false
        }
        
    } catch {
        Write-SelfHealthLog "Monitor script restart failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Send-CriticalAlert {
    <#
    .SYNOPSIS
    Send critical alert when monitoring system fails
    #>
    
    param(
        [string]$Message,
        [string]$Severity = "CRITICAL"
    )
    
    Write-SelfHealthLog "CRITICAL ALERT: $Message" "CRITICAL"
    
    # Log to main crash log as well
    $crashLogPath = Join-Path $PSScriptRoot "..\logs\crash_log.txt"
    if (Test-Path $crashLogPath) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content -Path $crashLogPath -Value "[$timestamp] [CRITICAL] Self-Health Monitor: $Message"
    }
    
    # TODO: Add external notification methods (email, Slack, etc.)
    # For now, just ensure it's logged prominently
}

function Start-SelfHealthMonitoring {
    <#
    .SYNOPSIS
    Start the self-health monitoring loop
    #>
    
    Write-SelfHealthLog "=== SELF-HEALTH MONITORING STARTED ===" "SUCCESS"
    Write-SelfHealthLog "Check interval: ${CheckInterval}s" "INFO"
    Write-SelfHealthLog "Max downtime: ${MaxDowntime}s ($([math]::Round($MaxDowntime/60, 1)) minutes)" "INFO"
    Write-SelfHealthLog "Monitor script: $MonitorScript" "INFO"
    Write-SelfHealthLog "Max restarts per hour: $script:MaxRestartsPerHour" "INFO"
    
    $consecutiveFailures = 0
    $maxConsecutiveFailures = 3
    
    while ($true) {
        try {
            $timestamp = Get-Date -Format "HH:mm:ss"
            
            # Test monitor script health
            $health = Test-MonitorScriptHealth
            
            if ($health.Overall) {
                if ($consecutiveFailures -gt 0) {
                    Write-SelfHealthLog "Monitor script recovered after $consecutiveFailures consecutive failures" "SUCCESS"
                    $consecutiveFailures = 0
                }
                
                # Log periodic status
                $checkCount = (Get-Date).Minute % 15
                if ($checkCount -eq 0) {
                    Write-SelfHealthLog "Self-health check: OK (Process: $($health.ProcessRunning), Log: $($health.LogFileActive), Downtime: $($health.DowntimeMinutes.ToString('F1'))min)" "INFO"
                }
            } else {
                $consecutiveFailures++
                Write-SelfHealthLog "Self-health check FAILED (attempt $consecutiveFailures)" "ERROR"
                Write-SelfHealthLog "  Process running: $($health.ProcessRunning)" "ERROR"
                Write-SelfHealthLog "  Log file active: $($health.LogFileActive)" "ERROR"
                Write-SelfHealthLog "  Downtime: $($health.DowntimeMinutes.ToString('F1')) minutes" "ERROR"
                
                if ($health.LastLogEntry) {
                    Write-SelfHealthLog "  Last log entry: $([math]::Round($health.DowntimeMinutes, 1)) minutes ago" "ERROR"
                }
                
                # Attempt recovery
                if ($consecutiveFailures -ge $maxConsecutiveFailures) {
                    Write-SelfHealthLog "Triggering monitor script recovery after $consecutiveFailures consecutive failures" "CRITICAL"
                    
                    $restartReason = "Self-health recovery after $consecutiveFailures consecutive failures (downtime: $($health.DowntimeMinutes.ToString('F1')) minutes)"
                    $restartSuccess = Restart-MonitorScript -Reason $restartReason
                    
                    if ($restartSuccess) {
                        $consecutiveFailures = 0
                        Write-SelfHealthLog "Monitor script recovery successful" "SUCCESS"
                    } else {
                        Write-SelfHealthLog "Monitor script recovery failed" "CRITICAL"
                        Send-CriticalAlert "Self-health monitoring unable to recover monitor script after $consecutiveFailures failures. Manual intervention required."
                    }
                }
            }
            
        } catch {
            Write-SelfHealthLog "Self-health monitoring loop error: $($_.Exception.Message)" "ERROR"
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Start self-health monitoring
Write-SelfHealthLog "Self-Health Monitor v1.0 starting..." "INFO"
Start-SelfHealthMonitoring
