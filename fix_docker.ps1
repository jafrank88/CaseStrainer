# Enhanced Docker Fix Script
Write-Host "Enhanced Docker Fix Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# 1. Force kill ALL Docker processes
Write-Host "1. Force killing ALL Docker processes..." -ForegroundColor Red
$dockerProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($dockerProcesses) {
    Write-Host "   Found Docker processes:" -ForegroundColor White
    foreach ($proc in $dockerProcesses) {
        Write-Host "     - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor White
        try {
            # Force kill with multiple methods
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 100
            
            # Double-check if still running
            $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
            if ($stillRunning) {
                Write-Host "       [RETRY] Process still running, trying harder..." -ForegroundColor Yellow
                taskkill /F /PID $proc.Id 2>$null
                Start-Sleep -Milliseconds 200
                
                # Final check
                $finalCheck = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                if ($finalCheck) {
                    Write-Host "       [FAILED] Could not kill process $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
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
} else {
    Write-Host "   No Docker processes found" -ForegroundColor Green
}

# 1.5. Kill ALL Docker processes with taskkill (comprehensive list)
Write-Host ""
Write-Host "1.5. Using taskkill to force kill ALL Docker processes..." -ForegroundColor Red
$dockerProcessNames = @(
    "Docker Desktop.exe",
    "com.docker.backend.exe", 
    "docker-cloud.exe",
    "Docker Desktop.exe",
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

# Also kill any remaining processes by pattern
Write-Host ""
Write-Host "1.6. Force killing any remaining Docker processes by pattern..." -ForegroundColor Red
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

# 1.6.5. Specifically target the stubborn processes you mentioned
Write-Host ""
Write-Host "1.6.5. Targeting specific stubborn Docker processes..." -ForegroundColor Red
$stubbornProcesses = @(
    "Docker Desktop",
    "com.docker.backend",
    "docker-cloud"
)

foreach ($processName in $stubbornProcesses) {
    try {
        # Try to find and kill by name pattern
        $processes = Get-Process -Name "*$processName*" -ErrorAction SilentlyContinue
        if ($processes) {
            Write-Host "   Found $($processes.Count) $processName processes:" -ForegroundColor White
            foreach ($proc in $processes) {
                Write-Host "     - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor White
                try {
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 100
                    
                    # Double-check if still running
                    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                    if ($stillRunning) {
                        Write-Host "       [RETRY] Using taskkill..." -ForegroundColor Yellow
                        taskkill /F /PID $proc.Id 2>$null
                        Start-Sleep -Milliseconds 200
                        
                        # Final check
                        $finalCheck = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                        if ($finalCheck) {
                            Write-Host "       [RETRY2] Using wmic..." -ForegroundColor Yellow
                            wmic process where "ProcessId=$($proc.Id)" delete 2>$null
                            Start-Sleep -Milliseconds 300
                            
                            # Final final check
                            $finalFinalCheck = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                            if ($finalFinalCheck) {
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
        } else {
            Write-Host "   [INFO] No $processName processes found" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "   [WARNING] Failed to check $processName : $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 1.7. Stop Docker services aggressively
Write-Host ""
Write-Host "1.7. Stopping Docker services aggressively..." -ForegroundColor Red
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

# 2. Wait longer for processes to stop
Write-Host ""
Write-Host "2. Waiting for all processes to fully stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 2.5. Final check - are any Docker processes still running?
Write-Host ""
Write-Host "2.5. Final check - any Docker processes still running?" -ForegroundColor Cyan
$remainingProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($remainingProcesses) {
    Write-Host "   [WARNING] Still running:" -ForegroundColor Yellow
    foreach ($proc in $remainingProcesses) {
        Write-Host "     - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Yellow
    }
    Write-Host "   [ADVICE] You may need to restart your computer" -ForegroundColor Red
} else {
    Write-Host "   [OK] All Docker processes successfully stopped!" -ForegroundColor Green
}

# 3. Start Docker Desktop
Write-Host ""
Write-Host "3. Starting Docker Desktop..." -ForegroundColor Yellow
$dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerDesktopPath) {
    try {
        # Kill any remaining Docker processes
        Get-Process -Name "*docker*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        
        # Start Docker Desktop with elevated privileges
        Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal -Verb RunAs
        Write-Host "   [OK] Docker Desktop started with elevated privileges" -ForegroundColor Green
        
        # Wait a bit for the process to start
        Start-Sleep -Seconds 3
        
        # Check if it's running
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerProcess) {
            Write-Host "   [OK] Docker Desktop process confirmed running (PID: $($dockerProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "   [WARNING] Docker Desktop process not found after start" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   [FAILED] Failed to start Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   [ERROR] Docker Desktop not found at: $dockerDesktopPath" -ForegroundColor Red
}

# 4. Instructions
Write-Host ""
Write-Host "4. Next Steps:" -ForegroundColor Yellow
Write-Host "   - Wait 3-5 minutes for Docker to fully initialize" -ForegroundColor White
Write-Host "   - Docker Desktop will show 'Docker Desktop is running' when ready" -ForegroundColor White
Write-Host "   - Then you can run: .\cslaunch.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "   If Docker still has issues, try:" -ForegroundColor White
Write-Host "   - Restart your computer" -ForegroundColor White
Write-Host "   - Check Windows Event Viewer for Docker errors" -ForegroundColor White
Write-Host "   - Use Windows Direct Mode: .\cslaunch.ps1 -Windows" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Manual Docker restart steps:" -ForegroundColor Magenta
Write-Host "   1. Press Ctrl+Shift+Esc to open Task Manager" -ForegroundColor White
Write-Host "   2. Look for any Docker processes and end them" -ForegroundColor White
Write-Host "   3. Open Docker Desktop manually from Start Menu" -ForegroundColor White
Write-Host "   4. Wait for 'Docker Desktop is running' message" -ForegroundColor White

Write-Host ""
Write-Host "=================" -ForegroundColor Cyan