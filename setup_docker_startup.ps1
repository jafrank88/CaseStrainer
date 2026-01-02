# Simple fix: Add monitoring to cslaunch startup

Write-Host "=== Adding Monitoring to Docker Startup ===" -ForegroundColor Cyan

# Create a startup script that starts monitoring
$startupScript = @'
# Docker startup with monitoring
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`"" -WindowStyle Hidden

# Start Docker Desktop
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to start
Write-Host "Waiting for Docker to start..." -ForegroundColor Yellow
$timeout = 300  # 5 minutes
$elapsed = 0

while ($elapsed -lt $timeout) {
    $null = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is ready!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "." -NoNewline
}

if ($elapsed -ge $timeout) {
    Write-Host "`nDocker failed to start within 5 minutes" -ForegroundColor Red
} else {
    # Start CaseStrainer containers
    Write-Host "Starting CaseStrainer containers..." -ForegroundColor Yellow
    & "D:\dev\casestrainer\cslaunch.bat"
}
'@

# Save the startup script
$startupScript | Out-File -FilePath "D:\dev\casestrainer\start_docker_with_monitoring.ps1" -Encoding UTF8 -Force
Write-Host "[OK] Created startup script" -ForegroundColor Green

# Create a scheduled task to run at startup
Write-Host "[INFO] Creating startup task..." -ForegroundColor Yellow

# Remove existing task
Get-ScheduledTask -TaskName "CaseStrainer-DockerStartup" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Create new task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\start_docker_with_monitoring.ps1`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT1M"  # Start 1 minute after system startup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Register-ScheduledTask -TaskName "CaseStrainer-DockerStartup" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
    Write-Host "[SUCCESS] Startup task created!" -ForegroundColor Green
    Write-Host "This will:" -ForegroundColor Gray
    Write-Host "  1. Start monitoring when system boots" -ForegroundColor Gray
    Write-Host "  2. Start Docker Desktop" -ForegroundColor Gray
    Write-Host "  3. Start CaseStrainer containers" -ForegroundColor Gray
    Write-Host "  4. Run without requiring user login" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to create startup task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You need to run this script as Administrator" -ForegroundColor Yellow
}

# Also create a logon task as backup
Write-Host "`n[INFO] Creating backup logon task..." -ForegroundColor Yellow
$logonAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`""
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn
$logonSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Register-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -Action $logonAction -Trigger $logonTrigger -Settings $logonSettings -RunLevel Highest -Force | Out-Null
    Write-Host "[OK] Logon task created as backup" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to create logon task" -ForegroundColor Red
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "1. Primary: CaseStrainer-DockerStartup (runs at system startup)" -ForegroundColor Gray
Write-Host "2. Backup: CaseStrainer-PersistentMonitor (runs at user logon)" -ForegroundColor Gray
Write-Host "`nThis ensures Docker and monitoring start even without login!" -ForegroundColor Green
