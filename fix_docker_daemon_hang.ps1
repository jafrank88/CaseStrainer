# Fix for Docker daemon communication hang
# Adds timeout protection to Docker daemon communication tests

function Test-DockerHealthWithTimeout {
    param(
        [int]$TimeoutSeconds = 30
    )
    
    Write-Host "Testing Docker daemon communication with timeout protection..." -ForegroundColor Cyan
    
    try {
        # Test Docker daemon with timeout protection
        
        # 1. Test Docker version
        Write-Host "Testing Docker version..." -ForegroundColor Gray
        $versionJob = Start-Job -ScriptBlock { docker --version 2>$null }
        $versionResult = Wait-Job -Job $versionJob -Timeout $TimeoutSeconds
        
        if (!$versionResult) {
            Stop-Job -Job $versionJob -Force
            Write-Host "Docker version check timed out" -ForegroundColor Red
            return $false
        }
        
        $dockerVersion = Receive-Job -Job $versionJob
        if (-not $dockerVersion) {
            Write-Host "Docker command not responding" -ForegroundColor Red
            return $false
        }
        
        Write-Host "  ✅ Docker version: $dockerVersion" -ForegroundColor Green
        
        # 2. Test Docker daemon info
        Write-Host "Testing Docker daemon info..." -ForegroundColor Gray
        $infoJob = Start-Job -ScriptBlock { docker info 2>$null }
        $infoResult = Wait-Job -Job $infoJob -Timeout $TimeoutSeconds
        
        if (!$infoResult) {
            Stop-Job -Job $infoJob -Force
            Write-Host "Docker daemon info check timed out" -ForegroundColor Red
            return $false
        }
        
        $dockerInfo = Receive-Job -Job $infoJob
        if (-not $dockerInfo) {
            Write-Host "Docker daemon not responding" -ForegroundColor Red
            return $false
        }
        
        Write-Host "  ✅ Docker daemon responsive" -ForegroundColor Green
        
        # 3. Test container listing
        Write-Host "Testing container listing..." -ForegroundColor Gray
        $containersJob = Start-Job -ScriptBlock { docker ps 2>$null }
        $containersResult = Wait-Job -Job $containersJob -Timeout $TimeoutSeconds
        
        if (!$containersResult) {
            Stop-Job -Job $containersJob -Force
            Write-Host "Container listing timed out" -ForegroundColor Red
            return $false
        }
        
        $containers = Receive-Job -Job $containersJob
        if (-not $containers) {
            Write-Host "Cannot list containers (or no containers running)" -ForegroundColor Yellow
            # This is not necessarily an error - just no containers
            return $true
        }
        
        Write-Host "  ✅ Container listing successful" -ForegroundColor Green
        if ($containers) {
            Write-Host "  Containers: $($containers -split '\n' | Where-Object { $_ -ne '' } | Measure-Object | Select-Object -ExpandProperty Count) running" -ForegroundColor Green
        }
        
        # Clean up jobs
        Remove-Job -Job $versionJob -Force
        Remove-Job -Job $infoJob -Force
        Remove-Job -Job $containersJob -Force
        
        return $true
        
    } catch {
        Write-Host "Docker health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Restart-DockerDesktopService {
    Write-Host "Attempting to restart Docker Desktop service..." -ForegroundColor Yellow
    
    try {
        # Try to restart Docker service
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Restarting Docker Desktop service..." -ForegroundColor Yellow
            Restart-Service -Name "com.docker.service" -Force
            Write-Host "Docker Desktop service restarted successfully" -ForegroundColor Green
            
            # Wait for Docker to be ready
            Write-Host "Waiting for Docker daemon to be ready..." -ForegroundColor Gray
            Start-Sleep -Seconds 10
            
            return $true
        } else {
            Write-Host "Docker Desktop service not found" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Failed to restart Docker service: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "=== Docker Daemon Communication Fix ===" -ForegroundColor Cyan

# Test current daemon health
$healthy = Test-DockerHealthWithTimeout -TimeoutSeconds 30

if ($healthy) {
    Write-Host "✅ Docker daemon communication is working properly" -ForegroundColor Green
} else {
    Write-Host "❌ Docker daemon communication is failing" -ForegroundColor Red
    
    # Attempt to restart Docker Desktop
    $restartSuccess = Restart-DockerDesktopService
    
    if ($restartSuccess) {
        Write-Host "🔄 Retesting Docker daemon communication..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        $healthyAfterRestart = Test-DockerHealthWithTimeout -TimeoutSeconds 30
        if ($healthyAfterRestart) {
            Write-Host "✅ Docker daemon communication restored" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker daemon communication still failing" -ForegroundColor Red
        }
    }
}

Write-Host "=== Fix Complete ===" -ForegroundColor Cyan
