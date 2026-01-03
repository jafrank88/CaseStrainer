# Docker Cleanup Scheduler
# Creates a scheduled task for weekly Docker cleanup

param(
    [Parameter()]
    [switch]$Remove
)

$TaskName = "CaseStrainer-Docker-WeeklyCleanup"
$ScriptPath = Join-Path $PSScriptRoot "cslaunch.ps1"
$LogPath = Join-Path $PSScriptRoot "logs\cleanup_scheduler.log"

function Write-CleanupLog {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Write-Host $logEntry
    
    # Ensure log directory exists
    $logDir = Split-Path $LogPath -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    Add-Content -Path $LogPath -Value $logEntry
}

function Install-CleanupTask {
    Write-CleanupLog "Installing weekly Docker cleanup task..."
    
    try {
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-CleanupLog "Task already exists - updating..." "WARN"
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
        
        # Create the task action
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -CleanupDocker"
        
        # Create the trigger (weekly on Sunday at 2 AM)
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
        
        # Create the settings
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        # Register the task
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM" -Force
        
        Write-CleanupLog "Successfully installed weekly cleanup task" "SUCCESS"
        Write-Host "  - Task will run every Sunday at 2:00 AM" -ForegroundColor Gray
        Write-Host "  - Logs will be written to: logs\docker_cleanup.log" -ForegroundColor Gray
        
    } catch {
        Write-CleanupLog "Failed to install cleanup task: $($_.Exception.Message)" "ERROR"
        return $false
    }
    
    return $true
}

function Remove-CleanupTask {
    Write-CleanupLog "Removing weekly Docker cleanup task..."
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-CleanupLog "Successfully removed cleanup task" "SUCCESS"
        } else {
            Write-CleanupLog "Cleanup task not found" "WARN"
        }
    } catch {
        Write-CleanupLog "Failed to remove cleanup task: $($_.Exception.Message)" "ERROR"
        return $false
    }
    
    return $true
}

# Main execution
if ($Remove) {
    Remove-CleanupTask
} else {
    Install-CleanupTask
}
