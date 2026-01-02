# Docker Daemon Monitor and Auto-Recovery Script
# Monitors Docker daemon health and automatically restarts if frozen
# This script addresses the recurring Docker daemon freeze issues

param(
    [int]$CheckInterval = 30,  # Check every 30 seconds
    [int]$FreezeTimeout = 15,  # Consider frozen if no response in 15 seconds
    [int]$MaxRestartsPerHour = 3,  # Maximum restarts per hour
    [switch]$AsJob,  # Run as background job
    [string]$LogFile = "logs\docker_daemon_monitor.log"
)

$ErrorActionPreference = "Continue"

# Ensure log directory exists
$logDir = Split-Path $LogFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-DaemonLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry }
    }
}

function Test-DockerDaemonHealth {
    param([int]$TimeoutSeconds = 15)
    
    $healthChecks = @{
        DockerInfo = $false
        DockerVersion = $false
        DockerPs = $false
        DockerService = $false
    }
    
    # Check 1: Docker info (most basic check)
    try {
        $job = Start-Job -ScriptBlock { docker info 2>&1 }
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $output = Receive-Job $job
            Remove-Job $job -Force
            if ($LASTEXITCODE -eq 0) {
                $healthChecks.DockerInfo = $true
            }
        } else {
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
            Write-DaemonLog "Docker info check timed out after ${TimeoutSeconds}s" "WARN"
        }
    } catch {
        Write-DaemonLog "Docker info check failed: $($_.Exception.Message)" "WARN"
    }
    
    # Check 2: Docker version (quick check)
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker version --format '{{.Server.Version}}' 2>&1 }
            if (Wait-Job $job -Timeout 5) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0 -and $output) {
                    $healthChecks.DockerVersion = $true
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Non-critical
        }
    }
    
    # Check 3: Docker ps (list containers)
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker ps --format '{{.Names}}' 2>&1 }
            if (Wait-Job $job -Timeout 10) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0) {
                    $healthChecks.DockerPs = $true
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Non-critical
        }
    }
    
    # Check 4: Docker service status (Windows)
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq 'Running') {
            $healthChecks.DockerService = $true
        }
    } catch {
        # Service might not exist or be accessible
    }
    
    return $healthChecks
}

function Get-DockerProcessStats {
    $stats = @{
        Processes = @()
        TotalMemoryMB = 0
        TotalCPUPercent = 0
        HighCPUProcesses = @()
    }
    
    try {
        $dockerProcesses = Get-Process | Where-Object { 
            $_.ProcessName -like "*docker*" -or 
            $_.ProcessName -like "*com.docker*" 
        } | Select-Object ProcessName, Id, @{Name='CPU';Expression={$_.CPU}}, @{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet64/1MB,2)}}
        
        foreach ($proc in $dockerProcesses) {
            $stats.Processes += $proc
            $stats.TotalMemoryMB += $proc.MemoryMB
            
            # Check for high CPU (if CPU > 100, it's likely a problem)
            if ($proc.CPU -gt 100) {
                $stats.HighCPUProcesses += $proc
            }
        }
        
        # Calculate total CPU percentage (approximate)
        $stats.TotalCPUPercent = ($stats.Processes | Measure-Object -Property CPU -Sum).Sum / 100
        
    } catch {
        Write-DaemonLog "Failed to get Docker process stats: $($_.Exception.Message)" "WARN"
    }
    
    return $stats
}

function Restart-DockerDaemon {
    param([string]$Reason = "Freeze detected")
    
    Write-DaemonLog "=== DOCKER DAEMON RESTART INITIATED ===" "WARN"
    Write-DaemonLog "Reason: $Reason" "WARN"
    
    # Get process stats before restart
    $beforeStats = Get-DockerProcessStats
    Write-DaemonLog "Process stats before restart:" "INFO"
    Write-DaemonLog "  Total Memory: $($beforeStats.TotalMemoryMB) MB" "INFO"
    Write-DaemonLog "  High CPU Processes: $($beforeStats.HighCPUProcesses.Count)" "INFO"
    foreach ($proc in $beforeStats.HighCPUProcesses) {
        Write-DaemonLog "    - $($proc.ProcessName) (PID: $($proc.Id)) CPU: $($proc.CPU)" "WARN"
    }
    
    try {
        # Step 1: Stop Docker Desktop gracefully
        Write-DaemonLog "Stopping Docker Desktop..." "INFO"
        $dockerDesktop = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerDesktop) {
            $dockerDesktop | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
        
        # Step 2: Stop Docker service
        Write-DaemonLog "Stopping Docker service..." "INFO"
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Step 3: Kill any remaining Docker processes
        Write-DaemonLog "Cleaning up remaining Docker processes..." "INFO"
        Get-Process | Where-Object { 
            $_.ProcessName -like "*docker*" -or 
            $_.ProcessName -like "*com.docker*" 
        } | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Step 4: Start Docker service
        Write-DaemonLog "Starting Docker service..." "INFO"
        Start-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        # Step 5: Start Docker Desktop
        Write-DaemonLog "Starting Docker Desktop..." "INFO"
        $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (-not (Test-Path $dockerDesktopPath)) {
            $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
        }
        
        if (Test-Path $dockerDesktopPath) {
            Start-Process -FilePath $dockerDesktopPath -ErrorAction SilentlyContinue
        } else {
            Write-DaemonLog "Docker Desktop executable not found at expected location" "ERROR"
            return $false
        }
        
        # Step 6: Wait for Docker to be ready
        Write-DaemonLog "Waiting for Docker to become ready..." "INFO"
        $maxWait = 120  # 2 minutes
        $startTime = Get-Date
        $dockerReady = $false
        
        while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
            $health = Test-DockerDaemonHealth -TimeoutSeconds 5
            if ($health.DockerInfo -and $health.DockerPs) {
                $dockerReady = $true
                break
            }
            Start-Sleep -Seconds 5
            Write-Host "." -NoNewline
        }
        
        if ($dockerReady) {
            Write-DaemonLog "=== DOCKER DAEMON RESTART SUCCESSFUL ===" "SUCCESS"
            Write-DaemonLog "Recovery completed in $([math]::Round(((Get-Date) - $startTime).TotalSeconds)) seconds" "SUCCESS"
            
            # Get Docker version
            try {
                $version = docker version --format '{{.Server.Version}}' 2>&1
                if ($version) {
                    Write-DaemonLog "Docker version: $version" "INFO"
                }
            } catch {
                # Non-critical
            }
            
            return $true
        } else {
            Write-DaemonLog "=== DOCKER DAEMON RESTART FAILED ===" "ERROR"
            Write-DaemonLog "Docker did not become ready within $maxWait seconds" "ERROR"
            return $false
        }
        
    } catch {
        Write-DaemonLog "Error during Docker restart: $($_.Exception.Message)" "ERROR"
        Write-DaemonLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
        return $false
    }
}

