# cslauncher.ps1
# CaseStrainer development launcher - fast and reliable code reload
#
# Usage:
#   .\cslauncher.ps1                  # Normal reload (enables auto-restart service)
#   .\cslauncher.ps1 -ServicesOff     # Reload without auto-restart service
#   .\cslauncher.ps1 -UpdateDocker    # Pause service for Docker update, then exit
#   .\cslauncher.ps1 -InstallService  # One-time setup: install auto-restart service (needs admin)
#   .\cslauncher.ps1 -Build           # Rebuild backend container
#   .\cslauncher.ps1 -CleanDocker     # Force Docker cleanup
#
# Features:
# - Worker-first restart order (critical for code reload!)
# - Multi-check verification (ensures fixes are deployed)
# - Smart Docker cleanup (memory/disk threshold-based)
# - Automatic cache clearing (Redis + in-memory via restart)
# - Build support (rebuild backend when needed)
# - Crash logging (track reload operations)
# - Admin check (warn if not admin for Docker operations)
# - Verbose mode (detailed output)
# - Skip health check (fast reloads)
# - Docker crash diagnostics (captures system state, container health, events)
# - Persistent healthcheck logging (tracks all healthcheck results)
# - Automatic crash detection and diagnostics capture
# - Docker auto-restart service management (enabled by default, -ServicesOff to disable)
# - Automatic Vue frontend build detection and rebuild (detects source changes, runs npm build)

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Build = $true,  # DEFAULT: rebuild backend + workers before restart (use -Build:$false to skip)

    [Parameter()]
    [switch]$CleanDocker,  # Force Docker cleanup (prune images, containers)

    [Parameter()]
    [int]$MemoryThresholdGB = 3,  # Auto-cleanup if Docker >3GB (increased from 2GB for dev)

    [Parameter()]
    [int]$DiskThresholdGB = 25,  # Auto-cleanup if Docker disk >25GB

    [Parameter()]
    [switch]$SkipHealthCheck,  # Skip backend health check (faster)

    [Parameter()]
    [switch]$LogErrors,  # Write operations to logs/reload.log

    [Parameter()]
    [switch]$ServicesOff,  # Disable Docker auto-restart service (default: enabled)

    [Parameter()]
    [switch]$UpdateDocker,  # Pause service for Docker update, then exit (run again after update)

    [Parameter()]
    [switch]$InstallService  # Install the auto-restart service (requires admin, one-time setup)
)

# Note: -Verbose is automatically provided by [CmdletBinding()]

$ErrorActionPreference = "Continue"

