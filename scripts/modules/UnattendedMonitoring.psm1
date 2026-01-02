function SetUnattendedMonitoring {
    Write-Host "[SETUP] Configuring unattended monitoring..." -ForegroundColor Yellow
    
    # Remove existing monitoring task
    Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Always create logon task as backup
    Write-Host "[INFO] Creating logon backup task..." -ForegroundColor Gray
    
    # Remove existing logon task
    Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Create logon task
    $logonAction = New-ScheduledTaskAction -Execute "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`""
    $logonTrigger = New-ScheduledTaskTrigger -AtLogOn
    $logonSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $logonAction -Trigger $logonTrigger -Settings $logonSettings -RunLevel Highest -Force | Out-Null
    
    # Start the logon task
    Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null
    
    # Summary
    Write-Host "`n[SUCCESS] Unattended monitoring configured!" -ForegroundColor Green
    Write-Host "Configuration:" -ForegroundColor Gray
    Write-Host "  Logon backup task: Starts when user logs in" -ForegroundColor Green
    Write-Host "  Monitoring: Checks Docker every 60 seconds" -ForegroundColor Gray
    Write-Host "  Auto-restart: Restarts Docker if it crashes" -ForegroundColor Gray
    Write-Host "`nLogs:" -ForegroundColor Gray
    Write-Host "  - Docker daemon: logs\docker_daemon_monitor.log" -ForegroundColor Gray
    Write-Host "  - Docker events: logs\docker_events.log" -ForegroundColor Gray
}

# Export the function
Export-ModuleMember -Function SetUnattendedMonitoring
