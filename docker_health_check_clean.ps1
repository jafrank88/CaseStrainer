# Enhanced Docker Health Check with Deep Diagnostics and Auto-Recovery
# Detects and fixes Docker unresponsiveness issues

param(
    [int]$MaxCPUPercent = 320,  # 80% of 4 cores = 320%
    [int]$MaxMemoryPercent = 85,
    [switch]$AutoRestart,
    [switch]$DeepDiagnostics,
    [switch]$CollectLogs
)

function Test-DockerDeepDiagnostics {
    Write-Host "Deep Diagnostics Mode..." -ForegroundColor Magenta
    
    # Check Docker Desktop logs
    $dockerLogPath = "$env:APPDATA\Docker\log.txt"
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
            $cpuPercent = [math]::Round(($proc.CPU / (Get-WmiObject -Class Win32_Processor).NumberOfLogicalProcessors), 1)
            Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: ${cpuPercent}%" -ForegroundColor $(if($cpuPercent -gt 50){"Yellow"}else{"Green"})
        } catch {
            Write-Host "  $($proc.ProcessName) (PID: $($proc.Id)) - CPU: N/A" -ForegroundColor Gray
        }
    }
}

function Start-DockerAutoRecovery {
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

function Collect-DockerLogs {
    Write-Host "Collecting Docker Logs..." -ForegroundColor Cyan
    
    $logDir = "logs\docker_diagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    
    # Collect Docker Desktop logs
    $dockerLogPath = "$env:APPDATA\Docker\log.txt"
    if (Test-Path $dockerLogPath) {
        Copy-Item $dockerLogPath "$logDir\docker_desktop.log"
        Write-Host "Docker Desktop logs saved to: $logDir\docker_desktop.log" -ForegroundColor Green
    }
    
    # Collect system information
    $systemInfo = @"
=== System Information ===
OS: $((Get-WmiObject -Class Win32_OperatingSystem).Caption)
Docker Version: $(docker --version 2>$null)
Docker Compose Version: $(docker-compose --version 2>$null)
Available Memory: $([math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory/1GB, 2)) GB
CPU Cores: $((Get-WmiObject -Class Win32_Processor).NumberOfLogicalProcessors)
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
        [int]$MaxMemoryPercent = 85,
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
    
    # Test 1: Docker CLI Responsiveness
    Write-Host "Testing Docker CLI responsiveness..." -ForegroundColor Gray
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "Docker CLI is responsive" -ForegroundColor Green
        } else {
            Write-Host "Docker CLI is not responsive" -ForegroundColor Red
            $results.Issues += "Docker CLI unresponsive"
            $results.RecoveryNeeded = $true
        }
    } catch {
        Write-Host "Docker CLI communication failed" -ForegroundColor Red
        $results.Issues += "Docker CLI communication error"
        $results.RecoveryNeeded = $true
    }
    
    # Test 2: Docker Daemon Communication
    Write-Host "Testing Docker daemon communication..." -ForegroundColor Gray
    try {
        $daemonInfo = docker system info 2>$null
        if ($daemonInfo) {
            Write-Host "Docker daemon is responding" -ForegroundColor Green
        } else {
            Write-Host "Docker daemon not responding" -ForegroundColor Red
            $results.Issues += "Docker daemon unresponsive"
            $results.RecoveryNeeded = $true
        }
    } catch {
        Write-Host "Docker daemon communication failed" -ForegroundColor Red
        $results.Issues += "Docker daemon communication error"
        $results.RecoveryNeeded = $true
    }
    
    # Test 3: Container Status (if Docker is responsive)
    if (-not $results.RecoveryNeeded) {
        Write-Host "Checking container status..." -ForegroundColor Gray
        try {
            # Get list of container IDs (quiet mode) to check existence
            $containerIds = docker ps -q 2>$null
            if ($containerIds) {
                # Containers exist – fetch a readable table for details
                $containersTable = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
                Write-Host "Containers are accessible" -ForegroundColor Green
                $count = ($containerIds | Measure-Object).Count
                $results.Details += "Containers: $count running"
                # Optionally include the table in details for debugging
                # Add container table as a separate detail entry for debugging
                $results.Details += $containersTable.Trim()
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
                if ($null -ne $proc.CPU) {
                    $cpuPercent = [math]::Round(($proc.CPU / (Get-WmiObject -Class Win32_Processor).NumberOfLogicalProcessors), 1)
                } else {
                    $cpuPercent = 0
                }
                $memoryMB = [math]::Round($proc.WorkingSet / 1MB, 1)
                
                $totalCPU += $cpuPercent
                $totalMemory += $memoryMB
                
                if ($cpuPercent -gt 50) {
                    Write-Host "High CPU usage: $($proc.ProcessName) - ${cpuPercent}%" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "Skipping CPU calculation for $($proc.ProcessName)" -ForegroundColor Gray
            }
        }
        
        Write-Host "Resource Summary: CPU: ${totalCPU}%, Memory: ${totalMemory}MB" -ForegroundColor Cyan
        
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
    
    # Test 5: Network Connectivity
    Write-Host "Testing network connectivity..." -ForegroundColor Gray
    try {
        $netTest = Test-NetConnection -ComputerName localhost -Port 2375 -InformationLevel Quiet 2>$null
        if ($netTest) {
            Write-Host "Docker socket is accessible" -ForegroundColor Green
        } else {
            Write-Host "Docker socket not accessible" -ForegroundColor Red
            $results.Issues += "Docker socket not accessible"
        }
    } catch {
        Write-Host "Network connectivity test failed" -ForegroundColor Red
        $results.Issues += "Network connectivity test failed"
    }
    
    # Determine overall health
    if ($results.Issues.Count -eq 0) {
        $results.Healthy = $true
        Write-Host "Docker is healthy" -ForegroundColor Green
    } else {
        Write-Host "Docker has issues: $($results.Issues -join ', ')" -ForegroundColor Red
        
        # Perform deep diagnostics if requested
        if ($DeepDiagnostics) {
            Test-DockerDeepDiagnostics
        }
        
        # Collect logs if requested
        if ($CollectLogs) {
            $logDir = Collect-DockerLogs
            $results.Details += "Logs saved to: $logDir"
        }
        
        # Auto-recovery if requested and recovery is needed
        if ($AutoRestart -and $results.RecoveryNeeded) {
            Write-Host "Attempting auto-recovery..." -ForegroundColor Yellow
            $recoverySuccess = Start-DockerAutoRecovery
            
            if ($recoverySuccess) {
                Write-Host "Auto-recovery successful!" -ForegroundColor Green
                $results.Healthy = $true
                $results.Issues = @()
                $results.Details += "Auto-recovery completed successfully"
            } else {
                Write-Host "Auto-recovery failed" -ForegroundColor Red
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
    $healthResults = Test-DockerHealth -MaxCPUPercent $MaxCPUPercent -MaxMemoryPercent $MaxMemoryPercent -AutoRestart:$AutoRestart -DeepDiagnostics:$DeepDiagnostics -CollectLogs:$CollectLogs
    
    Write-Host "=== Health Check Complete ===" -ForegroundColor Cyan
    Write-Host "Healthy: $($healthResults.Healthy)" -ForegroundColor $(if($healthResults.Healthy){"Green"}else{"Red"})
    
    if ($healthResults.Issues.Count -gt 0) {
        Write-Host "Issues: $($healthResults.Issues -join ', ')" -ForegroundColor Red
    }
    
    foreach ($detail in $healthResults.Details) {
        Write-Host "Detail: $detail" -ForegroundColor Gray
    }
} 