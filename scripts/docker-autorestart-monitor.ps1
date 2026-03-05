# docker-autorestart-monitor.ps1
# Docker Auto-Restart Monitor Service
# This script runs continuously to monitor Docker and restart it if needed

param(
    [int]$CheckInterval = 60,
    [int]$MaxRestartAttempts = 5,
    [string]$ProjectRoot = "D:\dev\casestrainer"
)

$ErrorActionPreference = "Continue"

# Paths
$logsDir = Join-Path $ProjectRoot "logs"
$serviceLogPath = Join-Path $logsDir "docker-autorestart-service.log"
$diagnosticsLogPath = Join-Path $logsDir "docker_diagnostics.log"
$healthcheckLogPath = Join-Path $logsDir "docker_healthchecks.log"
$pauseFlagPath = Join-Path $logsDir "docker-autorestart-PAUSED.flag"

# Ensure logs directory exists
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

function Write-ServiceLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $serviceLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-DiagnosticsLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $diagnosticsLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-HealthcheckLog {
    param([string]$ContainerName, [string]$Status, [string]$Details = "")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] HEALTHCHECK: $ContainerName -> $Status"
    if ($Details) {
        $logEntry += " ($Details)"
    }
    Add-Content -Path $healthcheckLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Get-SystemResources {
    try {
        $memInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        $cpuInfo = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue
        
        return @{
            TotalMemoryGB = [math]::Round($memInfo.TotalVisibleMemorySize / 1MB, 2)
            AvailableMemoryGB = [math]::Round($memInfo.FreePhysicalMemory / 1MB, 2)
            UsedMemoryGB = [math]::Round(($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / 1MB, 2)
            MemoryPercent = [math]::Round((($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / $memInfo.TotalVisibleMemorySize) * 100, 1)
            CPUName = $cpuInfo.Name
            CPUCount = $cpuInfo.NumberOfCores
        }
    } catch {
        return $null
    }
}

function Get-DockerDesktopProcessInfo {
    try {
        $processes = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($processes) {
            $info = @()
            foreach ($proc in $processes) {
                $info += @{
                    Id = $proc.Id
                    CPU = $proc.CPU
                    WorkingSetMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
                    StartTime = $proc.StartTime
                }
            }
            return $info
        }
        return $null
    } catch {
        return $null
    }
}

function Test-DockerHealth {
    try {
        $info = docker info 2>&1
        if ($LASTEXITCODE -eq 0 -and $info -notmatch "error|ERROR|Cannot connect|500 Internal Server Error") {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Get-DockerDesktopProcess {
    return Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
}

function Invoke-CaptureDiagnostics {
    param([string]$Context = "Routine Check")
    
    Write-DiagnosticsLog "=== DOCKER DIAGNOSTICS CAPTURE: $Context ===" "INFO"
    
    # System resources
    $resources = Get-SystemResources
    if ($resources) {
        Write-DiagnosticsLog "SYSTEM: Memory - Total: $($resources.TotalMemoryGB)GB, Available: $($resources.AvailableMemoryGB)GB, Used: $($resources.UsedMemoryGB)GB ($($resources.MemoryPercent)%)" "INFO"
        Write-DiagnosticsLog "SYSTEM: CPU - $($resources.CPUName) ($($resources.CPUCount) cores)" "INFO"
    }
    
    # Docker Desktop process info
    $dockerProcs = Get-DockerDesktopProcessInfo
    if ($dockerProcs) {
        foreach ($proc in $dockerProcs) {
            Write-DiagnosticsLog "DOCKER_DESKTOP: PID=$($proc.Id), CPU=$($proc.CPU)s, Memory=$($proc.WorkingSetMB)MB, Started=$($proc.StartTime)" "INFO"
        }
    } else {
        Write-DiagnosticsLog "DOCKER_DESKTOP: Process not found" "WARN"
    }
    
    # Docker daemon health
    if (Test-DockerHealth) {
        Write-DiagnosticsLog "DOCKER_DAEMON: Healthy - responding to 'docker info'" "INFO"
        Write-HealthcheckLog -ContainerName "docker-daemon" -Status "HEALTHY" -Details "docker info successful"
    } else {
        Write-DiagnosticsLog "DOCKER_DAEMON: Unhealthy - 'docker info' failed" "ERROR"
        Write-HealthcheckLog -ContainerName "docker-daemon" -Status "UNHEALTHY" -Details "docker info failed"
    }
    
    # Container health status
    try {
        $containers = docker ps -a --format "{{.Names}}|{{.Status}}|{{.State}}|{{.Health}}" 2>&1
        if ($LASTEXITCODE -eq 0 -and $containers) {
            foreach ($line in $containers) {
                $parts = $line -split '\|'
                if ($parts.Count -ge 4) {
                    $healthStatus = if ($parts[3]) { $parts[3] } else { "no-healthcheck" }
                    Write-DiagnosticsLog "CONTAINER: $($parts[0]) - State: $($parts[2]), Status: $($parts[1]), Health: $healthStatus" "INFO"
                    Write-HealthcheckLog -ContainerName $parts[0] -Status $healthStatus -Details $parts[1]
                }
            }
        }
    } catch {
        Write-DiagnosticsLog "CONTAINER: Failed to get container status: $($_.Exception.Message)" "WARN"
    }
    
    Write-DiagnosticsLog "=== DIAGNOSTICS CAPTURE COMPLETE ===" "INFO"
}

function Restart-DockerDesktop {
    param([int]$Attempt = 1)
    
    Write-ServiceLog "RESTART: Attempting Docker Desktop restart (attempt $Attempt)" "WARN"
    Write-DiagnosticsLog "RESTART: Docker Desktop restart initiated (attempt $Attempt)" "ERROR"
    
    # Capture diagnostics before restart
    Invoke-CaptureDiagnostics -Context "PRE-RESTART (Attempt $Attempt)"
    
    # Stop Docker Desktop processes
    $processes = Get-DockerDesktopProcess
    if ($processes) {
        foreach ($proc in $processes) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-ServiceLog "RESTART: Stopped Docker Desktop process (PID: $($proc.Id))" "INFO"
            } catch {
                Write-ServiceLog "RESTART: Failed to stop process $($proc.Id): $($_.Exception.Message)" "WARN"
            }
        }
    }
    
    # Wait for processes to fully stop
    $waitCount = 0
    while ((Get-DockerDesktopProcess) -and $waitCount -lt 10) {
        Start-Sleep -Seconds 1
        $waitCount++
    }
    
    # Start Docker Desktop
    $dockerPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerPath)) {
        Write-ServiceLog "RESTART: ERROR - Docker Desktop not found at $dockerPath" "ERROR"
        return $false
    }
    
    try {
        Start-Process -FilePath $dockerPath -WindowStyle Minimized -ErrorAction Stop
        Write-ServiceLog "RESTART: Docker Desktop start command issued" "INFO"
        
        # Wait for Docker to become healthy
        $maxWait = 120  # 2 minutes
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            
            if (Test-DockerHealth) {
                Write-ServiceLog "RESTART: Docker Desktop is healthy after $waited seconds" "SUCCESS"
                Write-DiagnosticsLog "RESTART: Docker Desktop recovered successfully after $waited seconds" "SUCCESS"
                Write-HealthcheckLog -ContainerName "docker-daemon" -Status "RECOVERED" -Details "Restart successful"
                
                # Start containers if docker-compose file exists
                $composeFile = Join-Path $ProjectRoot "docker-compose.prod.yml"
                if (Test-Path $composeFile) {
                    Write-ServiceLog "RESTART: Starting CaseStrainer containers..." "INFO"
                    Push-Location $ProjectRoot
                    docker-compose -f docker-compose.prod.yml up -d 2>&1 | Out-Null
                    Pop-Location
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-ServiceLog "RESTART: Containers started successfully" "SUCCESS"
                    } else {
                        Write-ServiceLog "RESTART: Warning - Container startup may have failed" "WARN"
                    }
                }
                
                # Capture post-restart diagnostics
                Start-Sleep -Seconds 10
                Invoke-CaptureDiagnostics -Context "POST-RESTART (Attempt $Attempt)"
                
                return $true
            }
        }
        
        Write-ServiceLog "RESTART: Docker Desktop did not become healthy within $maxWait seconds" "WARN"
        Write-DiagnosticsLog "RESTART: Docker Desktop did not recover within $maxWait seconds" "ERROR"
        return $false
    } catch {
        Write-ServiceLog "RESTART: Exception starting Docker Desktop: $($_.Exception.Message)" "ERROR"
        Write-DiagnosticsLog "RESTART: Exception: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main monitoring loop
Write-ServiceLog "=== DOCKER AUTO-RESTART MONITOR STARTED ===" "INFO"
Write-ServiceLog "Configuration: CheckInterval=$CheckInterval seconds, MaxRestartAttempts=$MaxRestartAttempts per hour" "INFO"
Write-DiagnosticsLog "=== MONITOR SERVICE STARTED ===" "INFO"

$restartHistory = @()
$lastRestartTime = $null
$consecutiveFailures = 0

while ($true) {
    try {
        # Honor pause flag (set by install-docker-autorestart-service.ps1 -Pause)
        if (Test-Path -LiteralPath $pauseFlagPath -ErrorAction SilentlyContinue) {
            Write-ServiceLog "Pause flag detected - exiting monitor so Docker can be updated" "INFO"
            exit 0
        }
        $dockerHealthy = Test-DockerHealth
        $dockerProcess = Get-DockerDesktopProcess
        
        if ($dockerHealthy) {
            if ($consecutiveFailures -gt 0) {
                Write-ServiceLog "Docker is now healthy (recovered from $consecutiveFailures consecutive failures)" "SUCCESS"
                Write-DiagnosticsLog "Docker recovered - was unhealthy for $consecutiveFailures checks" "SUCCESS"
                $consecutiveFailures = 0
            }
            
            # Periodic diagnostics (every 10 checks = ~10 minutes)
            if (($consecutiveFailures % 10) -eq 0) {
                Invoke-CaptureDiagnostics -Context "Periodic Health Check"
            }
        } else {
            $consecutiveFailures++
            Write-ServiceLog "Docker health check FAILED (consecutive failures: $consecutiveFailures)" "ERROR"
            Write-DiagnosticsLog "Docker health check failed (consecutive: $consecutiveFailures)" "ERROR"
            
            # Check if we should attempt restart
            $now = Get-Date
            $shouldRestart = $false
            
            if ($null -eq $lastRestartTime) {
                $shouldRestart = $true
            } else {
                $hoursSinceLastRestart = ($now - $lastRestartTime).TotalHours
                if ($hoursSinceLastRestart -ge 1) {
                    # Reset restart count after 1 hour
                    $restartHistory = @()
                    $shouldRestart = $true
                } elseif ($restartHistory.Count -lt $MaxRestartAttempts) {
                    $shouldRestart = $true
                } else {
                    Write-ServiceLog "RESTART: Rate limit reached - $($restartHistory.Count) restarts in last hour" "WARN"
                }
            }
            
            if ($shouldRestart) {
                $attempt = $restartHistory.Count + 1
                if (Restart-DockerDesktop -Attempt $attempt) {
                    $restartHistory += $now
                    $lastRestartTime = $now
                    $consecutiveFailures = 0
                } else {
                    $restartHistory += $now
                    $lastRestartTime = $now
                }
            }
        }
    } catch {
        Write-ServiceLog "Exception in monitoring loop: $($_.Exception.Message)" "ERROR"
        Write-DiagnosticsLog "Monitor exception: $($_.Exception.Message)" "ERROR"
    }
    
    Start-Sleep -Seconds $CheckInterval
}
