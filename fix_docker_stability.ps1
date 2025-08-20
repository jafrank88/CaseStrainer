# Docker Stability Fix Script for CaseStrainer
# Run this after resetting Docker Desktop to factory defaults

param(
    [switch]$Apply,
    [switch]$ShowCurrent
)

# Configuration paths
$DockerConfigPath = "$env:ProgramData\Docker\config\daemon.json"
$WSLConfigPath = "$env:USERPROFILE\.wslconfig"

Write-Host "Docker Stability Fix Script for CaseStrainer" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if ($ShowCurrent) {
    Write-Host "Current Docker Configuration:" -ForegroundColor Cyan
    
    # Check Docker CLI
    Write-Host "Docker CLI:" -ForegroundColor White
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "  Available: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "  Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Error checking version" -ForegroundColor Red
    }
    
    # Check daemon configuration
    Write-Host "Daemon Configuration:" -ForegroundColor White
    if (Test-Path $DockerConfigPath) {
        Write-Host "  Found at: $DockerConfigPath" -ForegroundColor Green
    } else {
        Write-Host "  Not found" -ForegroundColor Red
    }
    
    # Check WSL configuration
    Write-Host "WSL Configuration:" -ForegroundColor White
    if (Test-Path $WSLConfigPath) {
        Write-Host "  Found at: $WSLConfigPath" -ForegroundColor Green
    } else {
        Write-Host "  Not found" -ForegroundColor Red
    }
    
    exit 0
}

if ($Apply) {
    Write-Host "Applying Docker stability fixes..." -ForegroundColor Green
    
    # Create optimized daemon configuration
    Write-Host "Creating optimized Docker daemon configuration..." -ForegroundColor Cyan
    
    $daemonConfig = @{
        "builder" = @{
            "gc" = @{
                "defaultKeepStorage" = "20GB"
                "enabled" = $true
            }
        }
        "experimental" = $false
        "features" = @{
            "buildkit" = $true
        }
        "log-driver" = "json-file"
        "log-opts" = @{
            "max-size" = "10m"
            "max-file" = "3"
        }
        "storage-driver" = "overlay2"
        "max-concurrent-downloads" = 10
        "max-concurrent-uploads" = 5
        "shutdown-timeout" = 30
        "debug" = $false
        "dns" = @("8.8.8.8", "8.8.4.4")
        "ipv6" = $false
        "live-restore" = $true
        "max-memory" = "4GB"
        "max-cpu" = "4"
    }
    
    # Ensure Docker config directory exists
    $dockerConfigDir = Split-Path $DockerConfigPath -Parent
    if (!(Test-Path $dockerConfigDir)) {
        New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
        Write-Host "  Created Docker config directory" -ForegroundColor Green
    }
    
    # Write optimized configuration
    $daemonConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $DockerConfigPath -Force -Encoding utf8
    Write-Host "  Applied optimized Docker daemon configuration" -ForegroundColor Green
    
    # Create optimized WSL configuration
    Write-Host "Creating optimized WSL configuration..." -ForegroundColor Cyan
    
    $wslConfig = @"
# WSL Configuration for Docker Desktop - Optimized for CaseStrainer
[wsl2]

# Memory allocation - 4GB for Docker containers
memory=4GB

# CPU allocation - 4 cores for Docker containers  
processors=4

# Enable nested virtualization for better Docker performance
nestedVirtualization=true

# Enable WSLg for GUI applications
guiApplications=true

# Network configuration for Docker
networkingMode=mirrored
dnsTunneling=true
localhostForwarding=true

# Kernel optimizations for Docker
kernelCommandLine=vsyscall=emulate

# Enable experimental features for better performance
experimental=true

# Swap configuration - 2GB for memory management
swap=2GB

# Memory management optimizations
pageReporting=true
memoryReclaim=true

# Disk I/O optimizations
diskCache=true
diskCacheSize=1GB
"@
    
    # Write WSL configuration
    $wslConfig | Out-File -FilePath $WSLConfigPath -Force -Encoding utf8
    Write-Host "  Applied optimized WSL configuration" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Docker stability fixes completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Optimizations applied:" -ForegroundColor Cyan
    Write-Host "  - Enhanced Docker daemon configuration" -ForegroundColor White
    Write-Host "  - Optimized WSL2 settings for Docker" -ForegroundColor White
    Write-Host "  - Better stability and performance" -ForegroundColor White
    Write-Host "  - Resource limits to prevent crashes" -ForegroundColor White
    Write-Host ""
    Write-Host "Please restart Docker Desktop to apply changes" -ForegroundColor Yellow
    Write-Host "Then use '.\cslaunch.ps1' to start CaseStrainer" -ForegroundColor Green
    
} else {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\fix_docker_stability.ps1 -ShowCurrent    # Show current configuration" -ForegroundColor Cyan
    Write-Host "  .\fix_docker_stability.ps1 -Apply          # Apply stability fixes" -ForegroundColor Green
    Write-Host ""
    Write-Host "This script will fix Docker Desktop for:" -ForegroundColor White
    Write-Host "  - Better stability and performance" -ForegroundColor Gray
    Write-Host "  - Optimized resource allocation" -ForegroundColor Gray
    Write-Host "  - Enhanced WSL2 integration" -ForegroundColor Gray
    Write-Host "  - Production-ready daemon settings" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Recommended: Run with -Apply after factory reset" -ForegroundColor Green
}
