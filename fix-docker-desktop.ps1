#Requires -Version 5.1
<#
.SYNOPSIS
    Comprehensive Docker Desktop diagnostics and repair tool

.DESCRIPTION
    Diagnoses and fixes common Docker Desktop issues including:
    - UI crashes on startup
    - Resource conflicts
    - Permission issues
    - Configuration corruption
    - WSL2 integration problems

.EXAMPLE
    .\fix-docker-desktop.ps1 -Diagnose
    .\fix-docker-desktop.ps1 -FixUI
    .\fix-docker-desktop.ps1 -ResetAll
#>

param(
    [switch]$Diagnose,
    [switch]$FixUI,
    [switch]$ResetConfig,
    [switch]$ResetAll,
    [switch]$Verbose
)

$ErrorActionPreference = 'Continue'

function Write-DockerLog {
    param(
        [string]$Message,
        [string]$Level = 'INFO'
    )
    
    $timestamp = Get-Date -Format 'HH:mm:ss'
    $color = switch ($Level) {
        'ERROR' { 'Red' }
        'WARN'  { 'Yellow' }
        'SUCCESS' { 'Green' }
        default { 'White' }
    }
    
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-DockerDesktopHealth {
    Write-DockerLog "Performing Docker Desktop health check..." -Level INFO
    
    $results = @{}
    
    # Check Docker Engine
    try {
        $version = docker version --format "{{.Server.Version}}" 2>$null
        $results.Engine = if ($version) { "✅ Running ($version)" } else { "❌ Not responding" }
    }
    catch {
        $results.Engine = "❌ Error: $($_.Exception.Message)"
    }
    
    # Check UI Process
    $uiProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    $results.UI = if ($uiProcess) { "✅ Running (PID: $($uiProcess.Id))" } else { "❌ Not running" }
    
    # Check Backend Processes
    $backendProcesses = Get-Process "*docker*" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*docker*" }
    $results.Backend = "✅ $($backendProcesses.Count) processes running"
    
    # Check Context
    try {
        $context = docker context show 2>$null
        $results.Context = "✅ Using: $context"
    }
    catch {
        $results.Context = "❌ Context error"
    }
    
    # Check Containers
    try {
        $containers = docker ps --format "{{.Names}}" 2>$null
        $containerCount = if ($containers) { ($containers | Measure-Object).Count } else { 0 }
        $results.Containers = "✅ $containerCount containers running"
    }
    catch {
        $results.Containers = "❌ Cannot check containers"
    }
    
    # Check WSL2
    if (Get-Command wsl -ErrorAction SilentlyContinue) {
        try {
            $wslDistros = wsl -l -v 2>$null | Where-Object { $_ -match "docker" }
            $results.WSL2 = if ($wslDistros) { "✅ Docker WSL2 distros found" } else { "⚠️ No Docker WSL2 distros" }
        }
        catch {
            $results.WSL2 = "❌ WSL2 check failed"
        }
    }
    else {
        $results.WSL2 = "⚠️ WSL2 not available"
    }
    
    return $results
}

function Show-DiagnosticReport {
    $health = Test-DockerDesktopHealth
    
    Write-DockerLog "Docker Desktop Diagnostic Report" -Level SUCCESS
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
    foreach ($component in $health.GetEnumerator()) {
        Write-Host "  $($component.Key): $($component.Value)"
    }
    
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    
    # Recommendations
    $uiRunning = $health.UI -match "✅"
    $engineRunning = $health.Engine -match "✅"
    
    if ($engineRunning -and -not $uiRunning) {
        Write-DockerLog "DIAGNOSIS: Docker Engine is working but UI is not running" -Level WARN
        Write-DockerLog "RECOMMENDATION: Use -FixUI to restart the Docker Desktop UI" -Level INFO
    }
    elseif (-not $engineRunning) {
        Write-DockerLog "DIAGNOSIS: Docker Engine is not responding" -Level ERROR
        Write-DockerLog "RECOMMENDATION: Use -ResetAll to completely reset Docker Desktop" -Level INFO
    }
    else {
        Write-DockerLog "DIAGNOSIS: Docker Desktop appears to be working normally" -Level SUCCESS
    }
}

function Repair-DockerDesktopUI {
    Write-DockerLog "Repairing Docker Desktop UI..." -Level INFO
    
    # Stop UI process if running
    $uiProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    if ($uiProcess) {
        Write-DockerLog "Stopping existing Docker Desktop UI..." -Level INFO
        Stop-Process -Id $uiProcess.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
    
    # Clean UI cache
    $cacheDir = "$env:APPDATA\Docker"
    if (Test-Path $cacheDir) {
        Write-DockerLog "Cleaning Docker Desktop cache..." -Level INFO
        try {
            Remove-Item "$cacheDir\*.log" -Force -ErrorAction SilentlyContinue
            Remove-Item "$cacheDir\wc.dat" -Force -ErrorAction SilentlyContinue
        }
        catch {
            Write-DockerLog "Could not clean all cache files (some may be in use)" -Level WARN
        }
    }
    
    # Restart UI with admin privileges
    Write-DockerLog "Starting Docker Desktop UI with elevated privileges..." -Level INFO
    try {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -Verb RunAs -ErrorAction Stop
        Write-DockerLog "Docker Desktop UI started successfully" -Level SUCCESS
    }
    catch {
        Write-DockerLog "Failed to start Docker Desktop UI: $($_.Exception.Message)" -Level ERROR
        return $false
    }
    
    # Wait and verify
    Write-DockerLog "Waiting for UI to initialize..." -Level INFO
    Start-Sleep -Seconds 10
    
    $uiProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    if ($uiProcess) {
        Write-DockerLog "UI repair successful! Docker Desktop is now running." -Level SUCCESS
        return $true
    }
    else {
        Write-DockerLog "UI repair failed. The process may have crashed again." -Level ERROR
        return $false
    }
}

function Reset-DockerDesktopConfig {
    Write-DockerLog "Resetting Docker Desktop configuration..." -Level WARN
    
    # Stop all Docker processes
    Write-DockerLog "Stopping all Docker processes..." -Level INFO
    Stop-Process -Name "*docker*" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
    
    # Reset configuration files
    $configPaths = @(
        "$env:APPDATA\Docker\settings-store.json",
        "$env:APPDATA\Docker\features-overrides.json",
        "$env:APPDATA\Docker\locked-directories"
    )
    
    foreach ($path in $configPaths) {
        if (Test-Path $path) {
            Write-DockerLog "Resetting: $path" -Level INFO
            try {
                Remove-Item $path -Force
            }
            catch {
                Write-DockerLog "Could not reset ${path}: $($_.Exception.Message)" -Level WARN
            }
        }
    }
    
    Write-DockerLog "Configuration reset complete" -Level SUCCESS
}

function Reset-DockerDesktopCompletely {
    Write-DockerLog "Performing complete Docker Desktop reset..." -Level WARN
    Write-DockerLog "This will stop all containers and reset all settings!" -Level WARN
    
    # Stop everything
    Write-DockerLog "Stopping all Docker services and processes..." -Level INFO
    Stop-Process -Name "*docker*" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 10
    
    # Reset configuration
    Reset-DockerDesktopConfig
    
    # Clean more extensive cache
    $cleanupPaths = @(
        "$env:APPDATA\Docker",
        "$env:LOCALAPPDATA\Docker"
    )
    
    foreach ($path in $cleanupPaths) {
        if (Test-Path $path) {
            Write-DockerLog "Cleaning cache: $path" -Level INFO
            try {
                Get-ChildItem $path -File | Where-Object { $_.Name -match "\.(log|tmp|cache)$" } | Remove-Item -Force
            }
            catch {
                Write-DockerLog "Could not clean all files in ${path}" -Level WARN
            }
        }
    }
    
    # Restart Docker Desktop
    Write-DockerLog "Restarting Docker Desktop..." -Level INFO
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -Verb RunAs
    
    Write-DockerLog "Complete reset initiated. Please wait 30-60 seconds for Docker to fully restart." -Level SUCCESS
}

# Main execution
if ($Diagnose) {
    Show-DiagnosticReport
}
elseif ($FixUI) {
    $success = Repair-DockerDesktopUI
    if ($success) {
        Start-Sleep -Seconds 5
        Show-DiagnosticReport
    }
}
elseif ($ResetConfig) {
    Reset-DockerDesktopConfig
    Start-Sleep -Seconds 5
    Repair-DockerDesktopUI
}
elseif ($ResetAll) {
    $confirm = Read-Host "This will reset ALL Docker Desktop settings and stop containers. Continue? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Reset-DockerDesktopCompletely
    }
    else {
        Write-DockerLog "Reset cancelled" -Level INFO
    }
}
else {
    Write-DockerLog "Docker Desktop Repair Tool" -Level SUCCESS
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\fix-docker-desktop.ps1 -Diagnose      # Check current status"
    Write-Host "  .\fix-docker-desktop.ps1 -FixUI         # Fix UI startup issues"
    Write-Host "  .\fix-docker-desktop.ps1 -ResetConfig   # Reset configuration files"
    Write-Host "  .\fix-docker-desktop.ps1 -ResetAll      # Complete reset (destructive)"
    Write-Host ""
    Write-Host "Current Status:" -ForegroundColor Yellow
    Show-DiagnosticReport
}
