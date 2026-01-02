# Create persistent monitoring that works without login

Write-Host "=== Creating Unattended Persistent Monitoring ===" -ForegroundColor Cyan

# Create the monitoring script if it doesn't exist
$monitorScript = "D:\dev\casestrainer\persistent_monitor.ps1"
if (-not (Test-Path $monitorScript)) {
    Write-Host "[INFO] Creating monitoring script..." -ForegroundColor Yellow
    & "D:\dev\casestrainer\install_persistent_monitoring.ps1"
}

# Create scheduled task with proper configuration
Write-Host "[INFO] Creating scheduled task for unattended operation..." -ForegroundColor Yellow

# Remove any existing task
Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Action
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$monitorScript`""

# Multiple triggers for reliability
$trigger1 = New-ScheduledTaskTrigger -AtStartup
$trigger1.Delay = "PT2M"  # 2 minutes after startup

$trigger2 = New-ScheduledTaskTrigger -AtLogOn -User "NT AUTHORITY\SYSTEM"

# Settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd -WakeToRun

# Principal - use SYSTEM account for unattended operation
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $action -Trigger $trigger1,$trigger2 -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "[OK] Task created successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to create task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[INFO] Trying with current user instead..." -ForegroundColor Yellow
    
    # Fallback: create with current user but add startup trigger
    $userPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken -RunLevel Highest
    Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $action -Trigger $trigger1 -Settings $settings -Principal $userPrincipal -Force | Out-Null
    Write-Host "[OK] Task created with current user (requires login)" -ForegroundColor Yellow
}

# Start the task
Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null
Start-Sleep -Seconds 3

# Verify
$task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
Write-Host "`n=== Task Configuration ===" -ForegroundColor Cyan
Write-Host "State: $($task.State)" -ForegroundColor Gray
Write-Host "Principal: $($task.Principal.UserId)" -ForegroundColor Gray
Write-Host "LogonType: $($task.Principal.LogonType)" -ForegroundColor Gray
Write-Host "Triggers:" -ForegroundColor Gray
for ($i = 0; $i -lt $task.Triggers.Count; $i++) {
    $trigger = $task.Triggers[$i]
    $type = $trigger.GetType().Name
    $delay = if ($trigger.Delay) { $trigger.Delay } else { "None" }
    Write-Host "  - $type (Delay: $delay)" -ForegroundColor Gray
}

Write-Host "`n[SUCCESS] Persistent monitoring is configured!" -ForegroundColor Green
if ($task.Principal.UserId -eq "NT AUTHORITY\SYSTEM") {
    Write-Host "✓ Will run at system startup without login" -ForegroundColor Green
} else {
    Write-Host "⚠ Will run when user logs in (SYSTEM account requires admin)" -ForegroundColor Yellow
}
