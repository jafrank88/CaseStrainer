# monitoring_watchdog.ps1
# This script ensures the Docker monitoring service stays running and can recover from failures
# It should be set up to run at system startup or as a scheduled task

[CmdletBinding()]
param(
    [string]$ScriptRoot = $PSScriptRoot,
    [int]$CheckInterval = 30,  # How often to check if the monitor is running (seconds)
    [int]$MaxRestartsPerHour = 5,  # Maximum number of restarts to attempt per hour
    [string]$LogFile = "$ScriptRoot\logs\watchdog.log"
)

# Create logs directory if it doesn't exist
$logsDir = Split-Path -Parent $LogFile
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Function to write to log file
function Write-WatchdogLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    try {
        Add-Content -Path $LogFile -Value $logMessage -ErrorAction Stop
    } catch {
        Write-Error "Failed to write to watchdog log: $_"
    }
    
    # Also write to console when running interactively
    if ($Host.Name -eq "ConsoleHost") {
        $color = switch ($Level) {
            "ERROR" { "Red" }
            "WARN"  { "Yellow" }
            "DEBUG" { "Gray" }
            default { "White" }
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

# Track restart attempts
$restartHistory = [System.Collections.Generic.List[DateTime]]::new()
$monitorProcess = $null
$script:lastMonitorStart = $null

# Function to start the monitoring service
function Start-MonitoringService {
    param(
        [string]$ScriptPath = "$ScriptRoot\cslaunch.ps1"
    )
    
    try {
        Write-WatchdogLog "Starting monitoring service..."
        
        # Clean up any existing monitor jobs
        Get-Job -Name "CaseStrainer-Monitor" -ErrorAction SilentlyContinue | Remove-Job -Force
        
        # Start the monitoring service in a new job
        $script:lastMonitorStart = Get-Date
        $job = Start-Job -Name "CaseStrainer-Monitor" -ScriptBlock {
            param($ScriptPath)
            & $ScriptPath -Monitor
        } -ArgumentList $ScriptPath
        
        Write-WatchdogLog "Monitoring service started (Job ID: $($job.Id))"
        return $true
    } catch {
        $errorMsg = $_.Exception.Message
        Write-WatchdogLog "Failed to start monitoring service: $errorMsg" -Level "ERROR"
        Write-WatchdogLog $_.ScriptStackTrace -Level "DEBUG"
        return $false
    }
}

# Function to check if the monitoring service is healthy
function Test-MonitoringServiceHealth {
    $job = Get-Job -Name "CaseStrainer-Monitor" -ErrorAction SilentlyContinue
    
    if (-not $job) {
        Write-WatchdogLog "Monitoring job not found" -Level "WARN"
        return $false
    }
    
    if ($job.State -ne "Running") {
        Write-WatchdogLog "Monitoring job is not running (State: $($job.State))" -Level "WARN"
        return $false
    }
    
    # Check if the job has any errors
    $hasErrors = $job.ChildJobs | Where-Object { $_.HasMoreData -and $null -ne $_.Error } | Select-Object -First 1
    if ($hasErrors) {
        $errors = $hasErrors.Error | ForEach-Object { $_.ToString() }
        Write-WatchdogLog "Monitoring job has errors: $errors" -Level "ERROR"
        return $false
    }
    
    # Check if the job has been running for too long without activity
    if ($script:lastMonitorStart -and ((Get-Date) - $script:lastMonitorStart).TotalHours -gt 24) {
        Write-WatchdogLog "Monitoring job has been running for more than 24 hours, restarting..." -Level "WARN"
        return $false
    }
    
    return $true
}

# Function to check if we've restarted too many times recently
function Test-RestartLimitReached {
    param(
        [int]$MaxRestarts = 5,
        [int]$TimeWindowHours = 1
    )
    
    # Remove old restart times (older than TimeWindowHours)
    $cutoffTime = (Get-Date).AddHours(-$TimeWindowHours)
    $restartHistory.RemoveAll({ param($d) $d -lt $cutoffTime })
    
    # Check if we've exceeded the restart limit
    if ($restartHistory.Count -ge $MaxRestarts) {
        $nextAllowed = $restartHistory[0].AddHours($TimeWindowHours)
        $timeLeft = $nextAllowed - (Get-Date)
        $minutesLeft = [math]::Ceiling($timeLeft.TotalMinutes)
        
        if ($minutesLeft -gt 0) {
            Write-WatchdogLog "Restart limit reached. Next restart allowed in $minutesLeft minutes" -Level "WARN"
            return $true
        } else {
            # Reset the restart history if the time window has passed
            $restartHistory.Clear()
        }
    }
    
    return $false
}

# Main watchdog loop
Write-WatchdogLog "========================================"
Write-WatchdogLog "CaseStrainer Monitoring Watchdog Starting"
Write-WatchdogLog "========================================"
Write-WatchdogLog "Script Root: $ScriptRoot"
Write-WatchdogLog "Log File: $LogFile"
Write-WatchdogLog "Check Interval: $CheckInterval seconds"
Write-WatchdogLog "Max Restarts Per Hour: $MaxRestartsPerHour"

# Start the monitoring service initially
$monitorStarted = Start-MonitoringService
if (-not $monitorStarted) {
    Write-WatchdogLog "Failed to start monitoring service initially. Will retry..." -Level "ERROR"
}

try {
    while ($true) {
        $isHealthy = Test-MonitoringServiceHealth
        
        if (-not $isHealthy) {
            if (Test-RestartLimitReached -MaxRestarts $MaxRestartsPerHour) {
                # We've restarted too many times, wait before trying again
                Start-Sleep -Seconds $CheckInterval
                continue
            }
            
            # Stop any existing monitor job
            Get-Job -Name "CaseStrainer-Monitor" -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
            
            # Record the restart attempt
            $restartHistory.Add((Get-Date))
            
            # Start the monitoring service
            $monitorStarted = Start-MonitoringService
            
            if (-not $monitorStarted) {
                Write-WatchdogLog "Failed to restart monitoring service. Will retry in $CheckInterval seconds..." -Level "ERROR"
            }
        }
        
        # Wait before the next check
        Start-Sleep -Seconds $CheckInterval
    }
} catch {
    $errorMsg = $_.Exception.Message
    Write-WatchdogLog "Fatal error in watchdog: $errorMsg" -Level "ERROR"
    Write-WatchdogLog $_.ScriptStackTrace -Level "DEBUG"
    
    # Try to restart the watchdog service
    Write-WatchdogLog "Attempting to restart watchdog..." -Level "WARN"
    Start-Sleep -Seconds 10
    & "$PSCommandPath" @PSBoundParameters
}
finally {
    # Clean up before exiting
    Write-WatchdogLog "Watchdog is stopping. Cleaning up..."
    Get-Job -Name "CaseStrainer-Monitor" -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
    Write-WatchdogLog "Watchdog has stopped"
}
