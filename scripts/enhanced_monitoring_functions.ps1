# enhanced_monitoring_functions.ps1 - Clean version without Unicode character issues

function Start-EnhancedMonitoringSuite {
    <#
    .SYNOPSIS
    Start the comprehensive enhanced monitoring suite to prevent recurring Docker crashes
    #>
    
    Write-Host "[ENHANCED] Starting comprehensive monitoring suite..." -ForegroundColor Cyan
    
    $scriptsDir = Join-Path $PSScriptRoot ".."
    $monitoringJobs = @()
    
    # 1. Enhanced Docker Monitor
    if ($EnableEnhancedMonitoring) {
        Write-Host "[ENHANCED] Starting enhanced Docker monitor..." -ForegroundColor Green
        $enhancedMonitorScript = Join-Path $scriptsDir "scripts\enhanced_docker_monitor.ps1"
        
        if (Test-Path $enhancedMonitorScript) {
            try {
                $scriptArgs = @(
                    "-CheckInterval", $EnhancedCheckInterval,
                    "-DockerTimeout", $DockerDaemonTimeout,
                    "-MemoryThreshold", $MemoryThreshold,
                    "-CpuThreshold", $CpuThreshold
                )
                
                if ($EnableAutoRecovery) { $scriptArgs += "-EnableAutoRecovery" }
                if ($EnableResourceMonitoring) { $scriptArgs += "-EnableResourceMonitoring" }
                
                $job = Start-Job -Name "Enhanced-Docker-Monitor" -ScriptBlock {
                    param($ScriptPath, $ScriptArgs)
                    & $ScriptPath @ScriptArgs
                } -ArgumentList $enhancedMonitorScript, $scriptArgs
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] Enhanced Docker monitor started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start enhanced Docker monitor: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Enhanced Docker monitor script not found" -ForegroundColor Yellow
        }
    }
    
    # 2. Self-Health Monitor
    if ($EnableSelfHealthMonitoring) {
        Write-Host "[ENHANCED] Starting self-health monitor..." -ForegroundColor Green
        $selfHealthScript = Join-Path $scriptsDir "scripts\monitor_self_health.ps1"
        
        if (Test-Path $selfHealthScript) {
            try {
                $scriptArgs = @(
                    "-MonitorScript", "enhanced_docker_monitor.ps1"
                )
                
                $job = Start-Job -Name "Self-Health-Monitor" -ScriptBlock {
                    param($ScriptPath, $ScriptArgs)
                    & $ScriptPath @ScriptArgs
                } -ArgumentList $selfHealthScript, $scriptArgs
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] Self-health monitor started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start self-health monitor: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Self-health monitor script not found" -ForegroundColor Yellow
        }
    }
    
    # 3. System Recovery Logger
    if ($EnableSystemRecoveryLogging) {
        Write-Host "[ENHANCED] Starting system recovery logger..." -ForegroundColor Green
        $recoveryLoggerScript = Join-Path $scriptsDir "scripts\system_recovery_logger.ps1"
        
        if (Test-Path $recoveryLoggerScript) {
            try {
                $job = Start-Job -Name "System-Recovery-Logger" -ScriptBlock {
                    param($ScriptPath)
                    & $ScriptPath
                } -ArgumentList $recoveryLoggerScript
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] System recovery logger started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start system recovery logger: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] System recovery logger script not found" -ForegroundColor Yellow
        }
    }
    
    # 4. Escalation Manager
    if ($EnableEscalationManager) {
        Write-Host "[ENHANCED] Starting escalation manager..." -ForegroundColor Green
        $escalationScript = Join-Path $scriptsDir "scripts\escalation_manager.ps1"
        
        if (Test-Path $escalationScript) {
            try {
                $job = Start-Job -Name "Escalation-Manager" -ScriptBlock {
                    param($ScriptPath)
                    & $ScriptPath
                } -ArgumentList $escalationScript
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] Escalation manager started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start escalation manager: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Escalation manager script not found" -ForegroundColor Yellow
        }
    }
    
    # Summary
    Write-Host "[ENHANCED] Enhanced monitoring suite started with $($monitoringJobs.Count) components" -ForegroundColor Cyan
    Write-Host "[ENHANCED] Active monitoring jobs:" -ForegroundColor Gray
    foreach ($job in $monitoringJobs) {
        Write-Host "[ENHANCED]   - $($job.Name) (ID: $($job.Id))" -ForegroundColor Gray
    }
    
    Write-Host "[ENHANCED] Enhanced logs location: logs\enhanced_*.log" -ForegroundColor Gray
    Write-Host "[ENHANCED] Use 'Get-Job' to monitor job status" -ForegroundColor Gray
    
    return $monitoringJobs
}

