# Apply Nginx Configuration Changes Script
# This script will verify and apply the Nginx configuration changes

# Stop any running Nginx processes
Write-Host "Stopping any running Nginx processes..."
Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force

# Verify Nginx configuration
Write-Host "Verifying Nginx configuration..."
$configTest = & nginx -t -c "$PWD\nginx.production.conf" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Nginx configuration test failed:" -ForegroundColor Red
    Write-Host $configTest -ForegroundColor Red
    exit 1
}

# Backup current Nginx configuration
$backupDir = "$PWD\nginx_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir | Out-Null
Copy-Item "$PWD\nginx.production.conf" -Destination "$backupDir\nginx.production.conf.bak"
Write-Host "✅ Current configuration backed up to $backupDir" -ForegroundColor Green

# Copy the new configuration
Copy-Item "$PWD\nginx.production.conf" -Destination "C:\nginx\conf\nginx.conf" -Force

# Start Nginx
Write-Host "Starting Nginx..."
Start-Process -FilePath "C:\nginx\nginx.exe" -ArgumentList "-c `"C:\nginx\conf\nginx.conf`"

# Verify Nginx is running
Start-Sleep -Seconds 2
$nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue

if ($nginxProcess) {
    Write-Host "✅ Nginx started successfully" -ForegroundColor Green
    
    # Test the health endpoint
    Write-Host "`nTesting health endpoint..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost/health" -Method Get -TimeoutSec 10 -ErrorAction Stop
        Write-Host "✅ Health check successful:" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    }
    
    # Test the API endpoint
    Write-Host "`nTesting API endpoint..."
    try {
        $testPayload = @{
            text = "See Roe v. Wade, 410 U.S. 113 (1973)"
            options = @{
                include_context = $true
                verify_citations = $true
            }
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost/casestrainer/api/analyze" `
            -Method Post `
            -Body $testPayload `
            -ContentType "application/json" `
            -TimeoutSec 30 `
            -ErrorAction Stop
            
        Write-Host "✅ API test successful:" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Cyan
    } catch {
        Write-Host "❌ API test failed: $_" -ForegroundColor Red
        Write-Host "Response: $($_.Exception.Response.StatusCode.value__) - $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to start Nginx" -ForegroundColor Red
    exit 1
}

# Set up log rotation (Windows Task Scheduler)
Write-Host "`nSetting up log rotation..."
$logrotateScript = @'
# Log rotation script for Nginx on Windows
$logDir = "C:\nginx\logs"
$maxLogAge = 30 # days

Get-ChildItem -Path $logDir -Filter "*.log.*" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-$maxLogAge)
} | Remove-Item -Force -ErrorAction SilentlyContinue

# Reopen Nginx logs
& nginx -s reopen
'@

$logrotateScriptPath = "$PWD\nginx_logrotate.ps1"
Set-Content -Path $logrotateScriptPath -Value $logrotateScript

# Create scheduled task for log rotation
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$logrotateScriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName "NginxLogRotation" -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask `
    -TaskName "NginxLogRotation" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Write-Host "✅ Log rotation scheduled task created" -ForegroundColor Green

# Set up monitoring script
Write-Host "`nSetting up monitoring..."
$monitorScript = @'
# Monitoring script for CaseStrainer services
$services = @(
    @{Name="Nginx"; ProcessName="nginx"; Port=80},
    @{Name="Flask API"; ProcessName="python"; Port=5000}
)

$alerts = @()

# Check services
foreach ($service in $services) {
    $process = Get-Process -Name $service.ProcessName -ErrorAction SilentlyContinue
    $portTest = Test-NetConnection -ComputerName localhost -Port $service.Port -InformationLevel Quiet
    
    if (-not $process) {
        $alerts += "❌ $($service.Name) process is not running"
    } elseif (-not $portTest) {
        $alerts += "❌ $($service.Name) is not responding on port $($service.Port)"
    } else {
        Write-Host "✅ $($service.Name) is running and responding" -ForegroundColor Green
    }
}

# Check disk space
$disk = Get-PSDrive C | Select-Object Used,Free
$diskPercentFree = [math]::Round(($disk.Free / ($disk.Used + $disk.Free)) * 100, 2)
if ($diskPercentFree -lt 10) {
    $alerts += "⚠️  Low disk space: $diskPercentFree% free"
} else {
    Write-Host "✅ Disk space OK: $diskPercentFree% free" -ForegroundColor Green
}

# Send alerts if any
if ($alerts.Count -gt 0) {
    $body = $alerts -join "`n"
    Write-Host "`n=== ALERTS ===" -ForegroundColor Red
    Write-Host $body -ForegroundColor Red
    
    # Here you could add email notification logic
    # Send-MailMessage -To "admin@example.com" -From "monitor@example.com" -Subject "CaseStrainer Alert" -Body $body -SmtpServer "smtp.example.com"
}
'@

$monitorScriptPath = "$PWD\monitor_services.ps1"
Set-Content -Path $monitorScriptPath -Value $monitorScript

# Create scheduled task for monitoring
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$monitorScriptPath`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 15)
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName "CaseStrainerMonitor" -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask `
    -TaskName "CaseStrainerMonitor" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Write-Host "✅ Monitoring scheduled task created (runs every 15 minutes)" -ForegroundColor Green

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "1. Nginx configuration has been updated and verified"
Write-Host "2. Log rotation has been scheduled to run daily at 2 AM"
Write-Host "3. Service monitoring has been set up to run every 15 minutes"
Write-Host "`nYou can check the scheduled tasks in Task Scheduler (taskschd.msc)"
