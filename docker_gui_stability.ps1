# Docker Desktop GUI Stability Fix
# Addresses GUI crashes while keeping Docker daemon stable

param(
    [switch]$Apply,
    [switch]$Check,
    [switch]$Monitor
)

Write-Host "Docker Desktop GUI Stability Fix" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta

if ($Check) {
    Write-Host "Checking Docker Desktop GUI stability..." -ForegroundColor Cyan
    
    # Check if Docker Desktop GUI is running
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses.Count -gt 0) {
        Write-Host "Docker Desktop GUI: Running (PID: $($dockerProcesses[0].Id)" -ForegroundColor Green
        Write-Host "  Process Age: $((Get-Date) - $dockerProcesses[0].StartTime)" -ForegroundColor Gray
    } else {
        Write-Host "Docker Desktop GUI: Not running" -ForegroundColor Red
    }
    
    # Check Docker backend processes
    $backendProcesses = Get-Process -Name "com.docker.backend" -ErrorAction SilentlyContinue
    if ($backendProcesses.Count -gt 0) {
        Write-Host "Docker Backend: $($backendProcesses.Count) processes" -ForegroundColor Green
        foreach ($proc in $backendProcesses) {
            Write-Host "  PID: $($proc.Id), Age: $((Get-Date) - $proc.StartTime)" -ForegroundColor Gray
        }
    } else {
        Write-Host "Docker Backend: No processes" -ForegroundColor Red
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
    
    # Check if auto-restart job is running
    $autoRestartJob = Get-Job -Name "DockerAutoRestart" -ErrorAction SilentlyContinue
    if ($autoRestartJob) {
        Write-Host "Auto-Restart Job: Running (ID: $($autoRestartJob.Id))" -ForegroundColor Green
    } else {
        Write-Host "Auto-Restart Job: Not running" -ForegroundColor Red
    }
    
    exit 0
}

if ($Monitor) {
    Write-Host "Starting Docker Desktop GUI stability monitor..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    
    $crashCount = 0
    $startTime = Get-Date
    
    while ($true) {
        $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        $currentTime = Get-Date
        $uptime = $currentTime - $startTime
        
        if ($dockerProcesses.Count -gt 0) {
            $processAge = $currentTime - $dockerProcesses[0].StartTime
            Write-Host "[$($currentTime.ToString('HH:mm:ss'))] GUI: Running (PID: $($dockerProcesses[0].Id), Age: $($processAge.ToString('mm\:ss')), Total Uptime: $($uptime.ToString('mm\:ss'))" -ForegroundColor Green
        } else {
            $crashCount++
            Write-Host "[$($currentTime.ToString('HH:mm:ss'))] GUI: CRASHED! (Crash #$crashCount)" -ForegroundColor Red
            Write-Host "  Attempting auto-restart..." -ForegroundColor Yellow
            
            # Auto-restart the GUI
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
            Start-Sleep -Seconds 10
        }
        
        Start-Sleep -Seconds 5
    }
}

if ($Apply) {
    Write-Host "Applying Docker Desktop GUI stability fixes..." -ForegroundColor Magenta
    
    # Step 1: Create a more stable Docker Desktop settings file
    Write-Host "Step 1: Creating ultra-stable Docker Desktop settings..." -ForegroundColor Yellow
    
    $ultraStableSettings = @{
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
            "telemetry" = $false
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
            "proxies" = @{
                "httpProxy" = $null
                "httpsProxy" = $null
                "noProxy" = $null
            }
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
        "extensions" = @{
            "marketplace" = $false
        }
        "features" = @{
            "useDockerContentTrust" = $false
            "useLegacyVirtualizationEngine" = $false
        }
    }
    
    # Ensure Docker Desktop settings directory exists
    $desktopSettingsPath = "$env:APPDATA\Docker\settings.json"
    $desktopSettingsDir = Split-Path $desktopSettingsPath -Parent
    if (!(Test-Path $desktopSettingsDir)) {
        New-Item -ItemType Directory -Path $desktopSettingsDir -Force | Out-Null
    }
    
    # Write ultra-stable settings
    $ultraStableSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath $desktopSettingsPath -Force -Encoding utf8
    Write-Host "  Applied ultra-stable Docker Desktop settings" -ForegroundColor Green
    
    # Step 2: Create a more intelligent auto-restart script
    Write-Host "Step 2: Creating intelligent auto-restart script..." -ForegroundColor Yellow
    
    $intelligentRestartScript = @"
# Intelligent Docker Desktop GUI Auto-Restart Script
# Monitors GUI stability and restarts intelligently

`$crashCount = 0
`$maxCrashesPerHour = 5
`$crashHistory = @()
`$startTime = Get-Date

Write-Host "Starting intelligent Docker Desktop GUI monitor..." -ForegroundColor Green
Write-Host "Max crashes per hour: `$maxCrashesPerHour" -ForegroundColor Yellow

while (`$true) {
    `$currentTime = Get-Date
    
    # Clean old crash history (older than 1 hour)
    `$crashHistory = `$crashHistory | Where-Object { `$currentTime - `$_ -lt [TimeSpan]::FromHours(1) }
    
    `$dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    
    if (`$dockerProcesses.Count -eq 0) {
        `$crashCount++
        `$crashHistory += `$currentTime
        
        Write-Host "[`$(`$currentTime.ToString('HH:mm:ss'))] GUI CRASHED! (Crash #`$crashCount in last hour)" -ForegroundColor Red
        
        if (`$crashHistory.Count -le `$maxCrashesPerHour) {
            Write-Host "  Attempting intelligent restart..." -ForegroundColor Yellow
            
            # Wait a bit before restarting to avoid rapid restart loops
            Start-Sleep -Seconds ([Math]::Min(30, `$crashCount * 10))
            
            # Start Docker Desktop with minimal settings
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
            
            # Wait longer for restart
            Start-Sleep -Seconds ([Math]::Min(60, `$crashCount * 15))
        } else {
            Write-Host "  Too many crashes in last hour. Waiting 5 minutes before restart..." -ForegroundColor Red
            Start-Sleep -Seconds 300
            `$crashHistory.Clear()
            `$crashCount = 0
        }
    } else {
        `$processAge = `$currentTime - `$dockerProcesses[0].StartTime
        if (`$processAge.TotalMinutes -gt 5) {
            Write-Host "[`$(`$currentTime.ToString('HH:mm:ss'))] GUI: Stable (PID: `$(`$dockerProcesses[0].Id), Age: `$(`$processAge.ToString('mm\:ss')))" -ForegroundColor Green
        }
    }
    
    Start-Sleep -Seconds 10
}
"@
    
    $intelligentRestartPath = "docker_intelligent_restart.ps1"
    $intelligentRestartScript | Out-File -FilePath $intelligentRestartPath -Force -Encoding utf8
    Write-Host "  Created intelligent auto-restart script: $intelligentRestartPath" -ForegroundColor Green
    
    # Step 3: Create a Windows service-like approach
    Write-Host "Step 3: Creating Windows service-like Docker Desktop launcher..." -ForegroundColor Yellow
    
    $serviceLauncherScript = @"
