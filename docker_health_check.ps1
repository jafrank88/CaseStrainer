# Enhanced Docker Health Check with Deep Diagnostics and Auto-Recovery
# Detects and fixes Docker unresponsiveness issues
# Auto-restart is ENABLED by default for automatic recovery
# Includes comprehensive logging for freeze detection and restart tracking

param(
    [int]$MaxCPUPercent = 320,  # 80% of 4 cores = 320%
    [switch]$AutoRestart = $true,  # Auto-restart enabled by default
    [switch]$DeepDiagnostics,
    [switch]$CollectLogs
)

# Logging Configuration - Use absolute paths to avoid system32 issues
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir "logs"
$LogFile = Join-Path $LogDir "docker_health_monitor.log"
$RestartLogFile = Join-Path $LogDir "docker_restart_events.log"
$FreezeLogFile = Join-Path $LogDir "docker_freeze_detection.log"

# Ensure logs directory exists
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-HealthLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$LogPath = $LogFile
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to specified log file
    Add-Content -Path $LogPath -Value $logMessage -Force
    
    # Also write to console with appropriate color
    $color = switch($Level) { 
        "ERROR" { "Red" } 
        "WARN" { "Yellow" } 
        "SUCCESS" { "Green" }
        "RESTART" { "Magenta" }
        "FREEZE" { "Red" }
        "INFO" { "White" } 
        default { "Gray" } 
    }
    Write-Host $logMessage -ForegroundColor $color
}

function Test-DockerFreezeConditions {
    param(
        [string]$TestName,
        [scriptblock]$TestCommand,
        [int]$TimeoutSeconds = 15
    )
    
    Write-HealthLog "Testing for freeze conditions: $TestName" -Level "INFO"
    
    $job = Start-Job -ScriptBlock $TestCommand
    $completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
    
    if ($completed) {
        $result = Receive-Job -Job $job
        Remove-Job -Job $job
        Write-HealthLog "Test '$TestName' completed successfully" -Level "INFO"
        return @{
            Success = $true
            Result = $result
            TimedOut = $false
            Duration = "< $TimeoutSeconds seconds"
        }
    } else {
        Stop-Job -Job $job
        Remove-Job -Job $job
        Write-HealthLog "=== DOCKER FREEZE DETECTED ===" -Level "FREEZE" -LogPath $FreezeLogFile
        Write-HealthLog "Test: $TestName" -Level "FREEZE" -LogPath $FreezeLogFile
        Write-HealthLog "Timeout: $TimeoutSeconds seconds" -Level "FREEZE" -LogPath $FreezeLogFile
        Write-HealthLog "Docker appears to be frozen/unresponsive" -Level "FREEZE" -LogPath $FreezeLogFile
        
        # Collect diagnostic info during freeze
        $processes = Get-Process | Where-Object { $_.ProcessName -like "*docker*" } | Select-Object ProcessName, Id, CPU, WorkingSet
        $processInfo = $processes | Format-Table -AutoSize | Out-String
        Write-HealthLog "Docker processes during freeze:`n$processInfo" -Level "FREEZE" -LogPath $FreezeLogFile
        
        return @{
            Success = $false
            Result = $null
            TimedOut = $true
            Duration = "> $TimeoutSeconds seconds (TIMEOUT)"
        }
    }
}

function Test-DockerPortConflicts {
    Write-Host "Checking for Docker Desktop port conflicts..." -ForegroundColor Cyan
    
    # Check if Docker Desktop processes are binding to common ports
    $conflicts = @()
    
    # Check port 80
    $port80Processes = netstat -ano | findstr ":80" | findstr "LISTENING"
    if ($port80Processes -and ($port80Processes | findstr "13532\|10416")) {
        $conflicts += "Port 80: Docker Desktop processes are binding to port 80"
    }
    
    # Check port 443
    $port443Processes = netstat -ano | findstr ":443" | findstr "LISTENING"
    if ($port443Processes -and ($port443Processes | findstr "13532\|10416")) {
        $conflicts += "Port 443: Docker Desktop processes are binding to port 443"
    }
    
    if ($conflicts.Count -gt 0) {
        Write-Host "⚠️  Port conflicts detected:" -ForegroundColor Yellow
        foreach ($conflict in $conflicts) {
            Write-Host "  - $conflict" -ForegroundColor Yellow
        }
        return $true
    } else {
        Write-Host "✅ No port conflicts detected" -ForegroundColor Green
        return $false
    }
}

