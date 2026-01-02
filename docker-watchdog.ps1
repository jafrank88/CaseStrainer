# Docker CaseStrainer Watchdog
# Monitors and auto-restarts containers if they go down
# Run this as a Windows Scheduled Task that starts at system boot

$LogFile = "d:\dev\casestrainer\logs\docker-watchdog.log"
$ComposeFile = "d:\dev\casestrainer\docker-compose.prod.yml"
$CheckIntervalSeconds = 60  # Check every 60 seconds
$MaxRestartAttempts = 3
$RestartAttempts = 0

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage -ErrorAction SilentlyContinue
}

function Test-DockerDesktopRunning {
    $dockerProcesses = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    return ($null -ne $dockerProcesses -and $dockerProcesses.Count -gt 0)
}

function Get-ContainerStatus {
    try {
        $containers = docker ps -a --filter "name=casestrainer-" --format "{{.Names}}|{{.Status}}" 2>$null
        return $containers
    } catch {
        return $null
    }
}

function Test-AllContainersHealthy {
    try {
        $runningCount = (docker ps --filter "name=casestrainer-" --format "{{.Names}}" 2>$null | Measure-Object -Line).Lines
        # Expected: 8 containers (backend, redis, 3 workers, job-monitor, frontend, nginx)
        return $runningCount -ge 8
    } catch {
        return $false
    }
}

function Start-CasestrainerContainers {
    param($Reason)
    
    Write-Log "ATTEMPTING RESTART: $Reason"
    Write-Log "Running: docker-compose -f $ComposeFile up -d"
    
    try {
        Push-Location "d:\dev\casestrainer"
        $output = docker-compose -f docker-compose.prod.yml up -d 2>&1
        Write-Log "Docker-compose output: $output"
        
        # Wait 30 seconds for containers to start
        Write-Log "Waiting 30 seconds for containers to stabilize..."
        Start-Sleep -Seconds 30
        
        # Verify containers are running
        $status = Get-ContainerStatus
        Write-Log "Container status after restart:`n$status"
        
        return $true
    } catch {
        Write-Log "ERROR during restart: $_"
        return $false
    } finally {
        Pop-Location
    }
}

# Main watchdog loop
Write-Log "=== Docker Watchdog Started ==="
Write-Log "Monitoring CaseStrainer containers every $CheckIntervalSeconds seconds"
Write-Log "Compose file: $ComposeFile"

while ($true) {
    try {
        # Check if Docker Desktop is running
        if (-not (Test-DockerDesktopRunning)) {
            Write-Log "WARNING: Docker Desktop is not running. Waiting..."
            Start-Sleep -Seconds $CheckIntervalSeconds
            continue
        }
        
        # Check container health
        $allHealthy = Test-AllContainersHealthy
        
        if (-not $allHealthy) {
            Write-Log "ALERT: Not all containers are running!"
            
            # Get detailed status
            $status = Get-ContainerStatus
            Write-Log "Current status:`n$status"
            
            # Attempt restart if under max attempts
            if ($RestartAttempts -lt $MaxRestartAttempts) {
                $RestartAttempts++
                Write-Log "Restart attempt $RestartAttempts of $MaxRestartAttempts"
                
                $success = Start-CasestrainerContainers "Containers down - automatic recovery"
                
                if ($success) {
                    Write-Log "SUCCESS: Containers restarted successfully"
                    $RestartAttempts = 0  # Reset counter on success
                } else {
                    Write-Log "FAILED: Restart attempt $RestartAttempts failed"
                }
            } else {
                Write-Log "ERROR: Max restart attempts reached. Manual intervention required."
                # Reset counter after 10 minutes to try again
                Start-Sleep -Seconds 600
                $RestartAttempts = 0
            }
        } else {
            # All healthy - reset restart counter
            if ($RestartAttempts -gt 0) {
                Write-Log "INFO: All containers healthy. Resetting restart counter."
                $RestartAttempts = 0
            }
        }
        
    } catch {
        Write-Log "ERROR in watchdog loop: $_"
    }
    
    # Wait before next check
    Start-Sleep -Seconds $CheckIntervalSeconds
}
