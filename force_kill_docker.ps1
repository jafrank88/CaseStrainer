# Force Kill Docker Script - More Aggressive Cleanup
Write-Host "Force Kill Docker Script" -ForegroundColor Red
Write-Host "========================" -ForegroundColor Red
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

# 2. Kill ALL Docker processes with taskkill (comprehensive list)
Write-Host ""
Write-Host "2. Using taskkill to force kill ALL Docker processes..." -ForegroundColor Red
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
Write-Host "2.5. Force killing any remaining Docker processes by pattern..." -ForegroundColor Red
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

# 2.6. Specifically target the stubborn processes you mentioned
Write-Host ""
Write-Host "2.6. Targeting specific stubborn Docker processes..." -ForegroundColor Red
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

# 3. Stop Docker services aggressively
Write-Host ""
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
Write-Host ""
Write-Host "4. Waiting for all processes to fully stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 5. Final check - are any Docker processes still running?
Write-Host ""
Write-Host "5. Final check - any Docker processes still running?" -ForegroundColor Cyan
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

# 6. Instructions for restart
Write-Host ""
Write-Host "6. Next Steps:" -ForegroundColor Yellow
Write-Host "   - All Docker processes should now be stopped" -ForegroundColor White
Write-Host "   - Wait 30 seconds before starting Docker Desktop" -ForegroundColor White
Write-Host "   - Start Docker Desktop manually from Start Menu" -ForegroundColor White
Write-Host "   - Wait for 'Docker Desktop is running' message" -ForegroundColor White
Write-Host ""
Write-Host "   If Docker still won't start:" -ForegroundColor White
Write-Host "   - Restart your computer" -ForegroundColor White
Write-Host "   - Use Windows Direct Mode: .\cslaunch_simple.ps1" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================" -ForegroundColor Red
