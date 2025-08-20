# Docker Force Restart Script
# This script will completely stop and restart Docker Desktop

Write-Host "Docker Force Restart Script" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop all Docker processes
Write-Host "1. Stopping all Docker processes..." -ForegroundColor Yellow
$dockerProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($dockerProcesses) {
    Write-Host "   Found Docker processes:" -ForegroundColor White
    $dockerProcesses | ForEach-Object { 
        Write-Host "     - $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor White 
    }
    
    Write-Host "   Stopping processes..." -ForegroundColor Yellow
    foreach ($proc in $dockerProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "     ✓ Stopped $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "     ✗ Failed to stop $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   No Docker processes found" -ForegroundColor Green
}

# 2. Stop Docker services
Write-Host "`n2. Stopping Docker services..." -ForegroundColor Yellow
$dockerServices = Get-Service -Name "*docker*" -ErrorAction SilentlyContinue
if ($dockerServices) {
    foreach ($service in $dockerServices) {
        if ($service.Status -eq "Running") {
            try {
                Stop-Service -Name $service.Name -Force -ErrorAction SilentlyContinue
                Write-Host "   ✓ Stopped service: $($service.Name)" -ForegroundColor Green
            } catch {
                Write-Host "   ✗ Failed to stop service: $($service.Name)" -ForegroundColor Red
            }
        } else {
            Write-Host "   - Service $($service.Name) already stopped" -ForegroundColor White
        }
    }
} else {
    Write-Host "   No Docker services found" -ForegroundColor Green
}

# 3. Wait for processes to fully stop
Write-Host "`n3. Waiting for processes to fully stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 4. Check if any Docker processes are still running
$remainingProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($remainingProcesses) {
    Write-Host "   ⚠ Some Docker processes still running, forcing stop..." -ForegroundColor Yellow
    foreach ($proc in $remainingProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "     ✓ Force stopped $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Green
        } catch {
            Write-Host "     ✗ Could not force stop $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 3
}

# 5. Start Docker Desktop
Write-Host "`n4. Starting Docker Desktop..." -ForegroundColor Yellow
$dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerDesktopPath) {
    try {
        Start-Process -FilePath $dockerDesktopPath -WindowStyle Normal
        Write-Host "   ✓ Docker Desktop started" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed to start Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   ✗ Docker Desktop not found at: $dockerDesktopPath" -ForegroundColor Red
    Write-Host "   → Please start Docker Desktop manually" -ForegroundColor Yellow
}

# 6. Wait and check status
Write-Host "`n5. Waiting for Docker to initialize..." -ForegroundColor Yellow
Write-Host "   This may take 2-5 minutes..." -ForegroundColor White

$maxWaitTime = 300  # 5 minutes
$elapsed = 0
$dockerReady = $false

while ($elapsed -lt $maxWaitTime -and -not $dockerReady) {
    Start-Sleep -Seconds 10
    $elapsed += 10
    
    Write-Host "   Checking Docker status... ($([math]::Round($elapsed/60, 1)) minutes elapsed)" -ForegroundColor Cyan
    
    try {
        $job = Start-Job -ScriptBlock { docker --version } -Name "DockerVersionCheck"
        $result = Wait-Job -Job $job -Timeout 5
        
        if ($result) {
            $version = Receive-Job -Job $job
            Remove-Job -Job $job
            
            if ($version) {
                Write-Host "   ✓ Docker CLI responding: $version" -ForegroundColor Green
                
                # Test if daemon is ready
                try {
                    $job2 = Start-Job -ScriptBlock { docker info } -Name "DockerInfoCheck"
                    $result2 = Wait-Job -Job $job2 -Timeout 10
                    
                    if ($result2) {
                        $info = Receive-Job -Job $job2
                        Remove-Job -Job $job2
                        Write-Host "   ✓ Docker daemon ready!" -ForegroundColor Green
                        $dockerReady = $true
                        break
                    } else {
                        Write-Host "   ⚠ Docker CLI working, but daemon not ready yet..." -ForegroundColor Yellow
                        Remove-Job -Job $job2 -Force
                    }
                } catch {
                    Write-Host "   ⚠ Docker CLI working, but daemon not ready yet..." -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "   ⚠ Docker CLI not responding yet..." -ForegroundColor Yellow
            Remove-Job -Job $job -Force
        }
    } catch {
        Write-Host "   ⚠ Docker not ready yet..." -ForegroundColor Yellow
    }
}

# 7. Final status
Write-Host "`n6. Final Status:" -ForegroundColor Yellow
Write-Host "================" -ForegroundColor Cyan

if ($dockerReady) {
    Write-Host "`n✅ DOCKER SUCCESSFULLY RESTARTED!" -ForegroundColor Green
    Write-Host "Docker is now ready and responding to commands." -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -HealthCheck" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠ DOCKER RESTART INCOMPLETE" -ForegroundColor Yellow
    Write-Host "Docker may still be initializing or there may be an issue." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recommendations:" -ForegroundColor White
    Write-Host "1. Wait a few more minutes for Docker to fully initialize" -ForegroundColor White
    Write-Host "2. Check Docker Desktop UI for any error messages" -ForegroundColor White
    Write-Host "3. Try running: .\cslaunch.ps1 -HealthCheck" -ForegroundColor Cyan
    Write-Host "4. If issues persist, consider using: .\cslaunch.ps1 -Windows" -ForegroundColor Cyan
}

Write-Host "`n=============================" -ForegroundColor Cyan
