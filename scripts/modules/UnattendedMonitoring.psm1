# Setup unattended monitoring for CaseStrainer
# This creates monitoring that works without user login

function SetUnattendedMonitoring {
    Write-Host "[SETUP] Configuring unattended monitoring..." -ForegroundColor Yellow
    
    # Remove existing monitoring task
    Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Create startup script that includes monitoring
    $startupScript = @'
# Docker startup with monitoring
$scriptPath = "D:\dev\casestrainer"

# Start monitoring first
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath\persistent_monitor.ps1`"" -WindowStyle Hidden

# Start Docker Desktop if not running
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    $dockerPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerPath)) {
        $dockerPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    }
    if (Test-Path $dockerPath) {
        Start-Process -FilePath $dockerPath -WindowStyle Minimized
    }
}
'@
    
    # Save the startup script
    $startupScript | Out-File -FilePath "D:\dev\casestrainer\startup_with_monitoring.ps1" -Encoding UTF8 -Force
    
    # Try to create system-level startup task (requires admin)
    try {
        Write-Host "[INFO] Creating system startup task..." -ForegroundColor Gray
        
        # Remove existing startup task
        Get-ScheduledTask -TaskName "CaseStrainer-DockerStartup" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
        
        # Create new startup task
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\startup_with_monitoring.ps1`""
        $trigger = New-ScheduledTaskTrigger -AtStartup
        $trigger.Delay = "PT2M"  # Start 2 minutes after system startup
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd
        
        # Try with SYSTEM account first
        try {
            $principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
            Register-ScheduledTask -TaskName "CaseStrainer-DockerStartup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
            Write-Host "[SUCCESS] System startup task created (runs without login)" -ForegroundColor Green
            $systemTask = $true
        } catch {
            # Fallback to current user
            Write-Host "[WARN] Could not create system task (requires admin), using user task..." -ForegroundColor Yellow
            $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken -RunLevel Highest
            Register-ScheduledTask -TaskName "CaseStrainer-DockerStartup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
            Write-Host "[OK] User startup task created (requires login)" -ForegroundColor Yellow
            $systemTask = $false
        }
        
        # Start the task
        Start-ScheduledTask -TaskName "CaseStrainer-DockerStartup" | Out-Null
        
    } catch {
        Write-Host "[WARN] Failed to create startup task: $($_.Exception.Message)" -ForegroundColor Yellow
        $systemTask = $false
    }
    
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
    if ($systemTask) {
        Write-Host "  ✓ System startup task: Runs at boot without login" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ User startup task: Runs at boot (requires login)" -ForegroundColor Yellow
    }
    Write-Host "  ✓ Logon backup task: Starts when user logs in" -ForegroundColor Green
    Write-Host "  ✓ Monitoring: Checks Docker every 60 seconds" -ForegroundColor Gray
    Write-Host "  ✓ Auto-restart: Restarts Docker if it crashes" -ForegroundColor Gray
    Write-Host "`nLogs:" -ForegroundColor Gray
    Write-Host "  - Docker daemon: logs\docker_daemon_monitor.log" -ForegroundColor Gray
    Write-Host "  - Docker events: logs\docker_events.log" -ForegroundColor Gray
}

# Export the function
Export-ModuleMember -Function SetUnattendedMonitoring
