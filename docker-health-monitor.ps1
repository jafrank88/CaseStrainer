# docker-health-monitor.ps1
# Continuous Docker health monitoring with automatic recovery
# Run this in the background to monitor Docker health and prevent crashes

param(
    [Parameter()]
    [int]$CheckIntervalSeconds = 60,

    [Parameter()]
    [switch]$AutoRecover,

    [Parameter()]
    [switch]$LogToFile,

    [Parameter()]
    [string]$LogFile = "logs\docker-monitor.log"
)

# Setup logging
if ($LogToFile) {
    $logsDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
}

function Write-MonitorLog {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console with colors
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default  { Write-Host $logEntry -ForegroundColor Cyan }
    }
    
    # Write to file if enabled
    if ($LogToFile) {
        Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
    }
}

function Get-DockerHealthStatus {
    # Comprehensive Docker health check
    $status = @{
        Healthy = $false
        Issues = @()
        ServiceRunning = $false
        DesktopRunning = $false
        ContainerCount = 0
        MemoryUsage = 0
        LastCheck = Get-Date
    }
    
    # Check Docker Desktop processes
    $dockerProcs = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcs) {
        $status.DesktopRunning = $true
        $status.MemoryUsage = [math]::Round(($dockerProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 2)
    } else {
        $status.Issues += "Docker Desktop process not running"
    }
    
    # Check Docker service
    $svc = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
    if ($svc) {
        $status.ServiceRunning = ($svc.Status -eq "Running")
        if (-not $status.ServiceRunning) {
            $status.Issues += "Docker service status: $($svc.Status)"
        }
    } else {
        $status.Issues += "Docker service not found"
    }
    
    # Check Docker daemon connectivity
    try {
        $info = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($info -match "error|ERROR|Cannot connect|500 Internal Server Error") {
                $status.Issues += "Docker daemon reporting errors"
            } else {
                # Count running containers
                $containers = docker ps --format "{{.Names}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $status.ContainerCount = $containers.Count
                }
                $status.Healthy = $true
            }
        } else {
            $status.Issues += "Docker daemon not responding (exit code: $LASTEXITCODE)"
        }
    } catch {
        $status.Issues += "Exception checking Docker daemon: $($_.Exception.Message)"
    }
    
    return $status
}

function Invoke-AutoRecovery {
    Write-MonitorLog "Starting automatic Docker recovery..." "WARN"
    
    # Try soft recovery first
    try {
        Write-MonitorLog "Attempting soft recovery: docker desktop restart" "INFO"
        $restartResult = docker desktop restart 2>&1
        Start-Sleep -Seconds 30
        
        # Check if recovery worked
        $status = Get-DockerHealthStatus
        if ($status.Healthy) {
            Write-MonitorLog "✅ Soft recovery successful" "SUCCESS"
            return $true
        }
    } catch {
        Write-MonitorLog "Soft recovery failed: $($_.Exception.Message)" "WARN"
    }
    
    # Try hard recovery
    try {
        Write-MonitorLog "Attempting hard recovery: process restart" "INFO"
        
        # Stop all Docker processes
        Get-Process -Name "Docker Desktop","com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        
        # Start Docker Desktop
        $dockerExe = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerExe) {
            Start-Process -FilePath $dockerExe -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 60
            
            # Check if recovery worked
            $status = Get-DockerHealthStatus
            if ($status.Healthy) {
                Write-MonitorLog "✅ Hard recovery successful" "SUCCESS"
                return $true
            }
        }
    } catch {
        Write-MonitorLog "Hard recovery failed: $($_.Exception.Message)" "ERROR"
    }
    
    Write-MonitorLog "❌ All recovery attempts failed" "ERROR"
    return $false
}

# Main monitoring loop
Write-MonitorLog "=== Docker Health Monitor Started ===" "SUCCESS"
Write-MonitorLog "Check interval: $CheckIntervalSeconds seconds" "INFO"
Write-MonitorLog "Auto-recovery: $(if ($AutoRecover) { 'Enabled' } else { 'Disabled' })" "INFO"
Write-MonitorLog "Logging: $(if ($LogToFile) { "Enabled ($LogFile)" } else { 'Disabled' })" "INFO"

$unhealthyCount = 0
$maxUnhealthyChecks = 3

try {
    while ($true) {
        $status = Get-DockerHealthStatus
        
        if ($status.Healthy) {
            if ($unhealthyCount -gt 0) {
                Write-MonitorLog "✅ Docker health restored after $unhealthyCount unhealthy checks" "SUCCESS"
                $unhealthyCount = 0
            } else {
                Write-MonitorLog "✅ Docker healthy ($($status.ContainerCount) containers, $($status.MemoryUsage)MB memory)" "INFO"
            }
        } else {
            $unhealthyCount++
            Write-MonitorLog "❌ Docker unhealthy (check #$unhealthyCount): $($status.Issues -join '; ')" "ERROR"
            
            if ($AutoRecover -and $unhealthyCount -ge $maxUnhealthyChecks) {
                Write-MonitorLog "Triggering automatic recovery after $maxUnhealthyChecks consecutive unhealthy checks..." "WARN"
                
                if (Invoke-AutoRecovery) {
                    $unhealthyCount = 0
                } else {
                    Write-MonitorLog "Auto-recovery failed, continuing monitoring..." "WARN"
                }
            }
        }
        
        # Sleep until next check
        Start-Sleep -Seconds $CheckIntervalSeconds
    }
} catch {
    Write-MonitorLog "Monitor crashed: $($_.Exception.Message)" "ERROR"
    Write-MonitorLog "Restart monitor manually or check system stability" "WARN"
} finally {
    Write-MonitorLog "=== Docker Health Monitor Stopped ===" "WARN"
}