# Setup logging
$logsDir = Join-Path $PSScriptRoot "logs"
$reloadLogPath = Join-Path $logsDir "reload.log"
$dockerDiagnosticsLogPath = Join-Path $logsDir "docker_diagnostics.log"
$dockerHealthcheckLogPath = Join-Path $logsDir "docker_healthchecks.log"

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Invoke-ManageDockerService {
    # Manage Docker auto-restart service (install/enable or pause)
    # Service runs as SYSTEM, so admin privileges are required for all operations
    param([bool]$Disable = $false)

    $serviceScriptPath = Join-Path $PSScriptRoot "install-docker-autorestart-service.ps1"

    if (-not (Test-Path $serviceScriptPath)) {
        Write-ReloadLog "Docker service script not found: $serviceScriptPath" "WARN"
        return
    }

    # Check if we're admin - service operations require elevation
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdminForService = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    try {
        if ($Disable) {
            Write-ReloadLog "SERVICES: Disabling Docker auto-restart service..." "INFO"
            Write-Host "   Disabling Docker auto-restart service..." -ForegroundColor Yellow

            if (-not $isAdminForService) {
                Write-Host "   (Requires admin - launching elevated prompt...)" -ForegroundColor Gray
                Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$serviceScriptPath`" -Pause" -Wait -ErrorAction SilentlyContinue
                Write-ReloadLog "Docker auto-restart service paused (via elevation)" "SUCCESS"
                Write-Host "   Service paused" -ForegroundColor Green
                return
            }

            # Admin path - use direct cmdlet
            try {
                $task = Get-ScheduledTask -TaskName "CaseStrainer-Docker-AutoRestart" -ErrorAction SilentlyContinue
                if ($task) {
                    Disable-ScheduledTask -TaskName "CaseStrainer-Docker-AutoRestart" -ErrorAction Stop
                    Write-ReloadLog "Docker auto-restart service paused" "SUCCESS"
                    Write-Host "   Service paused (Docker will not auto-restart)" -ForegroundColor Green
                } else {
                    Write-ReloadLog "Service task not found - nothing to pause" "INFO"
                    Write-Host "   Service not installed (nothing to pause)" -ForegroundColor Gray
                }
            } catch {
                Write-ReloadLog "Failed to pause service: $($_.Exception.Message)" "WARN"
                Write-Host "   WARNING: Could not pause service: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        } else {
            Write-ReloadLog "SERVICES: Ensuring Docker auto-restart service is enabled..." "INFO"
            Write-Host "   Checking Docker auto-restart service..." -ForegroundColor Cyan

            if (-not $isAdminForService) {
                # Non-admin: Check if service exists by looking at the log file timestamp
                $logFile = Join-Path $PSScriptRoot "logs\docker-autorestart-service.log"
                if (Test-Path $logFile) {
                    $lastWrite = (Get-Item $logFile).LastWriteTime
                    $minutesAgo = ((Get-Date) - $lastWrite).TotalMinutes
                    if ($minutesAgo -lt 5) {
                        Write-ReloadLog "Service appears to be running (log updated $([int]$minutesAgo) min ago)" "INFO"
                        Write-Host "   Service is running (log active)" -ForegroundColor Green
                        return
                    }
                }
                # Service may not be running - offer to resume with elevation
                Write-Host "   Service status unknown (run as admin to manage)" -ForegroundColor Gray
                Write-Host "   Tip: Run '.\cslauncher.ps1 -InstallService' as admin for one-time setup" -ForegroundColor Gray
                return
            }

            # Admin path - direct check and enable
            try {
                $task = Get-ScheduledTask -TaskName "CaseStrainer-Docker-AutoRestart" -ErrorAction SilentlyContinue
            } catch {
                Write-ReloadLog "Exception checking service: $($_.Exception.Message)" "WARN"
                Write-Host "   WARNING: Could not check service status (skipping)" -ForegroundColor Yellow
                return
            }

            if ($task) {
                # Service exists - check if it's enabled
                if ($task.State -eq 'Running' -or $task.Settings.Enabled) {
                    Write-ReloadLog "Docker auto-restart service is already enabled" "INFO"
                    Write-Host "   Service is enabled" -ForegroundColor Green
                } else {
                    # Service exists but is disabled - resume it
                    Write-ReloadLog "Resuming Docker auto-restart service..." "INFO"
                    Write-Host "   Resuming service..." -ForegroundColor Yellow

                    try {
                        Enable-ScheduledTask -TaskName "CaseStrainer-Docker-AutoRestart" -ErrorAction Stop
                        # Also start the task to run immediately
                        Start-ScheduledTask -TaskName "CaseStrainer-Docker-AutoRestart" -ErrorAction SilentlyContinue
                        Write-ReloadLog "Docker auto-restart service resumed" "SUCCESS"
                        Write-Host "   Service resumed" -ForegroundColor Green
                    } catch {
                        Write-ReloadLog "Failed to resume service: $($_.Exception.Message)" "WARN"
                        Write-Host "   WARNING: Could not resume service: $($_.Exception.Message)" -ForegroundColor Yellow
                    }
                }
            } else {
                # Service doesn't exist - prompt for installation
                Write-ReloadLog "Service not installed" "INFO"
                Write-Host "   Service not installed" -ForegroundColor Yellow
                Write-Host "   Run '.\cslauncher.ps1 -InstallService' to set up auto-restart" -ForegroundColor Gray
            }
        }
    } catch {
        Write-ReloadLog "Exception managing Docker service: $($_.Exception.Message)" "WARN"
        Write-Host "   WARNING: Could not manage Docker service: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Test-AdminPrivileges {
    # Check if running with administrator privileges
    try {
        $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Write-ReloadLog {
    # Write to reload log file
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    if ($LogErrors -or $Level -eq "ERROR") {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$Level] $Message"
        Add-Content -Path $reloadLogPath -Value $logEntry -ErrorAction SilentlyContinue
    }

    switch ($Level) {
        "ERROR"   { Write-Host $Message -ForegroundColor Red }
        "WARN"    { Write-Host $Message -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        "INFO"    { Write-Host $Message -ForegroundColor Cyan }
        default   { Write-Host $Message }
    }
}

function Test-DockerHealth {
    # Check if Docker daemon is healthy
    param([bool]$AttemptRecovery = $false)

    try {
        $info = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-DockerDiagnosticsLog "DOCKER_HEALTH: Failed - exit code $LASTEXITCODE" "ERROR"
            if ($AttemptRecovery) {
                Invoke-CaptureCrashDiagnostics
                return Invoke-DockerRecovery
            }
            return $false
        }
        # Check for 500 errors or connection issues
        if ($info -match "error|ERROR|Cannot connect|500 Internal Server Error") {
            Write-DockerDiagnosticsLog "DOCKER_HEALTH: Failed - error in response: $($info -join ' ')" "ERROR"
            if ($AttemptRecovery) {
                Invoke-CaptureCrashDiagnostics
                return Invoke-DockerRecovery
            }
            return $false
        }
        Write-DockerDiagnosticsLog "DOCKER_HEALTH: Healthy" "INFO"
        return $true
    } catch {
        Write-DockerDiagnosticsLog "DOCKER_HEALTH: Exception: $($_.Exception.Message)" "ERROR"
        if ($AttemptRecovery) {
            Invoke-CaptureCrashDiagnostics
            return Invoke-DockerRecovery
        }
        return $false
    }
}

function Invoke-DockerRecovery {
    # Attempt to recover Docker Desktop automatically
    Write-Host "   Attempting Docker Desktop recovery..." -ForegroundColor Yellow

    # Try the official restart command first (cleanest approach)
    $restartResult = docker desktop restart 2>&1
    if ($LASTEXITCODE -eq 0 -or $restartResult -match "Starting") {
        Write-Host "   Docker Desktop restarting..." -ForegroundColor Cyan

        # Wait for Docker to become healthy
        $maxWait = 60  # seconds
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            Write-Host "   Waiting for Docker... ($waited/$maxWait sec)" -ForegroundColor Gray

            $testInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0 -and $testInfo -notmatch "500 Internal Server Error") {
                Write-Host "   Docker Desktop recovered!" -ForegroundColor Green
                return $true
            }
        }
    }

    Write-Host "   Auto-recovery failed. Manual restart required." -ForegroundColor Red
    return $false
}

function Get-DockerMemoryUsage {
    # Get Docker memory usage in GB
    try {
        # Get all container stats
        $dockerStats = docker stats --no-stream --format "{{.MemUsage}}" 2>$null | Select-Object -First 10
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        $totalGB = 0
        foreach ($stat in $dockerStats) {
            if ($stat -match '([\d.]+)([GMK]iB)') {
                $value = [decimal]$matches[1]
                $unit = $matches[2]

                switch ($unit) {
                    'GiB' { $totalGB += $value }
                    'MiB' { $totalGB += $value / 1024 }
                    'KiB' { $totalGB += $value / 1048576 }
                }
            }
        }

        return $totalGB
    } catch {
        return $null
    }
}

function Get-DockerDiskUsage {
    # Get Docker disk usage in GB
    try {
        $systemDf = docker system df --format "{{.Size}}" 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        $totalSize = 0
        $systemDf | ForEach-Object {
            if ($_ -match '([\d.]+)\s*(GB|MB|KB)') {
                $value = [decimal]$matches[1]
                $unit = $matches[2]

                switch ($unit) {
                    'GB' { $totalSize += $value }
                    'MB' { $totalSize += $value / 1024 }
                    'KB' { $totalSize += $value / 1048576 }
                }
            }
        }

        return $totalSize
    } catch {
        return $null
    }
}

function Invoke-SmartDockerCleanup {
    # Smart Docker cleanup based on memory/disk thresholds
    param([bool]$Force = $false)

    Write-ReloadLog "CLEANUP: Checking if Docker cleanup is needed..." "INFO"

    $memUsage = Get-DockerMemoryUsage
    $diskUsage = Get-DockerDiskUsage

    if ($memUsage) {
        Write-Host "   Docker memory: $([math]::Round($memUsage, 2)) GB" -ForegroundColor Gray
    }
    if ($diskUsage) {
        Write-Host "   Docker disk: $([math]::Round($diskUsage, 2)) GB" -ForegroundColor Gray
    }

    $needsCleanup = $Force
    $reason = ""

    if (-not $needsCleanup -and $memUsage -and $memUsage -gt $MemoryThresholdGB) {
        $needsCleanup = $true
        $reason = "Memory ($([math]::Round($memUsage, 2))GB) > threshold ($MemoryThresholdGB GB)"
    }

    if (-not $needsCleanup -and $diskUsage -and $diskUsage -gt $DiskThresholdGB) {
        $needsCleanup = $true
        $reason = "Disk ($([math]::Round($diskUsage, 2))GB) > threshold ($DiskThresholdGB GB)"
    }

    if ($needsCleanup) {
        Write-ReloadLog "   Cleanup needed: $reason" "WARN"

        Write-Host "   Pruning build cache..." -ForegroundColor Gray
        $pruneResult = docker builder prune -f 2>&1
        if ($LASTEXITCODE -eq 0) {
            $reclaimedMatch = $pruneResult | Select-String "Total reclaimed"
            if ($reclaimedMatch) {
                Write-Host "   $reclaimedMatch" -ForegroundColor Green
            }
        }

        Write-Host "   Pruning containers..." -ForegroundColor Gray
        docker container prune -f 2>&1 | Out-Null

        Write-Host "   Pruning images..." -ForegroundColor Gray
        docker image prune -f 2>&1 | Out-Null

        Write-ReloadLog "   Cleanup complete" "SUCCESS"
    } else {
        Write-Host "   No cleanup needed - resources within limits" -ForegroundColor Green
    }
}

function Write-DockerDiagnosticsLog {
    # Write to Docker diagnostics log file
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $dockerDiagnosticsLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-HealthcheckLog {
    # Write healthcheck results to persistent log
    param(
        [string]$ContainerName,
        [string]$Status,
        [string]$Details = ""
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] HEALTHCHECK: $ContainerName -> $Status"
    if ($Details) {
        $logEntry += " ($Details)"
    }
    Add-Content -Path $dockerHealthcheckLogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Get-SystemResources {
    # Get system resource usage
    try {
        $memInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        $cpuInfo = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue
        
        $resources = @{
            TotalMemoryGB = [math]::Round($memInfo.TotalVisibleMemorySize / 1MB, 2)
            AvailableMemoryGB = [math]::Round($memInfo.FreePhysicalMemory / 1MB, 2)
            UsedMemoryGB = [math]::Round(($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / 1MB, 2)
            MemoryPercent = [math]::Round((($memInfo.TotalVisibleMemorySize - $memInfo.FreePhysicalMemory) / $memInfo.TotalVisibleMemorySize) * 100, 1)
            CPUName = $cpuInfo.Name
            CPUCount = $cpuInfo.NumberOfCores
        }
        
        return $resources
    } catch {
        return $null
    }
}

function Get-DockerDesktopProcessInfo {
    # Get Docker Desktop process information
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

function Get-ContainerHealthStatus {
    # Get health status of all containers
    try {
        $containers = docker ps -a --format "{{.Names}}|{{.Status}}|{{.State}}|{{.Health}}" 2>&1
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        
        $status = @()
        foreach ($line in $containers) {
            $parts = $line -split '\|'
            if ($parts.Count -ge 4) {
                $status += @{
                    Name = $parts[0]
                    Status = $parts[1]
                    State = $parts[2]
                    Health = $parts[3]
                }
            }
        }
        return $status
    } catch {
        return $null
    }
}

function Invoke-CaptureDockerDiagnostics {
    # Capture comprehensive Docker diagnostics for crash analysis
    param([string]$Context = "Routine Check")
    
    Write-DockerDiagnosticsLog "=== DOCKER DIAGNOSTICS CAPTURE: $Context ===" "INFO"
    
    # System resources
    $resources = Get-SystemResources
    if ($resources) {
        Write-DockerDiagnosticsLog "SYSTEM: Memory - Total: $($resources.TotalMemoryGB)GB, Available: $($resources.AvailableMemoryGB)GB, Used: $($resources.UsedMemoryGB)GB ($($resources.MemoryPercent)%)" "INFO"
        Write-DockerDiagnosticsLog "SYSTEM: CPU - $($resources.CPUName) ($($resources.CPUCount) cores)" "INFO"
    }
    
    # Docker Desktop process info
    $dockerProcs = Get-DockerDesktopProcessInfo
    if ($dockerProcs) {
        foreach ($proc in $dockerProcs) {
            Write-DockerDiagnosticsLog "DOCKER_DESKTOP: PID=$($proc.Id), CPU=$($proc.CPU)s, Memory=$($proc.WorkingSetMB)MB, Started=$($proc.StartTime)" "INFO"
        }
    } else {
        Write-DockerDiagnosticsLog "DOCKER_DESKTOP: Process not found" "WARN"
    }
    
    # Docker daemon info
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-DockerDiagnosticsLog "DOCKER_DAEMON: Healthy - responding to 'docker info'" "INFO"
            
            # Extract key info
            if ($dockerInfo -match "Total Memory:\s*([\d.]+)\s*GiB") {
                Write-DockerDiagnosticsLog "DOCKER_DAEMON: Total Memory: $($matches[1]) GiB" "INFO"
            }
            if ($dockerInfo -match "CPUs:\s*(\d+)") {
                Write-DockerDiagnosticsLog "DOCKER_DAEMON: CPUs: $($matches[1])" "INFO"
            }
        } else {
            Write-DockerDiagnosticsLog "DOCKER_DAEMON: Unhealthy - 'docker info' failed (exit code: $LASTEXITCODE)" "ERROR"
            Write-DockerDiagnosticsLog "DOCKER_DAEMON: Error output: $($dockerInfo -join ' ')" "ERROR"
        }
    } catch {
        Write-DockerDiagnosticsLog "DOCKER_DAEMON: Exception checking daemon: $($_.Exception.Message)" "ERROR"
    }
    
    # Docker resource usage
    $memUsage = Get-DockerMemoryUsage
    $diskUsage = Get-DockerDiskUsage
    if ($memUsage) {
        Write-DockerDiagnosticsLog "DOCKER_RESOURCES: Memory usage: $([math]::Round($memUsage, 2)) GB" "INFO"
    }
    if ($diskUsage) {
        Write-DockerDiagnosticsLog "DOCKER_RESOURCES: Disk usage: $([math]::Round($diskUsage, 2)) GB" "INFO"
    }
    
    # Container health status
    $containerStatus = Get-ContainerHealthStatus
    if ($containerStatus) {
        foreach ($container in $containerStatus) {
            $healthStatus = if ($container.Health) { $container.Health } else { "no-healthcheck" }
            Write-DockerDiagnosticsLog "CONTAINER: $($container.Name) - State: $($container.State), Status: $($container.Status), Health: $healthStatus" "INFO"
            
            # Log healthcheck result
            Write-HealthcheckLog -ContainerName $container.Name -Status $healthStatus -Details $container.Status
        }
    }
    
    # Backend healthcheck (if container exists)
    try {
        $backendHealth = docker exec casestrainer-backend-prod curl -f http://localhost:5000/casestrainer/api/health 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-DockerDiagnosticsLog "BACKEND_HEALTHCHECK: Success - backend responding" "INFO"
            Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "200" -Details "API health check passed"
        } else {
            Write-DockerDiagnosticsLog "BACKEND_HEALTHCHECK: Failed - exit code: $LASTEXITCODE" "WARN"
            Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "FAILED" -Details "Exit code: $LASTEXITCODE"
        }
    } catch {
        Write-DockerDiagnosticsLog "BACKEND_HEALTHCHECK: Exception: $($_.Exception.Message)" "WARN"
        Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "ERROR" -Details $_.Exception.Message
    }
    
    # Recent Docker events (last 10) - with timeout to prevent hanging
    try {
        # Use a background job with timeout to prevent hanging
        $job = Start-Job -ScriptBlock {
            docker events --since 5m 2>&1 | Select-Object -First 10
        }
        $events = Wait-Job -Job $job -Timeout 3 | Receive-Job
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -ErrorAction SilentlyContinue
        
        if ($events -and $events.Count -gt 0) {
            Write-DockerDiagnosticsLog "DOCKER_EVENTS: Recent events (last 5 minutes):" "INFO"
            foreach ($event in $events) {
                if ($event) {
                    Write-DockerDiagnosticsLog "  $event" "INFO"
                }
            }
        }
    } catch {
        # Events may not be available, ignore
    }
    
    # Windows Event Log entries related to Docker (last 5)
    try {
        $dockerEvents = Get-EventLog -LogName Application -Source "*Docker*" -Newest 5 -ErrorAction SilentlyContinue
        if ($dockerEvents) {
            Write-DockerDiagnosticsLog "WINDOWS_EVENTS: Recent Docker-related events:" "INFO"
            foreach ($event in $dockerEvents) {
                Write-DockerDiagnosticsLog "  [$($event.TimeGenerated)] $($event.EntryType): $($event.Message)" "INFO"
            }
        }
    } catch {
        # May not have permissions, ignore
    }
    
    # System errors related to Docker (last 5)
    try {
        $systemErrors = Get-EventLog -LogName System -Source "*Docker*" -Newest 5 -ErrorAction SilentlyContinue
        if ($systemErrors) {
            Write-DockerDiagnosticsLog "SYSTEM_EVENTS: Recent Docker-related system events:" "INFO"
            foreach ($event in $systemErrors) {
                Write-DockerDiagnosticsLog "  [$($event.TimeGenerated)] $($event.EntryType): $($event.Message)" "WARN"
            }
        }
    } catch {
        # May not have permissions, ignore
    }
    
    Write-DockerDiagnosticsLog "=== DIAGNOSTICS CAPTURE COMPLETE ===" "INFO"
}

function Invoke-CaptureCrashDiagnostics {
    # Capture diagnostics when Docker crash is detected
    Write-DockerDiagnosticsLog "=== CRASH DETECTED - CAPTURING DIAGNOSTICS ===" "ERROR"
    
    # Capture full diagnostics
    Invoke-CaptureDockerDiagnostics -Context "CRASH DETECTED"
    
    # Try to capture container logs before they're lost
    $containers = @(
        "casestrainer-backend-prod",
        "casestrainer-rqworker1-prod",
        "casestrainer-rqworker2-prod"
    )
    
    foreach ($container in $containers) {
        try {
            $logs = docker logs --tail 50 $container 2>&1
            if ($LASTEXITCODE -eq 0) {
                $logFile = Join-Path $logsDir "crash_${container}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
                $logs | Out-File -FilePath $logFile -Encoding UTF8
                Write-DockerDiagnosticsLog "CRASH_LOG: Saved $container logs to $logFile" "INFO"
            }
        } catch {
            Write-DockerDiagnosticsLog "CRASH_LOG: Failed to capture logs for $container : $($_.Exception.Message)" "WARN"
        }
    }
    
    Write-DockerDiagnosticsLog "=== CRASH DIAGNOSTICS COMPLETE ===" "ERROR"
}

function Test-VueBuildNeeded {
    # Check if Vue frontend needs to be rebuilt
    # Returns true if Vue source files are newer than dist files, or if dist doesn't exist
    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    $distIndexPath = Join-Path $vueDir "dist\index.html"
    $srcDir = Join-Path $vueDir "src"
    
    if (-not (Test-Path $srcDir)) {
        Write-ReloadLog "Vue source directory not found: $srcDir" "WARN"
        return $false
    }
    
    # If dist doesn't exist, we need to build
    if (-not (Test-Path $distIndexPath)) {
        Write-ReloadLog "Vue dist not found - build needed" "INFO"
        return $true
    }
    
    # Check if any Vue source files are newer than dist
    try {
        $distTime = (Get-Item $distIndexPath).LastWriteTime
        $vueSourceFiles = Get-ChildItem -Path $srcDir -Recurse -File -Include "*.vue","*.js","*.ts","*.css","*.scss" -ErrorAction SilentlyContinue
        
        if ($vueSourceFiles) {
            $newestSource = $vueSourceFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($newestSource -and $newestSource.LastWriteTime -gt $distTime) {
                Write-ReloadLog "Vue source files newer than dist - build needed (newest: $($newestSource.Name) at $($newestSource.LastWriteTime))" "INFO"
                return $true
            }
        }
        
        return $false
    } catch {
        Write-ReloadLog "Error checking Vue build status: $($_.Exception.Message)" "WARN"
        return $false
    }
}

function Test-FrontendContainerRebuildNeeded {
    # Check if frontend container needs to be rebuilt
    # Returns true if dist is newer than the container, or if container doesn't exist
    try {
        # Get container creation time
        $containerInfo = docker inspect casestrainer-frontend-prod --format '{{.Created}}' 2>&1
        if ($LASTEXITCODE -ne 0 -or -not $containerInfo) {
            Write-ReloadLog "Frontend container not found or inspect failed - rebuild needed" "INFO"
            return $true
        }
        
        # Parse container creation time (ISO 8601 format)
        $containerTime = [DateTime]::Parse($containerInfo)
        
        # Get dist build time
        $distIndexPath = Join-Path $PSScriptRoot "casestrainer-vue-new\dist\index.html"
        if (-not (Test-Path $distIndexPath)) {
            Write-ReloadLog "Dist not found - container rebuild not needed (no dist to use)" "INFO"
            return $false
        }
        
        $distTime = (Get-Item $distIndexPath).LastWriteTime
        
        # If dist is newer than container, rebuild needed
        if ($distTime -gt $containerTime) {
            $timeDiff = $distTime - $containerTime
            Write-ReloadLog "Frontend container rebuild needed - dist is $([math]::Round($timeDiff.TotalHours, 1)) hours newer than container" "INFO"
            return $true
        }
        
        return $false
    } catch {
        Write-ReloadLog "Error checking frontend container rebuild status: $($_.Exception.Message)" "WARN"
        # If we can't check, assume rebuild is needed to be safe
        return $true
    }
}

function Invoke-BuildVueFrontend {
    # Build Vue.js frontend using npm
    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    
    if (-not (Test-Path $vueDir)) {
        Write-ReloadLog "Vue directory not found: $vueDir" "WARN"
        Write-Host "   WARNING: Vue directory not found - skipping frontend build" -ForegroundColor Yellow
        return $false
    }
    
    Push-Location $vueDir
    try {
        $buildStartTime = Get-Date
        Write-Host "   Building Vue frontend..." -ForegroundColor Yellow
        Write-ReloadLog "VUE BUILD: Starting npm run build..." "INFO"
        
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "   Installing npm dependencies..." -ForegroundColor Yellow
            Write-ReloadLog "VUE BUILD: Installing npm dependencies..." "INFO"
            $npmInstall = npm install 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ReloadLog "VUE BUILD: npm install failed - $npmInstall" "ERROR"
                Write-Host "   ERROR: npm install failed" -ForegroundColor Red
                return $false
            }
        }
        
        # Build Vue
        $buildOutput = npm run build 2>&1
        $buildExitCode = $LASTEXITCODE
        $buildDuration = ((Get-Date) - $buildStartTime).TotalSeconds
        
        if ($buildExitCode -eq 0) {
            Write-Host "   Vue frontend built successfully ($([math]::Round($buildDuration, 1))s)" -ForegroundColor Green
            Write-ReloadLog "VUE BUILD: Completed successfully in $([math]::Round($buildDuration, 1)) seconds" "SUCCESS"
            return $true
        } else {
            Write-ReloadLog "VUE BUILD: Failed with exit code $buildExitCode - $buildOutput" "ERROR"
            Write-Host "   ERROR: Vue build failed (exit code: $buildExitCode)" -ForegroundColor Red
            if ($VerbosePreference -eq 'Continue') {
                Write-Host "   Build output:" -ForegroundColor Gray
                $buildOutput | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkGray }
            }
            return $false
        }
    } catch {
        Write-ReloadLog "VUE BUILD: Exception during build: $($_.Exception.Message)" "ERROR"
        Write-Host "   ERROR: Vue build exception: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    } finally {
        Pop-Location
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CaseStrainer Development Launcher" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-ReloadLog "=== RELOAD STARTED ===" "INFO"

# Check admin privileges
$isAdmin = Test-AdminPrivileges
if (-not $isAdmin) {
    Write-ReloadLog "WARNING: Not running as Administrator" "WARN"
    Write-Host "   Some Docker operations may require admin privileges" -ForegroundColor Yellow
    Write-Host "   Right-click PowerShell and 'Run as Administrator' if issues occur" -ForegroundColor Gray
    Write-Host ""
}

# Handle -InstallService: Install the auto-restart service (requires admin, one-time setup)
if ($InstallService) {
    Write-Host ""
    Write-Host "=== INSTALLING DOCKER AUTO-RESTART SERVICE ===" -ForegroundColor Cyan
    Write-Host ""

    if (-not $isAdmin) {
        Write-Host "   ERROR: Installing the service requires Administrator privileges!" -ForegroundColor Red
        Write-Host ""
        Write-Host "   Please either:" -ForegroundColor Yellow
        Write-Host "   1. Run PowerShell as Administrator and try again" -ForegroundColor Gray
        Write-Host "   2. Or run: Start-Process PowerShell -Verb RunAs -ArgumentList '-File', '$PSCommandPath', '-InstallService'" -ForegroundColor Gray
        Write-Host ""

        $response = Read-Host "   Would you like to launch an elevated PowerShell to install? (Y/N)"
        if ($response -eq 'Y' -or $response -eq 'y') {
            Write-Host "   Launching elevated PowerShell..." -ForegroundColor Yellow
            Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSScriptRoot\install-docker-autorestart-service.ps1`" -Install -ProjectRoot `"$PSScriptRoot`""
            Write-Host "   Please complete the installation in the elevated window." -ForegroundColor Green
        }
        exit 0
    }

    # Run the installer directly
    $installerPath = Join-Path $PSScriptRoot "install-docker-autorestart-service.ps1"
    if (Test-Path $installerPath) {
        & $installerPath -Install -ProjectRoot $PSScriptRoot
    } else {
        Write-Host "   ERROR: Installer not found at: $installerPath" -ForegroundColor Red
    }
    exit 0
}

# Handle -UpdateDocker: Pause service for Docker update
if ($UpdateDocker) {
    Write-Host ""
    Write-Host "=== DOCKER UPDATE MODE ===" -ForegroundColor Cyan
    Write-Host ""

    if (-not $isAdmin) {
        Write-Host "   Pausing the service requires Administrator privileges." -ForegroundColor Yellow
        Write-Host ""
        $response = Read-Host "   Would you like to launch an elevated PowerShell to pause? (Y/N)"
        if ($response -eq 'Y' -or $response -eq 'y') {
            Write-Host "   Launching elevated PowerShell..." -ForegroundColor Yellow
            Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSScriptRoot\install-docker-autorestart-service.ps1`" -Pause" -Wait
            Write-Host ""
            Write-Host "   Service paused. You can now safely update Docker Desktop." -ForegroundColor Green
            Write-Host ""
            Write-Host "   After updating Docker:" -ForegroundColor Yellow
            Write-Host "   1. Start Docker Desktop" -ForegroundColor Gray
            Write-Host "   2. Wait for it to be ready" -ForegroundColor Gray
            Write-Host "   3. Run: .\cslauncher.ps1" -ForegroundColor Gray
            Write-Host "      (This will re-enable the auto-restart service)" -ForegroundColor Gray
        }
        exit 0
    }

    Write-Host "   Pausing Docker auto-restart service for update..." -ForegroundColor Yellow

    # Use the installer script's -Pause option for proper handling
    $installerPath = Join-Path $PSScriptRoot "install-docker-autorestart-service.ps1"
    if (Test-Path $installerPath) {
        & $installerPath -Pause
    } else {
        Invoke-ManageDockerService -Disable:$true
    }

    Write-Host ""
    Write-Host "   Service paused. You can now safely update Docker Desktop." -ForegroundColor Green
    Write-Host ""
    Write-Host "   After updating Docker:" -ForegroundColor Yellow
    Write-Host "   1. Start Docker Desktop" -ForegroundColor Gray
    Write-Host "   2. Wait for it to be ready" -ForegroundColor Gray
    Write-Host "   3. Run: .\cslauncher.ps1" -ForegroundColor Gray
    Write-Host "      (This will re-enable the auto-restart service)" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Manage Docker auto-restart service (default: enabled, unless -ServicesOff specified)
Invoke-ManageDockerService -Disable:$ServicesOff

# Capture baseline diagnostics before health check
Invoke-CaptureDockerDiagnostics -Context "Pre-HealthCheck Baseline"

# Check Docker health (with auto-recovery)
Write-ReloadLog "DOCKER: Checking Docker daemon..." "INFO"
if (-not (Test-DockerHealth -AttemptRecovery $false)) {
    Write-ReloadLog "DOCKER: Docker not healthy, attempting auto-recovery..." "WARN"
    if (-not (Test-DockerHealth -AttemptRecovery $true)) {
        Write-ReloadLog "ERROR: Docker daemon is not healthy and auto-recovery failed!" "ERROR"
        Write-Host ""
        Write-Host "   Diagnostics saved to: $dockerDiagnosticsLogPath" -ForegroundColor Cyan
        Write-Host "   Healthcheck log: $dockerHealthcheckLogPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   Please restart Docker Desktop manually:" -ForegroundColor Yellow
        Write-Host "   1. Right-click Docker icon in system tray" -ForegroundColor Gray
        Write-Host "   2. Select 'Quit Docker Desktop'" -ForegroundColor Gray
        Write-Host "   3. Wait 10 seconds" -ForegroundColor Gray
        Write-Host "   4. Start Docker Desktop again" -ForegroundColor Gray
        Write-Host "   Or run: docker desktop restart" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}
Write-Host "   Docker daemon is healthy" -ForegroundColor Green

# Capture diagnostics after successful health check
Invoke-CaptureDockerDiagnostics -Context "Post-HealthCheck Success"

# Step 1: Smart Docker Cleanup (if needed or forced)
Write-Host ""
if ($CleanDocker) {
    Invoke-SmartDockerCleanup -Force $true
} else {
    Invoke-SmartDockerCleanup -Force $false
}

# Step 2: Clear Python bytecode cache in ALL containers
Write-Host ""
Write-ReloadLog "BYTECODE: Clearing Python cache..." "INFO"

$containers = @(
    "casestrainer-backend-prod",
    "casestrainer-rqworker1-prod",
    "casestrainer-rqworker2-prod"
)

foreach ($container in $containers) {
    Write-Host "   Clearing $container..." -ForegroundColor Gray

    docker exec $container find /app/src -type d -name __pycache__ -exec rm -rf {} + 2>$null
    docker exec $container find /app/src -name "*.pyc" -delete 2>$null
    docker exec $container find /app/src -name "*.pyo" -delete 2>$null

    if ($VerbosePreference -eq 'Continue') {
        $remaining = docker exec $container find /app/src -name "*.pyc" -o -name "*.pyo" 2>$null
        if (-not $remaining) {
            Write-Host "      Verified: All bytecode cleared" -ForegroundColor DarkGreen
        }
    }
}

Write-ReloadLog "   Python bytecode cleared" "SUCCESS"

# Step 3: Clear ALL caches (Redis + file-based caches for reliability)
Write-Host ""
Write-ReloadLog "CACHE: Clearing ALL caches (Redis + file-based)..." "INFO"

# Clear Redis cache (suppress password warning by redirecting stderr to null first)
Write-Host "   Clearing Redis cache..." -ForegroundColor Gray
docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 FLUSHDB 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Redis cache cleared" -ForegroundColor Green
    Write-ReloadLog "   Redis FLUSHDB succeeded" "SUCCESS"

    if ($VerbosePreference -eq 'Continue') {
        $keyCount = docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 DBSIZE 2>$null
        if ($keyCount -match '^\d+$') {
            Write-Host "      Current keys: $keyCount" -ForegroundColor DarkGreen
            Write-ReloadLog "      Redis keys after flush: $keyCount" "INFO"
        }
    }
} else {
    Write-ReloadLog "   ERROR: Redis FLUSHDB failed (exit code: $LASTEXITCODE)" "ERROR"
    Write-Host "   WARNING: Could not clear Redis cache" -ForegroundColor Yellow
}

# Clear file-based citation cache
Write-Host "   Clearing citation cache files..." -ForegroundColor Gray
$citationCacheResult = docker exec casestrainer-backend-prod sh -c "rm -rf /app/citation_cache/*.json 2>/dev/null && echo 'cleared' || echo 'none'" 2>$null
if ($citationCacheResult -match "cleared") {
    Write-Host "   Citation cache files cleared" -ForegroundColor Green
    Write-ReloadLog "   Citation cache cleared" "SUCCESS"
} else {
    Write-Host "   No citation cache files found" -ForegroundColor DarkGray
    Write-ReloadLog "   No citation cache files to clear" "INFO"
}

# Clear verification cache JSON file
Write-Host "   Clearing verification cache..." -ForegroundColor Gray
$verificationCacheResult = docker exec casestrainer-backend-prod sh -c "rm -f /app/data/verification_cache.json 2>/dev/null && echo 'cleared' || echo 'none'" 2>$null
if ($verificationCacheResult -match "cleared") {
    Write-Host "   Verification cache cleared" -ForegroundColor Green
    Write-ReloadLog "   Verification cache cleared" "SUCCESS"
} else {
    Write-Host "   No verification cache found" -ForegroundColor DarkGray
    Write-ReloadLog "   No verification cache to clear" "INFO"
}

Write-Host "   All caches cleared" -ForegroundColor Green
Write-ReloadLog "   Cache clearing complete: Redis + file-based caches cleared" "SUCCESS"

# Step 4: Build Vue frontend (if needed)
Write-Host ""
Write-ReloadLog "FRONTEND: Checking if Vue frontend needs rebuild..." "INFO"

$frontendRebuilt = $false
$vueBuildNeeded = Test-VueBuildNeeded
$containerRebuildNeeded = Test-FrontendContainerRebuildNeeded

if ($vueBuildNeeded) {
    Write-Host "   Vue source files changed - building frontend..." -ForegroundColor Cyan
    if (Invoke-BuildVueFrontend) {
        Write-Host "   Frontend build complete" -ForegroundColor Green
        $containerRebuildNeeded = $true  # Always rebuild container after successful build
    } else {
        Write-Host "   WARNING: Frontend build failed - continuing with existing dist" -ForegroundColor Yellow
        Write-ReloadLog "FRONTEND: Build failed but continuing with existing dist" "WARN"
    }
} else {
    Write-Host "   Vue frontend is up to date (no rebuild needed)" -ForegroundColor Gray
    Write-ReloadLog "FRONTEND: No rebuild needed - dist is current" "INFO"
}

# Rebuild frontend container if dist is newer than container (even if we didn't just build)
if ($containerRebuildNeeded) {
    Write-Host "   Rebuilding frontend container (to use latest dist files)..." -ForegroundColor Yellow
    Write-ReloadLog "FRONTEND: Rebuilding container to pick up dist changes..." "INFO"
    
    docker-compose -f docker-compose.prod.yml build frontend-prod 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Frontend container rebuilt successfully" -ForegroundColor Green
        Write-ReloadLog "FRONTEND: Container rebuilt successfully" "SUCCESS"
        $frontendRebuilt = $true
    } else {
        Write-Host "   WARNING: Frontend container rebuild failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-ReloadLog "FRONTEND: Container rebuild failed (exit code: $LASTEXITCODE)" "WARN"
    }
} else {
    Write-Host "   Frontend container is up to date (no rebuild needed)" -ForegroundColor Gray
    Write-ReloadLog "FRONTEND: Container is current - no rebuild needed" "INFO"
}

# Step 5: Rebuild backend + workers (if requested)
if ($Build) {
    Write-Host ""
    Write-ReloadLog "BUILD: Rebuilding backend + worker containers..." "INFO"

    # IMPORTANT:
    # The rqworker containers actually execute the citation extraction / verification code.
    # Rebuilding ONLY the backend image can leave workers running old code.
    # To ensure fixes (like strict extraction + name validation) are deployed, we rebuild:
    #   - backend
    #   - rqworker1
    #   - rqworker2
    #
    # CRITICAL: Use --no-cache to ensure source code changes are picked up!
    # Docker layer caching can cause stale code to be used if files haven't changed
    # but logic within them has.
    Write-Host "   Building with --no-cache to ensure latest code..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml build --no-cache backend rqworker1 rqworker2
    if ($LASTEXITCODE -ne 0) {
        Write-ReloadLog "ERROR: Backend/worker build failed!" "ERROR"
        exit 1
    }
    Write-Host "   Backend + workers rebuilt successfully" -ForegroundColor Green
}

# Step 6: Clean up RQ jobs and stale workers BEFORE recreating containers
# This prevents jobs from becoming orphaned when workers are replaced
Write-Host ""
Write-ReloadLog "RQ CLEANUP: Cleaning up stale workers and orphaned jobs..." "INFO"

Write-Host "   Cleaning up stale RQ workers and jobs..." -ForegroundColor Gray
$rqCleanupScript = @'
from redis import Redis
import sys

try:
    r = Redis.from_url('redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')

    # Delete all stale worker registrations
    worker_keys = r.keys('rq:worker:*')
    if worker_keys:
        for key in worker_keys:
            r.delete(key)
        print(f'Cleaned {len(worker_keys)} stale worker registrations')

    # Clean up started job registry (orphaned jobs)
    started_jobs = r.zrange('rq:started:casestrainer', 0, -1)
    if started_jobs:
        for job_id in started_jobs:
            job_id_str = job_id.decode() if isinstance(job_id, bytes) else job_id
            r.delete(f'rq:job:{job_id_str}')
        r.delete('rq:started:casestrainer')
        print(f'Cleaned {len(started_jobs)} orphaned jobs from started registry')

    print('RQ cleanup complete')
except Exception as e:
    print(f'RQ cleanup error (non-fatal): {e}', file=sys.stderr)
    sys.exit(0)  # Don't fail the whole script
'@

# Run cleanup via backend container (has Redis access)
$rqCleanupResult = docker exec casestrainer-backend-prod python -c $rqCleanupScript 2>&1
if ($rqCleanupResult) {
    $rqCleanupResult | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
}
Write-ReloadLog "   RQ cleanup complete" "SUCCESS"

# Step 7: Recreate containers with new images (CRITICAL: use 'up -d' not 'restart'!)
# 'restart' only restarts existing containers - it does NOT use newly built images!
# 'up -d' recreates containers if the image has changed
Write-Host ""
Write-ReloadLog "RESTART: Recreating containers with new images..." "INFO"

Write-Host "   Recreating RQ workers with new images..." -ForegroundColor Gray
docker-compose -f docker-compose.prod.yml up -d rqworker1 rqworker2 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-ReloadLog "   WARNING: Some workers may have failed" "WARN"
}

