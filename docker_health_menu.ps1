# Docker Health Monitoring Menu
# This script provides a menu for Docker health monitoring options

param(
    [string]$Action = ""
)

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

# Docker Health Check Functions
function Test-DockerHealth {
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [int]$MaxCPUPercent = 80,
        [int]$MaxMemoryPercent = 85,
        [switch]$AutoRestart
    )
    
    $results = @{
        DockerCLI = $false
        ResourceUsage = $false
        ContainersHealthy = $false
        HighCPU = $false
        HighMemory = $false
        StuckContainers = @()
        Details = @()
    }
    
    # Check if Docker CLI is responsive
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $results.DockerCLI = $true
            $results.Details += "✅ Docker CLI is responsive"
        } else {
            throw "Docker CLI not responsive"
        }
    } catch {
        $results.Details += "❌ Docker CLI is unresponsive"
        if ($AutoRestart) {
            $results.Details += "🔄 Attempting Docker restart..."
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            $results.Details += "🔄 Docker Desktop restarted"
        }
        return $results
    }
    
    # Check container resource usage
    try {
        $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $results.ResourceUsage = $true
            $highUsage = $false
            
            foreach ($line in $stats) {
                if ($line -match "(\d+\.\d+)%") {
                    $cpuPercent = [double]$matches[1]
                    if ($cpuPercent -gt $MaxCPUPercent) {
                        $results.HighCPU = $true
                        $results.Details += "⚠️  High CPU usage detected: $cpuPercent%"
                        $highUsage = $true
                    }
                }
            }
            
            if (-not $highUsage) {
                $results.Details += "✅ Resource usage is normal"
            }
        } else {
            $results.Details += "❌ Cannot check container stats"
        }
    } catch {
        $results.Details += "❌ Cannot check container stats: $_"
    }
    
    # Check for stuck containers
    try {
        $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $stuckContainers = $containers | Select-String -Pattern "Up.*\(health: starting\)" | ForEach-Object { $_.ToString().Trim() }
            
            if ($stuckContainers) {
                $results.StuckContainers = $stuckContainers
                $results.Details += "⚠️  Found containers stuck in 'starting' state:"
                foreach ($container in $stuckContainers) {
                    $results.Details += "   $container"
                }
            } else {
                $results.ContainersHealthy = $true
                $results.Details += "✅ All containers are healthy"
            }
        } else {
            $results.Details += "❌ Cannot check container status"
        }
    } catch {
        $results.Details += "❌ Cannot check container status: $_"
    }
    
    return $results
}

function Start-DockerHealthMonitoring {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [int]$CheckIntervalMinutes = 5
    )
    
    try {
        $taskName = "DockerHealthCheck"
        $scriptPath = Join-Path $PSScriptRoot "docker_health_check.ps1"
        
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }
        
        # Create the scheduled task
        $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $CheckIntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365)
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
        
        Write-Host "✅ Docker health monitoring started (every $CheckIntervalMinutes minutes)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to start Docker health monitoring: $_" -ForegroundColor Red
        return $false
    }
}

function Stop-DockerHealthMonitoring {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    $taskName = "DockerHealthCheck"
    
    try {
        $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "✅ Docker health monitoring stopped" -ForegroundColor Green
            return $true
        } else {
            Write-Host "ℹ️  No Docker health monitoring task found" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ Failed to stop Docker health monitoring: $_" -ForegroundColor Red
        return $false
    }
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
} 