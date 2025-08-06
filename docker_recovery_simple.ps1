# Simple Docker Recovery Script

param(
    [switch]$CheckOnly,
    [switch]$Quick,
    [switch]$Full,
    [switch]$Emergency
)

Write-Host "=== Docker Recovery Script ===" -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "Running diagnostics..." -ForegroundColor Yellow
    
    # Check Docker responsiveness
    $startTime = Get-Date
    docker info >$null 2>&1
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is responsive (response time: $([math]::Round($duration, 2))s)" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker is unresponsive" -ForegroundColor Red
    }
    
    # Show container status
    Write-Host "`nContainer Status:" -ForegroundColor Yellow
    docker ps -a
    
    # Show system resources
    $cpu = Get-Counter "\Processor(_Total)\% Processor Time" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $memory = Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $totalMemory = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB
    $memoryPercent = (($totalMemory - $memory) / $totalMemory) * 100
    
    Write-Host "`nSystem Resources:" -ForegroundColor Yellow
    Write-Host "CPU Usage: $([math]::Round($cpu, 2))%" -ForegroundColor Green
    Write-Host "Memory Usage: $([math]::Round($memoryPercent, 2))%" -ForegroundColor Green
}
elseif ($Quick) {
    Write-Host "Performing quick recovery..." -ForegroundColor Yellow
    
    # Stop all casestrainer containers
    Write-Host "1. Stopping containers..." -ForegroundColor Yellow
    docker stop $(docker ps -q --filter "name=casestrainer") 2>$null
    
    # Start containers
    Write-Host "2. Starting containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml up -d
    
    Write-Host "✓ Quick recovery completed" -ForegroundColor Green
}
elseif ($Full) {
    Write-Host "Performing full recovery..." -ForegroundColor Yellow
    
    # Stop all containers
    Write-Host "1. Stopping all containers..." -ForegroundColor Yellow
    docker stop $(docker ps -q) 2>$null
    
    # Clean up
    Write-Host "2. Cleaning up Docker resources..." -ForegroundColor Yellow
    docker container prune -f 2>$null
    docker system prune -f 2>$null
    
    # Restart Docker Desktop
    Write-Host "3. Restarting Docker Desktop..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 10
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # Wait for Docker
    Write-Host "4. Waiting for Docker to start..." -ForegroundColor Yellow
    $timeout = 120
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        docker info >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Docker is ready" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
        Write-Host "Waiting... ($elapsed/$timeout seconds)" -ForegroundColor Yellow
    }
    
    # Start application
    Write-Host "5. Starting application..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml up -d --build
    
    Write-Host "✓ Full recovery completed" -ForegroundColor Green
}
elseif ($Emergency) {
    Write-Host "Performing emergency recovery..." -ForegroundColor Red
    
    # Stop everything
    Write-Host "1. Stopping all containers..." -ForegroundColor Yellow
    docker stop $(docker ps -q) 2>$null
    
    # Clean everything
    Write-Host "2. Cleaning all Docker resources..." -ForegroundColor Yellow
    docker container prune -f 2>$null
    docker image prune -f 2>$null
    docker volume prune -f 2>$null
    docker network prune -f 2>$null
    docker system prune -af 2>$null
    
    # Restart Docker Desktop
    Write-Host "3. Restarting Docker Desktop..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 15
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # Wait for Docker
    Write-Host "4. Waiting for Docker to start..." -ForegroundColor Yellow
    $timeout = 180
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        docker info >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Docker is ready" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 10
        $elapsed += 10
        Write-Host "Waiting... ($elapsed/$timeout seconds)" -ForegroundColor Yellow
    }
    
    # Rebuild everything
    Write-Host "5. Rebuilding application..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build --force-recreate
    
    Write-Host "✓ Emergency recovery completed" -ForegroundColor Green
}
else {
    Write-Host "Docker Recovery Script for CaseStrainer" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\docker_recovery_simple.ps1 -CheckOnly    # Run diagnostics only" -ForegroundColor White
    Write-Host "  .\docker_recovery_simple.ps1 -Quick        # Quick recovery (restart containers)" -ForegroundColor White
    Write-Host "  .\docker_recovery_simple.ps1 -Full         # Full recovery (restart Docker)" -ForegroundColor White
    Write-Host "  .\docker_recovery_simple.ps1 -Emergency    # Emergency recovery (reset everything)" -ForegroundColor White
    Write-Host ""
    Write-Host "Recommended approach:" -ForegroundColor Yellow
    Write-Host "1. Start with -CheckOnly to diagnose the issue" -ForegroundColor White
    Write-Host "2. Try -Quick for minor issues" -ForegroundColor White
    Write-Host "3. Use -Full for persistent problems" -ForegroundColor White
    Write-Host "4. Use -Emergency as a last resort" -ForegroundColor White
} 