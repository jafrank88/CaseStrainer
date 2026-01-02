# Docker monitoring and restart fixes for cslaunch.ps1
# This file contains enhanced functions to fix Docker event logging and restart issues

# Enhanced function to capture Docker events
function Start-DockerEventMonitoring {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    <#
    .SYNOPSIS
        Starts capturing Docker events in the background and logs them.
    #>
    
    $eventLogPath = Join-Path $PSScriptRoot "logs\docker_events.log"
    
    if (-not $PSCmdlet.ShouldProcess("Docker event monitoring", "Start capturing Docker events to $eventLogPath")) {
        Write-Host "Docker event monitoring was not started (user cancelled)." -ForegroundColor Yellow
        return
    }
    
    # Create event monitoring script block
    $eventScriptBlock = {
        param($LogPath)
        
        # Import logging function (renamed to avoid conflict with built-in Write-EventLog)
        function Write-DockerEventLog {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $LogPath -Value $logEntry
        }
        
        try {
            Write-DockerEventLog "=== DOCKER EVENT MONITORING STARTED ==="
            
            # Stream Docker events continuously
            docker events --format 'Type={{.Type}} Action={{.Action}} Object={{.Object}} Time={{.Time}} Status={{.Status}}' 2>&1 | ForEach-Object {
                if ($_ -and $_.Trim()) {
                    Write-DockerEventLog $_
                }
            }
        } catch {
            Write-DockerEventLog "ERROR: Docker event monitoring failed: $($_.Exception.Message)"
        }
    }
    
    # Start event monitoring in background job
    $eventJob = Start-Job -Name "Docker-Event-Monitor" -ScriptBlock $eventScriptBlock -ArgumentList $eventLogPath
    
    Write-Host "[EVENTS] Docker event monitoring started (job ID: $($eventJob.Id))" -ForegroundColor Cyan
    Write-Host "  - Event log: $eventLogPath" -ForegroundColor Gray
    Write-Host "  - Stop with: Stop-Job -Name Docker-Event-Monitor; Remove-Job -Name Docker-Event-Monitor" -ForegroundColor Gray
    
    return $eventJob
}

# Enhanced Docker health test with better diagnostics
function Test-DockerDaemonHealthDetailed {
    param([int]$TimeoutSeconds = 15)
    
    $healthChecks = @{
        DockerInfo = $false
        DockerVersion = $false
        DockerPs = $false
        DockerService = $false
        Diagnostics = ""
    }
    
    # Check 1: Docker info with detailed error capture
    try {
        $job = Start-Job -ScriptBlock { 
            $result = docker info 2>&1 
            if ($LASTEXITCODE -eq 0) { 
                return @{ success = $true; output = $result }
            } else { 
                return @{ success = $false; output = $result; error = $Error[0].Exception.Message }
            }
        }
        
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $result = Receive-Job $job
            Remove-Job $job -Force
            
            if ($result.success) {
                $healthChecks.DockerInfo = $true
            } else {
                $healthChecks.Diagnostics += "Docker info failed: $($result.error)`n"
            }
        } else {
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
            $healthChecks.Diagnostics += "Docker info check timed out after ${TimeoutSeconds}s`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Docker info exception: $($_.Exception.Message)`n"
    }
    
    # Check 2: Docker service status
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            $healthChecks.DockerService = ($service.Status -eq "Running")
            if (-not $healthChecks.DockerService) {
                $healthChecks.Diagnostics += "Docker service status: $($service.Status)`n"
            }
        } else {
            $healthChecks.Diagnostics += "Docker service not found`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Failed to check Docker service: $($_.Exception.Message)`n"
    }
    
    # Check 3: Docker Desktop process
    try {
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $dockerProcess) {
            $healthChecks.Diagnostics += "Docker Desktop process not running`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Failed to check Docker Desktop process: $($_.Exception.Message)`n"
    }
    
    # Check 4: Quick docker ps test
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker ps 2>&1 }
            if (Wait-Job $job -Timeout 5) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0) {
                    $healthChecks.DockerPs = $true
                } else {
                    $healthChecks.Diagnostics += "Docker ps failed: $($output -join "`n")`n"
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                $healthChecks.Diagnostics += "Docker ps check timed out`n"
            }
        } catch {
            $healthChecks.Diagnostics += "Docker ps exception: $($_.Exception.Message)`n"
        }
    }
    
    return $healthChecks
}

