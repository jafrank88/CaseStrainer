# Script to diagnose and fix Docker Desktop connectivity issues
# Run this script as Administrator for best results

param (
    [switch]$RestartDocker,
    [switch]$CheckOnly,
    [switch]$ResetWSL
)

function Write-Status {
    param($Message, $Status = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = @{
        "INFO" = "White"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR" = "Red"
    }[$Status]
    
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $color
}

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Status "This script should be run as Administrator for full functionality" -Status "WARNING"
}

# Check Docker service status
function Test-DockerService {
    try {
        $service = Get-Service -Name com.docker.service -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Status "Docker Desktop service not found" -Status "ERROR"
            return $false
        }
        
        if ($service.Status -ne 'Running') {
            Write-Status "Docker Desktop service is not running (Status: $($service.Status))" -Status "WARNING"
            return $false
        }
        
        Write-Status "Docker Desktop service is running" -Status "SUCCESS"
        return $true
    } catch {
        Write-Status "Error checking Docker service: $_" -Status "ERROR"
        return $false
    }
}

# Check Docker CLI connectivity
function Test-DockerConnection {
    try {
        $dockerVersion = docker version --format '{{.Client.Version}}' 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $dockerVersion
        }
        
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $dockerInfo
        }
        
        Write-Status "Docker CLI is working (Version: $dockerVersion)" -Status "SUCCESS"
        return $true
    } catch {
        Write-Status "Docker CLI is not working: $_" -Status "ERROR"
        return $false
    }
}

# Check WSL status
function Test-WslStatus {
    try {
        if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
            Write-Status "WSL is not installed" -Status "WARNING"
            return $false
        }
        
        $wslList = wsl --list --verbose 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $wslList
        }
        
        $wslStatus = wsl --status 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $wslStatus
        }
        
        Write-Status "WSL is running and accessible" -Status "SUCCESS"
        Write-Host $wslStatus -ForegroundColor Gray
        return $true
    } catch {
        Write-Status "WSL check failed: $_" -Status "ERROR"
        return $false
    }
}

# Restart Docker Desktop
function Restart-DockerDesktop {
    try {
        Write-Status "Stopping Docker Desktop..."
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "Docker" -Force -ErrorAction SilentlyContinue
        
        # Make sure the service is stopped
        $service = Get-Service -Name com.docker.service -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq 'Running') {
            Stop-Service -Name com.docker.service -Force -ErrorAction SilentlyContinue
        }
        
        # Wait for processes to stop
        Start-Sleep -Seconds 5
        
        # Start Docker Desktop
        Write-Status "Starting Docker Desktop..."
        Start-Process -FilePath "$env:LOCALAPPDATA\Docker\Docker Desktop\Docker Desktop.exe"
        
        # Wait for Docker to start
        $attempts = 0
        $maxAttempts = 30  # 30 seconds max
        $dockerReady = $false
        
        while ($attempts -lt $maxAttempts) {
            if (Test-DockerConnection) {
                $dockerReady = $true
                break
            }
            $attempts++
            Write-Status "Waiting for Docker to start... (Attempt $attempts/$maxAttempts)" -Status "INFO"
            Start-Sleep -Seconds 1
        }
        
        if (-not $dockerReady) {
            throw "Docker failed to start after $maxAttempts seconds"
        }
        
        Write-Status "Docker Desktop restarted successfully" -Status "SUCCESS"
        return $true
    } catch {
        Write-Status "Failed to restart Docker Desktop: $_" -Status "ERROR"
        return $false
    }
}

# Reset WSL if needed
function Reset-WslIfNeeded {
    if (-not $ResetWSL) {
        return $true
    }
    
    try {
        Write-Status "Resetting WSL..." -Status "WARNING"
        
        # Stop all WSL instances
        wsl --shutdown
        
        # Reset Docker data
        wsl --unregister docker-desktop
        wsl --unregister docker-desktop-data
        
        Write-Status "WSL has been reset. Please restart your computer for changes to take effect." -Status "SUCCESS"
        return $true
    } catch {
        Write-Status "Failed to reset WSL: $_" -Status "ERROR"
        return $false
    }
}

# Main execution
Write-Status "=== Docker Desktop Diagnostic Tool ===" -Status "INFO"

# Check Docker service
$serviceOk = Test-DockerService

# Check Docker CLI
$cliOk = Test-DockerConnection

# Check WSL
$wslOk = Test-WslStatus

# Show summary
Write-Status "`n=== Diagnostic Summary ===" -Status "INFO"
Write-Host "Docker Service: $(if ($serviceOk) { 'OK' } else { 'NOT OK' })" -ForegroundColor $(if ($serviceOk) { 'Green' } else { 'Red' })
Write-Host "Docker CLI: $(if ($cliOk) { 'OK' } else { 'NOT OK' })" -ForegroundColor $(if ($cliOk) { 'Green' } else { 'Red' })
Write-Host "WSL Status: $(if ($wslOk) { 'OK' } else { 'NOT OK' })" -ForegroundColor $(if ($wslOk) { 'Green' } else { 'Red' })

# Take action if needed
if ($CheckOnly) {
    exit
}

# Reset WSL if requested
if ($ResetWSL) {
    Reset-WslIfNeeded
    exit
}

# Restart Docker if requested or if there are issues
if ($RestartDocker -or -not ($serviceOk -and $cliOk)) {
    if (-not $isAdmin) {
        Write-Status "Restarting Docker requires administrator privileges. Please run this script as Administrator." -Status "ERROR"
        exit 1
    }
    
    $success = Restart-DockerDesktop
    if (-not $success) {
        Write-Status "Failed to fix Docker issues automatically. Please try restarting your computer." -Status "ERROR"
        exit 1
    }
}

# Final check
if (Test-DockerConnection) {
    Write-Status "Docker is now working correctly!" -Status "SUCCESS"
} else {
    Write-Status "Docker is still not working. Please try restarting your computer." -Status "ERROR"
    exit 1
}

Write-Status "=== Diagnostic Complete ===" -Status "INFO"