Write-Host "   Waiting for workers to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host "   Recreating backend with new image..." -ForegroundColor Gray
docker-compose -f docker-compose.prod.yml up -d backend 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-ReloadLog "ERROR: Backend recreation failed!" "ERROR"
    exit 1
}

# Restart frontend if it was rebuilt
if ($frontendRebuilt) {
    Write-Host "   Restarting frontend (to use rebuilt container)..." -ForegroundColor Gray
    docker-compose -f docker-compose.prod.yml up -d frontend-prod 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Frontend restarted with new build" -ForegroundColor Green
        Write-ReloadLog "FRONTEND: Restarted with new build" "SUCCESS"
    } else {
        Write-Host "   WARNING: Frontend restart failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-ReloadLog "FRONTEND: Restart failed (exit code: $LASTEXITCODE)" "WARN"
    }
}

Write-ReloadLog "   All services restarted" "SUCCESS"

# Step 7b: Clear __pycache__ on NEW containers (critical for rq_worker.py code reload)
# The pre-recreation clear (Step 2) runs on OLD containers. The Docker image may
# have baked-in .pyc files that override volume-mounted .py files.
Write-Host ""
Write-ReloadLog "BYTECODE: Clearing __pycache__ on NEW containers..." "INFO"
Start-Sleep -Seconds 2  # Wait for containers to be fully up
foreach ($container in $containers) {
    docker exec $container find /app/src -type d -name __pycache__ -exec rm -rf {} + 2>$null
    docker exec $container find /app/src -name "*.pyc" -delete 2>$null
}
Write-Host "   Bytecode cleared on new containers" -ForegroundColor Green
Write-ReloadLog "   Post-recreation bytecode clear complete" "SUCCESS"

