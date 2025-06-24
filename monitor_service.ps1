# CaseStrainer Health Monitor Service Script
# Run as Administrator to install/uninstall the service

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "status")]
    [string]$Action = "status"
)

$ServiceName = "CaseStrainerHealthMonitor"
$ServiceDisplayName = "CaseStrainer Health Monitor"
$ServiceDescription = "Monitors CaseStrainer production server health and sends alerts"
$ScriptPath = Join-Path $PSScriptRoot "monitor_health.py"
$ConfigPath = Join-Path $PSScriptRoot "config.json"
$LogPath = Join-Path $PSScriptRoot "logs"

# Create logs directory if it doesn't exist
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

function Install-Service {
    Write-Host "Installing $ServiceDisplayName..." -ForegroundColor Green
    
    $ServiceExists = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if ($ServiceExists) {
        Write-Host "Service already exists. Uninstalling first..." -ForegroundColor Yellow
        Uninstall-Service
    }
    
    # Create the service
    $ServiceArgs = @{
        Name = $ServiceName
        DisplayName = $ServiceDisplayName
        Description = $ServiceDescription
        BinaryPathName = "python.exe `"$ScriptPath`" --config `"$ConfigPath`" --continuous"
        StartMode = "Automatic"
        LogOnAsLocalSystem = $true
    }
    
    try {
        New-Service @ServiceArgs
        Write-Host "Service installed successfully!" -ForegroundColor Green
        Write-Host "Use 'Start-Service $ServiceName' to start the service" -ForegroundColor Cyan
    }
    catch {
        Write-Host "Failed to install service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Uninstall-Service {
    Write-Host "Uninstalling $ServiceDisplayName..." -ForegroundColor Yellow
    
    try {
        $Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        
        if ($Service) {
            if ($Service.Status -eq "Running") {
                Write-Host "Stopping service..." -ForegroundColor Yellow
                Stop-Service -Name $ServiceName -Force
            }
            
            Remove-Service -Name $ServiceName
            Write-Host "Service uninstalled successfully!" -ForegroundColor Green
        }
        else {
            Write-Host "Service not found." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Failed to uninstall service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Start-MonitorService {
    Write-Host "Starting $ServiceDisplayName..." -ForegroundColor Green
    
    try {
        Start-Service -Name $ServiceName
        Write-Host "Service started successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to start service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Stop-MonitorService {
    Write-Host "Stopping $ServiceDisplayName..." -ForegroundColor Yellow
    
    try {
        Stop-Service -Name $ServiceName -Force
        Write-Host "Service stopped successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to stop service: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Get-MonitorStatus {
    Write-Host "Checking $ServiceDisplayName status..." -ForegroundColor Cyan
    
    try {
        $Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        
        if ($Service) {
            $Status = $Service.Status
            $StartType = $Service.StartType
            
            Write-Host "Service Name: $ServiceName" -ForegroundColor White
            Write-Host "Display Name: $ServiceDisplayName" -ForegroundColor White
            Write-Host "Status: $Status" -ForegroundColor $(if ($Status -eq "Running") { "Green" } else { "Red" })
            Write-Host "Start Type: $StartType" -ForegroundColor White
            
            # Check if Python script is running
            $PythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*monitor_health.py*" }
            if ($PythonProcesses) {
                Write-Host "Python Monitor Processes: $($PythonProcesses.Count)" -ForegroundColor Green
            }
            else {
                Write-Host "No Python monitor processes found" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "Service not installed." -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Error checking service status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Check if running as Administrator
if ($Action -in @("install", "uninstall") -and -not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This action requires Administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

# Execute the requested action
switch ($Action) {
    "install" { Install-Service }
    "uninstall" { Uninstall-Service }
    "start" { Start-MonitorService }
    "stop" { Stop-MonitorService }
    "status" { Get-MonitorStatus }
    default {
        Write-Host "Usage: .\monitor_service.ps1 [-Action {install|uninstall|start|stop|status}]" -ForegroundColor Yellow
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  install   - Install the service (requires Admin)" -ForegroundColor White
        Write-Host "  uninstall - Remove the service (requires Admin)" -ForegroundColor White
        Write-Host "  start     - Start the service" -ForegroundColor White
        Write-Host "  stop      - Stop the service" -ForegroundColor White
        Write-Host "  status    - Check service status (default)" -ForegroundColor White
    }
} 