function Start-DockerDesktopRecovery {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Reason = "Health check detected issues")
    
    $restartId = [guid]::NewGuid().ToString("N").Substring(0,8)
    Write-HealthLog "=== DOCKER RESTART INITIATED ===" -Level "RESTART" -LogPath $RestartLogFile
    Write-HealthLog "Restart ID: $restartId" -Level "RESTART" -LogPath $RestartLogFile
    Write-HealthLog "Reason: $Reason" -Level "RESTART" -LogPath $RestartLogFile
    Write-HealthLog "Initiated by: Docker Health Check (Auto-Recovery)" -Level "RESTART" -LogPath $RestartLogFile
    
    Write-Host "Starting Docker Desktop recovery... (ID: $restartId)" -ForegroundColor Red
    
    # Step 1: Stop all Docker processes
    Write-Host "1. Stopping Docker Desktop processes..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "com.docker.build" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "wslrelay" -Force -ErrorAction SilentlyContinue
    
    # Step 2: Wait for processes to stop
    Write-Host "2. Waiting for processes to stop..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Step 3: Clean up any hanging processes
    Write-Host "3. Cleaning up hanging processes..." -ForegroundColor Yellow
    $hangingProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*docker*" -and $_.ProcessName -ne "docker-scout" 
    }
    if ($hangingProcesses) {
        $hangingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "   Stopped $($hangingProcesses.Count) hanging processes" -ForegroundColor Yellow
    }
    
    # Step 4: Restart Docker Desktop
    Write-Host "4. Restarting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # Step 5: Wait for Docker to initialize
    Write-Host "5. Waiting for Docker to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 45
    
    # Step 6: Test Docker functionality
    Write-Host "6. Testing Docker functionality..." -ForegroundColor Yellow
    $retryCount = 0
    $maxRetries = 15
    
    do {
        $retryCount++
        Write-Host "   Attempt $retryCount/$maxRetries..." -ForegroundColor Gray
        
        try {
            $dockerVersion = docker --version 2>$null
            if ($dockerVersion) {
                Write-Host "Docker is responsive!" -ForegroundColor Green
                Write-HealthLog "=== DOCKER RESTART SUCCESSFUL ===" -Level "SUCCESS" -LogPath $RestartLogFile
                Write-HealthLog "Restart ID: $restartId" -Level "SUCCESS" -LogPath $RestartLogFile
                Write-HealthLog "Recovery completed in $($retryCount * 10 + 45) seconds" -Level "SUCCESS" -LogPath $RestartLogFile
                Write-HealthLog "Docker version: $dockerVersion" -Level "SUCCESS" -LogPath $RestartLogFile
                return $true
            }
        } catch {
            Write-Host "   Still initializing..." -ForegroundColor Gray
        }
        
        Start-Sleep -Seconds 10
    } while ($retryCount -lt $maxRetries)
    
    Write-Host "Docker failed to recover after $maxRetries attempts" -ForegroundColor Red
    Write-HealthLog "=== DOCKER RESTART FAILED ===" -Level "ERROR" -LogPath $RestartLogFile
    Write-HealthLog "Restart ID: $restartId" -Level "ERROR" -LogPath $RestartLogFile
    Write-HealthLog "Failed after $maxRetries attempts ($(($maxRetries * 10) + 45) seconds)" -Level "ERROR" -LogPath $RestartLogFile
    Write-HealthLog "Manual intervention required" -Level "ERROR" -LogPath $RestartLogFile
    return $false
}

