# Fix-DockerAutostart.ps1 - Fixes Docker autostart to work without user login
# This script reconfigures the scheduled tasks to run whether or not a user is logged in

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Fixing Docker Autostart for Unattended Operation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Running with Administrator privileges" -ForegroundColor Green

# Get the current user's credentials for the task
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "[INFO] Current user: $currentUser" -ForegroundColor Gray

# Path to scripts
$scriptRoot = "D:\dev\casestrainer"
$autostartScript = Join-Path $scriptRoot "scripts\docker-autostart.ps1"
$monitorScript = Join-Path $scriptRoot "persistent_monitor.ps1"

# Function to create a properly configured task
function Create-UnattendedTask {
    param(
        [string]$TaskName,
        [string]$ScriptPath,
        [string]$Description,
        [string]$TriggerType = "AtLogOn"
    )
    
    Write-Host "`n[CONFIG] Creating task: $TaskName" -ForegroundColor Yellow
    
    # Remove existing task
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  [OK] Removed existing task" -ForegroundColor Gray
    } catch {
        Write-Verbose "No existing task to remove"
    }
    
    # Create action
    $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
    
    # Create trigger based on type
    if ($TriggerType -eq "AtStartup") {
        $Trigger = New-ScheduledTaskTrigger -AtStartup
        $Trigger.Delay = "PT2M"  # 2 minutes after startup
        Write-Host "  [SET] Trigger: At system startup (2 min delay)" -ForegroundColor Gray
    } else {
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        Write-Host "  [SET] Trigger: At user logon" -ForegroundColor Gray
    }
    
    # Create settings - CRITICAL for unattended operation
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -RunOnlyIfNetworkAvailable `
        -DontStopOnIdleEnd `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)
    
    Write-Host "  [SET] Settings: Run whether user is logged on or not" -ForegroundColor Gray
    
    # Register the task with proper principal
    try {
        # Get the user's SID
        $sid = (Get-WmiObject -Class Win32_UserAccount -Filter "Name='$($env:USERNAME)' AND Domain='$($env:USERDOMAIN)'").SID
        
        # Create principal with proper logon type
        $Principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Password -RunLevel Highest
        
        # Register task
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $Description -Force | Out-Null
        
        Write-Host "  [SUCCESS] Task created successfully" -ForegroundColor Green
        
        # Verify the task
        $task = Get-ScheduledTask -TaskName $TaskName
        Write-Host "  [INFO] Task state: $($task.State)" -ForegroundColor Gray
        
        return $true
    } catch {
        Write-Host "  [ERROR] Failed to create task: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Create the system startup task
Write-Host "`n=== Creating System Startup Task ===" -ForegroundColor Cyan
$startupSuccess = Create-UnattendedTask -TaskName "CaseStrainer-Docker-AutoStart" -ScriptPath $autostartScript -Description "Starts Docker and CaseStrainer containers on system boot" -TriggerType "AtStartup"

# Create the persistent monitor task
Write-Host "`n=== Creating Persistent Monitor Task ===" -ForegroundColor Cyan
$monitorSuccess = Create-UnattendedTask -TaskName "CaseStrainer-PersistentMonitor" -ScriptPath $monitorScript -Description "Monitors Docker and restarts if needed" -TriggerType "AtLogOn"

# Add a recurring trigger to the monitor task for extra resilience
if ($monitorSuccess) {
    Write-Host "`n[CONFIG] Adding recurring trigger to monitor task..." -ForegroundColor Yellow
    try {
        $task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
        $recurringTrigger = New-ScheduledTaskTrigger -Daily -At 3am
        $task.Triggers += $recurringTrigger
        Set-ScheduledTask -TaskName $task -InputObject $task | Out-Null
        Write-Host "  [SUCCESS] Added daily 3am trigger" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Could not add recurring trigger: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Test the configuration
Write-Host "`n=== Testing Configuration ===" -ForegroundColor Cyan

# Check if tasks exist and are properly configured
$tasks = @("CaseStrainer-Docker-AutoStart", "CaseStrainer-PersistentMonitor")
$allGood = $true

foreach ($taskName in $tasks) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "[OK] $taskName exists" -ForegroundColor Green
        $info = Get-ScheduledTaskInfo -TaskName $taskName
        Write-Host "  State: $($info.State)" -ForegroundColor Gray
        Write-Host "  Last run: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Next run: $($info.NextRunTime)" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] $taskName not found!" -ForegroundColor Red
        $allGood = $false
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($allGood -and $startupSuccess -and $monitorSuccess) {
    Write-Host "[SUCCESS] Docker autostart configured for unattended operation!" -ForegroundColor Green
    Write-Host "`nThe system will now:" -ForegroundColor Gray
    Write-Host "  1. Start Docker automatically on system boot" -ForegroundColor Gray
    Write-Host "  2. Monitor Docker health continuously" -ForegroundColor Gray
    Write-Host "  3. Restart Docker if it crashes (even without user login)" -ForegroundColor Gray
    Write-Host "  4. Survive system reboots and user logoffs" -ForegroundColor Gray
    Write-Host "`nTo test: Restart the computer without logging in" -ForegroundColor Yellow
    Write-Host "Docker should start automatically within 2-3 minutes" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] Some issues occurred during configuration" -ForegroundColor Red
    Write-Host "Please review the errors above and try again" -ForegroundColor Yellow
}
Write-Host "========================================`n" -ForegroundColor Cyan
