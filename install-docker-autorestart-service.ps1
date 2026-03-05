# install-docker-autorestart-service.ps1
# Standalone Windows Service installer for Docker auto-restart
# This creates a service that monitors Docker and restarts it automatically
# Works without user login - runs as SYSTEM account
#
# Usage:
#   .\install-docker-autorestart-service.ps1 -Install    # Install the service
#   .\install-docker-autorestart-service.ps1 -Uninstall  # Remove the service
#   .\install-docker-autorestart-service.ps1 -Status    # Check service status

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Install,
    
    [Parameter()]
    [switch]$Uninstall,
    
    [Parameter()]
    [switch]$Status,
    
    [Parameter()]
    [switch]$Pause,  # Temporarily disable the service
    
    [Parameter()]
    [switch]$Resume,  # Re-enable the service after pause
    
    [Parameter()]
    [int]$CheckInterval = 60,  # Check Docker every N seconds
    
    [Parameter()]
    [int]$MaxRestartAttempts = 5,  # Max restart attempts per hour
    
    [Parameter()]
    [string]$ProjectRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

# Service configuration
$serviceName = "CaseStrainerDockerMonitor"
$serviceDisplayName = "CaseStrainer Docker Auto-Restart Monitor"
$serviceDescription = "Monitors Docker Desktop and automatically restarts it if it crashes. Runs without user login."
$taskName = "CaseStrainer-Docker-AutoRestart"

# Paths
$logsDir = Join-Path $ProjectRoot "logs"
$monitorScriptPath = Join-Path $ProjectRoot "scripts\docker-autorestart-monitor.ps1"
$serviceLogPath = Join-Path $logsDir "docker-autorestart-service.log"
$pauseFlagPath = Join-Path $logsDir "docker-autorestart-PAUSED.flag"

# Ensure logs directory exists
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

function Write-InstallLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $serviceLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Test-AdminPrivileges {
    try {
        $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
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

function Restart-DockerDesktop {
    param([int]$Attempt = 1)
    
    Write-InstallLog "RESTART: Attempting Docker Desktop restart (attempt $Attempt)" "WARN"
    
    # Stop Docker Desktop processes
    $processes = Get-DockerDesktopProcess
    if ($processes) {
        foreach ($proc in $processes) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-InstallLog "RESTART: Stopped Docker Desktop process (PID: $($proc.Id))" "INFO"
            } catch {
                Write-InstallLog "RESTART: Failed to stop process $($proc.Id): $($_.Exception.Message)" "WARN"
            }
        }
    }
    
    # Wait for processes to fully stop
    $waitCount = 0
    while ((Get-DockerDesktopProcess) -and $waitCount -lt 10) {
        Start-Sleep -Seconds 1
        $waitCount++
    }
    
    if ($waitCount -ge 10) {
        Write-InstallLog "RESTART: Warning - Docker Desktop processes may still be running" "WARN"
    }
    
    # Start Docker Desktop
    $dockerPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerPath)) {
        Write-InstallLog "RESTART: ERROR - Docker Desktop not found at $dockerPath" "ERROR"
        return $false
    }
    
    try {
        Start-Process -FilePath $dockerPath -WindowStyle Minimized -ErrorAction Stop
        Write-InstallLog "RESTART: Docker Desktop start command issued" "INFO"
        
        # Wait for Docker to become healthy
        $maxWait = 120  # 2 minutes
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            
            if (Test-DockerHealth) {
                Write-InstallLog "RESTART: Docker Desktop is healthy after $waited seconds" "SUCCESS"
                
                # Start containers if docker-compose file exists
                $composeFile = Join-Path $ProjectRoot "docker-compose.prod.yml"
                if (Test-Path $composeFile) {
                    Write-InstallLog "RESTART: Starting CaseStrainer containers..." "INFO"
                    Push-Location $ProjectRoot
                    docker-compose -f docker-compose.prod.yml up -d 2>&1 | Out-Null
                    Pop-Location
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-InstallLog "RESTART: Containers started successfully" "SUCCESS"
                    } else {
                        Write-InstallLog "RESTART: Warning - Container startup may have failed" "WARN"
                    }
                }
                
                return $true
            }
        }
        
        Write-InstallLog "RESTART: Docker Desktop did not become healthy within $maxWait seconds" "WARN"
        return $false
    } catch {
        Write-InstallLog "RESTART: Exception starting Docker Desktop: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Create the monitor script
$monitorScript = @'
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
'@

# Main script logic
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CaseStrainer Docker Auto-Restart Service Installer" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-AdminPrivileges)) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($Status) {
    Write-Host "Checking service status..." -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Service Status:" -ForegroundColor Green
        Write-Host "  Name: $($task.TaskName)" -ForegroundColor Gray
        Write-Host "  State: $($task.State)" -ForegroundColor Gray
        Write-Host "  Enabled: $($task.Settings.Enabled)" -ForegroundColor $(if ($task.Settings.Enabled) { "Green" } else { "Yellow" })
        Write-Host "  Principal: $($task.Principal.UserId)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Recent log entries:" -ForegroundColor Cyan
        if (Test-Path $serviceLogPath) {
            Get-Content $serviceLogPath -Tail 20
        } else {
            Write-Host "  No log file found" -ForegroundColor Gray
        }
    } else {
        Write-Host "Service is not installed" -ForegroundColor Yellow
    }
    exit 0
}