# Windows Service-like Docker Desktop Launcher
# Runs Docker Desktop as a monitored service

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

`$serviceName = "DockerDesktopService"
`$processName = "Docker Desktop"
`$exePath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

if (`$Start) {
    Write-Host "Starting Docker Desktop service..." -ForegroundColor Green
    
    # Kill any existing processes
    Get-Process -Name `$processName -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Start the service
    Start-Process `$exePath -WindowStyle Minimized
    
    # Wait for startup
    Start-Sleep -Seconds 30
    
    # Start the intelligent monitor
    Start-Job -ScriptBlock { & ".\docker_intelligent_restart.ps1" } -Name "DockerIntelligentMonitor"
    
    Write-Host "Docker Desktop service started with intelligent monitoring" -ForegroundColor Green
}

if (`$Stop) {
    Write-Host "Stopping Docker Desktop service..." -ForegroundColor Yellow
    
    # Stop the intelligent monitor
    Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue | Stop-Job -Force
    Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue | Remove-Job -Force
    
    # Stop Docker Desktop
    Get-Process -Name `$processName -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Write-Host "Docker Desktop service stopped" -ForegroundColor Green
}

if (`$Status) {
    `$dockerProcesses = Get-Process -Name `$processName -ErrorAction SilentlyContinue
    `$monitorJob = Get-Job -Name "DockerIntelligentMonitor" -ErrorAction SilentlyContinue
    
    Write-Host "Docker Desktop Service Status:" -ForegroundColor Cyan
    Write-Host "  GUI Process: `$(if (`$dockerProcesses.Count -gt 0) { "Running (PID: `$(`$dockerProcesses[0].Id))" } else { "Not running" })" -ForegroundColor `$(if (`$dockerProcesses.Count -gt 0) { "Green" } else { "Red" })
    Write-Host "  Monitor Job: `$(if (`$monitorJob) { "Active (ID: `$(`$monitorJob.Id))" } else { "Not running" })" -ForegroundColor `$(if (`$monitorJob) { "Green" } else { "Red" })
}

if (-not `$Start -and -not `$Stop -and -not `$Status) {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\docker_service_launcher.ps1 -Start    # Start Docker Desktop service" -ForegroundColor Cyan
    Write-Host "  .\docker_service_launcher.ps1 -Stop     # Stop Docker Desktop service" -ForegroundColor Red
    Write-Host "  .\docker_service_launcher.ps1 -Status   # Check service status" -ForegroundColor Yellow
}
"@
    
    $serviceLauncherPath = "docker_service_launcher.ps1"
    $serviceLauncherScript | Out-File -FilePath $serviceLauncherPath -Force -Encoding utf8
    Write-Host "  Created service launcher: $serviceLauncherPath" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Docker Desktop GUI stability fixes applied!" -ForegroundColor Green
    Write-Host ""
    Write-Host "What was created:" -ForegroundColor Cyan
    Write-Host "  - Ultra-stable Docker Desktop settings" -ForegroundColor White
    Write-Host "  - Intelligent auto-restart script" -ForegroundColor White
    Write-Host "  - Windows service-like launcher" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Stop current Docker Desktop" -ForegroundColor White
    Write-Host "  2. Start with service launcher: .\docker_service_launcher.ps1 -Start" -ForegroundColor White
    Write-Host "  3. Monitor stability: .\docker_gui_stability.ps1 -Monitor" -ForegroundColor White
    Write-Host ""
    Write-Host "Service launcher: .\docker_service_launcher.ps1" -ForegroundColor Green
    Write-Host "Intelligent restart: .\docker_intelligent_restart.ps1" -ForegroundColor Green
    
} else {
    Write-Host "Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\docker_gui_stability.ps1 -Check     # Check current status" -ForegroundColor Cyan
    Write-Host "  .\docker_gui_stability.ps1 -Apply     # Apply GUI stability fixes" -ForegroundColor Magenta
    Write-Host "  .\docker_gui_stability.ps1 -Monitor   # Monitor GUI stability in real-time" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This script addresses Docker Desktop GUI crashes specifically" -ForegroundColor White
    Write-Host "while keeping the Docker daemon stable and running." -ForegroundColor Gray
}
