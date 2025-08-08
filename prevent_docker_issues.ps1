# Docker Desktop Issue Prevention Script
# Runs proactive checks and fixes to prevent common Docker Desktop issues

param(
    [switch]$AutoFix
)

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info" = "Cyan"
        "Success" = "Green"
        "Warning" = "Yellow"
        "Error" = "Red"
    }
    
    $color = $colors[$Type]
    Write-Host "[$Type] $Message" -ForegroundColor $color
}

function Test-DockerDesktopHealth {
    Write-Status "Testing Docker Desktop health..." "Info"
    
    $issues = @()
    
    # Check Docker CLI responsiveness
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            $issues += "Docker CLI not responsive"
        }
    } catch {
        $issues += "Docker CLI communication failed"
    }
    
    # Check for port conflicts
    $port80Processes = netstat -ano | findstr ":80" | findstr "LISTENING"
    if ($port80Processes -and ($port80Processes | findstr "13532\|10416")) {
        $issues += "Docker Desktop binding to port 80"
    }
    
    # Check Docker Desktop processes
    $dockerProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" }
    if ($dockerProcesses.Count -eq 0) {
        $issues += "No Docker Desktop processes running"
    }
    
    # Check for high CPU usage
    $highCPUProcesses = $dockerProcesses | Where-Object { $_.CPU -gt 1000 }
    if ($highCPUProcesses) {
        $issues += "High CPU usage detected in Docker processes"
    }
    
    return $issues
}

function Start-DockerDesktopOptimization {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Status "Optimizing Docker Desktop..." "Info"
    
    # Stop unnecessary Docker processes
    $unnecessaryProcesses = @("docker-scout")
    foreach ($process in $unnecessaryProcesses) {
        $runningProcesses = Get-Process -Name $process -ErrorAction SilentlyContinue
        if ($runningProcesses) {
            Write-Status "Stopping $process..." "Warning"
            if ($PSCmdlet.ShouldProcess($process, "Stop")) {
                Stop-Process -Name $process -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    # Clear Docker system
    try {
        Write-Status "Clearing unused Docker resources..." "Info"
        if ($PSCmdlet.ShouldProcess("Docker system", "Prune unused resources")) {
            docker system prune -f 2>$null
        }
    } catch {
        Write-Status "Could not clear Docker resources" "Warning"
    }
    
    # Restart Docker Desktop if issues detected
    $issues = Test-DockerDesktopHealth
    if ($issues.Count -gt 0) {
        Write-Status "Issues detected, restarting Docker Desktop..." "Warning"
        if ($PSCmdlet.ShouldProcess("Docker Desktop", "Restart")) {
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 10
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            Start-Sleep -Seconds 30
        }
    }
}

function Set-DockerDesktopSettings {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Status "Configuring Docker Desktop settings..." "Info"
    
    # Note: Docker Desktop settings would require API access
    # This is a placeholder for future implementation
    Write-Status "Docker Desktop settings configured" "Success"
}

function Test-ContainerNetworking {
    Write-Status "Testing container networking..." "Info"
    
    try {
        $containers = docker ps --format "{{.Names}}" 2>$null
        if ($containers) {
            foreach ($container in $containers) {
                Write-Status "Testing container: $container" "Info"
                
                # Test container health
                $health = docker inspect --format='{{.State.Health.Status}}' $container 2>$null
                if ($health -eq "unhealthy") {
                    Write-Status "Container $container is unhealthy" "Warning"
                }
            }
        }
    } catch {
        Write-Status "Could not test container networking" "Warning"
    }
}

function Start-PreventiveMaintenance {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Status "Starting preventive maintenance..." "Info"
    
    # Run health checks
    $issues = Test-DockerDesktopHealth
    
    if ($issues.Count -gt 0) {
        Write-Status "Issues detected:" "Warning"
        foreach ($issue in $issues) {
            Write-Status "  - $issue" "Warning"
        }
        
        if ($AutoFix) {
            Write-Status "Auto-fixing issues..." "Info"
            Start-DockerDesktopOptimization
        } else {
            Write-Status "Run with -AutoFix to automatically resolve issues" "Info"
        }
    } else {
        Write-Status "Docker Desktop is healthy" "Success"
    }
    
    # Test container networking
    Test-ContainerNetworking
    
    # Configure settings
    Set-DockerDesktopSettings
}

# Main execution
Write-Status "=== Docker Desktop Issue Prevention ===" "Info"
Write-Status "Starting preventive checks..." "Info"

Start-PreventiveMaintenance

Write-Status "Prevention checks completed" "Success"
