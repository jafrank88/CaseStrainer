# Setup Docker Watchdog as a Windows Scheduled Task
# Run this script as Administrator to install the watchdog service

$TaskName = "CaseStrainer-Docker-Watchdog"
$ScriptPath = "d:\dev\casestrainer\docker-watchdog.ps1"
$LogPath = "d:\dev\casestrainer\logs"

# Ensure logs directory exists
if (-not (Test-Path $LogPath)) {
    New-Item -Path $LogPath -ItemType Directory -Force | Out-Null
    Write-Host "Created logs directory: $LogPath"
}

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run this script again."
    exit 1
}

Write-Host "Setting up Docker Watchdog Scheduled Task..." -ForegroundColor Cyan

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Create trigger - start at system startup and run indefinitely
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings - run whether user is logged on or not, restart on failure
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Create principal - run with highest privileges as SYSTEM
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Monitors and auto-restarts CaseStrainer Docker containers when they go down" | Out-Null

Write-Host "`n✓ Scheduled Task created successfully!" -ForegroundColor Green
Write-Host "`nTask Details:" -ForegroundColor Cyan
Write-Host "  Name: $TaskName"
Write-Host "  Script: $ScriptPath"
Write-Host "  Log File: $LogPath\docker-watchdog.log"
Write-Host "  Trigger: At system startup"
Write-Host "  Run As: SYSTEM account"
Write-Host "`nThe watchdog will:" -ForegroundColor Yellow
Write-Host "  • Start automatically when Windows boots"
Write-Host "  • Check container health every 60 seconds"
Write-Host "  • Auto-restart containers if they're down"
Write-Host "  • Log all actions to docker-watchdog.log"

Write-Host "`n=== Starting Watchdog Now ===" -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2

# Check if task is running
$task = Get-ScheduledTask -TaskName $TaskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Task Status: $($task.State)" -ForegroundColor Green
Write-Host "Last Run: $($taskInfo.LastRunTime)"
Write-Host "Next Run: $($taskInfo.NextRunTime)"

Write-Host "`n=== Management Commands ===" -ForegroundColor Cyan
Write-Host "View logs:        Get-Content '$LogPath\docker-watchdog.log' -Tail 50 -Wait"
Write-Host "Stop watchdog:    Stop-ScheduledTask -TaskName '$TaskName'"
Write-Host "Start watchdog:   Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Remove watchdog:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host "Task status:      Get-ScheduledTask -TaskName '$TaskName' | Select-Object TaskName,State"

Write-Host "`n✓ Setup complete! Watchdog is now monitoring your containers." -ForegroundColor Green
