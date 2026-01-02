function SetUnattendedMonitoring {
    Write-Host "[SETUP] Configuring unattended monitoring..." -ForegroundColor Yellow
    
    # Check if running as Administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "[WARN] Not running as Administrator. Scheduled task creation will fail." -ForegroundColor Yellow
        Write-Host "[INFO] To create scheduled tasks, run PowerShell as Administrator" -ForegroundColor Gray
    }
    
    # Remove existing monitoring task
    Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Always create logon task as backup
    Write-Host "[INFO] Creating logon backup task..." -ForegroundColor Gray
    
    # Remove existing logon task
    Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Create logon task
    try {
        $logonAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`"" -ErrorAction Stop
        $logonTrigger = New-ScheduledTaskTrigger -AtLogOn
        $logonSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $logonAction -Trigger $logonTrigger -Settings $logonSettings -RunLevel Highest -Force -ErrorAction Stop | Out-Null
        
        # Start the logon task
        Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction Stop | Out-Null
        Write-Host "[SUCCESS] Logon task created and started" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "[INFO] Monitoring will work only while cslaunch is running" -ForegroundColor Gray
    }
    
    # Summary
    Write-Host "`n[SUCCESS] Unattended monitoring configured!" -ForegroundColor Green
    Write-Host "Configuration:" -ForegroundColor Gray
    if ($isAdmin) {
        Write-Host "  Logon backup task: Starts when user logs in" -ForegroundColor Green
    } else {
        Write-Host "  Logon backup task: Failed (requires Administrator)" -ForegroundColor Yellow
        Write-Host "  Current session: Monitoring active while cslaunch runs" -ForegroundColor Yellow
    }
    Write-Host "  Monitoring: Checks Docker every 60 seconds" -ForegroundColor Gray
    Write-Host "  Auto-restart: Restarts Docker if it crashes" -ForegroundColor Gray
    Write-Host "`nLogs:" -ForegroundColor Gray
    Write-Host "  - Docker daemon: logs\docker_daemon_monitor.log" -ForegroundColor Gray
    Write-Host "  - Docker events: logs\docker_events.log" -ForegroundColor Gray
}

# Export the function
Export-ModuleMember -Function SetUnattendedMonitoring
