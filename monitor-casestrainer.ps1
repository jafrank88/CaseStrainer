# CaseStrainer Service Monitor
# This script monitors CaseStrainer services and automatically restarts them if they crash

param(
    [string]$Environment = "Production",
    [int]$CheckInterval = 30,
    [int]$MaxRestartAttempts = 5,
    [int]$RestartDelay = 10,
    [switch]$Verbose,
    [switch]$Help
)

# Configuration
$LogDirectory = "logs"
$LogFile = Join-Path $LogDirectory "monitor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$BackendHealthUrl = "http://127.0.0.1:5000/casestrainer/api/health"
$BackendPort = 5000
$FrontendPort = 5173
$ProductionPort = 443

# Statistics
$script:RestartCount = 0
$script:LastRestartTime = $null
$script:StartTime = Get-Date
$script:MonitoringActive = $true

function Show-Help {
    Write-Host "CaseStrainer Service Monitor`n" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\monitor-casestrainer.ps1 [Options]`n"
    Write-Host "Options:"
    Write-Host "  -Environment <Production|Development>  # Environment to monitor (default: Production)"
    Write-Host "  -CheckInterval <seconds>              # Health check interval (default: 30)"
    Write-Host "  -MaxRestartAttempts <number>          # Max restart attempts (default: 5)"
    Write-Host "  -RestartDelay <seconds>               # Delay before restart (default: 10)"
    Write-Host "  -Verbose                              # Enable verbose logging"
    Write-Host "  -Help                                 # Show this help message`n"
    Write-Host "Examples:"
    Write-Host "  .\monitor-casestrainer.ps1                           # Monitor production"
    Write-Host "  .\monitor-casestrainer.ps1 -Environment Development  # Monitor development"
    Write-Host "  .\monitor-casestrainer.ps1 -CheckInterval 60         # Check every minute`n"
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    if (!(Test-Path $LogDirectory)) {
        New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    }
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
    
    # Write to console with colors
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "INFO"  { Write-Host $logEntry -ForegroundColor White }
        "DEBUG" { 
            if ($Verbose) {
                Write-Host $logEntry -ForegroundColor Gray 
            }
        }
        default { Write-Host $logEntry }
    }
}

function Test-BackendHealth {
    try {
        $response = Invoke-RestMethod -Uri $BackendHealthUrl -TimeoutSec 10 -ErrorAction Stop
        if ($response.status -eq "ok" -or $response.status -eq "healthy") {
            return @{ Healthy = $true; Details = "Status: $($response.status)" }
        } else {
            return @{ Healthy = $false; Details = "Status: $($response.status)" }
        }
    } catch {
        return @{ Healthy = $false; Details = "Error: $($_.Exception.Message)" }
    }
}

function Test-BackendProcess {
    $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
    
    if ($backendProcesses) {
        return @{ Running = $true; PID = $backendProcesses[0].Id; Process = $backendProcesses[0] }
    } else {
        return @{ Running = $false; PID = $null; Process = $null }
    }
}

function Test-NginxProcess {
    $nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
    if ($nginxProcesses) {
        return @{ Running = $true; PID = $nginxProcesses[0].Id; Process = $nginxProcesses[0] }
    } else {
        return @{ Running = $false; PID = $null; Process = $null }
    }
}

function Test-FrontendProcess {
    $frontendProcesses = Get-Process node -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*vue-cli-service*' }
    
    if ($frontendProcesses) {
        return @{ Running = $true; PID = $frontendProcesses[0].Id; Process = $frontendProcesses[0] }
    } else {
        return @{ Running = $false; PID = $null; Process = $null }
    }
}

function Test-RedisConnection {
    try {
        $testConnection = python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{ Available = $true; Details = "Redis is accessible" }
        } else {
            return @{ Available = $false; Details = "Redis connection failed" }
        }
    } catch {
        return @{ Available = $false; Details = "Redis error: $($_.Exception.Message)" }
    }
}