if ($Pause) {
    Write-Host "Pausing Docker auto-restart (scheduled task)..." -ForegroundColor Yellow
    # 1) Create pause flag so any running monitor script will exit on next loop
    try {
        if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
        Set-Content -Path $pauseFlagPath -Value ("Paused at " + (Get-Date -Format "o")) -Force -ErrorAction Stop
        Write-InstallLog "Created pause flag: $pauseFlagPath" "INFO"
    } catch {
        Write-InstallLog "Could not create pause flag: $($_.Exception.Message)" "WARN"
    }
    # 2) Find and stop/disable the scheduled task
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task) {
        $task = Get-ScheduledTask | Where-Object { $_.TaskName -eq $taskName } | Select-Object -First 1
    }
    if ($task) {
        try {
            # Stop any running instance first
            try {
                if ($task.State -eq "Running") {
                    Stop-ScheduledTask -InputObject $task -ErrorAction Stop
                    Write-InstallLog "Stopped running monitor task instance" "INFO"
                    Start-Sleep -Seconds 2
                }
            } catch {
                Write-InstallLog "Stop task: $($_.Exception.Message)" "WARN"
            }
            Disable-ScheduledTask -InputObject $task -ErrorAction Stop
            Write-InstallLog "Service paused by user" "INFO"
        } catch {
            Write-Host "[ERROR] Failed to pause task: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    # 3) Kill any lingering PowerShell process running the monitor script (so it can't "wake" and restart Docker)
    try {
        $monitorName = [System.IO.Path]::GetFileName($monitorScriptPath)
        Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue | ForEach-Object {
            $cmd = $_.CommandLine
            if ($cmd -and $cmd -match [regex]::Escape($monitorName)) {
                Write-InstallLog "Stopping monitor process PID $($_.ProcessId)" "INFO"
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-InstallLog "Kill monitor processes: $($_.Exception.Message)" "WARN"
    }
    Write-Host "[OK] Auto-restart is disabled (task + pause flag + monitor processes stopped)" -ForegroundColor Green
    Write-Host ""
    Write-Host "To resume: .\install-docker-autorestart-service.ps1 -Resume" -ForegroundColor Yellow
    exit 0
}

if ($Resume) {
    Write-Host "Resuming Docker auto-restart service..." -ForegroundColor Yellow
    # Remove pause flag so the monitor is allowed to run
    if (Test-Path -LiteralPath $pauseFlagPath -ErrorAction SilentlyContinue) {
        Remove-Item -LiteralPath $pauseFlagPath -Force -ErrorAction SilentlyContinue
        Write-InstallLog "Removed pause flag" "INFO"
    }
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task) {
        $task = Get-ScheduledTask | Where-Object { $_.TaskName -eq $taskName } | Select-Object -First 1
    }
    if ($task) {
        try {
            # Enable the task
            Enable-ScheduledTask -InputObject $task -ErrorAction Stop
            Write-InstallLog "Service resumed by user" "INFO"
            Write-Host "[OK] Service resumed - Docker auto-restart is now enabled" -ForegroundColor Green
            Write-Host ""
            
            # Try to start the task if it's not running
            $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
            if ($taskInfo.LastTaskResult -ne 0) {
                try {
                    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
                    Write-Host "[OK] Service started" -ForegroundColor Green
                } catch {
                    Write-Host "[INFO] Service will start automatically at next trigger" -ForegroundColor Gray
                }
            }
        } catch {
            Write-Host "[ERROR] Failed to resume service: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[WARN] Service is not installed" -ForegroundColor Yellow
    }
    exit 0
}

if ($Uninstall) {
    Write-Host "Uninstalling Docker auto-restart service..." -ForegroundColor Yellow
    
    # Remove scheduled task
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-InstallLog "Uninstalled scheduled task: $taskName" "INFO"
        Write-Host "[OK] Service task removed" -ForegroundColor Green
    } catch {
        Write-InstallLog "Failed to remove task: $($_.Exception.Message)" "WARN"
        Write-Host "[WARN] Task may not have existed" -ForegroundColor Yellow
    }
    
    # Remove monitor script (optional - user may want to keep it)
    Write-Host ""
    Write-Host "Service uninstalled successfully!" -ForegroundColor Green
    Write-Host "Note: Monitor script at $monitorScriptPath was not deleted" -ForegroundColor Gray
    Write-Host "      You can delete it manually if desired" -ForegroundColor Gray
    exit 0
}

if ($Install) {
    Write-Host "Installing Docker auto-restart service..." -ForegroundColor Yellow
    Write-InstallLog "=== INSTALLATION STARTED ===" "INFO"
    
    # Ensure scripts directory exists
    $scriptsDir = Split-Path $monitorScriptPath -Parent
    if (-not (Test-Path $scriptsDir)) {
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }
    
    # Create the monitor script with actual values
    $monitorScriptContent = $monitorScript -replace 'D:\\dev\\casestrainer', $ProjectRoot
    $monitorScriptContent | Out-File -FilePath $monitorScriptPath -Encoding UTF8 -Force
    Write-InstallLog "Created monitor script: $monitorScriptPath" "INFO"
    Write-Host "[OK] Monitor script created" -ForegroundColor Green
    
    # Remove existing task if it exists
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-InstallLog "Removed existing task: $taskName" "INFO"
    } catch {
        # Task doesn't exist, that's fine
    }
    
    # Create scheduled task action
    $action = New-ScheduledTaskAction `
        -Execute "PowerShell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$monitorScriptPath`" -CheckInterval $CheckInterval -MaxRestartAttempts $MaxRestartAttempts -ProjectRoot `"$ProjectRoot`""
    
    # Create triggers
    $triggers = @()
    
    # Trigger 1: At startup (delayed by 2 minutes to let system stabilize)
    $startupTrigger = New-ScheduledTaskTrigger -AtStartup
    $startupTrigger.Delay = "PT2M"  # 2 minute delay
    $triggers += $startupTrigger
    
    # Trigger 2: On logon (as backup, but runs as SYSTEM so won't require login)
    $logonTrigger = New-ScheduledTaskTrigger -AtLogOn
    $triggers += $logonTrigger
    
    # Create settings for unattended operation
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -RunOnlyIfNetworkAvailable `
        -DontStopOnIdleEnd `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5) `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit
    
    # Get current user for running the task
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    Write-Host ""
    Write-Host "The task will run as: $currentUser" -ForegroundColor Cyan
    Write-Host "This allows Docker Desktop to start properly (requires user session access)." -ForegroundColor Gray
    Write-Host ""

    # Prompt for password securely
    Write-Host "Enter your Windows password to allow the task to run whether you're logged in or not:" -ForegroundColor Yellow
    $securePassword = Read-Host -AsSecureString "Password"
    $credential = New-Object System.Management.Automation.PSCredential($currentUser, $securePassword)
    $plainPassword = $credential.GetNetworkCredential().Password

    if ([string]::IsNullOrEmpty($plainPassword)) {
        Write-Host "[ERROR] Password cannot be empty" -ForegroundColor Red
        exit 1
    }

    # Register the task with user credentials
    try {
        Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $triggers `
            -Settings $settings `
            -User $currentUser `
            -Password $plainPassword `
            -RunLevel Highest `
            -Description $serviceDescription `
            -Force | Out-Null
        
        # Clear password from memory
        $plainPassword = $null
        $securePassword.Dispose()

        Write-InstallLog "Registered scheduled task: $taskName (as $currentUser)" "INFO"
        Write-Host "[OK] Scheduled task created" -ForegroundColor Green
    } catch {
        # Clear password from memory on error too
        $plainPassword = $null
        if ($securePassword) { $securePassword.Dispose() }

        Write-InstallLog "Failed to register task: $($_.Exception.Message)" "ERROR"
        Write-Host "[ERROR] Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    # Start the task immediately
    try {
        Start-ScheduledTask -TaskName $taskName
        Write-InstallLog "Started scheduled task: $taskName" "INFO"
        Write-Host "[OK] Service started" -ForegroundColor Green
    } catch {
        Write-InstallLog "Failed to start task: $($_.Exception.Message)" "WARN"
        Write-Host "[WARN] Task created but could not start immediately" -ForegroundColor Yellow
        Write-Host "      It will start automatically at next boot or logon" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "====================================================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "====================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service Details:" -ForegroundColor Cyan
    Write-Host "  Name: $taskName" -ForegroundColor Gray
    Write-Host "  Monitor Script: $monitorScriptPath" -ForegroundColor Gray
    Write-Host "  Service Log: $serviceLogPath" -ForegroundColor Gray
    Write-Host "  Diagnostics Log: $(Join-Path $logsDir 'docker_diagnostics.log')" -ForegroundColor Gray
    Write-Host "  Healthcheck Log: $(Join-Path $logsDir 'docker_healthchecks.log')" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  Check Interval: $CheckInterval seconds" -ForegroundColor Gray
    Write-Host "  Max Restart Attempts: $MaxRestartAttempts per hour" -ForegroundColor Gray
    Write-Host "  Runs As: $currentUser (runs whether logged in or not)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "The service will:" -ForegroundColor Yellow
    Write-Host "  1. Start automatically at system boot (2 min delay)" -ForegroundColor Gray
    Write-Host "  2. Monitor Docker every $CheckInterval seconds" -ForegroundColor Gray
    Write-Host "  3. Automatically restart Docker if it crashes" -ForegroundColor Gray
    Write-Host "  4. Start CaseStrainer containers after Docker recovers" -ForegroundColor Gray
    Write-Host "  5. Log all diagnostics for crash analysis" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To check status:" -ForegroundColor Yellow
    Write-Host "  .\install-docker-autorestart-service.ps1 -Status" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To pause (for Docker updates):" -ForegroundColor Yellow
    Write-Host "  .\install-docker-autorestart-service.ps1 -Pause" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To resume after pause:" -ForegroundColor Yellow
    Write-Host "  .\install-docker-autorestart-service.ps1 -Resume" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To uninstall:" -ForegroundColor Yellow
    Write-Host "  .\install-docker-autorestart-service.ps1 -Uninstall" -ForegroundColor Gray
    Write-Host ""
    
    Write-InstallLog "=== INSTALLATION COMPLETE ===" "SUCCESS"
    exit 0
}

# No action specified - show usage
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  .\install-docker-autorestart-service.ps1 -Install      # Install the service" -ForegroundColor Gray
Write-Host "  .\install-docker-autorestart-service.ps1 -Uninstall    # Remove the service" -ForegroundColor Gray
Write-Host "  .\install-docker-autorestart-service.ps1 -Status      # Check service status" -ForegroundColor Gray
Write-Host "  .\install-docker-autorestart-service.ps1 -Pause       # Temporarily disable (for Docker updates)" -ForegroundColor Gray
Write-Host "  .\install-docker-autorestart-service.ps1 -Resume      # Re-enable after pause" -ForegroundColor Gray
Write-Host ""
Write-Host "Options:" -ForegroundColor Yellow
Write-Host "  -CheckInterval <seconds>        # How often to check Docker (default: 60)" -ForegroundColor Gray
Write-Host "  -MaxRestartAttempts <count>     # Max restarts per hour (default: 5)" -ForegroundColor Gray
Write-Host "  -ProjectRoot <path>             # Project root directory (default: script location)" -ForegroundColor Gray
Write-Host ""
Write-Host "Example - Updating Docker:" -ForegroundColor Cyan
Write-Host "  1. .\install-docker-autorestart-service.ps1 -Pause    # Disable auto-restart" -ForegroundColor Gray
Write-Host "  2. Update Docker Desktop" -ForegroundColor Gray
Write-Host "  3. .\install-docker-autorestart-service.ps1 -Resume   # Re-enable auto-restart" -ForegroundColor Gray
Write-Host ""
