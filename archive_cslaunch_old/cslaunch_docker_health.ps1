# Modified cslaunch.ps1 with Docker Health Monitoring Integration
# This script adds Docker health monitoring to the existing cslaunch functionality

# Call the original cslaunch script but add Docker health monitoring
Write-Host "=== CaseStrainer Launcher with Docker Health Monitoring ===" -ForegroundColor Cyan

# Check if Docker health monitoring is active
$taskName = "DockerHealthCheck"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "✅ Docker health monitoring is ACTIVE" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Docker health monitoring is NOT ACTIVE" -ForegroundColor Yellow
    Write-Host "   Run '.\integrate_docker_health.ps1' to start monitoring" -ForegroundColor Gray
}

Write-Host "`nStarting CaseStrainer with Docker health monitoring..." -ForegroundColor Green

# Call the original cslaunch script
& .\cslaunch.ps1 @PSBoundParameters 