# Step 8: Restart nginx to clear DNS cache and pick up new backend IP
# CRITICAL: nginx caches DNS lookups for upstream servers. When backend container
# is recreated, it may get a new IP. A simple reload doesn't clear the DNS cache,
# so we need a full restart to ensure nginx routes to the new backend container.
Write-Host ""
Write-Host "   Restarting nginx to clear DNS cache..." -ForegroundColor Gray
try {
    # First verify config is valid
    docker exec casestrainer-nginx-prod nginx -t > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        # Full restart to clear DNS cache (reload doesn't clear it)
        docker-compose -f docker-compose.prod.yml restart nginx 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   Nginx restarted (DNS cache cleared)" -ForegroundColor Green
            Write-ReloadLog "   Nginx restarted successfully (DNS cache cleared)" "SUCCESS"
        } else {
            Write-Host "   WARNING: Nginx restart failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
            Write-ReloadLog "   WARNING: Nginx restart failed (exit code: $LASTEXITCODE)" "WARN"
        }
    } else {
        Write-Host "   WARNING: Nginx config test failed, skipping restart" -ForegroundColor Yellow
        Write-ReloadLog "   WARNING: Nginx config test failed, skipping restart" "WARN"
    }
} catch {
    Write-Host "   WARNING: Nginx restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-ReloadLog "   WARNING: Nginx restart exception: $($_.Exception.Message)" "WARN"
}

