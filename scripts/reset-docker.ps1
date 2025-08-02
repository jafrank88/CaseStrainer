# Docker Reset Script
# Resets Docker environment to fix common issues including 500 errors

# Requires admin privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Set error action preference
$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Invoke-SafeCommand {
    param([string]$Command, [string]$ErrorMessage, [switch]$ContinueOnError)
    
    Write-Host "  $Command" -ForegroundColor Gray
    try {
        Invoke-Expression $Command -ErrorAction Stop
        return $true
    } catch {
        if (-not $ContinueOnError) {
            Write-Host "  [ERROR] $ErrorMessage" -ForegroundColor Red
            Write-Host "  Details: $_" -ForegroundColor Red
            return $false
        } else {
            Write-Host "  [WARNING] $ErrorMessage" -ForegroundColor Yellow
            Write-Host "  Details: $_" -ForegroundColor Yellow
            return $true
        }
    }
}

# 1. Stop all running containers
Write-Header "Stopping all running containers"
$containers = docker ps -q 2>$null
if ($containers) {
    $containers | ForEach-Object {
        Invoke-SafeCommand -Command "docker stop $_" -ErrorMessage "Failed to stop container $_" -ContinueOnError
    }
} else {
    Write-Host "  No running containers found" -ForegroundColor Gray
}

# 2. Remove all containers
Write-Header "Removing all containers"
Invoke-SafeCommand -Command "docker rm -f $(docker ps -aq 2>$null) 2>$null" -ErrorMessage "Failed to remove containers" -ContinueOnError

# 3. Remove all volumes
Write-Header "Removing all volumes"
Invoke-SafeCommand -Command "docker volume rm $(docker volume ls -q 2>$null) 2>$null" -ErrorMessage "Failed to remove volumes" -ContinueOnError

# 4. Remove all networks (except default)
Write-Header "Removing custom networks"
$networks = docker network ls --format '{{.Name}}' 2>$null | Where-Object { $_ -ne 'bridge' -and $_ -ne 'host' -and $_ -ne 'none' }
if ($networks) {
    $networks | ForEach-Object {
        Invoke-SafeCommand -Command "docker network rm $_" -ErrorMessage "Failed to remove network $_" -ContinueOnError
    }
} else {
    Write-Host "  No custom networks found" -ForegroundColor Gray
}

# 5. Prune system
Write-Header "Pruning Docker system"
Invoke-SafeCommand -Command "docker system prune -a -f --volumes" -ErrorMessage "Failed to prune Docker system" -ContinueOnError

# 6. Stop Docker Desktop service
Write-Header "Stopping Docker Desktop"
$service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -eq 'Running') {
        Invoke-SafeCommand -Command "Stop-Service -Name 'com.docker.service' -Force" -ErrorMessage "Failed to stop Docker service"
    } else {
        Write-Host "  Docker service is already stopped" -ForegroundColor Gray
    }
} else {
    Write-Host "  Docker service not found" -ForegroundColor Yellow
}

# 7. Kill any remaining Docker processes
Write-Header "Stopping Docker processes"
$processes = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($processes) {
    $processes | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force -ErrorAction Stop
            Write-Host "  Stopped process: $($_.Name) (PID: $($_.Id))" -ForegroundColor Gray
        } catch {
            Write-Host "  [WARNING] Failed to stop process: $($_.Name) (PID: $($_.Id))" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  No Docker processes found" -ForegroundColor Gray
}

# 8. Wait a moment for processes to fully stop
Start-Sleep -Seconds 5

# 9. Start Docker Desktop service
Write-Header "Starting Docker Desktop"
if ($service) {
    Invoke-SafeCommand -Command "Start-Service -Name 'com.docker.service'" -ErrorMessage "Failed to start Docker service"
    
    # Wait for Docker to fully initialize
    Write-Host "  Waiting for Docker to initialize..." -ForegroundColor Gray
    $attempts = 0
    $maxAttempts = 30
    $dockerReady = $false
    
    while ($attempts -lt $maxAttempts) {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            break
        }
        $attempts++
        Write-Progress -Activity "Waiting for Docker to start" -Status "Attempt $attempts of $maxAttempts" -PercentComplete (($attempts / $maxAttempts) * 100)
        Start-Sleep -Seconds 2
    }
    
    if ($dockerReady) {
        Write-Host "  Docker started successfully" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Docker may not have started correctly" -ForegroundColor Yellow
        Write-Host "  Last error: $dockerInfo" -ForegroundColor Yellow
    }
    
    # Reset Docker context to default
    Invoke-SafeCommand -Command "docker context use default" -ErrorMessage "Failed to reset Docker context" -ContinueOnError
} else {
    Write-Host "  Docker service not found, cannot start" -ForegroundColor Red
    exit 1
}

# 10. Verify Docker is working
Write-Header "Verifying Docker installation"
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  $dockerVersion" -ForegroundColor Green
    
    # Run a test container
    Write-Host "  Running test container..." -ForegroundColor Gray
    $testResult = docker run --rm hello-world 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Docker is working correctly!" -ForegroundColor Green
        $testResult | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        if ($testResult.Count -gt 5) { Write-Host "  ..." -ForegroundColor Gray }
    } else {
        Write-Host "  [WARNING] Docker test container failed" -ForegroundColor Yellow
        Write-Host "  $testResult" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [ERROR] Docker is not working correctly" -ForegroundColor Red
    Write-Host "  $dockerVersion" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Docker reset complete! ===" -ForegroundColor Green
Write-Host "You may need to restart Docker Desktop for all changes to take effect." -ForegroundColor Yellow
