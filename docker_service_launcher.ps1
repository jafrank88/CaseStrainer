# Windows Service-like Docker Desktop Launcher
# Runs Docker Desktop as a monitored service

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$serviceName = "DockerDesktopService"
$processName = "Docker Desktop"
$exePath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

if ($Start) {
    Write-Host "Starting Docker Desktop service..." -ForegroundColor Green
    
    # Kill any existing processes
    Get-Process -Name $processName -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Start the service
    Start-Process $exePath -WindowStyle Minimized
    
    # Wait for startup
    Start-Sleep -Seconds 30
    
    # Start the intelligent monitor
    Start-Job -ScriptBlock { & ".\docker_intelligent_restart.ps1" } -Name "DockerIntelligentMonitor"
    
    Write-Host "Docker Desktop service started with intelligent monitoring" -ForegroundColor Green
}

if ($Stop) {
    Write-Host "Stopping Docker Desktop service..." -ForegroundColor Yellow
    
    # Stop the intelligent monitor
    Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue | Stop-Job
    Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue | Remove-Job
    
    # Stop Docker Desktop
    Get-Process -Name $processName -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-Host "Docker Desktop service stopped" -ForegroundColor Green
}

if ($Status) {
    $dockerProcesses = Get-Process -Name $processName -ErrorAction SilentlyContinue
    $monitorJob = Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue
    
    Write-Host "Docker Desktop Service Status:" -ForegroundColor Cyan
    Write-Host "  GUI Process: $(if ($dockerProcesses.Count -gt 0) { "Running (PID: $($dockerProcesses[0].Id))" } else { "Not running" })" -ForegroundColor $(if ($dockerProcesses.Count -gt 0) { "Green" } else { "Red" })
    Write-Host "  Monitor Job: $(if ($monitorJob) { "Active (ID: $($monitorJob.Id))" } else { "Not running" })" -ForegroundColor $(if ($monitorJob) { "Green" } else { "Red" })
}

if (-not $Start -and -not $Stop -and -not $Status) {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\docker_service_launcher.ps1 -Start    # Start Docker Desktop service" -ForegroundColor Cyan
    Write-Host "  .\docker_service_launcher.ps1 -Stop     # Stop Docker Desktop service" -ForegroundColor Red
    Write-Host "  .\docker_service_launcher.ps1 -Status   # Check service status" -ForegroundColor Yellow
}
