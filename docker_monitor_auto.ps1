# Docker Auto-Monitor with Deep Diagnostics and Auto-Recovery
# Designed to run as a scheduled task to prevent Docker unresponsiveness

param(
    [switch]$InstallScheduledTask,
    [switch]$RemoveScheduledTask,
    [switch]$TestMode,
    [int]$CheckIntervalMinutes = 5
)

function Install-DockerMonitoringTask {
    """Install a scheduled task to run Docker health monitoring."""
    
    Write-Host "📅 Installing Docker monitoring scheduled task..." -ForegroundColor Cyan
    
    $taskName = "DockerHealthMonitor"
    $scriptPath = (Get-Location).Path + "\docker_health_check.ps1"
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -AutoRestart -DeepDiagnostics"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $CheckIntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Docker Health Monitor - Prevents Docker unresponsiveness" -Force
        Write-Host "✅ Scheduled task installed successfully!" -ForegroundColor Green
        Write-Host "   Task Name: $taskName" -ForegroundColor Gray
        Write-Host "   Check Interval: $CheckIntervalMinutes minutes" -ForegroundColor Gray
        Write-Host "   Script: $scriptPath" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Failed to install scheduled task: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}

function Remove-DockerMonitoringTask {
    """Remove the Docker monitoring scheduled task."""
    
    Write-Host "🗑️ Removing Docker monitoring scheduled task..." -ForegroundColor Cyan
    
    $taskName = "DockerHealthMonitor"
    
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "✅ Scheduled task removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to remove scheduled task: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}

function Start-ContinuousMonitoring {
    """Run continuous monitoring with auto-recovery."""
    
    Write-Host "🔄 Starting continuous Docker monitoring..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    
    $checkCount = 0
    $lastRecoveryTime = $null
    
    while ($true) {
        $checkCount++
        $currentTime = Get-Date -Format "HH:mm:ss"
        
        Write-Host "`n[${currentTime}] Check #$checkCount" -ForegroundColor Gray
        
        # Run health check with auto-recovery
        $healthResults = & .\docker_health_check.ps1 -AutoRestart -DeepDiagnostics
        
        # Check if recovery was needed
        if ($healthResults.RecoveryNeeded -and $healthResults.Healthy) {
            $lastRecoveryTime = Get-Date
            Write-Host "🔄 Auto-recovery completed at $($lastRecoveryTime.ToString('HH:mm:ss'))" -ForegroundColor Green
            
            # Log the recovery
            $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): Auto-recovery completed successfully"
            Add-Content -Path "logs\docker_recovery.log" -Value $logEntry
        }
        
        # Show status
        if ($healthResults.Healthy) {
            Write-Host "✅ Docker is healthy" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker has issues: $($healthResults.Issues -join ', ')" -ForegroundColor Red
        }
        
        # Wait before next check
        Write-Host "⏳ Waiting $CheckIntervalMinutes minutes before next check..." -ForegroundColor Gray
        Start-Sleep -Seconds ($CheckIntervalMinutes * 60)
    }
}

function Show-MonitoringStatus {
    """Show the current status of Docker monitoring."""
    
    Write-Host "📊 Docker Monitoring Status" -ForegroundColor Cyan
    
    # Check if scheduled task exists
    $taskName = "DockerHealthMonitor"
    $scheduledTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($scheduledTask) {
        Write-Host "✅ Scheduled task is installed" -ForegroundColor Green
        Write-Host "   Task Name: $($scheduledTask.TaskName)" -ForegroundColor Gray
        Write-Host "   State: $($scheduledTask.State)" -ForegroundColor Gray
        Write-Host "   Last Run: $($scheduledTask.LastRunTime)" -ForegroundColor Gray
        Write-Host "   Next Run: $($scheduledTask.NextRunTime)" -ForegroundColor Gray
    } else {
        Write-Host "❌ No scheduled task found" -ForegroundColor Red
    }
    
    # Check recent recovery logs
    $recoveryLogPath = "logs\docker_recovery.log"
    if (Test-Path $recoveryLogPath) {
        $recentRecoveries = Get-Content $recoveryLogPath -Tail 5
        if ($recentRecoveries) {
            Write-Host "`n📋 Recent Auto-Recoveries:" -ForegroundColor Cyan
            $recentRecoveries | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }
    }
    
    # Run a quick health check
    Write-Host "`n🔍 Current Docker Health:" -ForegroundColor Cyan
    & .\docker_health_check.ps1
}

# Main execution
if ($InstallScheduledTask) {
    Install-DockerMonitoringTask
} elseif ($RemoveScheduledTask) {
    Remove-DockerMonitoringTask
} elseif ($TestMode) {
    Start-ContinuousMonitoring
} else {
    Show-MonitoringStatus
} 