# Emergency Docker Daemon Communication Fix
# Handles the immediate Docker daemon hang issue

function Test-DockerDaemon {
    param([int]$TimeoutSeconds = 15)
    
    Write-Host "Testing Docker daemon communication..." -ForegroundColor Yellow
    
    # Method 1: Try direct command with timeout
    try {
        $process = Start-Process -FilePath "docker" -ArgumentList "info" -NoNewWindow -PassThru -RedirectStandardOutput "temp_docker_output.txt" -RedirectStandardError "temp_docker_error.txt"
        
        $completed = $process.WaitForExit($TimeoutSeconds * 1000)
        
        if (-not $completed) {
            Write-Host "Docker daemon communication TIMED OUT" -ForegroundColor Red
            $process.Kill()
            return $false
        }
        
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ Docker daemon communication successful" -ForegroundColor Green
            return $true
        } else {
            $errorContent = Get-Content "temp_docker_error.txt" -ErrorAction SilentlyContinue
            Write-Host "Docker daemon communication FAILED: $errorContent" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Docker daemon communication ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        Remove-Item "temp_docker_output.txt" -ErrorAction SilentlyContinue
        Remove-Item "temp_docker_error.txt" -ErrorAction SilentlyContinue
    }
}

function Restart-DockerService {
    Write-Host "Attempting to restart Docker Desktop..." -ForegroundColor Yellow
    
    try {
        # Stop Docker Desktop if running
        $dockerProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
        foreach ($proc in $dockerProcesses) {
            try {
                $proc.Kill()
                Write-Host "Stopped Docker process: $($proc.ProcessName)" -ForegroundColor Gray
            } catch {}
        }
        
        Start-Sleep 3
        
        # Start Docker Desktop
        Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
        
        Write-Host "Waiting for Docker daemon to initialize..." -ForegroundColor Gray
        Start-Sleep 20
        
        return $true
    }
    catch {
        Write-Host "Failed to restart Docker: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "=== Emergency Docker Fix ===" -ForegroundColor Cyan

$daemonWorking = Test-DockerDaemon -TimeoutSeconds 10

if ($daemonWorking) {
    Write-Host "✅ Docker daemon is working properly" -ForegroundColor Green
} else {
    Write-Host "❌ Docker daemon communication failed" -ForegroundColor Red
    
    Write-Host "Attempting Docker Desktop restart..." -ForegroundColor Yellow
    $restartSuccess = Restart-DockerService
    
    if ($restartSuccess) {
        Write-Host "🔄 Testing daemon after restart..." -ForegroundColor Yellow
        Start-Sleep 10
        
        $daemonWorkingAfter = Test-DockerDaemon -TimeoutSeconds 15
        if ($daemonWorkingAfter) {
            Write-Host "✅ Docker daemon communication restored" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker daemon still not responding" -ForegroundColor Red
            Write-Host "Manual Docker Desktop restart may be required" -ForegroundColor Yellow
        }
    }
}

Write-Host "=== Fix Complete ===" -ForegroundColor Cyan