# Enhanced restart function with better diagnostics
function Restart-DockerEnhancedFixed {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [string]$Reason = "Auto-restart triggered",
        [int]$MaxRetries = 3,
        [int]$RetryDelay = 30
    )

    Write-Host "[DOCKER] Starting enhanced Docker restart with diagnostics..." -ForegroundColor Cyan
    Write-DockerDaemonLog "=== ENHANCED DOCKER RESTART INITIATED ===" "WARN"
    Write-DockerDaemonLog "Reason: $Reason" "WARN"

    # Capture system state before restart
    Write-DockerDaemonLog "CAPTURING PRE-RESTART DIAGNOSTICS:" "INFO"
    
    # Check running processes
    $processesBefore = Get-Process | Where-Object { $_.ProcessName -like "*docker*" } | Select-Object ProcessName, Id, CPU, WorkingSet
    Write-DockerDaemonLog "Docker processes before restart: $($processesBefore.Count)" "INFO"
    foreach ($proc in $processesBefore) {
        Write-DockerDaemonLog "  - $($proc.ProcessName) (PID: $($proc.Id), CPU: $([math]::Round($proc.CPU, 2)), Memory: $([math]::Round($proc.WorkingSet/1MB, 2)) MB)" "INFO"
    }
    
    # Check disk space
    $systemDrive = Get-CimInstance -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
    if ($systemDrive) {
        $freeSpaceGB = [math]::Round($systemDrive.FreeSpace / 1GB, 2)
        Write-DockerDaemonLog "C: drive free space: ${freeSpaceGB} GB" "INFO"
        if ($freeSpaceGB -lt 5) {
            Write-DockerDaemonLog "WARNING: Low disk space may prevent Docker from starting" "WARN"
        }
    }
    
    # Check memory usage
    $totalMemory = (Get-CimInstance -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    $freeMemory = (Get-CimInstance -Class Win32_OperatingSystem).FreePhysicalMemory / 1MB
    Write-DockerDaemonLog "System memory: ${totalMemory} GB total, ${freeMemory} GB free" "INFO"
    
    $attempt = 1
    $success = $false
    $isAdmin = Test-AdminPrivileges

    while ($attempt -le $MaxRetries -and -not $success) {
        Write-Host "[DOCKER] Restart attempt $attempt of $MaxRetries..." -ForegroundColor Cyan
        Write-DockerDaemonLog "Restart attempt $attempt of $MaxRetries" "INFO"
        
        try {
            # Step 1: Graceful stop with timeout
            Write-Host "[DOCKER] Stopping Docker Desktop gracefully..." -ForegroundColor Yellow
            
            # Try graceful shutdown first
            $dockerDesktop = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
            if ($dockerDesktop) {
                $dockerDesktop.CloseMainWindow() | Out-Null
                Start-Sleep -Seconds 10
                
                # Check if it's still running
                if ($null -eq $dockerDesktop.HasExited -or -not $dockerDesktop.HasExited) {
                    Write-DockerDaemonLog "Graceful shutdown failed, forcing stop" "WARN"
                    $dockerDesktop.Kill()
                    Start-Sleep -Seconds 5
                }
            }
            
            # Step 2: Stop Docker service if admin
            if ($isAdmin) {
                Write-DockerDaemonLog "Stopping Docker service..." "INFO"
                try {
                    Stop-Service -Name "com.docker.service" -Force -ErrorAction Stop
                    Start-Sleep -Seconds 3
                } catch {
                    Write-DockerDaemonLog "Failed to stop Docker service: $($_.Exception.Message)" "WARN"
                }
            }
            
            # Step 3: Clean up processes
            Write-DockerDaemonLog "Cleaning up Docker processes..." "INFO"
            Get-Process | Where-Object { 
                $_.ProcessName -like "*docker*" -or 
                $_.ProcessName -like "*com.docker*" -or
                $_.ProcessName -like "*vpnkit*" -or
                $_.ProcessName -like "*wsl*" -or
                $_.ProcessName -like "*wslservice*"
            } | Stop-Process -Force -ErrorAction SilentlyContinue
            
            # Step 4: Clean WSL distributions if needed
            if ($isAdmin) {
                try {
                    Write-DockerDaemonLog "Cleaning WSL distributions..." "INFO"
                    wsl --shutdown 2>$null
                    Start-Sleep -Seconds 5
                } catch {
                    Write-DockerDaemonLog "WSL cleanup failed: $($_.Exception.Message)" "WARN"
                }
            }
            
            # Step 5: Start Docker service if admin
            if ($isAdmin) {
                Write-DockerDaemonLog "Starting Docker service..." "INFO"
                try {
                    Start-Service -Name "com.docker.service" -ErrorAction Stop
                    Start-Sleep -Seconds 5
                } catch {
                    Write-DockerDaemonLog "Failed to start Docker service: $($_.Exception.Message)" "WARN"
                }
            }
            
            # Step 6: Start Docker Desktop
            Write-DockerDaemonLog "Starting Docker Desktop..." "INFO"
            $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
            
            if (Test-Path $dockerDesktopPath) {
                $process = Start-Process -FilePath $dockerDesktopPath -PassThru -ErrorAction Stop
                Write-DockerDaemonLog "Started Docker Desktop (PID: $($process.Id))" "INFO"
            } else {
                throw "Docker Desktop executable not found at $dockerDesktopPath"
            }
            
            # Step 7: Wait for Docker with progressive timeout
            Write-DockerDaemonLog "Waiting for Docker to become ready..." "INFO"
            $maxWait = 180  # Increased to 3 minutes
            $startTime = Get-Date
            $dockerReady = $false
            
            for ($i = 0; $i -lt 18; $i++) {  # Check every 10 seconds
                Start-Sleep -Seconds 10
                
                # Try progressively more stringent checks
                if ($i -lt 6) {
                    # First minute: just check if process is running
                    $testProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
                    $dockerReady = ($testProcess -ne $null)
                } elseif ($i -lt 12) {
                    # Second minute: check docker info
                    $null = docker info 2>$null
                    $dockerReady = ($LASTEXITCODE -eq 0)
                } else {
                    # Third minute: check both docker info and docker ps
                    $null = docker info 2>$null
                    $dockerPsResult = docker ps 2>$null
                    $dockerReady = ($LASTEXITCODE -eq 0 -and $dockerPsResult)
                }
                
                if ($dockerReady) {
                    $recoveryTime = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
                    Write-Host "`n[DOCKER] Docker restarted successfully in ${recoveryTime}s!" -ForegroundColor Green
                    Write-DockerDaemonLog "Docker restart successful after ${recoveryTime}s" "SUCCESS"
                    
                    # Capture post-restart diagnostics
                    Write-DockerDaemonLog "POST-RESTART VERIFICATION:" "INFO"
                    $version = docker version --format '{{.Server.Version}}' 2>&1
                    if ($version) {
                        Write-DockerDaemonLog "Docker version: $version" "INFO"
                    }
                    
                    $containers = docker ps -q 2>$null
                    $containerCount = if ($containers) { ($containers | Measure-Object).Count } else { 0 }
                    Write-DockerDaemonLog "Running containers: $containerCount" "INFO"
                    
                    $success = $true
                    break
                }
                
                $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
                Write-Host "[DOCKER] Still waiting... (${elapsed}s elapsed)" -ForegroundColor Yellow
            }
            
            if (-not $dockerReady) {
                throw "Docker did not become ready within $maxWait seconds"
            }
            
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "[DOCKER] Attempt $attempt failed: $errorMsg" -ForegroundColor Red
            Write-DockerDaemonLog "Restart attempt $attempt failed: $errorMsg" "ERROR"
            Write-DockerDaemonLog "Full error: $($_.Exception.ToString())" "ERROR"
            
            # Capture additional diagnostics on failure
            Write-DockerDaemonLog "FAILURE DIAGNOSTICS:" "INFO"
            
            # Check event log for Docker errors
            try {
                $dockerEvents = Get-WinEvent -LogName Application -MaxEvents 5 | Where-Object { $_.Message -like "*Docker*" } | Select-Object TimeCreated, LevelDisplayName, Message
                if ($dockerEvents) {
                    Write-DockerDaemonLog "Recent Application log entries for Docker:" "INFO"
                    foreach ($dockerEvent in $dockerEvents) {
                        Write-DockerDaemonLog "  - $($dockerEvent.TimeCreated): $($dockerEvent.LevelDisplayName) - $($dockerEvent.Message.Substring(0, [math]::Min(200, $dockerEvent.Message.Length)))" "INFO"
                    }
                }
            } catch {
                Write-DockerDaemonLog "Could not check event log: $($_.Exception.Message)" "WARN"
            }
            
            $attempt++
            
            if ($attempt -le $MaxRetries) {
                $retryTime = Get-Date
                Write-Host "[DOCKER] Retrying in $RetryDelay seconds..." -ForegroundColor Yellow
                Write-DockerDaemonLog "Will retry Docker restart at $($retryTime.AddSeconds($RetryDelay))" "WARN"
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }
    
    if (-not $success) {
        $errorMsg = "Failed to restart Docker after $MaxRetries attempts"
        Write-Host "[DOCKER] $errorMsg" -ForegroundColor Red
        Write-DockerDaemonLog $errorMsg "ERROR"
        
        # Final diagnostic dump
        Write-DockerDaemonLog "FINAL DIAGNOSTIC DUMP:" "ERROR"
        
        # Check system resources
        $cpuInfo = Get-CimInstance -Class Win32_Processor | Select-Object LoadPercentage
        $memoryInfo = Get-CimInstance -Class Win32_OperatingSystem | Select-Object @{Name="FreeMemoryGB"; Expression={[math]::Round($_.FreePhysicalMemory / 1GB, 2)}}
        Write-DockerDaemonLog "CPU Load: $($cpuInfo.LoadPercentage)%" "ERROR"
        Write-DockerDaemonLog "Free Memory: $($memoryInfo.FreeMemoryGB) GB" "ERROR"
        
        return $false
    }
    
    return $true
}

# Function to check if Docker is actually frozen (not just slow)
function Test-DockerFrozen {
    param([int]$TimeoutSeconds = 15)
    
    $frozen = $false
    $diagnostics = ""
    
    # Test 1: Check if docker info responds within timeout
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $job = Start-Job -ScriptBlock { docker info 2>&1 }
        
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $output = Receive-Job $job
            $stopwatch.Stop()
            
            if ($LASTEXITCODE -ne 0) {
                $frozen = $true
                $diagnostics = "Docker info returned error: $($output -join '`n')"
            } elseif ($stopwatch.Elapsed.TotalSeconds -gt ($TimeoutSeconds * 0.8)) {
                $diagnostics = "Docker responding very slowly ($([math]::Round($stopwatch.Elapsed.TotalSeconds, 1))s)"
            }
        } else {
            $frozen = $true
            $diagnostics = "Docker info timed out after ${TimeoutSeconds}s"
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
        }
    } catch {
        $frozen = $true
        $diagnostics = "Exception testing Docker: $($_.Exception.Message)"
    }
    
    return @{
        Frozen = $frozen
        Diagnostics = $diagnostics
    }
}

# Function to implement exponential backoff for restart attempts
function Get-BackoffDelay {
    param(
        [int]$AttemptNumber,
        [int]$BaseDelay = 30,
        [int]$MaxDelay = 300
    )
    
    $delay = [math]::Min($BaseDelay * [math]::Pow(2, $AttemptNumber - 1), $MaxDelay)
    return $delay
}

Write-Host "Docker monitoring fixes loaded. Available functions:" -ForegroundColor Green
Write-Host "  - Start-DockerEventMonitoring" -ForegroundColor Gray
Write-Host "  - Test-DockerDaemonHealthDetailed" -ForegroundColor Gray
Write-Host "  - Restart-DockerEnhancedFixed" -ForegroundColor Gray
Write-Host "  - Test-DockerFrozen" -ForegroundColor Gray
Write-Host "  - Get-BackoffDelay" -ForegroundColor Gray
