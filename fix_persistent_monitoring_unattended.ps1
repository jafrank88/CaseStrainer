# Fix persistent monitoring to run without user login

Write-Host "=== Fixing Persistent Monitoring for Unattended Operation ===" -ForegroundColor Cyan

# Remove existing task
Write-Host "[INFO] Removing existing scheduled task..." -ForegroundColor Yellow
Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Create new task with SYSTEM account and startup trigger
Write-Host "[INFO] Creating new scheduled task with SYSTEM account..." -ForegroundColor Yellow

# Task action
$taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`""

# Multiple triggers for better reliability
$taskTrigger1 = New-ScheduledTaskTrigger -AtStartup
$taskTrigger1.Delay = "PT2M"  # Wait 2 minutes after startup

$taskTrigger2 = New-ScheduledTaskTrigger -AtLogOn -User "NT AUTHORITY\SYSTEM"

# Settings for unattended operation
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -DontStopOnIdleEnd -WakeToRun

# Principal with SYSTEM account for unattended access
$taskPrincipal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $taskAction -Trigger $taskTrigger1,$taskTrigger2 -Settings $taskSettings -Principal $taskPrincipal -Force | Out-Null

Write-Host "[OK] Scheduled task created with SYSTEM account" -ForegroundColor Green

# Start the task immediately
Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null
Start-Sleep -Seconds 3

# Verify it's running
$task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
if ($task.State -eq "Running") {
    Write-Host "[SUCCESS] Persistent monitoring is now running!" -ForegroundColor Green
    Write-Host "  - Runs at system startup (no login required)" -ForegroundColor Gray
    Write-Host "  - Uses SYSTEM account for unattended operation" -ForegroundColor Gray
    Write-Host "  - Has backup trigger at logon" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Failed to start monitoring task" -ForegroundColor Red
}

Write-Host "`n=== Verification ===" -ForegroundColor Cyan
Write-Host "Task details:" -ForegroundColor Gray
Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Select-Object TaskName, State, @{Name="Principal";Expression={$_.Principal.UserId}}, @{Name="LogonType";Expression={$_.Principal.LogonType}} | Format-Table -AutoSize

Write-Host "`nLogs location:" -ForegroundColor Gray
Write-Host "  - Daemon: logs\docker_daemon_monitor.log" -ForegroundColor Gray
Write-Host "  - Events: logs\docker_events.log" -ForegroundColor Gray

Write-Host "`nThe monitoring will now survive reboots and run without any user logged in!" -ForegroundColor Green
