# Smart Docker Monitor for CaseStrainer
# Enhanced to handle unresponsive Docker daemon and automatic recovery

param(
    [int]$CheckInterval = 300,  # Check every 5 minutes
    [int]$MaxDockerProcesses = 15,  # Maximum reasonable Docker processes
    [int]$MaxUnresponsiveRetries = 3,  # Number of retries before restarting Docker
    [int]$DockerStartupWait = 30,  # Seconds to wait for Docker to start
    [switch]$Verbose,
    [switch]$DryRun
)

$LogFile = "logs/smart_docker_monitor.log"
$DockerUnresponsiveCount = 0  # Track consecutive unresponsive states

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"

    Write-Host $logMessage -ForegroundColor $(switch($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "INFO" { "Green" }
        "CLEANUP" { "Magenta" }
        default { "White" }
    })

    Add-Content -Path $LogFile -Value $logMessage -Force
}

function Test-DockerResponsive {
    try {
        $null = docker info 2>&1
        return $true
    } catch {
        return $false
    }
}

function Restart-DockerDesktop {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would restart Docker Desktop" -Level "INFO"
        return $true
    }
    
    try {
        Write-Log "Attempting to restart Docker Desktop..." -Level "WARN"
        
        # Stop Docker Desktop
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction Stop
        Start-Sleep -Seconds 5
        
        # Start Docker Desktop
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        
        # Wait for Docker to be responsive
        $maxWait = 120  # seconds
        $startTime = Get-Date
        $dockerReady = $false
        
        Write-Log "Waiting for Docker to start..." -Level "INFO"
        
        while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
            if (Test-DockerResponsive) {
                $dockerReady = $true
                break
            }
            Start-Sleep -Seconds 5
        }
        
        if ($dockerReady) {
            Write-Log "Docker Desktop restarted successfully" -Level "INFO"
            return $true
        } else {
            Write-Log "Failed to restart Docker Desktop: Timeout waiting for Docker to start" -Level "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error restarting Docker Desktop: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Get-SmartDockerAnalysis {
    # First check if Docker is responsive
    $dockerResponsive = Test-DockerResponsive
    
    if (-not $dockerResponsive) {
        Write-Log "Docker daemon is not responding" -Level "ERROR"
        return @{ DockerUnresponsive = $true }
    }
    
    $allProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" }

    # Categorize processes
    $legitimate = @()
    $suspicious = @()
    $zombie = @()

    foreach ($proc in $allProcesses) {
        $isLegitimate = $false

        # Skip known legitimate Docker processes but log them appropriately
        $legitimateProcesses = @(
            "com.docker.backend", "com.docker.build", "Docker Desktop", "docker"
        )

        foreach ($legitProc in $legitimateProcesses) {
            $processes = Get-Process -Name $legitProc -ErrorAction SilentlyContinue
            if ($processes) {
                Write-Host "  Docker process running normally: $legitProc" -ForegroundColor Green
                continue
            }
        }

        # Check if it's a critical Docker service
        if ($proc.ProcessName -match "com\.docker\.service|com\.docker\.backend|Docker Desktop") {
            $isLegitimate = $true
        }

        # Check if it's an active CLI process (recent CPU usage)
        if ($proc.CPU -gt 0.1 -and $proc.ProcessName -eq "docker") {
            $isLegitimate = $true
        }

        # Check age (processes older than 1 hour with no CPU might be zombies)
        $age = (Get-Date) - $proc.StartTime
        if ($age.TotalHours -gt 1 -and $proc.CPU -lt 0.01) {
            $zombie += $proc
        } elseif (!$isLegitimate) {
            $suspicious += $proc
        } else {
            $legitimate += $proc
        }
    }

    return @{
        Legitimate = $legitimate
        Suspicious = $suspicious
        Zombie = $zombie
        Total = $allProcesses.Count
    }
}

