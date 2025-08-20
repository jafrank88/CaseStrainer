# Aggressive Docker Desktop Stability Fix
# Addresses persistent crashing and disappearing issues

param(
    [switch]$Apply,
    [switch]$Check
)

Write-Host "Aggressive Docker Desktop Stability Fix" -ForegroundColor Red
Write-Host "=======================================" -ForegroundColor Red

if ($Check) {
    Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan
    
    # Check if Docker Desktop is running
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses.Count -gt 0) {
        Write-Host "Docker Desktop is running (PID: $($dockerProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "Docker Desktop is not running" -ForegroundColor Red
    }
    
    # Check Docker backend processes
    $backendProcesses = Get-Process -Name "com.docker.backend" -ErrorAction SilentlyContinue
    if ($backendProcesses.Count -gt 0) {
        Write-Host "Docker backend processes: $($backendProcesses.Count)" -ForegroundColor Green
    } else {
        Write-Host "No Docker backend processes" -ForegroundColor Red
    }
    
    # Check Docker CLI
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "Docker CLI: Available" -ForegroundColor Green
        } else {
            Write-Host "Docker CLI: Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "Docker CLI: Error" -ForegroundColor Red
    }
    
    exit 0
}

if ($Apply) {
    Write-Host "Applying aggressive Docker stability fixes..." -ForegroundColor Red
    
    # Step 1: Create ultra-conservative daemon configuration
    Write-Host "Step 1: Creating ultra-conservative daemon configuration..." -ForegroundColor Yellow
    
    $ultraConservativeConfig = @{
        "experimental" = $false
        "features" = @{
            "buildkit" = $false
        }
        "log-driver" = "json-file"
        "log-opts" = @{
            "max-size" = "5m"
            "max-file" = "1"
        }
        "storage-driver" = "overlay2"
        "max-concurrent-downloads" = 1
        "max-concurrent-uploads" = 1
        "shutdown-timeout" = 10
        "debug" = $false
        "live-restore" = $false
        "max-memory" = "2GB"
        "max-cpu" = "2"
        "default-ulimits" = @{
            "nofile" = @{
                "Name" = "nofile"
                "Hard" = 4096
                "Soft" = 1024
            }
        }
        "storage-opts" = @(
            "overlay2.override_kernel_check=true"
        )
        "dns" = @("8.8.8.8")
        "ipv6" = $false
        "userland-proxy" = $false
        "icc" = $false
        "ip-forward" = $false
        "ip-masq" = $false
    }
    
    # Ensure Docker config directory exists
    $dockerConfigPath = "$env:ProgramData\Docker\config\daemon.json"
    $dockerConfigDir = Split-Path $dockerConfigPath -Parent
    if (!(Test-Path $dockerConfigDir)) {
        New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
    }
    
    # Write ultra-conservative configuration
    $ultraConservativeConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $dockerConfigPath -Force -Encoding utf8
    Write-Host "  Applied ultra-conservative daemon configuration" -ForegroundColor Green
    
    # Step 2: Create ultra-conservative WSL configuration
    Write-Host "Step 2: Creating ultra-conservative WSL configuration..." -ForegroundColor Yellow
    
    $ultraConservativeWslConfig = @"
# Ultra-Conservative WSL Configuration for Docker Desktop
[wsl2]
# Very conservative memory allocation
memory=1GB
# Very conservative CPU allocation
processors=1
# Disable all experimental features
experimental=false
# Minimal swap
swap=512MB
# Basic memory management only
pageReporting=true
# Disable advanced features
nestedVirtualization=false
guiApplications=false
networkingMode=mirrored
dnsTunneling=false
localhostForwarding=false
diskCache=false
"@
    
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    $ultraConservativeWslConfig | Out-File -FilePath $wslConfigPath -Force -Encoding utf8
    Write-Host "  Applied ultra-conservative WSL configuration" -ForegroundColor Green
    
    # Step 3: Create Docker Desktop settings for maximum stability
    Write-Host "Step 3: Creating Docker Desktop settings for maximum stability..." -ForegroundColor Yellow
    
    $stableDesktopSettings = @{
        "dockerEngine" = @{
            "experimental" = $false
            "features" = @{
                "buildkit" = $false
            }
        }
        "general" = @{
            "autoStart" = $false
            "checkForUpdates" = $false
            "includeBetaVersions" = $false
            "openTunnels" = @()
            "showStartupMessage" = $false
            "startDockerDesktop" = $false
        }
        "resources" = @{
            "cpu" = @{
                "count" = 1
                "limit" = 1
            }
            "memory" = @{
                "limit" = 1024
                "swap" = 512
            }
            "disk" = @{
                "imageStorage" = @{
                    "path" = "C:\\Users\\$env:USERNAME\\AppData\\Local\\Docker\\wsl\\data\\ext4.vhdx"
                    "size" = 128000
                }
            }
        }
        "advanced" = @{
            "debug" = $false
            "experimental" = $false
            "hosts" = @()
            "registryMirrors" = @()
            "insecureRegistries" = @()
        }
        "kubernetes" = @{
            "enabled" = $false
        }
        "pro" = @{
            "enabled" = $false
        }
        "softwareUpdates" = @{
            "checkForUpdates" = $false
            "includeBetaVersions" = $false
        }
    }
    
    # Ensure Docker Desktop settings directory exists
    $desktopSettingsPath = "$env:APPDATA\Docker\settings.json"
    $desktopSettingsDir = Split-Path $desktopSettingsPath -Parent
    if (!(Test-Path $desktopSettingsDir)) {
        New-Item -ItemType Directory -Path $desktopSettingsDir -Force | Out-Null
    }
    
    # Write stable settings
    $stableDesktopSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath $desktopSettingsPath -Force -Encoding utf8
    Write-Host "  Applied Docker Desktop settings for maximum stability" -ForegroundColor Green
    
    # Step 4: Create a Docker Desktop auto-restart script
    Write-Host "Step 4: Creating Docker Desktop auto-restart script..." -ForegroundColor Yellow
    
    $autoRestartScript = @"
# Docker Desktop Auto-Restart Script
# Run this in background to keep Docker Desktop running

while (`$true) {
    `$dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if (`$dockerProcesses.Count -eq 0) {
        Write-Host "Docker Desktop crashed, restarting..." -ForegroundColor Yellow
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
        Start-Sleep -Seconds 30
    }
    Start-Sleep -Seconds 10
}
"@
    
    $autoRestartScriptPath = "docker_auto_restart.ps1"
    $autoRestartScript | Out-File -FilePath $autoRestartScriptPath -Force -Encoding utf8
    Write-Host "  Created auto-restart script: $autoRestartScriptPath" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Aggressive stability fixes applied!" -ForegroundColor Green
    Write-Host ""
    Write-Host "What was applied:" -ForegroundColor Cyan
    Write-Host "  - Ultra-conservative Docker daemon configuration" -ForegroundColor White
    Write-Host "  - Ultra-conservative WSL2 settings" -ForegroundColor White
    Write-Host "  - Maximum stability Docker Desktop settings" -ForegroundColor White
    Write-Host "  - Auto-restart script for persistent crashes" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Restart Docker Desktop to apply changes" -ForegroundColor White
    Write-Host "  2. If it still crashes, run the auto-restart script" -ForegroundColor White
    Write-Host "  3. Test stability before starting CaseStrainer" -ForegroundColor White
    Write-Host ""
    Write-Host "Auto-restart script: .\docker_auto_restart.ps1" -ForegroundColor Green
    
} else {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\aggressive_docker_fix.ps1 -Check    # Check current status" -ForegroundColor Cyan
    Write-Host "  .\aggressive_docker_fix.ps1 -Apply    # Apply aggressive fixes" -ForegroundColor Red
    Write-Host ""
    Write-Host "This script will:" -ForegroundColor White
    Write-Host "  - Create ultra-conservative Docker configuration" -ForegroundColor Gray
    Write-Host "  - Disable all experimental features" -ForegroundColor Gray
    Write-Host "  - Minimize resource usage" -ForegroundColor Gray
    Write-Host "  - Create auto-restart capability" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Use this if Docker Desktop keeps crashing!" -ForegroundColor Red
}