# Step 8: Health check (unless skipped)
if (-not $SkipHealthCheck) {
    Write-Host ""
    Write-ReloadLog "HEALTH: Waiting for backend..." "INFO"

    Start-Sleep -Seconds 5

    $maxRetries = 15
    $retries = 0
    $healthy = $false

    while (-not $healthy -and $retries -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                Write-Host "   Backend is healthy" -ForegroundColor Green
                Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "200" -Details "API health check successful"

                if ($VerbosePreference -eq 'Continue') {
                    $healthData = $response.Content | ConvertFrom-Json
                    Write-Host "      Status: $($healthData.status)" -ForegroundColor DarkGreen
                    Write-Host "      Version: $($healthData.version)" -ForegroundColor DarkGreen
                }
            } else {
                Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "$($response.StatusCode)" -Details "Non-200 response"
            }
        } catch {
            $retries++
            Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "FAILED" -Details "Attempt $retries/$maxRetries : $($_.Exception.Message)"
            if ($retries -lt $maxRetries) {
                Write-Host "   Waiting... ($retries/$maxRetries)" -ForegroundColor Gray
                Start-Sleep -Seconds 2
            }
        }
    }

    if (-not $healthy) {
        Write-ReloadLog "   WARNING: Health check timed out (backend may still be starting)" "WARN"
        Write-HealthcheckLog -ContainerName "casestrainer-backend-prod" -Status "TIMEOUT" -Details "Failed after $maxRetries attempts"
    }
}