function Restart-Backend {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    if ($PSCmdlet.ShouldProcess("backend", "restart")) {
        Write-Log "Restarting backend..." -Level "WARN"
        
        # Stop existing backend processes
        $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
        
        if ($backendProcesses) {
            Write-Log "Stopping existing backend processes..." -Level "INFO"
            $backendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Start backend using launcher
        try {
            $launcherPath = Join-Path $PSScriptRoot "launcher.ps1"
            if (Test-Path $launcherPath) {
                Write-Log "Starting backend via launcher..." -Level "INFO"
                Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "`"$launcherPath`"", "-Environment", $Environment, "-NoMenu" -WindowStyle Hidden
                Start-Sleep -Seconds $RestartDelay
            } else {
                Write-Log "Launcher not found, attempting direct start..." -Level "WARN"
                # Fallback: try to start backend directly
                $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
                if (Test-Path $venvPython) {
                    Start-Process -FilePath $venvPython -ArgumentList "-m", "src.app_final_vue" -WindowStyle Hidden
                }
            }
            
            $script:RestartCount++
            $script:LastRestartTime = Get-Date
            Write-Log "Backend restart completed (Attempt $($script:RestartCount) of $MaxRestartAttempts)" -Level "INFO"
            
        } catch {
            Write-Log "Failed to restart backend: $($_.Exception.Message)" -Level "ERROR"
        }
    }
}

function Restart-Nginx {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    if ($PSCmdlet.ShouldProcess("nginx", "restart")) {
        Write-Log "Restarting Nginx..." -Level "WARN"
        
        # Stop existing Nginx processes
        $nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
        if ($nginxProcesses) {
            Write-Log "Stopping existing Nginx processes..." -Level "INFO"
            $nginxProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Start Nginx
        try {
            $nginxDir = Join-Path $PSScriptRoot "nginx"
            $nginxExe = Join-Path $nginxDir "nginx.exe"
            
            if (Test-Path $nginxExe) {
                Set-Location $nginxDir
                & ".\nginx.exe" -c "production.conf" 2>&1 | Out-Null
                Set-Location $PSScriptRoot
                Write-Log "Nginx restarted successfully" -Level "INFO"
            } else {
                Write-Log "Nginx executable not found" -Level "ERROR"
            }
        } catch {
            Write-Log "Failed to restart Nginx: $($_.Exception.Message)" -Level "ERROR"
        }
    }
}

function Show-Statistics {
    $uptime = (Get-Date) - $script:StartTime
    $uptimeString = "{0:dd}:{1:hh}:{2:mm}:{3:ss}" -f $uptime.Days, $uptime.Hours, $uptime.Minutes, $uptime.Seconds
    
    Write-Log "=== Monitoring Statistics ===" -Level "INFO"
    Write-Log "Uptime: $uptimeString" -Level "INFO"
    Write-Log "Restart Count: $($script:RestartCount)" -Level "INFO"
    if ($script:LastRestartTime) {
        Write-Log "Last Restart: $($script:LastRestartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -Level "INFO"
    }
    Write-Log "Log File: $LogFile" -Level "INFO"
}

function Test-AllServices {
    $issues = @()
    
    # Test backend
    $backendProcess = Test-BackendProcess
    $backendHealth = Test-BackendHealth
    
    if (-not $backendProcess.Running) {
        $issues += "Backend process not running"
    } elseif (-not $backendHealth.Healthy) {
        $issues += "Backend health check failed: $($backendHealth.Details)"
    }
    
    # Test Nginx (production mode)
    if ($Environment -eq "Production") {
        $nginxProcess = Test-NginxProcess
        if (-not $nginxProcess.Running) {
            $issues += "Nginx process not running"
        }
    }
    
    # Test frontend (development mode)
    if ($Environment -eq "Development") {
        $frontendProcess = Test-FrontendProcess
        if (-not $frontendProcess.Running) {
            $issues += "Frontend dev server not running"
        }
    }
    
    # Test Redis
    $redisStatus = Test-RedisConnection
    if (-not $redisStatus.Available) {
        $issues += "Redis not available: $($redisStatus.Details)"
    }
    
    return @{
        Issues = $issues
        BackendProcess = $backendProcess
        BackendHealth = $backendHealth
        NginxProcess = if ($Environment -eq "Production") { Test-NginxProcess } else { @{ Running = $true; PID = $null } }
        FrontendProcess = if ($Environment -eq "Development") { Test-FrontendProcess } else { @{ Running = $true; PID = $null } }
        RedisStatus = $redisStatus
    }
}

# Main monitoring loop
function Start-Monitoring {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    if ($PSCmdlet.ShouldProcess("monitoring", "start")) {
        Write-Log "Starting CaseStrainer service monitor" -Level "INFO"
        Write-Log "Environment: $Environment" -Level "INFO"
        Write-Log "Check Interval: $CheckInterval seconds" -Level "INFO"
        Write-Log "Max Restart Attempts: $MaxRestartAttempts" -Level "INFO"
        Write-Log "Log File: $LogFile" -Level "INFO"
        Write-Log "Press Ctrl+C to stop monitoring" -Level "INFO"
        Write-Log "========================================" -Level "INFO"
        
        $checkCount = 0
        
        while ($script:MonitoringActive) {
            $checkCount++
            Write-Log "Health check #$checkCount" -Level "DEBUG"
            
            $serviceStatus = Test-AllServices
            
            if ($serviceStatus.Issues.Count -gt 0) {
                Write-Log "Service issues detected:" -Level "WARN"
                foreach ($issue in $serviceStatus.Issues) {
                    Write-Log "  - $issue" -Level "WARN"
                }
                
                # Check if we should attempt restart
                if ($script:RestartCount -lt $MaxRestartAttempts) {
                    Write-Log "Attempting service restart..." -Level "WARN"
                    
                    # Restart backend if needed
                    if (-not $serviceStatus.BackendProcess.Running -or -not $serviceStatus.BackendHealth.Healthy) {
                        Restart-Backend
                    }
                    
                    # Restart Nginx if needed (production mode)
                    if ($Environment -eq "Production" -and -not $serviceStatus.NginxProcess.Running) {
                        Restart-Nginx
                    }
                    
                } else {
                    Write-Log "Maximum restart attempts reached. Manual intervention required." -Level "ERROR"
                    Write-Log "Stopping monitoring..." -Level "ERROR"
                    break
                }
            } else {
                Write-Log "All services healthy" -Level "DEBUG"
                # Reset restart count if services are healthy
                if ($script:RestartCount -gt 0) {
                    Write-Log "Services recovered, resetting restart count" -Level "INFO"
                    $script:RestartCount = 0
                }
            }
            
            # Show periodic statistics
            if ($checkCount % 10 -eq 0) {
                Show-Statistics
            }
            
            Start-Sleep -Seconds $CheckInterval
        }
    }
}

# Handle Ctrl+C gracefully
Register-EngineEvent PowerShell.Exiting -Action { 
    $script:MonitoringActive = $false
    Write-Log "Monitoring stopped by user" -Level "INFO"
    Show-Statistics
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

try {
    Start-Monitoring
} catch {
    Write-Log "Fatal error in monitoring: $($_.Exception.Message)" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    exit 1
} finally {
    Write-Log "Monitoring stopped" -Level "INFO"
}
