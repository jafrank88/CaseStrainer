#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Setup automatic weekly Redis maintenance for CaseStrainer
    
.DESCRIPTION
    Creates a Windows Task Scheduler task that runs Redis maintenance
    every Sunday at 2:00 AM to prevent AOF bloat.
    
.EXAMPLE
    .\setup_automatic_maintenance.ps1
#>

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Automatic Redis Maintenance" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get the full path to the maintenance script
$maintenanceScript = Join-Path $PSScriptRoot 'scripts\redis_maintenance.ps1'

if (-not (Test-Path $maintenanceScript)) {
    Write-Host "[ERROR] Maintenance script not found at: $maintenanceScript" -ForegroundColor Red
    Write-Host "  Make sure you're running this from the CaseStrainer directory" -ForegroundColor Yellow
    exit 1
}

$fullPath = Resolve-Path $maintenanceScript

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Task Name: CaseStrainer Redis Maintenance" -ForegroundColor Gray
Write-Host "   Schedule: Every Sunday at 2:00 AM" -ForegroundColor Gray
Write-Host "   Script: $fullPath" -ForegroundColor Gray
Write-Host "   Mode: Force (no prompts)" -ForegroundColor Gray

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName "CaseStrainer Redis Maintenance" -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "`n⚠️  Task already exists!" -ForegroundColor Yellow
    $response = Read-Host "Remove and recreate? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "`n[REMOVING] Existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName "CaseStrainer Redis Maintenance" -Confirm:$false
        Write-Host "  ✅ Removed existing task" -ForegroundColor Green
    } else {
        Write-Host "`n[CANCELLED] Keeping existing task" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "`n[CREATING] Scheduled task..." -ForegroundColor Yellow

try {
    # Create the action
    $action = New-ScheduledTaskAction `
        -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$fullPath`" -Force" `
        -WorkingDirectory $PSScriptRoot
    
    # Create the trigger (Sunday at 2 AM)
    $trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Sunday `
        -At 2am
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    
    # Register the task
    $task = Register-ScheduledTask `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -TaskName "CaseStrainer Redis Maintenance" `
        -Description "Weekly Redis cleanup to prevent bloat and maintain fast startup times" `
        -User $env:USERNAME `
        -RunLevel Highest
    
    Write-Host "  ✅ Task created successfully!" -ForegroundColor Green
    
    # Display task info
    Write-Host "`n📊 Task Details:" -ForegroundColor Cyan
    Write-Host "   Status: $($task.State)" -ForegroundColor Gray
    Write-Host "   Next Run: $(Get-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance' | Get-ScheduledTaskInfo | Select-Object -ExpandProperty NextRunTime)" -ForegroundColor Gray
    Write-Host "   Last Result: $(Get-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance' | Get-ScheduledTaskInfo | Select-Object -ExpandProperty LastTaskResult)" -ForegroundColor Gray
    
} catch {
    Write-Host "  ❌ Failed to create task: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n📅 Automatic Maintenance Schedule:" -ForegroundColor Yellow
Write-Host "   Every Sunday at 2:00 AM" -ForegroundColor Gray
Write-Host "   Will clean old jobs and compact Redis AOF" -ForegroundColor Gray
Write-Host "   Runs automatically in background" -ForegroundColor Gray

Write-Host "`n🔧 To manage the task:" -ForegroundColor Yellow
Write-Host "   View: Get-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance'" -ForegroundColor Gray
Write-Host "   Run now: Start-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance'" -ForegroundColor Gray
Write-Host "   Disable: Disable-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance'" -ForegroundColor Gray
Write-Host "   Remove: Unregister-ScheduledTask -TaskName 'CaseStrainer Redis Maintenance'" -ForegroundColor Gray

Write-Host "`n💡 You can also view/manage in Task Scheduler (taskschd.msc)" -ForegroundColor Cyan
Write-Host "`n"
