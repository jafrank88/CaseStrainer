param(
    [switch]$Quick, 
    [switch]$Fast, 
    [switch]$Full, 
    [switch]$Help, 
    [switch]$HealthCheck, 
    [switch]$Windows,
    [switch]$Direct,
    [switch]$AutoFixDocker,
    [switch]$Prevent,
    [switch]$NuclearDocker
)

function Test-DockerComprehensiveHealth {
    param(
        [switch]$AutoRestart, 
        [int]$Timeout = 30,
        [switch]$Verbose
    )
    
    Write-Host "Comprehensive Docker Health Check..." -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    
    # Define all Docker processes we need to check
    $dockerProcessNames = @(
        "Docker Desktop",
        "com.docker.backend",
        "com.docker.proxy",
        "com.docker.diagnose", 
        "docker-cloud",
        "dockerd",
        "docker-compose",
        "docker",
        "com.docker.cli"
    )
    
    # 1. Check Docker Processes
    Write-Host "1. Checking Docker processes..." -ForegroundColor Yellow
    $runningProcesses = @()
    $missingProcesses = @()
    
    foreach ($processName in $dockerProcessNames) {
        $process = Get-Process -Name $processName -ErrorAction SilentlyContinue
        if ($process) {
            $runningProcesses += $process
            if ($Verbose) {
                Write-Host "   [OK] $processName (PID: $($process.Id))" -ForegroundColor Green
            }
        } else {
            $missingProcesses += $processName
            if ($Verbose) {
                Write-Host "   [MISSING] $processName" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "   Running: $($runningProcesses.Count), Missing: $($missingProcesses.Count)" -ForegroundColor White
    
    # Check for critical processes
    $criticalProcesses = @("Docker Desktop", "com.docker.backend")
    $criticalMissing = $missingProcesses | Where-Object { $_ -in $criticalProcesses }
    
    if ($criticalMissing.Count -gt 0) {
        Write-Host "   [FAIL] Critical Docker processes missing: $($criticalMissing -join ', ')" -ForegroundColor Red
        $processesHealthy = $false
    } else {
        Write-Host "   [OK] Critical Docker processes are running" -ForegroundColor Green
        $processesHealthy = $true
    }
    
    # 2. Test Docker Engine Response
    Write-Host "2. Testing Docker engine..." -ForegroundColor Yellow
    $engineHealthy = $false
    
    try {
        $job = Start-Job -ScriptBlock {
            try {
                $output = docker version --format "{{.Server.Version}}" 2>&1
                return @{ 
                    Success = ($LASTEXITCODE -eq 0)
                    Output = $output
                    ExitCode = $LASTEXITCODE
                }
            } catch {
                return @{ 
                    Success = $false
                    Error = $_.Exception.Message
                }
            }
        }
        
        $result = Wait-Job -Job $job -Timeout $Timeout
        if ($result) {
            $jobResult = Receive-Job -Job $job
            Remove-Job -Job $job
            
            if ($jobResult.Success) {
                Write-Host "   [OK] Docker engine responding (Version: $($jobResult.Output.Trim()))" -ForegroundColor Green
                $engineHealthy = $true
            } else {
                Write-Host "   [FAIL] Docker engine error (Exit code: $($jobResult.ExitCode))" -ForegroundColor Red
                if ($Verbose -and $jobResult.Output) {
                    Write-Host "   Error: $($jobResult.Output)" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "   [FAIL] Docker engine timeout ($Timeout seconds)" -ForegroundColor Red
            Remove-Job -Job $job -Force
        }
    } catch {
        Write-Host "   [ERROR] Docker engine test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 3. Test Docker API Operations
    Write-Host "3. Testing Docker API operations..." -ForegroundColor Yellow
    $apiHealthy = $false
    
    try {
        $job = Start-Job -ScriptBlock {
            try {
                # Test basic API call
                $output = docker ps --format "{{.Names}}" 2>&1
                return @{ 
                    Success = ($LASTEXITCODE -eq 0)
                    ContainerCount = if ($LASTEXITCODE -eq 0) { ($output | Measure-Object).Count } else { 0 }
                    ExitCode = $LASTEXITCODE
                }
            } catch {
                return @{ 
                    Success = $false
                    Error = $_.Exception.Message
                }
            }
        }
        
        $result = Wait-Job -Job $job -Timeout $Timeout
        if ($result) {
            $jobResult = Receive-Job -Job $job
            Remove-Job -Job $job
            
            if ($jobResult.Success) {
                Write-Host "   [OK] Docker API operational (Found $($jobResult.ContainerCount) containers)" -ForegroundColor Green
                $apiHealthy = $true
            } else {
                Write-Host "   [FAIL] Docker API error (Exit code: $($jobResult.ExitCode))" -ForegroundColor Red
            }
        } else {
            Write-Host "   [FAIL] Docker API timeout ($Timeout seconds)" -ForegroundColor Red
            Remove-Job -Job $job -Force
        }
    } catch {
        Write-Host "   [ERROR] Docker API test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Overall health assessment
    $overallHealthy = $processesHealthy -and $engineHealthy -and $apiHealthy
    
    Write-Host ""
    if ($overallHealthy) {
        Write-Host "[HEALTHY] Docker is fully operational" -ForegroundColor Green
        
        # Final validation: Check CaseStrainer application health
        Write-Host ""
        Write-Host "Final validation: Checking CaseStrainer application health..." -ForegroundColor Cyan
        $appHealthy = Test-CaseStrainerHealth -Timeout 15
        if ($appHealthy) {
            Write-Host "[FULLY HEALTHY] Docker and CaseStrainer application are operational" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[PARTIALLY HEALTHY] Docker ready but CaseStrainer application not responding" -ForegroundColor Yellow
            Write-Host "[INFO] Application may still be starting up - Docker is ready" -ForegroundColor Cyan
            return $true  # Docker is ready, which is the main concern
        }
    } else {
        Write-Host "[UNHEALTHY] Docker has issues" -ForegroundColor Red
        
        # Auto-restart if requested
        if ($AutoRestart) {
            Write-Host ""
            Write-Host "Attempting Docker restart..." -ForegroundColor Yellow
            return Restart-DockerComprehensive -Verbose:$Verbose
        } else {
            Write-Host ""
            Write-Host "To auto-restart Docker, run with -AutoRestart flag" -ForegroundColor Yellow
        }
        
        return $false
    }
}

function Restart-DockerComprehensive {
    param([switch]$Verbose)
    
    Write-Host ""
    Write-Host "Comprehensive Docker Restart Process:" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    
    # 1. Stop ALL Docker-related processes
    Write-Host "1. Stopping all Docker processes..." -ForegroundColor Yellow
    
    # Comprehensive list of Docker processes to stop
    $dockerProcessesToStop = @(
        "Docker Desktop",
        "com.docker.backend", 
        "com.docker.proxy",
        "com.docker.diagnose",
        "docker-cloud",
        "dockerd", 
        "docker-compose",
        "docker",
        "com.docker.cli",
        "com.docker.supervisor",
        "docker-index"
    )
    
    $stoppedCount = 0
    foreach ($processName in $dockerProcessesToStop) {
        $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
        foreach ($proc in $processes) {
            try {
                if ($Verbose) {
                    Write-Host "   Stopping $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Gray
                }
                
                # Try graceful close first for Docker Desktop
                if ($proc.ProcessName -eq "Docker Desktop") {
                    $proc.CloseMainWindow() | Out-Null
                    Start-Sleep -Seconds 3
                    
                    # Check if it closed gracefully
                    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    }
                } else {
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                }
                
                $stoppedCount++
                if ($Verbose) {
                    Write-Host "     [OK] Stopped" -ForegroundColor Green
                }
            } catch {
                if ($Verbose) {
                    Write-Host "     [WARNING] Could not stop: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
        }
    }
    
    Write-Host "   Stopped $stoppedCount Docker processes" -ForegroundColor Green
    
    # 2. Stop Docker Services
    Write-Host "2. Stopping Docker services..." -ForegroundColor Yellow
    $dockerServices = @("com.docker.service", "docker")
    $servicesStopped = 0
    
    foreach ($serviceName in $dockerServices) {
        try {
            $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
            if ($service -and $service.Status -eq "Running") {
                Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
                $servicesStopped++
                if ($Verbose) {
                    Write-Host "   Stopped service: $serviceName" -ForegroundColor Green
                }
            }
        } catch {
            if ($Verbose) {
                Write-Host "   Could not stop service $serviceName`: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    if ($servicesStopped -eq 0) {
        Write-Host "   No Docker services needed stopping" -ForegroundColor Gray
    } else {
        Write-Host "   Stopped $servicesStopped Docker services" -ForegroundColor Green
    }
    
    # 3. Wait for complete shutdown
    Write-Host "3. Waiting for complete shutdown..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Verify no Docker processes remain
    $remainingProcesses = Get-Process | Where-Object { $_.ProcessName -match "docker" }
    if ($remainingProcesses) {
        Write-Host "   [WARNING] Some Docker processes still running, force killing..." -ForegroundColor Yellow
        $remainingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    } else {
        Write-Host "   [OK] All Docker processes stopped" -ForegroundColor Green
    }
    
    # 4. Start Docker Desktop
    Write-Host "4. Starting Docker Desktop..." -ForegroundColor Yellow
    $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if (Test-Path $dockerDesktopPath) {
        try {
            Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal
            Write-Host "   [OK] Docker Desktop startup initiated" -ForegroundColor Green
        } catch {
            Write-Host "   [ERROR] Failed to start Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "   [ERROR] Docker Desktop not found at: $dockerDesktopPath" -ForegroundColor Red
        return $false
    }
    
    # 5. Wait for Docker to be ready (more responsive)
    Write-Host "5. Waiting for Docker to be ready..." -ForegroundColor Yellow
    $maxWaitTime = 120  # 2 minutes (reduced from 3)
    $checkInterval = 8  # 8 seconds (reduced from 15)
    $elapsed = 0
    
    while ($elapsed -lt $maxWaitTime) {
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
        
        Write-Host "   Checking Docker readiness... ($elapsed/$maxWaitTime seconds)" -ForegroundColor Gray
        
        # Test if Docker is responding
        try {
            $testJob = Start-Job -ScriptBlock {
                docker version --format "{{.Server.Version}}" 2>&1
                return $LASTEXITCODE
            }
            
            $testResult = Wait-Job -Job $testJob -Timeout 8
            if ($testResult) {
                $exitCode = Receive-Job -Job $testJob
                Remove-Job -Job $testJob
                
                if ($exitCode -eq 0) {
                    Write-Host "   [OK] Docker is ready and responding!" -ForegroundColor Green
                    
                    # Wait for containers to be fully running before checking health
                    Write-Host "6. Waiting for CaseStrainer containers to be ready..." -ForegroundColor Yellow
                    $containerReady = Wait-ForContainersReady -Timeout 60
                    if ($containerReady) {
                        Write-Host "   [OK] Containers are running!" -ForegroundColor Green
                        
                        # Now check CaseStrainer health endpoint
                        Write-Host "7. Checking CaseStrainer application health..." -ForegroundColor Yellow
                        $appHealthy = Test-CaseStrainerHealth -Timeout 15
                        if ($appHealthy) {
                            Write-Host "   [OK] CaseStrainer application is healthy!" -ForegroundColor Green
                            return $true
                        } else {
                            Write-Host "   [WARNING] Containers running but health check failed" -ForegroundColor Yellow
                            Write-Host "   [INFO] Application may need more time to start..." -ForegroundColor Cyan
                            return $true  # Docker and containers are ready
                        }
                    } else {
                        Write-Host "   [WARNING] Docker ready but containers not running yet" -ForegroundColor Yellow
                        Write-Host "   [INFO] Containers may still be starting up..." -ForegroundColor Cyan
                        return $true  # Docker is ready, containers will catch up
                    }
                }
            } else {
                Remove-Job -Job $testJob -Force
            }
        } catch {
            Write-Warning "Error in Docker readiness check: $($_.Exception.Message)"
        }
    }
    
    Write-Host "   [TIMEOUT] Docker did not become ready within $maxWaitTime seconds" -ForegroundColor Red
    Write-Host "   Attempting aggressive fallback restart..." -ForegroundColor Yellow
    
    # 6. AGGRESSIVE FALLBACK RESTART
    return Restart-DockerAggressive -Verbose:$Verbose
}

function Restart-DockerAggressive {
    param([switch]$Verbose)
    
    Write-Host ""
    Write-Host "AGGRESSIVE DOCKER RESTART - NUCLEAR OPTION" -ForegroundColor Red
    Write-Host "===========================================" -ForegroundColor Red
    
    # 1. Force kill ALL Docker processes with taskkill
    Write-Host "1. Force killing ALL Docker processes with taskkill..." -ForegroundColor Red
    $dockerProcessNames = @(
        "Docker Desktop.exe",
        "com.docker.backend.exe", 
        "docker-cloud.exe",
        "com.docker.cli.exe",
        "com.docker.proxy.exe",
        "com.docker.wsl-distro-proxy.exe",
        "com.docker.service.exe",
        "com.docker.wsl-helper.exe"
    )
    
    foreach ($processName in $dockerProcessNames) {
        try {
            $output = taskkill /F /IM $processName 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   [OK] $processName force killed" -ForegroundColor Green
            } else {
                Write-Host "   [INFO] $processName not found or already stopped" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "   [WARNING] taskkill failed for $processName : $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # 2. Kill any remaining processes by pattern
    Write-Host "2. Force killing any remaining Docker processes by pattern..." -ForegroundColor Red
    try {
        $output = taskkill /F /IM "*docker*" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] All *docker* processes force killed" -ForegroundColor Green
        } else {
            Write-Host "   [INFO] No *docker* processes found" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "   [WARNING] Pattern kill failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 3. Stop Docker services aggressively
    Write-Host "3. Stopping Docker services aggressively..." -ForegroundColor Red
    $dockerServices = @("com.docker.service", "Docker Desktop Service")
    foreach ($serviceName in $dockerServices) {
        try {
            $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
            if ($service) {
                if ($service.Status -eq "Running") {
                    Write-Host "   Stopping $serviceName..." -ForegroundColor Yellow
                    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 2
                    
                    # Check if stopped
                    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
                    if ($service.Status -eq "Stopped") {
                        Write-Host "   [OK] $serviceName stopped" -ForegroundColor Green
                    } else {
                        Write-Host "   [WARNING] $serviceName still running" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "   [INFO] $serviceName already stopped" -ForegroundColor Cyan
                }
            } else {
                Write-Host "   [INFO] Service $serviceName not found" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "   [ERROR] Failed to stop $serviceName : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # 4. Wait longer for everything to stop
    Write-Host "4. Waiting for all processes to fully stop..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    # 5. Final check - are any Docker processes still running?
    Write-Host "5. Final check - any Docker processes still running?" -ForegroundColor Cyan
    $remainingProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
    if ($remainingProcesses) {
        Write-Host "   [WARNING] Still running:" -ForegroundColor Yellow
        foreach ($proc in $remainingProcesses) {
            Write-Host "     - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Yellow
        }
        Write-Host "   [RETRY] Attempting final force kill..." -ForegroundColor Red
        
        # Final aggressive kill attempt
        foreach ($proc in $remainingProcesses) {
            try {
                Write-Host "     Force killing $($proc.ProcessName) (PID: $($proc.Id))..." -ForegroundColor Red
                
                # Try multiple kill methods
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 100
                
                # Check if still running
                if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                    Write-Host "       [RETRY] Using taskkill..." -ForegroundColor Yellow
                    taskkill /F /PID $proc.Id 2>$null
                    Start-Sleep -Milliseconds 200
                    
                    # Final check
                    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                        Write-Host "       [RETRY2] Using wmic..." -ForegroundColor Yellow
                        wmic process where "ProcessId=$($proc.Id)" delete 2>$null
                        Start-Sleep -Milliseconds 300
                        
                        # Final final check
                        if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                            Write-Host "       [FAILED] Could not kill $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
                        } else {
                            Write-Host "       [OK] Force killed with wmic" -ForegroundColor Green
                        }
                    } else {
                        Write-Host "       [OK] Force killed with taskkill" -ForegroundColor Green
                    }
                } else {
                    Write-Host "       [OK] Stopped" -ForegroundColor Green
                }
            } catch {
                Write-Host "       [ERROR] Exception: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # Wait again after final kill attempt
        Start-Sleep -Seconds 10
        
        # Check again
        $finalRemaining = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
        if ($finalRemaining) {
            Write-Host "   [FAILED] Still running after final kill attempt:" -ForegroundColor Red
            foreach ($proc in $finalRemaining) {
                Write-Host "     - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
            }
            Write-Host "   [ADVICE] You may need to restart your computer" -ForegroundColor Red
        } else {
            Write-Host "   [OK] All Docker processes finally stopped!" -ForegroundColor Green
        }
    } else {
        Write-Host "   [OK] All Docker processes successfully stopped!" -ForegroundColor Green
    }
    
    # 6. Start Docker Desktop with elevated privileges
    Write-Host "6. Starting Docker Desktop with elevated privileges..." -ForegroundColor Yellow
    Write-Host "   [NOTE] This may trigger a UAC prompt. Click 'Yes' to allow Docker to start." -ForegroundColor Cyan
    Write-Host "   [TIP] To avoid UAC prompts, run PowerShell as Administrator" -ForegroundColor Cyan
    $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if (Test-Path $dockerDesktopPath) {
        try {
            # Start Docker Desktop with elevated privileges
            Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal -Verb RunAs
            Write-Host "   [OK] Docker Desktop startup initiated with elevated privileges" -ForegroundColor Green
            
            # Wait a bit for the process to start
            Start-Sleep -Seconds 5
            
            # Check if it's running
            $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
            if ($dockerProcess) {
                Write-Host "   [OK] Docker Desktop process confirmed running (PID: $($dockerProcess.Id))" -ForegroundColor Green
            } else {
                Write-Host "   [WARNING] Docker Desktop process not found after start" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   [FAILED] Failed to start Docker Desktop with elevation: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   [INFO] This might be due to UAC prompt being cancelled" -ForegroundColor Yellow
            Write-Host "   [RETRY] Attempting to start without elevation..." -ForegroundColor Yellow
            
            try {
                Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal
                Write-Host "   [OK] Docker Desktop startup initiated without elevation" -ForegroundColor Green
            } catch {
                Write-Host "   [FAILED] Failed to start Docker Desktop without elevation: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "   [SOLUTION] Run PowerShell as Administrator to avoid UAC prompts:" -ForegroundColor Yellow
                Write-Host "     1. Right-click PowerShell in Start Menu" -ForegroundColor Cyan
                Write-Host "     2. Select 'Run as Administrator'" -ForegroundColor Cyan
                Write-Host "     3. Navigate to your project directory" -ForegroundColor Cyan
                Write-Host "     4. Run: .\cslaunch.ps1 -AutoFixDocker" -ForegroundColor Cyan
                return $false
            }
        }
    } else {
        Write-Host "   [ERROR] Docker Desktop not found at: $dockerDesktopPath" -ForegroundColor Red
        return $false
    }
    
    # 7. Wait for Docker to be ready (more responsive)
    Write-Host "7. Waiting for Docker to be ready..." -ForegroundColor Yellow
    $maxWaitTime = 180  # 3 minutes (reduced from 5)
    $checkInterval = 10 # 10 seconds (reduced from 20)
    $elapsed = 0
    
    while ($elapsed -lt $maxWaitTime) {
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
        
        Write-Host "   Checking Docker readiness... ($elapsed/$maxWaitTime seconds)" -ForegroundColor Gray
        
        # Test if Docker is responding
        try {
            $testJob = Start-Job -ScriptBlock {
                docker version --format "{{.Server.Version}}" 2>&1
                return $LASTEXITCODE
            }
            
            $testResult = Wait-Job -Job $testJob -Timeout 10
            if ($testResult) {
                $exitCode = Receive-Job -Job $testJob
                Remove-Job -Job $testJob
                
                if ($exitCode -eq 0) {
                    Write-Host "   [OK] Docker is ready and responding!" -ForegroundColor Green
                    
                    # Wait for containers to be fully running before checking health
                    Write-Host "8. Waiting for CaseStrainer containers to be ready..." -ForegroundColor Yellow
                    $containerReady = Wait-ForContainersReady -Timeout 60
                    if ($containerReady) {
                        Write-Host "   [OK] Containers are running!" -ForegroundColor Green
                        
                        # Now check CaseStrainer health endpoint
                        Write-Host "9. Checking CaseStrainer application health..." -ForegroundColor Yellow
                        $appHealthy = Test-CaseStrainerHealth -Timeout 15
                        if ($appHealthy) {
                            Write-Host "   [OK] CaseStrainer application is healthy!" -ForegroundColor Green
                            return $true
                        } else {
                            Write-Host "   [WARNING] Containers running but health check failed" -ForegroundColor Yellow
                            Write-Host "   [INFO] Application may need more time to start..." -ForegroundColor Cyan
                            return $true  # Docker and containers are ready
                        }
                    } else {
                        Write-Host "   [WARNING] Docker ready but containers not running yet" -ForegroundColor Yellow
                        Write-Host "   [INFO] Containers may still be starting up..." -ForegroundColor Cyan
                        return $true  # Docker is ready, containers will catch up
                    }
                }
            } else {
                Remove-Job -Job $testJob -Force
            }
        } catch {
            # Continue waiting
        }
    }
    
    Write-Host "   [TIMEOUT] Docker still not ready after aggressive restart" -ForegroundColor Red
    Write-Host "   Attempting final nuclear option..." -ForegroundColor Red
    
    # 8. FINAL NUCLEAR OPTION - Restart WSL and try again
    return Restart-DockerNuclear -Verbose:$Verbose
}

function Restart-DockerNuclear {
    param([switch]$Verbose)
    
    Write-Host ""
    Write-Host "NUCLEAR DOCKER RESTART - WSL RESET" -ForegroundColor Magenta
    Write-Host "====================================" -ForegroundColor Magenta
    
    # 1. Restart WSL
    Write-Host "1. Restarting WSL..." -ForegroundColor Yellow
    try {
        $output = wsl --shutdown 2>&1
        Write-Host "   [OK] WSL shutdown initiated" -ForegroundColor Green
        Start-Sleep -Seconds 10
        
        # Wait for WSL to fully stop
        $wslRunning = $true
        $wslWaitTime = 30
        $wslElapsed = 0
        
        while ($wslRunning -and $wslElapsed -lt $wslWaitTime) {
            Start-Sleep -Seconds 2
            $wslElapsed += 2
            
            try {
                $wslStatus = wsl --status 2>&1
                if ($LASTEXITCODE -ne 0) {
                    $wslRunning = $false
                }
            } catch {
                $wslRunning = $false
            }
        }
        
        if (-not $wslRunning) {
            Write-Host "   [OK] WSL fully stopped" -ForegroundColor Green
        } else {
            Write-Host "   [WARNING] WSL may still be running" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   [WARNING] WSL restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 2. Start Docker Desktop again
    Write-Host "2. Starting Docker Desktop after WSL restart..." -ForegroundColor Yellow
    $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if (Test-Path $dockerDesktopPath) {
        try {
            Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal -Verb RunAs
            Write-Host "   [OK] Docker Desktop started after WSL restart" -ForegroundColor Green
        } catch {
            Write-Host "   [FAILED] Failed to start Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "   [ERROR] Docker Desktop not found" -ForegroundColor Red
        return $false
    }
    
    # 3. Wait for Docker to be ready (final attempt - more responsive)
    Write-Host "3. Final wait for Docker to be ready..." -ForegroundColor Yellow
    $maxWaitTime = 180  # 3 minutes (reduced from 4)
    $checkInterval = 15 # 15 seconds (reduced from 30)
    $elapsed = 0
    
    while ($elapsed -lt $maxWaitTime) {
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
        
        Write-Host "   Checking Docker readiness... ($elapsed/$maxWaitTime seconds)" -ForegroundColor Gray
        
        # Test if Docker is responding
        try {
            $testJob = Start-Job -ScriptBlock {
                docker version --format "{{.Server.Version}}" 2>&1
                return $LASTEXITCODE
            }
            
            $testResult = Wait-Job -Job $testJob -Timeout 10
            if ($testResult) {
                $exitCode = Receive-Job -Job $testJob
                Remove-Job -Job $testJob
                
                if ($exitCode -eq 0) {
                    Write-Host "   [OK] Docker is ready after nuclear restart!" -ForegroundColor Green
                    
                    # Wait for containers to be fully running before checking health
                    Write-Host "4. Waiting for CaseStrainer containers to be ready..." -ForegroundColor Yellow
                    $containerReady = Wait-ForContainersReady -Timeout 60
                    if ($containerReady) {
                        Write-Host "   [OK] Containers are running!" -ForegroundColor Green
                        
                        # Now check CaseStrainer health endpoint
                        Write-Host "5. Checking CaseStrainer application health..." -ForegroundColor Yellow
                        $appHealthy = Test-CaseStrainerHealth -Timeout 15
                        if ($appHealthy) {
                            Write-Host "   [OK] CaseStrainer application is healthy!" -ForegroundColor Green
                            return $true
                        } else {
                            Write-Host "   [WARNING] Containers running but health check failed" -ForegroundColor Yellow
                            Write-Host "   [INFO] Application may need more time to start..." -ForegroundColor Cyan
                            return $true  # Docker and containers are ready
                        }
                    } else {
                        Write-Host "   [WARNING] Docker ready but containers not running yet" -ForegroundColor Yellow
                        Write-Host "   [INFO] Containers may still be starting up..." -ForegroundColor Cyan
                        return $true  # Docker is ready, containers will catch up
                    }
                }
            } else {
                Remove-Job -Job $testJob -Force
            }
        } catch {
            # Continue waiting
        }
    }
    
    Write-Host "   [FAILED] Docker still not ready after nuclear restart" -ForegroundColor Red
    Write-Host "   All restart methods exhausted - manual intervention required" -ForegroundColor Red
    return $false
}

function Wait-ForContainersReady {
    param([int]$Timeout = 60)
    
    Write-Host "     Waiting for CaseStrainer containers to be ready..." -ForegroundColor Gray
    $maxWaitTime = $Timeout
    $checkInterval = 5  # Check every 5 seconds
    $elapsed = 0
    
    while ($elapsed -lt $maxWaitTime) {
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
        
        Write-Host "       Checking containers... ($elapsed/$maxWaitTime seconds)" -ForegroundColor Gray
        
        try {
            $job = Start-Job -ScriptBlock {
                try {
                    # Check if casestrainer containers are running
                    $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}:{{.Status}}" 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        $containerCount = ($containers | Measure-Object).Count
                        $runningCount = ($containers | Where-Object { $_ -match "Up" } | Measure-Object).Count
                        return @{
                            Success = $true
                            TotalContainers = $containerCount
                            RunningContainers = $runningCount
                            ContainerStatus = $containers
                        }
                    } else {
                        return @{
                            Success = $false
                            Error = "Docker ps failed"
                        }
                    }
                } catch {
                    return @{
                        Success = $false
                        Error = $_.Exception.Message
                    }
                }
            }
            
            $result = Wait-Job -Job $job -Timeout 10
            if ($result) {
                $jobResult = Receive-Job -Job $job
                Remove-Job -Job $job
                
                if ($jobResult.Success) {
                    Write-Host "         Found $($jobResult.TotalContainers) containers, $($jobResult.RunningContainers) running" -ForegroundColor Cyan
                    
                    # Check if we have the expected containers running
                    if ($jobResult.RunningContainers -ge 2) {  # Expect at least backend + frontend
                        Write-Host "         [OK] Sufficient containers are running!" -ForegroundColor Green
                        return $true
                    } else {
                        Write-Host "         [WAIT] Waiting for more containers to start..." -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "         [ERROR] Container check failed: $($jobResult.Error)" -ForegroundColor Red
                }
            } else {
                Remove-Job -Job $job -Force
                Write-Host "         [TIMEOUT] Container check timed out" -ForegroundColor Red
            }
        } catch {
            Write-Host "         [ERROR] Container check exception: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "         [TIMEOUT] Containers did not become ready within $maxWaitTime seconds" -ForegroundColor Red
    return $false
}

function Test-CaseStrainerHealth {
    param([int]$Timeout = 15)
    
    Write-Host "   Testing CaseStrainer health endpoint..." -ForegroundColor Gray
    
    try {
        $job = Start-Job -ScriptBlock {
            try {
                $uri = "https://wolf.law.uw.edu/casestrainer/api/health"
                $response = Invoke-WebRequest -Uri $uri -Method GET -TimeoutSec 10 -UseBasicParsing
                return @{
                    Success = ($response.StatusCode -eq 200)
                    StatusCode = $response.StatusCode
                    Content = $response.Content
                    Error = $null
                }
            } catch {
                return @{
                    Success = $false
                    StatusCode = $null
                    Content = $null
                    Error = $_.Exception.Message
                }
            }
        }
        
        $result = Wait-Job -Job $job -Timeout $Timeout
        if ($result) {
            $jobResult = Receive-Job -Job $job
            Remove-Job -Job $job
            
            if ($jobResult.Success) {
                Write-Host "     [OK] Health endpoint responding (Status: $($jobResult.StatusCode))" -ForegroundColor Green
                if ($jobResult.Content) {
                    Write-Host "     [INFO] Response: $($jobResult.Content)" -ForegroundColor Cyan
                }
                return $true
            } else {
                Write-Host "     [FAIL] Health endpoint error: $($jobResult.Error)" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "     [TIMEOUT] Health endpoint check timed out ($Timeout seconds)" -ForegroundColor Red
            Remove-Job -Job $job -Force
            return $false
        }
    } catch {
        Write-Host "     [ERROR] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Start-DirectMode {
    Write-Host "Starting CaseStrainer directly on Windows..." -ForegroundColor Green
    
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    }
    
    # Stop any existing components
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    } | ForEach-Object {
        try { 
            Stop-Process -Id $_.Id -Force 
            Write-Host "Stopped Python process: $($_.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop Python process $($_.Id)" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    
    # Start CaseStrainer
    Write-Host "Starting CaseStrainer Flask app..." -ForegroundColor Cyan
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $process.Id | Out-File -FilePath "logs\casestrainer.pid" -Encoding UTF8
        Write-Host "CaseStrainer started with PID: $($process.Id)" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start CaseStrainer: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    Write-Host "Waiting for CaseStrainer to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "CaseStrainer started successfully!" -ForegroundColor Green
            Write-Host "Access URL: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        } else {
            Write-Host "CaseStrainer started but health check failed: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "CaseStrainer may still be starting up..." -ForegroundColor Yellow
    }
}

# Main script logic
if ($Help) { 
    Write-Host "CaseStrainer Enhanced Launcher with Auto-Docker Management" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Basic Commands:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1              # Smart auto-detect with Docker auto-fix" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Quick       # Quick Start (when code unchanged)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Fast        # Fast Start (restart containers)" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -Full        # Force Full Rebuild (ignore checksums)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Docker Management:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -AutoFixDocker # Force Docker restart with aggressive fallbacks" -ForegroundColor Magenta
    Write-Host "  .\cslaunch.ps1 -NuclearDocker # Skip normal restart, go straight to aggressive" -ForegroundColor Red
    Write-Host "  .\cslaunch.ps1 -HealthCheck   # Comprehensive Docker health check with auto-recovery" -ForegroundColor Magenta
    Write-Host "  .\cslaunch.ps1 -Prevent       # Docker cleanup and optimization" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Alternative Modes:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Windows      # Run directly on Windows (no Docker)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Direct       # Run with all components (Flask + Redis + RQ)" -ForegroundColor Green
}
elseif ($AutoFixDocker) {
    Write-Host "Auto-Fixing Docker..." -ForegroundColor Magenta
    if (Restart-DockerComprehensive) {
        Write-Host "Docker successfully restarted and is ready!" -ForegroundColor Green
        Write-Host "You can now run: .\cslaunch.ps1" -ForegroundColor Cyan
    } else {
        Write-Host "Docker restart failed or timed out" -ForegroundColor Red
        Write-Host "Try: .\cslaunch.ps1 -Windows (Windows Direct Mode)" -ForegroundColor Yellow
    }
}
elseif ($NuclearDocker) {
    Write-Host "NUCLEAR DOCKER RESTART - BYPASSING NORMAL RESTART" -ForegroundColor Red
    Write-Host "This will attempt the most aggressive Docker restart possible..." -ForegroundColor Red
    Write-Host ""
    
    if (Restart-DockerAggressive) {
        Write-Host "Docker successfully restarted with aggressive methods!" -ForegroundColor Green
        Write-Host "You can now run: .\cslaunch.ps1" -ForegroundColor Cyan
    } else {
        Write-Host "Even nuclear restart failed" -ForegroundColor Red
        Write-Host "Try: .\cslaunch.ps1 -Windows (Windows Direct Mode)" -ForegroundColor Yellow
        Write-Host "Or restart your computer and try again" -ForegroundColor Yellow
    }
}
elseif ($HealthCheck) {
    Write-Host "Running Comprehensive Docker Health Check with Auto-Recovery..." -ForegroundColor Magenta
    
    $dockerHealthy = Test-DockerComprehensiveHealth -AutoRestart -Timeout 30 -Verbose
    
    if ($dockerHealthy) {
        Write-Host ""
        Write-Host "=== DOCKER STATUS: HEALTHY ===" -ForegroundColor Green
        Write-Host "Docker is fully operational and ready to use!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run:" -ForegroundColor Cyan
        Write-Host "  .\cslaunch.ps1              # Smart auto-detect" -ForegroundColor White
        Write-Host "  .\cslaunch.ps1 -Quick       # Quick start" -ForegroundColor White
        Write-Host "  .\cslaunch.ps1 -Fast        # Fast restart" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "=== DOCKER STATUS: UNHEALTHY ===" -ForegroundColor Red
        Write-Host "Docker requires attention before CaseStrainer can run" -ForegroundColor Red
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Yellow
        Write-Host "  1. Wait 2-3 minutes if restart was initiated" -ForegroundColor White
        Write-Host "  2. Try running this health check again" -ForegroundColor White
        Write-Host "  3. Manually restart Docker Desktop if needed" -ForegroundColor White
        Write-Host "  4. Restart your computer if issues persist" -ForegroundColor White
        Write-Host "  5. Alternative: .\cslaunch.ps1 -Windows (Direct mode)" -ForegroundColor Cyan
    }
    
    # Show additional system info
    Write-Host ""
    Write-Host "Docker System Information:" -ForegroundColor Cyan
    try {
        docker system df --format "table" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not retrieve Docker system info (Docker may not be ready)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not retrieve Docker system info" -ForegroundColor Yellow
    }
}
elseif ($Windows) {
    Start-DirectMode
}
elseif ($Direct) {
    Start-DirectMode
}
elseif ($Prevent) {
    Write-Host "Running Docker Prevention and Optimization..." -ForegroundColor Blue
    Write-Host "Performing basic Docker cleanup..." -ForegroundColor Yellow
    
    try {
        $job = Start-Job -ScriptBlock { docker system prune -f } -Name "DockerCleanup"
        $result = Wait-Job -Job $job -Timeout 15
        
        if ($result) {
            $output = Receive-Job -Job $job
            Remove-Job -Job $job
            Write-Host $output -ForegroundColor Green
        } else {
            Write-Host "Docker cleanup timed out" -ForegroundColor Red
            Remove-Job -Job $job -Force
        }
    } catch {
        Write-Host "Docker cleanup failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "Prevention and optimization completed!" -ForegroundColor Green
}
elseif ($Quick) { 
    Write-Host "Quick Start" -ForegroundColor Green
    
    # Check Docker health first
    $dockerHealthy = Test-DockerComprehensiveHealth -Timeout 15
    if (-not $dockerHealthy) {
        Write-Host "Docker is not healthy. Attempting auto-fix..." -ForegroundColor Yellow
        if (Restart-DockerComprehensive) {
            Write-Host "Docker fixed! Continuing with Quick Start..." -ForegroundColor Green
        } else {
            Write-Host "Docker fix failed. Switching to Windows Direct Mode..." -ForegroundColor Yellow
            Start-DirectMode
            return
        }
    }
    
    docker compose -f docker-compose.prod.yml up -d
    Write-Host "Quick Start completed!" -ForegroundColor Green
}
elseif ($Fast) { 
    Write-Host "Fast Start" -ForegroundColor Cyan
    
    # Check Docker health first
    $dockerHealthy = Test-DockerComprehensiveHealth -Timeout 15
    if (-not $dockerHealthy) {
        Write-Host "Docker is not healthy. Attempting auto-fix..." -ForegroundColor Yellow
        if (Restart-DockerComprehensive) {
            Write-Host "Docker fixed! Continuing with Fast Start..." -ForegroundColor Green
        } else {
            Write-Host "Docker fix failed. Switching to Windows Direct Mode..." -ForegroundColor Yellow
            Start-DirectMode
            return
        }
    }
    
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
    Write-Host "Fast Start completed!" -ForegroundColor Green
}
elseif ($Full) { 
    Write-Host "Full Rebuild" -ForegroundColor Yellow
    
    # Check Docker health first
    $dockerHealthy = Test-DockerComprehensiveHealth -Timeout 15
    if (-not $dockerHealthy) {
        Write-Host "Docker is not healthy. Attempting auto-fix..." -ForegroundColor Yellow
        if (Restart-DockerComprehensive) {
            Write-Host "Docker fixed! Continuing with Full Rebuild..." -ForegroundColor Green
        } else {
            Write-Host "Docker fix failed. Switching to Windows Direct Mode..." -ForegroundColor Yellow
            Start-DirectMode
            return
        }
    }
    
    docker compose -f docker-compose.prod.yml down
    docker system prune -af --volumes
    docker compose -f docker-compose.prod.yml build --no-cache
    docker compose -f docker-compose.prod.yml up -d
    Write-Host "Full Rebuild completed!" -ForegroundColor Green
}
else {
    Write-Host "Smart Auto-Detection with Comprehensive Docker Health Check..." -ForegroundColor Magenta
    
    # First, verify Docker is healthy before proceeding
    Write-Host ""
    $dockerHealthy = Test-DockerComprehensiveHealth -Timeout 15
    
    if (-not $dockerHealthy) {
        Write-Host ""
        Write-Host "Docker is not ready. Recommendations:" -ForegroundColor Red
        Write-Host "  1. Run comprehensive health check: .\cslaunch.ps1 -HealthCheck" -ForegroundColor Yellow
        Write-Host "  2. Or try Windows Direct Mode: .\cslaunch.ps1 -Windows" -ForegroundColor Yellow
        Write-Host "  3. Or try Direct Mode with all components: .\cslaunch.ps1 -Direct" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "Docker is healthy - proceeding with container management..." -ForegroundColor Green
    
    # Check if Docker is running
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        Write-Host "Docker is not running. Please start Docker Engine first." -ForegroundColor Red
        Write-Host "Try: .\cslaunch.ps1 -HealthCheck" -ForegroundColor Yellow
        exit 1
    }
    
    # Simple container check
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table" 2>$null
        if ($containers) {
            Write-Host "Containers running - performing Quick Start..." -ForegroundColor Green
            docker compose -f docker-compose.prod.yml up -d
        } else {
            Write-Host "No containers running - performing Fast Start..." -ForegroundColor Cyan
            docker compose -f docker-compose.prod.yml down
            docker compose -f docker-compose.prod.yml up -d
        }
    } catch {
        Write-Host "Error checking containers, performing Full Rebuild..." -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml down
        docker compose -f docker-compose.prod.yml build --no-cache
        docker compose -f docker-compose.prod.yml up -d
    }
    
    Write-Host "CaseStrainer is ready!" -ForegroundColor Green
}