function Test-DockerDeepDiagnostics {
    Write-Host "Deep Diagnostics Mode..." -ForegroundColor Magenta

    # Check Docker Desktop logs
    $dockerLogPath = "$env:LOCALAPPDATA\Docker\log\host\com.docker.backend.exe.log"
    if (Test-Path $dockerLogPath) {
        Write-Host "Docker Desktop Logs (last 20 lines):" -ForegroundColor Cyan
        Get-Content $dockerLogPath -Tail 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "Docker Desktop logs not found at: $dockerLogPath" -ForegroundColor Yellow
    }

    # Check Docker daemon status
    Write-Host "Docker Daemon Status:" -ForegroundColor Cyan
    try {
        $daemonInfo = docker system info 2>$null
        if ($daemonInfo) {
            Write-Host "Docker daemon is responding" -ForegroundColor Green
        } else {
            Write-Host "Docker daemon not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "Docker daemon communication failed" -ForegroundColor Red
    }

    # Check network connectivity
    Write-Host "Network Connectivity:" -ForegroundColor Cyan
    try {
        $netTest = Test-NetConnection -ComputerName localhost -Port 2375 -InformationLevel Quiet 2>$null
        if ($netTest) {
            Write-Host "Docker socket is accessible" -ForegroundColor Green
        } else {
            Write-Host "Docker socket not accessible" -ForegroundColor Red
        }
    } catch {
        Write-Host "Network connectivity test failed" -ForegroundColor Red
    }

    # Check Docker Desktop processes
    Write-Host "Docker Desktop Processes:" -ForegroundColor Cyan
    $dockerProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" }
    foreach ($proc in $dockerProcesses) {
        try {
            $cpuPercent = [math]::Round(($proc.CPU / (Get-CimInstance -ClassName Win32_Processor).NumberOfLogicalProcessors), 1)
            Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: ${cpuPercent}%" -ForegroundColor $(if($cpuPercent -gt 50){"Yellow"}else{"Green"})
        } catch {
            Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: N/A" -ForegroundColor Gray
        }
    }
}

function Start-DockerAutoRecovery {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Host "Auto-Recovery Mode..." -ForegroundColor Red

    # Step 1: Force stop Docker processes
    Write-Host "1. Force stopping Docker processes..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "com.docker.build" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "docker-compose" -Force -ErrorAction SilentlyContinue

    # Step 2: Wait for processes to stop
    Write-Host "2. Waiting for processes to stop..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    # Step 3: Clean up any hanging processes
    Write-Host "3. Cleaning up hanging processes..." -ForegroundColor Yellow
    $hangingProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" -and $_.ProcessName -ne "docker-scout" }
    if ($hangingProcesses) {
        $hangingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "   Stopped $($hangingProcesses.Count) hanging processes" -ForegroundColor Yellow
    }

    # Step 4: Restart Docker Desktop
    Write-Host "4. Restarting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    # Step 5: Wait for Docker to initialize
    Write-Host "5. Waiting for Docker to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # Step 6: Test Docker functionality
    Write-Host "6. Testing Docker functionality..." -ForegroundColor Yellow
    $retryCount = 0
    $maxRetries = 10

    do {
        $retryCount++
        Write-Host "   Attempt $retryCount/$maxRetries..." -ForegroundColor Gray

        try {
            $dockerVersion = docker --version 2>$null
            if ($dockerVersion) {
                Write-Host "Docker is responsive!" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "   Still initializing..." -ForegroundColor Gray
        }

        Start-Sleep -Seconds 10
    } while ($retryCount -lt $maxRetries)

    Write-Host "Docker failed to recover after $maxRetries attempts" -ForegroundColor Red
    return $false
}

function Get-DockerLogs {
    Write-Host "Collecting Docker Logs..." -ForegroundColor Cyan

    $logDir = "logs\docker_diagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null

    # Collect Docker Desktop logs
    $dockerLogPath = "$env:LOCALAPPDATA\Docker\log\host\com.docker.backend.exe.log"
    if (Test-Path $dockerLogPath) {
        Copy-Item $dockerLogPath "$logDir\docker_desktop.log"
        Write-Host "Docker Desktop logs saved to: $logDir\docker_desktop.log" -ForegroundColor Green
    }

    # Collect system information
    $systemInfo = @"
=== System Information ===
OS: $((Get-CimInstance -ClassName Win32_OperatingSystem).Caption)
Docker Version: $(docker --version 2>$null)
Docker Compose Version: $(docker-compose --version 2>$null)
Available Memory: $([math]::Round((Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory/1GB, 2)) GB
CPU Cores: $((Get-CimInstance -ClassName Win32_Processor).NumberOfLogicalProcessors)
"@

    $systemInfo | Out-File "$logDir\system_info.txt"

    # Collect process information
    $processInfo = Get-Process | Where-Object { $_.ProcessName -like "*docker*" } |
                   Select-Object ProcessName, Id, CPU, WorkingSet, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet/1MB,2)}} |
                   Format-Table -AutoSize | Out-String

    $processInfo | Out-File "$logDir\docker_processes.txt"

    Write-Host "Diagnostic logs saved to: $logDir" -ForegroundColor Green
    return $logDir
}

