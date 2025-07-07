# Windows Service Installation Script for CaseStrainer
# This script installs CaseStrainer as a Windows service for automatic startup

param(
    [string]$ServiceName = "CaseStrainer",
    [string]$DisplayName = "CaseStrainer Citation Verification Service",
    [string]$Description = "CaseStrainer citation verification and analysis service",
    [string]$Environment = "Production",
    [switch]$Uninstall,
    [switch]$Force
)

# Configuration
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$LauncherPath = Join-Path $ScriptPath "..\launcher.ps1"
$ServicePath = "powershell.exe"
$ServiceArgs = "-ExecutionPolicy Bypass -File `"$LauncherPath`" -Environment $Environment -NoMenu"
$LogPath = Join-Path $ScriptPath "..\logs\windows-service.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Write-Host $logEntry -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "Green" })
    Add-Content -Path $LogPath -Value $logEntry -ErrorAction SilentlyContinue
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-WindowsService {
    Write-Log "Installing CaseStrainer as Windows service..." -Level "INFO"
    
    # Check if service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        if ($Force) {
            Write-Log "Service already exists. Removing existing service..." -Level "WARN"
            Uninstall-WindowsService
        } else {
            Write-Log "Service '$ServiceName' already exists. Use -Force to overwrite." -Level "ERROR"
            return $false
        }
    }
    
    try {
        # Create the service
        $serviceParams = @{
            Name = $ServiceName
            DisplayName = $DisplayName
            Description = $Description
            BinaryPathName = "$ServicePath $ServiceArgs"
            StartupType = "Automatic"
            ErrorControl = "Normal"
        }
        
        New-Service @serviceParams | Out-Null
        
        # Configure service recovery options
        $recoveryParams = @{
            Name = $ServiceName
            FailureAction = "Restart"
            RestartDelay = 30000  # 30 seconds
            ResetPeriod = 86400   # 24 hours
        }
        
        Set-Service @recoveryParams -ErrorAction SilentlyContinue
        
        Write-Log "Windows service installed successfully" -Level "INFO"
        Write-Log "Service Name: $ServiceName" -Level "INFO"
        Write-Log "Display Name: $DisplayName" -Level "INFO"
        Write-Log "Startup Type: Automatic" -Level "INFO"
        Write-Log "Recovery: Restart after 30 seconds" -Level "INFO"
        
        return $true
        
    } catch {
        Write-Log "Failed to install Windows service: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Uninstall-WindowsService {
    Write-Log "Uninstalling CaseStrainer Windows service..." -Level "INFO"
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            # Stop the service if it's running
            if ($service.Status -eq "Running") {
                Write-Log "Stopping service..." -Level "INFO"
                Stop-Service -Name $ServiceName -Force
                Start-Sleep -Seconds 5
            }
            
            # Remove the service
            Remove-Service -Name $ServiceName -Force
            Write-Log "Windows service uninstalled successfully" -Level "INFO"
            return $true
        } else {
            Write-Log "Service '$ServiceName' not found" -Level "WARN"
            return $true
        }
    } catch {
        Write-Log "Failed to uninstall Windows service: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Start-WindowsService {
    Write-Log "Starting CaseStrainer Windows service..." -Level "INFO"
    
    try {
        Start-Service -Name $ServiceName
        Write-Log "Service started successfully" -Level "INFO"
        return $true
    } catch {
        Write-Log "Failed to start service: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Stop-WindowsService {
    Write-Log "Stopping CaseStrainer Windows service..." -Level "INFO"
    
    try {
        Stop-Service -Name $ServiceName -Force
        Write-Log "Service stopped successfully" -Level "INFO"
        return $true
    } catch {
        Write-Log "Failed to stop service: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Get-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Log "Service Status: $($service.Status)" -Level "INFO"
            Write-Log "Startup Type: $($service.StartType)" -Level "INFO"
            return $service.Status
        } else {
            Write-Log "Service not found" -Level "WARN"
            return $null
        }
    } catch {
        Write-Log "Failed to get service status: $($_.Exception.Message)" -Level "ERROR"
        return $null
    }
}

function Show-ServiceCommands {
    Write-Log "=== Windows Service Management Commands ===" -Level "INFO"
    Write-Log "Start Service:   Start-Service -Name '$ServiceName'" -Level "INFO"
    Write-Log "Stop Service:    Stop-Service -Name '$ServiceName'" -Level "INFO"
    Write-Log "Restart Service: Restart-Service -Name '$ServiceName'" -Level "INFO"
    Write-Log "Service Status:  Get-Service -Name '$ServiceName'" -Level "INFO"
    Write-Log "View Logs:       Get-EventLog -LogName Application -Source '$ServiceName'" -Level "INFO"
    Write-Log "==========================================" -Level "INFO"
}

# Main execution
try {
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Log "This script requires administrator privileges. Please run as administrator." -Level "ERROR"
        exit 1
    }
    
    # Create log directory
    $logDir = Split-Path -Parent $LogPath
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    Write-Log "CaseStrainer Windows Service Management" -Level "INFO"
    Write-Log "Script Path: $ScriptPath" -Level "INFO"
    Write-Log "Launcher Path: $LauncherPath" -Level "INFO"
    Write-Log "Environment: $Environment" -Level "INFO"
    
    if ($Uninstall) {
        $success = Uninstall-WindowsService
        if ($success) {
            Write-Log "Service uninstallation completed" -Level "INFO"
        } else {
            Write-Log "Service uninstallation failed" -Level "ERROR"
            exit 1
        }
    } else {
        # Install the service
        $success = Install-WindowsService
        if ($success) {
            Write-Log "Service installation completed" -Level "INFO"
            
            # Show service commands
            Show-ServiceCommands
            
            # Ask if user wants to start the service
            $response = Read-Host "Do you want to start the service now? (y/n)"
            if ($response -eq "y" -or $response -eq "Y") {
                Start-WindowsService
            }
        } else {
            Write-Log "Service installation failed" -Level "ERROR"
            exit 1
        }
    }
    
} catch {
    Write-Log "Script execution failed: $($_.Exception.Message)" -Level "ERROR"
    exit 1
} finally {
    Write-Log "Script execution completed" -Level "INFO"
} 