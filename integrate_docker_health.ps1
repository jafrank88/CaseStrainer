# Docker Health Integration Script
# This script integrates Docker health monitoring into cslaunch

param(
    [string]$Action = ""
)

# Import the working functions from test_docker_health.ps1
. .\test_docker_health.ps1

function Show-DockerHealthMenu {
    Write-Host "`n=== Docker Health Monitoring ===" -ForegroundColor Cyan
    Write-Host "1. Start Docker Health Monitoring" -ForegroundColor Green
    Write-Host "2. Stop Docker Health Monitoring" -ForegroundColor Red
    Write-Host "3. Run Docker Health Check Now" -ForegroundColor Yellow
    Write-Host "4. View Monitoring Status" -ForegroundColor Blue
    Write-Host "0. Back to Main Menu" -ForegroundColor Gray
    
    $healthChoice = Read-Host "`nSelect an option (0-4)"
    
    switch ($healthChoice) {
        "1" {
            Write-Host "`nStarting Docker health monitoring..." -ForegroundColor Green
            try {
                $result = Start-DockerHealthMonitoring -CheckIntervalMinutes 5
                if ($result) {
                    Write-Host "✅ Docker health monitoring started successfully!" -ForegroundColor Green
                } else {
                    Write-Host "❌ Failed to start Docker health monitoring" -ForegroundColor Red
                }
            } catch {
                Write-Host "❌ Error starting Docker health monitoring: $_" -ForegroundColor Red
            }
        }
        "2" {
            Write-Host "`nStopping Docker health monitoring..." -ForegroundColor Yellow
            try {
                $result = Stop-DockerHealthMonitoring
                if ($result) {
                    Write-Host "✅ Docker health monitoring stopped successfully!" -ForegroundColor Green
                } else {
                    Write-Host "ℹ️  No Docker health monitoring was running" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "❌ Error stopping Docker health monitoring: $_" -ForegroundColor Red
            }
        }
        "3" {
            Write-Host "`nRunning Docker health check..." -ForegroundColor Yellow
            try {
                $healthResults = Test-DockerHealth
                Write-Host "`n=== Docker Health Check Results ===" -ForegroundColor Cyan
                foreach ($detail in $healthResults.Details) {
                    Write-Host $detail
                }
                
                if ($healthResults.DockerCLI -and $healthResults.ResourceUsage -and $healthResults.ContainersHealthy) {
                    Write-Host "`n✅ Docker is healthy!" -ForegroundColor Green
                } else {
                    Write-Host "`n⚠️  Docker health issues detected" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "❌ Error running Docker health check: $_" -ForegroundColor Red
            }
        }
        "4" {
            Write-Host "`nChecking Docker health monitoring status..." -ForegroundColor Blue
            try {
                $taskName = "DockerHealthCheck"
                $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
                
                if ($existingTask) {
                    $state = $existingTask.State
                    Write-Host "✅ Docker health monitoring is ACTIVE" -ForegroundColor Green
                    Write-Host "   Task State: $state" -ForegroundColor Gray
                    Write-Host "   Next Run: $($existingTask.NextRunTime)" -ForegroundColor Gray
                } else {
                    Write-Host "ℹ️  Docker health monitoring is NOT ACTIVE" -ForegroundColor Yellow
                    Write-Host "   Use option 1 to start monitoring" -ForegroundColor Gray
                }
            } catch {
                Write-Host "❌ Error checking monitoring status: $_" -ForegroundColor Red
            }
        }
        "0" {
            Write-Host "Returning to main menu..." -ForegroundColor Gray
            return
        }
        default {
            Write-Host "Invalid selection. Please enter a number between 0 and 4." -ForegroundColor Red
        }
    }
    
    Write-Host "`nPress any key to continue..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main execution
if ($Action) {
    # Direct action mode
    switch ($Action) {
        "start" { Start-DockerHealthMonitoring }
        "stop" { Stop-DockerHealthMonitoring }
        "check" { 
            $healthResults = Test-DockerHealth
            foreach ($detail in $healthResults.Details) {
                Write-Host $detail
            }
        }
        "status" {
            $taskName = "DockerHealthCheck"
            $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($existingTask) {
                Write-Host "ACTIVE" -ForegroundColor Green
            } else {
                Write-Host "INACTIVE" -ForegroundColor Red
            }
        }
        default {
            Write-Host "Unknown action: $Action" -ForegroundColor Red
            Write-Host "Valid actions: start, stop, check, status" -ForegroundColor Yellow
        }
    }
} else {
    # Interactive menu mode
    Show-DockerHealthMenu
} 