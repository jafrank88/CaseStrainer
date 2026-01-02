# Quick fix to add startup trigger to existing monitoring task

Write-Host "=== Adding Startup Trigger to Persistent Monitoring ===" -ForegroundColor Cyan

# Get current task
$task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
if (-not $task) {
    Write-Host "[ERROR] Task not found" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Current task configuration:" -ForegroundColor Gray
Write-Host "  Principal: $($task.Principal.UserId)" -ForegroundColor Gray
Write-Host "  LogonType: $($task.Principal.LogonType)" -ForegroundColor Gray

# Export current task definition
$taskDef = Export-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"

# Add startup trigger
$startupTrigger = New-ScheduledTaskTrigger -AtStartup
$startupTrigger.Delay = "PT2M"  # 2 minute delay after startup

# Add to existing triggers
$taskDef.Triggers += $startupTrigger

# Update settings to be more resilient
$taskDef.Settings.StartWhenAvailable = $true
$taskDef.Settings.RunOnlyIfNetworkAvailable = $false  # Don't require network for basic monitoring

# Unregister and re-register with new configuration
Write-Host "[INFO] Updating task with startup trigger..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Confirm:$false
Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -InputObject $taskDef -Force | Out-Null

# Start the task
Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null

# Verify
$updatedTask = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
Write-Host "`n[SUCCESS] Task updated!" -ForegroundColor Green
Write-Host "Triggers:" -ForegroundColor Gray
$updatedTask.Triggers | Select-Object @{Name="Type";Expression={$_.GetType().Name}}, Enabled, Delay | Format-Table -AutoSize

Write-Host "`nThe monitoring will now:" -ForegroundColor Cyan
Write-Host "  1. Start at system startup (2 min delay)" -ForegroundColor Gray
Write-Host "  2. Still start at user logon (backup)" -ForegroundColor Gray
Write-Host "  3. Run without network requirement" -ForegroundColor Gray