function Invoke-SmartCleanup {
    $analysis = Get-SmartDockerAnalysis
    
    # Handle unresponsive Docker daemon
    if ($analysis.DockerUnresponsive) {
        $script:DockerUnresponsiveCount++
        Write-Log "Docker daemon is unresponsive (Attempt $($script:DockerUnresponsiveCount)/$MaxUnresponsiveRetries)" -Level "ERROR"
        
        if ($script:DockerUnresponsiveCount -ge $MaxUnresponsiveRetries) {
            Write-Log "Max unresponsive retries reached, attempting to restart Docker..." -Level "WARN"
            $restartSuccess = Restart-DockerDesktop
            if ($restartSuccess) {
                $script:DockerUnresponsiveCount = 0
                # Wait for Docker to fully initialize before continuing
                Start-Sleep -Seconds $DockerStartupWait
                # Get fresh analysis after restart
                $analysis = Get-SmartDockerAnalysis
            } else {
                Write-Log "Failed to recover Docker after $MaxUnresponsiveRetries attempts. Manual intervention required." -Level "ERROR"
                return $false
            }
        } else {
            return $false
        }
    } else {
        # Reset counter if Docker is responsive
        $script:DockerUnresponsiveCount = 0
    }

    Write-Log "=== SMART DOCKER CLEANUP ===" -Level "INFO"
    Write-Log "Total processes: $($analysis.Total)" -Level "INFO"
    Write-Log "Legitimate: $($analysis.Legitimate.Count)" -Level "INFO"
    Write-Log "Suspicious: $($analysis.Suspicious.Count)" -Level "WARN"
    Write-Log "Zombie: $($analysis.Zombie.Count)" -Level "CLEANUP"

    if ($analysis.Total -gt $MaxDockerProcesses) {
        Write-Log "Process count exceeds threshold ($MaxDockerProcesses)" -Level "WARN"
    }

    # Kill only zombie processes (old, inactive)
    $killed = 0
    foreach ($proc in $analysis.Zombie) {
        Write-Log "Killing zombie process: $($proc.ProcessName) (PID: $($proc.Id), Age: $([math]::Round(((Get-Date) - $proc.StartTime).TotalHours, 1))h)" -Level "CLEANUP"

        if (!$DryRun) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                $killed++
                # Give the process a moment to terminate
                Start-Sleep -Milliseconds 100
            } catch {
                Write-Log "Failed to kill process $($proc.Id): $($_.Exception.Message)" -Level "ERROR"
                
                # If we can't kill the process, it might be a sign of a bigger issue
                if ($_.Exception.Message -like "*Access is denied*" -or 
                    $_.Exception.Message -like "*Cannot find a process with the process identifier*" -or
                    $_.Exception.Message -like "*The process cannot access the file because it is being used by another process*") {
                    Write-Log "Critical process termination issue detected. Attempting Docker restart..." -Level "ERROR"
                    Restart-DockerDesktop | Out-Null
                    Start-Sleep -Seconds $DockerStartupWait
                    break
                }
            }
        }
    }

    # Log suspicious but don't auto-kill (could be test scripts)
    foreach ($proc in $analysis.Suspicious) {
        Write-Log "Suspicious process detected: $($proc.ProcessName) (PID: $($proc.Id))" -Level "WARN"
    }
    
    return $killed
}

function Start-ContinuousMonitoring {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()

    if ($PSCmdlet.ShouldProcess("Docker monitoring", "Start continuous monitoring")) {
        Write-Log "Starting Enhanced Smart Docker Monitor (interval: ${CheckInterval}s)" -Level "INFO"
        Write-Log "Docker unresponsive retries: $MaxUnresponsiveRetries" -Level "INFO"
        Write-Log "Docker startup wait time: ${DockerStartupWait}s" -Level "INFO"

        # Initial Docker health check
        if (-not (Test-DockerResponsive)) {
            Write-Log "Initial check: Docker is not responsive. Attempting recovery..." -Level "WARN"
            $restartSuccess = Restart-DockerDesktop
            if (-not $restartSuccess) {
                Write-Log "Failed to recover Docker during startup. Exiting." -Level "ERROR"
                exit 1
            }
        }

        while ($true) {
            $cleanupResult = Invoke-SmartCleanup
            
            # If cleanup failed critically, wait longer before next check
            if ($cleanupResult -eq $false) {
                $retryWait = [math]::Min($CheckInterval * 2, 300)  # Cap at 5 minutes
                Write-Log "Critical issue detected. Waiting ${retryWait}s before next check..." -Level "WARN"
                Start-Sleep -Seconds $retryWait
            } else {
                Start-Sleep -Seconds $CheckInterval
            }
        }
    }
}

# Create startup script
function Start-MonitorService {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()

    if ($PSCmdlet.ShouldProcess("Docker monitoring service", "Start monitoring service")) {
        Write-Log "Starting Docker process monitoring service..."

        # Ensure log directory exists
        if (!(Test-Path "logs")) {
            New-Item -ItemType Directory -Path "logs" -Force | Out-Null
        }

        # Initial cleanup
        $initialKilled = Invoke-SmartCleanup
        if ($initialKilled -gt 0) {
            Write-Log "Initial cleanup: killed $initialKilled zombie processes" -Level "CLEANUP"
        }

        # Start continuous monitoring
        Start-ContinuousMonitoring
    }
}

# Integration with cslaunch
Write-Log "Enhanced Smart Docker Monitor ready" -Level "INFO"
Write-Log "Usage:" -Level "INFO"
Write-Log "  .\smart_docker_monitor.ps1                    # Run once" -Level "INFO"
Write-Log "  .\smart_docker_monitor.ps1 -CheckInterval 60  # Run every minute" -Level "INFO"
Write-Log "  .\smart_docker_monitor.ps1 -DryRun            # Preview actions" -Level "INFO"
Write-Log "  .\smart_docker_monitor.ps1 -MaxUnresponsiveRetries 5  # Set max retries" -Level "INFO"
Write-Log "  .\smart_docker_monitor.ps1 -DockerStartupWait 45     # Set Docker startup wait time" -Level "INFO"

# Ensure log directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Run based on parameters
try {
    if ($MyInvocation.BoundParameters.Count -eq 0) {
        Invoke-SmartCleanup
    } else {
        Start-MonitorService
    }
} catch {
    $errorMsg = $_.Exception.Message
    Write-Log "Fatal error in Docker monitor: $errorMsg" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    
    # Attempt emergency Docker restart on fatal error
    try {
        Write-Log "Attempting emergency Docker restart..." -Level "WARN"
        Restart-DockerDesktop | Out-Null
    } catch {
        Write-Log "Emergency Docker restart failed: $($_.Exception.Message)" -Level "ERROR"
    }
    
    exit 1
}
