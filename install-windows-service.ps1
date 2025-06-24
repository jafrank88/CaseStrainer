# CaseStrainer Windows Service Installer
# This script installs CaseStrainer as a Windows service for automatic restart capabilities

param(
    [switch]$Uninstall,
    [switch]$Help
)

# Configuration
$ServiceName = "CaseStrainer"
$ServiceDisplayName = "CaseStrainer Citation Validator"
$ServiceDescription = "CaseStrainer citation validation service with auto-restart capabilities"
$ServicePath = Join-Path $PSScriptRoot "launcher.ps1"
$ServiceArguments = "-Environment Production -NoMenu"

function Show-Help {
    Write-Host "CaseStrainer Windows Service Installer`n" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\install-windows-service.ps1 [Options]`n"
    Write-Host "Options:"
    Write-Host "  -Uninstall    Remove the Windows service"
    Write-Host "  -Help         Show this help message`n"
    Write-Host "Examples:"
    Write-Host "  .\install-windows-service.ps1              # Install the service"
    Write-Host "  .\install-windows-service.ps1 -Uninstall   # Remove the service`n"
    Write-Host "Note: This script must be run as Administrator" -ForegroundColor Yellow
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Service {
    Write-Host "Installing CaseStrainer as Windows service..." -ForegroundColor Green
    
    # Check if service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "Service '$ServiceName' already exists. Removing it first..." -ForegroundColor Yellow
        Uninstall-Service
    }
    
    # Create the service
    try {
        $serviceArgs = @{
            Name = $ServiceName
            DisplayName = $ServiceDisplayName
            Description = $ServiceDescription
            BinaryPathName = "powershell.exe -ExecutionPolicy Bypass -File `"$ServicePath`" $ServiceArguments"
            StartupType = "Automatic"
            ErrorAction = "Stop"
        }
        
        New-Service @serviceArgs | Out-Null
        
        Write-Host "Service installed successfully!" -ForegroundColor Green
        Write-Host "Service Name: $ServiceName" -ForegroundColor White
        Write-Host "Display Name: $ServiceDisplayName" -ForegroundColor White
        Write-Host "Startup Type: Automatic" -ForegroundColor White
        Write-Host ""
        Write-Host "To start the service:" -ForegroundColor Cyan
        Write-Host "  Start-Service $ServiceName" -ForegroundColor White
        Write-Host ""
        Write-Host "To stop the service:" -ForegroundColor Cyan
        Write-Host "  Stop-Service $ServiceName" -ForegroundColor White
        Write-Host ""
        Write-Host "To view service status:" -ForegroundColor Cyan
        Write-Host "  Get-Service $ServiceName" -ForegroundColor White
        Write-Host ""
        Write-Host "The service will automatically restart if it crashes." -ForegroundColor Green
        
    } catch {
        Write-Host "Failed to install service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Uninstall-Service {
    Write-Host "Removing CaseStrainer Windows service..." -ForegroundColor Yellow
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        
        # Stop the service if it's running
        if ($service.Status -eq "Running") {
            Write-Host "Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Remove the service
        Remove-Service -Name $ServiceName -ErrorAction Stop
        
        Write-Host "Service removed successfully!" -ForegroundColor Green
        
    } catch {
        Write-Host "Failed to remove service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

# Check if running as Administrator
if (-not (Test-Administrator)) {
    Write-Host "This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Check if launcher script exists
if (-not (Test-Path $ServicePath)) {
    Write-Host "Launcher script not found at: $ServicePath" -ForegroundColor Red
    Write-Host "Please run this script from the CaseStrainer root directory." -ForegroundColor Yellow
    exit 1
}

if ($Uninstall) {
    Uninstall-Service
} else {
    Install-Service
} 