function Restart-DockerEnhanced {
    <#
    .SYNOPSIS
    Enhanced Docker restart with deep cleanup and memory optimization
    #>
    
    param([string]$Reason = "Manual enhanced restart")
    
    Write-Host "[ENHANCED] Starting enhanced Docker restart..." -ForegroundColor Yellow
    Write-Host "[ENHANCED] Reason: $Reason" -ForegroundColor Gray
    
    $enhancedRestartScript = Join-Path $PSScriptRoot "..\scripts\enhanced_docker_restart.ps1"
    
    if (Test-Path $enhancedRestartScript) {
        try {
            $restartArgs = @()
            if ($Force) { $restartArgs += "-Force" }
            if ($DeepCleanRestart) { $restartArgs += "-DeepClean" }
            if ($MemoryOptimizeRestart) { $restartArgs += "-MemoryOptimize" }
            
            Write-Host "[ENHANCED] Executing enhanced restart with args: $($restartArgs -join ' ')" -ForegroundColor Gray
            
            $process = Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$enhancedRestartScript`"", $restartArgs -Wait -PassThru
            
            if ($process.ExitCode -eq 0) {
                Write-Host "[ENHANCED] Enhanced Docker restart completed successfully" -ForegroundColor Green
                return $true
            } else {
                Write-Host "[ENHANCED] Enhanced Docker restart failed (exit code: $($process.ExitCode))" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "[ENHANCED] Enhanced restart failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "[ENHANCED] Enhanced restart script not found at $enhancedRestartScript" -ForegroundColor Yellow
        return $false
    }
}

function Show-EnhancedMonitoringStatus {
    <#
    .SYNOPSIS
    Show status of all enhanced monitoring components
    #>
    
    Write-Host "`n[ENHANCED] Enhanced Monitoring Status" -ForegroundColor Cyan
    Write-Host "[ENHANCED] ===========================" -ForegroundColor Cyan
    
    # Check monitoring jobs
    $enhancedJobs = Get-Job | Where-Object { $_.Name -match "Enhanced|Self-Health|System-Recovery|Escalation" }
    
    if ($enhancedJobs.Count -gt 0) {
        Write-Host "[ENHANCED] Active monitoring jobs: $($enhancedJobs.Count)" -ForegroundColor Green
        foreach ($job in $enhancedJobs) {
            $status = switch ($job.State) {
                "Running" { "RUNNING" }
                "Failed" { "FAILED" }
                "Stopped" { "STOPPED" }
                default { "$($job.State.ToUpper())" }
            }
            Write-Host "[ENHANCED]   $($job.Name): $status (ID: $($job.Id))" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ENHANCED] No enhanced monitoring jobs running" -ForegroundColor Yellow
    }
    
    # Check log files
    $logsDir = Join-Path $PSScriptRoot "..\logs"
    $enhancedLogs = @(
        "enhanced_monitor.log",
        "self_health_monitor.log", 
        "system_recovery.log",
        "escalation.log"
    )
    
    Write-Host "[ENHANCED]`nLog file status:" -ForegroundColor Gray
    foreach ($logFile in $enhancedLogs) {
        $logPath = Join-Path $logsDir $logFile
        if (Test-Path $logPath) {
            $file = Get-Item $logPath
            $timeSince = (Get-Date) - $file.LastWriteTime
            $status = if ($timeSince.TotalMinutes -lt 30) { "ACTIVE" } 
                     elseif ($timeSince.TotalMinutes -lt 120) { "RECENT" } 
                     else { "STALE" }
            Write-Host "[ENHANCED]   $logFile`: $status (Last: $($timeSince.TotalMinutes.ToString('F0'))m ago)" -ForegroundColor Gray
        } else {
            Write-Host "[ENHANCED]   $logFile`: NOT FOUND" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}
