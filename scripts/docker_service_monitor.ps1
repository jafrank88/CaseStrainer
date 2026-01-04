# Docker Desktop Service Monitor and Recovery Script
# This script monitors the Docker Desktop service and automatically restarts it when it fails

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$RunOnce,
    [int]$CheckInterval = 60,
    [string]$LogPath = "logs\docker_service_monitor.log"
)

# Import necessary modules
Add-Type -AssemblyName System.Windows.Forms

# Configuration
$serviceName = "com.docker.service"
$dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
$maxRestartAttempts = 3
$restartDelay = 30
$logFile = Join-Path $PSScriptRoot ".." $LogPath

# Ensure log directory exists
$logDir = Split-Path $logFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $logFile -Value $logEntry
}

function Test-DockerDesktopHealth {
    # Check if Docker Desktop service is running
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if (-not $service -or $service.Status -ne "Running") {
        return $false
    }

    # Check if Docker Desktop process is running
    $process = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if (-not $process) {
        return $false
    }

    # Check if Docker daemon responds
    try {
        $result = & docker.exe info 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    }
    catch {
        return $false
    }

    return $false
}

function Start-DockerDesktopSafely {
    Write-Log "Starting Docker Desktop..."
    
    # Kill any existing Docker processes
    Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "VpnService" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Start-Sleep -Seconds 5
    
    # Start Docker Desktop
    Start-Process -FilePath $dockerDesktopPath -WindowStyle Minimized
    
    # Wait for Docker to be ready
    $maxWait = 120
    $waited = 0
    while ($waited -lt $maxWait) {
        if (Test-DockerDesktopHealth) {
            Write-Log "Docker Desktop started successfully"
            return $true
        }
        Start-Sleep -Seconds 2
        $waited += 2
    }
    
    Write-Log "Failed to start Docker Desktop within timeout period" "ERROR"
    return $false
}

function Restart-DockerDesktop {
    param([int]$Attempt = 1)
    
    Write-Log "Restart attempt $Attempt of $maxRestartAttempts" "WARN"
    
    # Stop Docker Desktop service
    try {
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Write-Log "Stopped Docker service"
    }
    catch {
        Write-Log "Failed to stop Docker service: $($_.Exception.Message)" "WARN"
    }
    
    # Kill remaining processes
    Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Start-Sleep -Seconds $restartDelay
    
    # Start Docker Desktop
    if (Start-DockerDesktopSafely) {
        Write-Log "Docker Desktop restarted successfully"
        
        # Start CaseStrainer containers if they exist
        $composeFile = Join-Path $PSScriptRoot "..\docker-compose.prod.yml"
        if (Test-Path $composeFile) {
            Write-Log "Starting CaseStrainer containers..."
            Set-Location (Split-Path $composeFile -Parent)
            & docker-compose -f docker-compose.prod.yml up -d
            Write-Log "CaseStrainer containers started"
        }
        
        return $true
    }
    
    return $false
}

function Install-ServiceMonitor {
    Write-Log "Installing Docker Service Monitor as a scheduled task..."
    
    $taskName = "Docker-Service-Monitor"
    $scriptPath = $PSCommandPath
    
    # Remove existing task if it exists
    Unregister-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    # Create the scheduled task
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -DontStopOnIdleEnd
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $Principal -Force
    
    Write-Log "Docker Service Monitor installed successfully"
}

function Uninstall-ServiceMonitor {
    Write-Log "Uninstalling Docker Service Monitor..."
    
    $taskName = "Docker-Service-Monitor"
    Unregister-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    Write-Log "Docker Service Monitor uninstalled"
}

function Start-Monitoring {
    Write-Log "Starting Docker Service Monitor (check interval: $CheckInterval seconds)"
    
    $consecutiveFailures = 0
    
    while ($true) {
        if (Test-DockerDesktopHealth) {
            if ($consecutiveFailures -gt 0) {
                Write-Log "Docker Desktop is back online"
            }
            $consecutiveFailures = 0
        }
        else {
            $consecutiveFailures++
            Write-Log "Docker Desktop health check failed (failure #$consecutiveFailures)" "WARN"
            
            if ($consecutiveFailures -ge 2) {
                Write-Log "Multiple failures detected, attempting recovery..." "ERROR"
                
                for ($attempt = 1; $attempt -le $maxRestartAttempts; $attempt++) {
                    if (Restart-DockerDesktop -Attempt $attempt) {
                        $consecutiveFailures = 0
                        break
                    }
                    
                    if ($attempt -lt $maxRestartAttempts) {
                        Write-Log "Waiting before next attempt..." "WARN"
                        Start-Sleep -Seconds ($restartDelay * 2)
                    }
                }
                
                if ($consecutiveFailures -gt 0) {
                    Write-Log "All restart attempts failed, sending notification..." "ERROR"
                    # Send notification (Windows toast)
                    [Windows.Forms.MessageBox]::Show("Docker Desktop failed to start after $maxRestartAttempts attempts. Manual intervention required.", "Docker Service Monitor", "OK", "Error") | Out-Null
                }
            }
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Main execution
if ($Install) {
    Install-ServiceMonitor
}
elseif ($Uninstall) {
    Uninstall-ServiceMonitor
}
elseif ($RunOnce) {
    Write-Log "Running one-time health check..."
    if (Test-DockerDesktopHealth) {
        Write-Log "Docker Desktop is healthy"
    }
    else {
        Write-Log "Docker Desktop is not healthy, attempting restart..." "WARN"
        Restart-DockerDesktop
    }
}
else {
    Start-Monitoring
}
