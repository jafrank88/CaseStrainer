# Emergency Docker Desktop Fix Script
# Addresses the opening/closing issue after factory reset

param(
    [switch]$Fix,
    [switch]$Check
)

Write-Host "Emergency Docker Desktop Fix Script" -ForegroundColor Red
Write-Host "====================================" -ForegroundColor Red

if ($Check) {
    Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan
    
    # Check if Docker Desktop is running
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses.Count -gt 0) {
        Write-Host "Docker Desktop is running (PID: $($dockerProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "Docker Desktop is not running" -ForegroundColor Red
    }
    
    # Check Docker service
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Docker service status: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Running"){"Green"}else{"Red"})
        } else {
            Write-Host "Docker service not found" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error checking Docker service" -ForegroundColor Red
    }
    
    # Check WSL status
    try {
        $wslStatus = wsl --status 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "WSL is running" -ForegroundColor Green
        } else {
            Write-Host "WSL is not running" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error checking WSL status" -ForegroundColor Red
    }
    
    exit 0
}

if ($Fix) {
    Write-Host "Applying emergency Docker Desktop fixes..." -ForegroundColor Red
    
    # Step 1: Kill all Docker processes
    Write-Host "Step 1: Killing all Docker processes..." -ForegroundColor Yellow
    Get-Process -Name "*docker*" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "*Docker*" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 3
    
    # Step 2: Stop Docker service
    Write-Host "Step 2: Stopping Docker service..." -ForegroundColor Yellow
    try {
        Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "Docker service already stopped or not found" -ForegroundColor Gray
    }
    
    # Step 3: Clean up Docker resources
    Write-Host "Step 3: Cleaning up Docker resources..." -ForegroundColor Yellow
    
    # Remove Docker Desktop settings
    $dockerSettingsPath = "$env:APPDATA\Docker\settings.json"
    if (Test-Path $dockerSettingsPath) {
        Remove-Item $dockerSettingsPath -Force
        Write-Host "  Removed Docker Desktop settings" -ForegroundColor Green
    }
    
    # Remove Docker daemon config
    $dockerConfigPath = "$env:ProgramData\Docker\config\daemon.json"
    if (Test-Path $dockerConfigPath) {
        Remove-Item $dockerConfigPath -Force
        Write-Host "  Removed Docker daemon config" -ForegroundColor Green
    }
    
    # Step 4: Reset WSL
    Write-Host "Step 4: Resetting WSL..." -ForegroundColor Yellow
    try {
        wsl --shutdown
        Start-Sleep -Seconds 3
        Write-Host "  WSL shutdown completed" -ForegroundColor Green
    } catch {
        Write-Host "  WSL shutdown failed" -ForegroundColor Red
    }
    
    # Step 5: Clean up Docker data
    Write-Host "Step 5: Cleaning up Docker data..." -ForegroundColor Yellow
    $dockerDataPath = "$env:USERPROFILE\AppData\Local\Docker"
    if (Test-Path $dockerDataPath) {
        try {
            Remove-Item "$dockerDataPath\wsl" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  Cleaned WSL data" -ForegroundColor Green
        } catch {
            Write-Host "  Could not clean WSL data" -ForegroundColor Yellow
        }
    }
    
    # Step 6: Create minimal stable configuration
    Write-Host "Step 6: Creating minimal stable configuration..." -ForegroundColor Yellow
    
    # Create minimal daemon config
    $minimalConfig = @{
        "experimental" = $false
        "features" = @{
            "buildkit" = $true
        }
        "log-driver" = "json-file"
        "log-opts" = @{
            "max-size" = "10m"
            "max-file" = "1"
        }
        "storage-driver" = "overlay2"
        "max-concurrent-downloads" = 3
        "max-concurrent-uploads" = 2
        "shutdown-timeout" = 15
        "debug" = $false
        "live-restore" = $false
    }
    
    # Ensure Docker config directory exists
    $dockerConfigDir = Split-Path $dockerConfigPath -Parent
    if (!(Test-Path $dockerConfigDir)) {
        New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
    }
    
    # Write minimal configuration
    $minimalConfig | ConvertTo-Json -Depth 5 | Out-File -FilePath $dockerConfigPath -Force -Encoding utf8
    Write-Host "  Created minimal daemon config" -ForegroundColor Green
    
    # Create minimal WSL config
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    $minimalWslConfig = @"
# Minimal WSL Configuration for Docker Desktop
[wsl2]
# Conservative memory allocation
memory=2GB
# Conservative CPU allocation
processors=2
# Disable experimental features
experimental=false
# Basic swap
swap=1GB
# Basic memory management
pageReporting=true
"@
    
    $minimalWslConfig | Out-File -FilePath $wslConfigPath -Force -Encoding utf8
    Write-Host "  Created minimal WSL config" -ForegroundColor Green
    
    # Step 7: Start Docker Desktop with minimal settings
    Write-Host "Step 7: Starting Docker Desktop..." -ForegroundColor Yellow
    
    $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        Start-Process -FilePath $dockerDesktopPath -WindowStyle Minimized
        Write-Host "  Docker Desktop started" -ForegroundColor Green
        } else {
        Write-Host "  Docker Desktop executable not found" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Emergency fixes applied!" -ForegroundColor Green
    Write-Host ""
    Write-Host "What was fixed:" -ForegroundColor Cyan
    Write-Host "  - Killed all Docker processes" -ForegroundColor White
    Write-Host "  - Stopped Docker service" -ForegroundColor White
    Write-Host "  - Cleaned up Docker settings and data" -ForegroundColor White
    Write-Host "  - Reset WSL" -ForegroundColor White
    Write-Host "  - Created minimal stable configuration" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Wait for Docker Desktop to fully start" -ForegroundColor White
    Write-Host "  2. Test if it stays running" -ForegroundColor White
    Write-Host "  3. If stable, run '.\fix_docker_stability.ps1 -Apply' for full optimization" -ForegroundColor White
    Write-Host "  4. Then use '.\cslaunch.ps1' to start CaseStrainer" -ForegroundColor White
    
} else {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\emergency_docker_fix.ps1 -Check    # Check current status" -ForegroundColor Cyan
    Write-Host "  .\emergency_docker_fix.ps1 -Fix      # Apply emergency fixes" -ForegroundColor Red
    Write-Host ""
    Write-Host "This script will:" -ForegroundColor White
    Write-Host "  - Kill all Docker processes" -ForegroundColor Gray
    Write-Host "  - Clean up Docker data and settings" -ForegroundColor Gray
    Write-Host "  - Reset WSL integration" -ForegroundColor Gray
    Write-Host "  - Create minimal stable configuration" -ForegroundColor Gray
    Write-Host "  - Start Docker Desktop fresh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Use this if Docker Desktop keeps opening and closing!" -ForegroundColor Red
}
