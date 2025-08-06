# Setup Docker Monitoring
# This script creates a scheduled task to monitor Docker health

Write-Host "Setting up Docker health monitoring..." -ForegroundColor Cyan
Write-Host "Note: CPU threshold set to 320% (80% of 4 cores)" -ForegroundColor Gray

# Create the monitoring script path
$scriptPath = Join-Path $PWD "docker_health_check.ps1"
$taskName = "DockerHealthCheck"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the scheduled task
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description "Monitor Docker health every 5 minutes"

Register-ScheduledTask -TaskName $taskName -InputObject $task -User $env:USERNAME -Force

Write-Host "✅ Docker health monitoring scheduled to run every 5 minutes" -ForegroundColor Green
Write-Host "Task name: $taskName" -ForegroundColor Green
Write-Host "Script: $scriptPath" -ForegroundColor Green

# Test the script
Write-Host "`nTesting the health check script..." -ForegroundColor Cyan
& $scriptPath 