# Main monitoring loop
function Start-DockerDaemonMonitoring {
    Write-DaemonLog "=== DOCKER DAEMON MONITOR STARTED ===" "SUCCESS"
    Write-DaemonLog "Check interval: ${CheckInterval}s" "INFO"
    Write-DaemonLog "Freeze timeout: ${FreezeTimeout}s" "INFO"
    Write-DaemonLog "Max restarts per hour: $MaxRestartsPerHour" "INFO"
    
    $restartHistory = @()  # Track restart times
    $consecutiveFailures = 0
    $lastHealthCheck = $null
    
    while ($true) {
        $checkStart = Get-Date
        
        try {
            # Perform health check
            $health = Test-DockerDaemonHealth -TimeoutSeconds $FreezeTimeout
            
            # Determine overall health
            $isHealthy = $health.DockerInfo -and $health.DockerPs
            
            if ($isHealthy) {
                if ($consecutiveFailures -gt 0) {
                    Write-DaemonLog "Docker daemon recovered after $consecutiveFailures consecutive failures" "SUCCESS"
                    $consecutiveFailures = 0
                }
                
                # Log periodic health status (every 10 checks)
                if ($null -eq $lastHealthCheck -or ((Get-Date) - $lastHealthCheck).TotalMinutes -ge 5) {
                    Write-DaemonLog "Docker daemon health check: OK (Info: $($health.DockerInfo), Ps: $($health.DockerPs), Service: $($health.DockerService))" "INFO"
                    $lastHealthCheck = Get-Date
                }
                
            } else {
                $consecutiveFailures++
                Write-DaemonLog "Docker daemon health check FAILED (attempt $consecutiveFailures)" "ERROR"
                Write-DaemonLog "  DockerInfo: $($health.DockerInfo), DockerPs: $($health.DockerPs), DockerService: $($health.DockerService)" "ERROR"
                
                # Get process stats for diagnostics
                $stats = Get-DockerProcessStats
                Write-DaemonLog "  Process stats: $($stats.Processes.Count) processes, $($stats.TotalMemoryMB) MB memory" "INFO"
                
                # If multiple consecutive failures, attempt restart
                if ($consecutiveFailures -ge 2) {
                    # Check restart rate limit
                    $now = Get-Date
                    $recentRestarts = $restartHistory | Where-Object { ($now - $_).TotalHours -lt 1 }
                    
                    if ($recentRestarts.Count -lt $MaxRestartsPerHour) {
                        Write-DaemonLog "Attempting Docker daemon restart (${consecutiveFailures} consecutive failures)" "WARN"
                        
                        $restartSuccess = Restart-DockerDaemon -Reason "Health check failed ($consecutiveFailures consecutive failures)"
                        
                        if ($restartSuccess) {
                            $restartHistory += Get-Date
                            $consecutiveFailures = 0
                            
                            # Clean up old restart history (keep last 24 hours)
                            $restartHistory = $restartHistory | Where-Object { ($now - $_).TotalHours -lt 24 }
                        } else {
                            Write-DaemonLog "Docker daemon restart failed - manual intervention may be required" "ERROR"
                        }
                    } else {
                        Write-DaemonLog "Restart rate limit reached ($($recentRestarts.Count) restarts in last hour) - skipping restart" "WARN"
                    }
                }
            }
            
        } catch {
            Write-DaemonLog "Error during health check: $($_.Exception.Message)" "ERROR"
            $consecutiveFailures++
        }
        
        # Calculate sleep time
        $elapsed = ((Get-Date) - $checkStart).TotalSeconds
        $sleepTime = [math]::Max(1, $CheckInterval - [math]::Floor($elapsed))
        Start-Sleep -Seconds $sleepTime
    }
}

# Entry point
if ($AsJob) {
    Write-Host "Starting Docker daemon monitor as background job..." -ForegroundColor Cyan
    $job = Start-Job -ScriptBlock ${function:Start-DockerDaemonMonitoring} -Name "DockerDaemonMonitor"
    Write-Host "Monitor started as job: $($job.Name) (ID: $($job.Id))" -ForegroundColor Green
    Write-Host "To view logs: Get-Content $LogFile -Tail 50 -Wait" -ForegroundColor Yellow
    Write-Host "To stop: Stop-Job -Name DockerDaemonMonitor; Remove-Job -Name DockerDaemonMonitor" -ForegroundColor Yellow
    return $job
} else {
    Write-Host "Starting Docker daemon monitor (Press Ctrl+C to stop)..." -ForegroundColor Cyan
    Start-DockerDaemonMonitoring
}