# Step 9: Verify code changes
Write-Host ""
Write-ReloadLog "VERIFY: Checking code changes..." "INFO"

$verifications = @{
    "OOM fix: _cit_count guard (worker)" = "docker exec casestrainer-rqworker1-prod grep -c '_cit_count' /app/src/rq_worker.py"
    "OOM fix: malloc_trim in verification (worker)" = "docker exec casestrainer-rqworker1-prod grep -c 'malloc_trim' /app/src/verification/master.py"
    "OOM fix: gc+malloc_trim in processor (worker)" = "docker exec casestrainer-rqworker1-prod grep -c 'OOM-FIX' /app/src/unified_citation_processor_v2.py"
    "Verification pipeline (worker)" = "docker exec casestrainer-rqworker1-prod grep -c 'verify_citations_batch' /app/src/verification/master.py"
    "Clustering master (backend)" = "docker exec casestrainer-backend-prod grep -c 'cluster_citations_unified_master' /app/src/unified_processing_pipeline.py"
}

$allVerified = $true
foreach ($check in $verifications.GetEnumerator()) {
    $oldErrorAction = $null
    try {
        # Save current error action preference
        $oldErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'SilentlyContinue'
        $result = Invoke-Expression $check.Value 2>$null
        
        # Convert result to integer, defaulting to 0 if it's not a number
        $count = 0
        if ($null -ne $result) {
            if ($result -is [int]) {
                $count = $result
            } elseif ($result -is [string]) {
                $trimmed = $result.Trim()
                if ($trimmed -match '^\d+$') {
                    $count = [int]$trimmed
                }
            }
        }
        
        if ($count -gt 0) {
            Write-Host "   [OK] $($check.Key)" -ForegroundColor Green
        } else {
            Write-Host "   [MISSING] $($check.Key)" -ForegroundColor Red
            Write-ReloadLog "   MISSING FIX: $($check.Key)" "ERROR"
            $allVerified = $false
        }
    } catch {
        Write-Host "   [ERROR] $($check.Key): $($_.Exception.Message)" -ForegroundColor Red
        Write-ReloadLog "   ERROR checking $($check.Key): $($_.Exception.Message)" "ERROR"
        $allVerified = $false
    } finally {
        # Always restore error action preference
        if ($null -ne $oldErrorAction) {
            $ErrorActionPreference = $oldErrorAction
        }
    }
}

