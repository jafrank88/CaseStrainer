# Create a persistent monitoring solution using scheduled tasks

Write-Host "=== Creating Persistent Monitoring ===" -ForegroundColor Cyan

# Remove existing jobs first
Get-Job | Where-Object { $_.Name -like "*Monitor*" -or $_.Name -like "*Docker*" } | Remove-Job -Force -ErrorAction SilentlyContinue

# Create scheduled task for monitoring
$taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\cslaunch.ps1`" -Monitor"
$taskTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register the monitoring task
Register-ScheduledTask -TaskName "CaseStrainer-Monitor" -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -RunLevel Highest -Force | Out-Null

Write-Host "[OK] Created persistent monitoring task" -ForegroundColor Green
Write-Host "  - Runs every 5 minutes" -ForegroundColor Gray
Write-Host "  - Survives reboots" -ForegroundColor Gray
Write-Host "  - View with: Get-ScheduledTask CaseStrainer-Monitor" -ForegroundColor Gray

# Start the task immediately
Start-ScheduledTask -TaskName "CaseStrainer-Monitor" | Out-Null
Write-Host "[OK] Monitoring started" -ForegroundColor Green