function Test-DockerHealth {
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [int]$MaxCPUPercent = 320,
        [switch]$AutoRestart,
        [switch]$DeepDiagnostics,
        [switch]$CollectLogs
    )

    $results = @{
        Healthy = $false
        Issues = @()
        Details = @()
        RecoveryNeeded = $false
    }

    Write-Host "=== Enhanced Docker Health Check ===" -ForegroundColor Cyan
    Write-HealthLog "=== HEALTH CHECK STARTED ===" -Level "INFO"
    Write-HealthLog "Auto-restart enabled: $AutoRestart" -Level "INFO"
    Write-HealthLog "Max CPU threshold: $MaxCPUPercent%" -Level "INFO"

    # Test 0: Port Conflict Detection
    Write-Host "Testing for port conflicts..." -ForegroundColor Gray
    $portConflicts = Test-DockerPortConflicts
    if ($portConflicts) {
        $results.Issues += "Docker Desktop port conflicts detected"
        $results.RecoveryNeeded = $true
    }

    # Test 1: Docker CLI Responsiveness (with freeze detection)
    Write-Host "Testing Docker CLI responsiveness..." -ForegroundColor Gray
    $cliTest = Test-DockerFreezeConditions -TestName "Docker CLI Version Check" -TestCommand {
        $version = docker --version 2>$null
        if ($version -and $version -match "Docker version") {
            return 0  # Success
        } else {
            return 1  # Failure
        }
    } -TimeoutSeconds 10
    
    if ($cliTest.Success -and $cliTest.Result -eq 0) {
        Write-Host "Docker CLI is responsive ($($cliTest.Duration))" -ForegroundColor Green
        Write-HealthLog "Docker CLI test passed in $($cliTest.Duration)" -Level "INFO"
    } elseif ($cliTest.TimedOut) {
        Write-Host "Docker CLI is frozen/unresponsive (timeout after 10s)" -ForegroundColor Red
        Write-HealthLog "Docker CLI freeze detected - timeout after 10 seconds" -Level "FREEZE" -LogPath $FreezeLogFile
        $results.Issues += "Docker CLI frozen (timeout)"
        $results.RecoveryNeeded = $true
    } else {
        Write-Host "Docker CLI is not responsive" -ForegroundColor Red
        Write-HealthLog "Docker CLI not responsive - returned: $($cliTest.Result)" -Level "ERROR"
        $results.Issues += "Docker CLI unresponsive"
        $results.RecoveryNeeded = $true
    }

    # Test 2: Docker Daemon Communication (with freeze detection)
    Write-Host "Testing Docker daemon communication..." -ForegroundColor Gray
    $daemonTest = Test-DockerFreezeConditions -TestName "Docker Daemon Info" -TestCommand {
        $info = docker system info 2>$null
        if ($info) { return 0 } else { return 1 }
    } -TimeoutSeconds 15
    
    if ($daemonTest.Success -and $daemonTest.Result -eq 0) {
        Write-Host "Docker daemon is responding ($($daemonTest.Duration))" -ForegroundColor Green
        Write-HealthLog "Docker daemon test passed in $($daemonTest.Duration)" -Level "INFO"
    } elseif ($daemonTest.TimedOut) {
        Write-Host "Docker daemon is frozen/unresponsive (timeout after 15s)" -ForegroundColor Red
        Write-HealthLog "Docker daemon freeze detected - timeout after 15 seconds" -Level "FREEZE" -LogPath $FreezeLogFile
        $results.Issues += "Docker daemon frozen (timeout)"
        $results.RecoveryNeeded = $true
    } else {
        Write-Host "Docker daemon not responding" -ForegroundColor Red
        Write-HealthLog "Docker daemon not responding" -Level "ERROR"
        $results.Issues += "Docker daemon unresponsive"
        $results.RecoveryNeeded = $true
    }

    # Test 3: Container Status (if Docker is responsive)
    if (-not $results.RecoveryNeeded) {
        Write-Host "Checking container status..." -ForegroundColor Gray
        try {
            $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
            if ($containers) {
                Write-Host "Containers are accessible" -ForegroundColor Green
                $results.Details += "Containers: $($containers.Count) running"
            } else {
                Write-Host "No containers found or containers not accessible" -ForegroundColor Yellow
                $results.Details += "No containers found"
            }
        } catch {
            Write-Host "Container status check failed" -ForegroundColor Red
            $results.Issues += "Container status check failed"
        }
    }

    # Test 4: Resource Usage
    Write-Host "Checking resource usage..." -ForegroundColor Gray
    $dockerProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" -and $_.ProcessName -ne "docker-scout" }

    if ($dockerProcesses) {
        $totalCPU = 0
        $totalMemory = 0

        foreach ($proc in $dockerProcesses) {
            try {
                # Get memory usage (this usually works)
                $memoryMB = [math]::Round($proc.WorkingSet / 1MB, 1)
                
                # Get CPU usage using WMI (most reliable method)
                $cpuPercent = 0
                try {
                    $wmiProc = Get-WmiObject -Class Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue
                    if ($wmiProc -and $wmiProc.PercentProcessorTime -ne $null) {
                        $cpuPercent = [math]::Round($wmiProc.PercentProcessorTime, 1)
                    }
                } catch {
                    # If WMI fails, try to get basic process info
                    $cpuPercent = 0
                }
                
                $totalCPU += $cpuPercent
                $totalMemory += $memoryMB

                if ($cpuPercent -gt 50) {
                    Write-Host "High CPU usage: $($proc.ProcessName) - ${cpuPercent}%" -ForegroundColor Yellow
                }
                
                Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: ${cpuPercent}%, Memory: ${memoryMB}MB" -ForegroundColor $(if($cpuPercent -gt 50){"Yellow"}else{"Green"})
            } catch {
                Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: N/A, Memory: N/A" -ForegroundColor Gray
            }
        }

        Write-Host "Resource Summary: CPU: ${totalCPU}%, Memory: ${totalMemory}MB" -ForegroundColor Cyan
        Write-Host "  Process Count: $($dockerProcesses.Count) Docker processes monitored" -ForegroundColor Gray

        if ($totalCPU -gt $MaxCPUPercent) {
            $perCoreCPU = [math]::Round($totalCPU/4,1)
            Write-Host "High CPU usage detected: $totalCPU% ($perCoreCPU% per core)" -ForegroundColor Yellow
            $results.Issues += "High CPU usage: $totalCPU%"
        }

        if ($totalMemory -gt 2048) { # 2GB threshold
            Write-Host "High memory usage detected: ${totalMemory}MB" -ForegroundColor Yellow
            $results.Issues += "High memory usage: ${totalMemory}MB"
        }
    } else {
        Write-Host "No Docker processes found" -ForegroundColor Yellow
        $results.Issues += "No Docker processes running"
    }

    # Test 5: Network Connectivity (Docker Desktop uses named pipes, not TCP sockets)
    Write-Host "Testing Docker connectivity..." -ForegroundColor Gray
    try {
        # Test if Docker API is accessible via CLI (more reliable for Docker Desktop)
        $dockerInfoTest = docker info --format "{{.ID}}" 2>$null
        if ($dockerInfoTest) {
            Write-Host "Docker API is accessible via CLI" -ForegroundColor Green
        } else {
            Write-Host "Docker API not accessible" -ForegroundColor Red
            $results.Issues += "Docker API not accessible"
            $results.RecoveryNeeded = $true
        }
    } catch {
        Write-Host "Docker connectivity test failed" -ForegroundColor Red
        $results.Issues += "Docker connectivity test failed"
        $results.RecoveryNeeded = $true
    }

    # Determine overall health
    if ($results.Issues.Count -eq 0) {
        $results.Healthy = $true
        Write-Host "Docker is healthy" -ForegroundColor Green
        Write-HealthLog "=== HEALTH CHECK PASSED ===" -Level "SUCCESS"
        Write-HealthLog "All tests passed - Docker is healthy" -Level "SUCCESS"
    } else {
        Write-Host "Docker has issues: $($results.Issues -join ', ')" -ForegroundColor Red
        Write-HealthLog "=== HEALTH CHECK FAILED ===" -Level "ERROR"
        Write-HealthLog "Issues detected: $($results.Issues -join ', ')" -Level "ERROR"
        Write-HealthLog "Recovery needed: $($results.RecoveryNeeded)" -Level "ERROR"

        # Perform deep diagnostics if requested
        if ($DeepDiagnostics) {
            Write-HealthLog "Running deep diagnostics..." -Level "INFO"
            Test-DockerDeepDiagnostics
        }

        # Collect logs if requested
        if ($CollectLogs) {
            Write-HealthLog "Collecting diagnostic logs..." -Level "INFO"
            $logDir = Collect-DockerLogs
            $results.Details += "Logs saved to: $logDir"
            Write-HealthLog "Logs saved to: $logDir" -Level "INFO"
        }

        # Auto-recovery if requested and recovery is needed
        if ($AutoRestart -and $results.RecoveryNeeded) {
            Write-Host "Attempting auto-recovery..." -ForegroundColor Yellow
            Write-HealthLog "Auto-recovery triggered" -Level "RESTART"
            $issuesDescription = $results.Issues -join ', '
            $recoverySuccess = Start-DockerDesktopRecovery -Reason "Health check failed: $issuesDescription"

            if ($recoverySuccess) {
                Write-Host "Auto-recovery successful!" -ForegroundColor Green
                Write-HealthLog "Auto-recovery completed successfully" -Level "SUCCESS"
                $results.Healthy = $true
                $results.Issues = @()
                $results.Details += "Auto-recovery completed successfully"
            } else {
                Write-Host "Auto-recovery failed" -ForegroundColor Red
                Write-HealthLog "Auto-recovery failed - manual intervention required" -Level "ERROR"
                $results.Issues += "Auto-recovery failed"
            }
        }
    }

    return $results
}

# Main execution
if ($DeepDiagnostics) {
    Test-DockerDeepDiagnostics
} elseif ($CollectLogs) {
    Collect-DockerLogs
} else {
    $healthResults = Test-DockerHealth -MaxCPUPercent $MaxCPUPercent -AutoRestart:$AutoRestart -DeepDiagnostics:$DeepDiagnostics -CollectLogs:$CollectLogs

    Write-Host "=== Health Check Complete ===" -ForegroundColor Cyan
    Write-Host "Healthy: $($healthResults.Healthy)" -ForegroundColor $(if($healthResults.Healthy){"Green"}else{"Red"})

    if ($healthResults.Issues.Count -gt 0) {
        Write-Host "Issues: $($healthResults.Issues -join ', ')" -ForegroundColor Red
    }

    foreach ($detail in $healthResults.Details) {
        Write-Host "Detail: $detail" -ForegroundColor Gray
    }
}