if ($allVerified) {
    Write-ReloadLog "   All code changes verified!" "SUCCESS"
} else {
    Write-ReloadLog "   WARNING: Some fixes missing!" "WARN"
    Write-Host ""
    Write-Host "   Volume mount may not be working. Try:" -ForegroundColor Yellow
    Write-Host "      docker-compose -f docker-compose.prod.yml down" -ForegroundColor Gray
    Write-Host "      docker-compose -f docker-compose.prod.yml up -d" -ForegroundColor Gray
}

# Final summary
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "  Code Reload Complete!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""

if ($LogErrors) {
    Write-Host "Reload log: $reloadLogPath" -ForegroundColor Cyan
}

Write-Host "Diagnostics:" -ForegroundColor Yellow
Write-Host "   Docker diagnostics: $dockerDiagnosticsLogPath" -ForegroundColor Cyan
Write-Host "   Healthcheck log: $dockerHealthcheckLogPath" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Clear browser cache (Ctrl+Shift+Delete or Incognito)" -ForegroundColor Gray
Write-Host "   2. Test with fresh document/PDF" -ForegroundColor Gray
Write-Host "   3. Check logs:" -ForegroundColor Gray
Write-Host "      docker logs -f casestrainer-backend-prod | Select-String 'DATE|VERIFY'" -ForegroundColor DarkGray
Write-Host "   4. If Docker crashes, check diagnostics:" -ForegroundColor Gray
Write-Host "      Get-Content $dockerDiagnosticsLogPath -Tail 100" -ForegroundColor DarkGray
Write-Host ""

Write-ReloadLog "=== RELOAD COMPLETE ===" "SUCCESS"

# Capture final diagnostics after successful reload
Invoke-CaptureDockerDiagnostics -Context "Post-Reload Complete"

if ($Verbose) {
    Write-Host "Container Status:" -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml ps
    Write-Host ""
}
