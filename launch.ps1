<# : Begin batch (batch script header for PowerShell)
@echo off
title CaseStrainer Launcher

:: Check if running from CMD or PowerShell
set "POWERSHELL_BITS=%PROCESSOR_ARCHITEW6432%"
if not defined POWERSHELL_BITS set "POWERSHELL_BITS=%PROCESSOR_ARCHITECTURE%"

:: If running from CMD, restart with PowerShell
if "%POWERSHELL_BITS%" neq "" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dpn0.ps1' %*"
    exit /b %ERRORLEVEL%
)

echo This should not be reached if PowerShell is available
exit /b 1

#>
# Begin PowerShell script

param(
    [ValidateSet("Development", "Production", "Menu")]
    [string]$Environment = "Menu",
    [switch]$NoMenu,
    [switch]$Help
)

function Show-Menu {
    param (
        [string]$Title = 'CaseStrainer Launcher',
        [string]$Message = 'Select an option:'
    )
    Clear-Host
    Write-Host "`n"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($Message) {
        Write-Host " $Message" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host " 1. Development Mode" -ForegroundColor Green
    Write-Host "    - Starts frontend dev server"
    Write-Host "    - Backend API only (no Nginx)"
    Write-Host ""
    
    Write-Host " 2. Production Mode" -ForegroundColor Green
    Write-Host "    - Uses Nginx with production config"
    Write-Host "    - Serves built frontend files"
    Write-Host ""
    
    Write-Host " 3. Check Server Status" -ForegroundColor Yellow
    Write-Host " 4. Stop All Services" -ForegroundColor Red
    Write-Host " 5. View Logs" -ForegroundColor Yellow
    Write-Host " 6. Help" -ForegroundColor Cyan
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    $selection = Read-Host "Select an option (0-6)"
    return $selection
}

function Show-Help {
    Clear-Host
    Write-Host "`nCaseStrainer Launcher - Help`n" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\launch.ps1 [Options]`n"
    Write-Host "Options:"
    Write-Host "  -Environment <Development|Production|Menu>"
    Write-Host "      Select environment directly (default: Menu)`n"
    Write-Host "  -NoMenu"
    Write-Host "      Run without showing the interactive menu`n"
    Write-Host "  -Help"
    Write-Host "      Show this help message`n"
    Write-Host "Examples:"
    Write-Host "  .\launch.ps1                     # Show interactive menu"
    Write-Host "  .\launch.ps1 -Environment Dev     # Start in Development mode"
    Write-Host "  .\launch.ps1 -NoMenu -Env Prod   # Start Production mode without menu`n"
    Write-Host "Press any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-ServerStatus {
    Clear-Host
    Write-Host "`n=== Server Status ===`n" -ForegroundColor Cyan
    
    # Check backend
    $backend = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*app_final_vue.py*' }
    
    Write-Host "Backend (Flask):" -NoNewline
    if ($backend) {
        Write-Host " RUNNING (PID: $($backend.Id))" -ForegroundColor Green
    } else {
        Write-Host " STOPPED" -ForegroundColor Red
    }
    
    # Check frontend
    $frontend = Get-Process node -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*vue-cli-service*' }
    
    Write-Host "Frontend (Vue):" -NoNewline
    if ($frontend) {
        Write-Host "  RUNNING (PID: $($frontend.Id))" -ForegroundColor Green
    } else {
        Write-Host "  STOPPED" -ForegroundColor Red
    }
    
    # Check Nginx
    $nginx = Get-Process nginx -ErrorAction SilentlyContinue
    Write-Host "Nginx:" -NoNewline
    if ($nginx) {
        Write-Host "         RUNNING (PID: $($nginx[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "         STOPPED" -ForegroundColor Red
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Stop-AllServices {
    Clear-Host
    Write-Host "`n=== Stopping All Services ===`n" -ForegroundColor Red
    
    # Stop frontend
    $frontend = Get-Process node -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*vue-cli-service*' }
    
    if ($frontend) {
        Write-Host "Stopping frontend (PID: $($frontend.Id))..." -NoNewline
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Frontend is not running" -ForegroundColor Gray
    }
    
    # Stop backend
    $backend = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*app_final_vue.py*' }
    
    if ($backend) {
        Write-Host "Stopping backend (PID: $($backend.Id))..." -NoNewline
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Backend is not running" -ForegroundColor Gray
    }
    
    # Stop Nginx
    $nginx = Get-Process nginx -ErrorAction SilentlyContinue
    if ($nginx) {
        Write-Host "Stopping Nginx..." -NoNewline
        Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Nginx is not running" -ForegroundColor Gray
    }
    
    Write-Host "`nAll services have been stopped."
    Write-Host "Press any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-Logs {
    param(
        [string]$LogType = ""
    )
    
    $logDir = "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $logFiles = @{
        "1" = @{ Name = "Backend"; Pattern = "backend_*.log" }
        "2" = @{ Name = "Frontend"; Pattern = "frontend_*.log" }
        "3" = @{ Name = "Nginx Access"; Pattern = "nginx_access.log" }
        "4" = @{ Name = "Nginx Error"; Pattern = "nginx_error.log" }
    }
    
    if (-not $LogType) {
        Clear-Host
        Write-Host "`n=== View Logs ===`n" -ForegroundColor Cyan
        Write-Host "Select log to view:`n"
        $logFiles.GetEnumerator() | Sort-Object Key | ForEach-Object {
            Write-Host " $($_.Key). $($_.Value.Name)"
        }
        Write-Host ""
        Write-Host " 0. Back to Menu"
        Write-Host ""
        
        $LogType = Read-Host "Select log (0-4)"
        if ($LogType -eq "0") { return }
        if (-not $logFiles.ContainsKey($LogType)) { return }
    }
    
    $logFile = Get-ChildItem -Path $logDir -Filter $logFiles[$LogType].Pattern | 
               Sort-Object LastWriteTime -Descending | 
               Select-Object -First 1
    
    if ($logFile) {
        Clear-Host
        Write-Host "`n=== $($logFiles[$LogType].Name) Log ===`n" -ForegroundColor Cyan
        Get-Content $logFile.FullName -Tail 50 -Wait
    } else {
        Write-Host "No log files found for $($logFiles[$LogType].Name)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

# Handle command line arguments
if ($Help) {
    Show-Help
    exit 0
}

# If environment is set via parameter and NoMenu is specified, skip the menu
if ($Environment -ne "Menu" -and $NoMenu) {
    # Continue with the specified environment
} else {
    # Show interactive menu
    do {
        $selection = Show-Menu
        
        switch ($selection) {
            '1' { $Environment = "Development"; break }
            '2' { $Environment = "Production"; break }
            '3' { Show-ServerStatus; continue }
            '4' { Stop-AllServices; continue }
            '5' { Show-Logs; continue }
            '6' { Show-Help; continue }
            '0' { exit 0 }
            default { 
                Write-Host "`nInvalid selection. Please try again." -ForegroundColor Red
                Start-Sleep -Seconds 1
                continue 
            }
        }
        
        # If we got here, user selected a valid environment
        break
    } while ($true)
}

# If we're here, we have a valid environment to run
Write-Host "`nStarting CaseStrainer in $Environment mode..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

# ==============================================
# Configuration - Edit these values as needed
# ==============================================
$config = @{
    Environment = $Environment
    
    # Paths
    BackendPath = "src/app_final_vue.py"
    FrontendPath = "casestrainer-vue-new"
    NginxPath = "nginx-1.27.5"
    NginxConfig = "conf/nginx.conf"
    NginxExe = "nginx.exe"
    NginxProcessName = "nginx"
    
    # Ports
    BackendPort = 5000
    FrontendPort = 5173
    NginxPort = 80
    NginxSslPort = 443
    
    # URLs
    BackendUrl = "http://localhost:5000"
    FrontendUrl = "http://localhost:5173"
    NginxUrl = "https://localhost"
    
    # Endpoints
    HealthCheckEndpoint = "/api/health"
    
    # Environment-specific settings
    Development = @{
        FlaskEnv = "development"
        DebugMode = $true
        LogLevel = "DEBUG"
        StartFrontend = $true
        StartNginx = $false
    }
    
    Production = @{
        FlaskEnv = "production"
        DebugMode = $false
        LogLevel = "INFO"
        StartFrontend = $false
        StartNginx = $true
    }
}

# Set environment-specific settings
$envConfig = $config[$Environment]
$config.FlaskEnv = $envConfig.FlaskEnv
$config.DebugMode = $envConfig.DebugMode
$config.LogLevel = $envConfig.LogLevel

# Functions
function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host "          CASESTRAINER DEVELOPMENT LAUNCHER" -ForegroundColor Cyan
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Environment: $($config.Environment)" -ForegroundColor Yellow
    Write-Host "  Backend:    $($config.BackendUrl)" -ForegroundColor Cyan
    Write-Host "  Frontend:   $($config.FrontendUrl)" -ForegroundColor Cyan
    Write-Host "  Debug Mode: $($config.DebugMode)" -ForegroundColor $(if ($config.DebugMode) { 'Green' } else { 'Gray' })
    Write-Host ""
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Starting services..." -ForegroundColor Gray
    Write-Host ""
}

function Start-Backend {
    param (
        [string]$BackendPath,
        [int]$Port
    )
    
    Write-Host "Starting backend server..." -ForegroundColor Green
    
    # Set Python path
    $env:PYTHONPATH = $PSScriptRoot
    
    # Start Python process
    $script = @"
import os
import sys
import logging
from flask_cors import CORS

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
from src.app_final_vue import app, create_app

# Create the app with CORS enabled
app = create_app()
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=$Port, debug=True)
"@

    $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
    $script | Out-File -FilePath $tempFile -Encoding ascii -Force
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $tempFile -PassThru -NoNewWindow -ErrorAction Stop
        Write-Host "Backend started with PID: $($process.Id)" -ForegroundColor Green
        return $process
    } catch {
        Write-Host "Failed to start backend: $_" -ForegroundColor Red
        return $null
    }
}

function Start-Frontend {
    param (
        [string]$FrontendPath,
        [int]$Port
    )
    
    Write-Host "Starting frontend development server..." -ForegroundColor Green
    
    # Check if port is already in use
    $portInUse = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet
    if ($portInUse) {
        Write-Host "Port $Port is already in use. Attempting to free it..." -ForegroundColor Yellow
        
        # Find and kill the process using the port
        $processInfo = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                        Select-Object -ExpandProperty OwningProcess -First 1
        
        if ($processInfo) {
            try {
                Stop-Process -Id $processInfo -Force -ErrorAction Stop
                Write-Host "Killed process $processInfo that was using port $Port" -ForegroundColor Yellow
                Start-Sleep -Seconds 2  # Give the port time to be released
            } catch {
                Write-Host "Failed to kill process $processInfo : $_" -ForegroundColor Red
                return $null
            }
        } else {
            Write-Host "Could not identify the process using port $Port" -ForegroundColor Red
            return $null
        }
    }
    
    $originalLocation = Get-Location
    
    try {
        $frontendPath = Join-Path $PSScriptRoot $FrontendPath
        if (-not (Test-Path $frontendPath)) {
            Write-Host "Frontend directory not found at: $frontendPath" -ForegroundColor Red
            return $null
        }
        
        Set-Location -Path $frontendPath -ErrorAction Stop
        
        # Check if npm is available
        $npmCmd = "npm.cmd"  # Use .cmd explicitly for Windows
        if (-not (Get-Command $npmCmd -ErrorAction SilentlyContinue)) {
            Write-Host "npm command not found. Please ensure Node.js is installed and in your PATH." -ForegroundColor Red
            return $null
        }
        
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
            & $npmCmd install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to install npm dependencies" -ForegroundColor Red
                return $null
            }
        }
        
        # Set environment variables for the frontend
        $env:NODE_ENV = "development"
        $env:VITE_API_BASE_URL = "/api"  # Use /api in development (handled by Vite proxy)
        $env:VITE_APP_ENV = "development"
        $env:PORT = $Port
        
        # Start npm dev server with explicit port
        Write-Host "Starting Vue development server on port $Port..." -ForegroundColor Cyan
        $process = Start-Process -FilePath $npmCmd -ArgumentList "run", "dev", "--", "--port", $Port, "--host" -PassThru -NoNewWindow -ErrorAction Stop
        
        # Wait a moment for the server to start
        Start-Sleep -Seconds 2
        
        # Check if the process is still running
        if ($process.HasExited -and $process.ExitCode -ne 0) {
            Write-Host "Failed to start frontend server. Exit code: $($process.ExitCode)" -ForegroundColor Red
            return $null
        }
        
        Write-Host "Frontend started with PID: $($process.Id)" -ForegroundColor Green
        return $process
    } catch {
        Write-Host "Failed to start frontend: $_" -ForegroundColor Red
        return $null
    } finally {
        Set-Location $originalLocation
    }
}

function Start-Nginx {
    param (
        [string]$NginxPath,
        [string]$ConfigFile
    )
    
    Write-Host "Starting Nginx..." -ForegroundColor Green
    
    # Stop any running Nginx instances
    try {
        $nginxProcesses = Get-Process -Name $config.NginxProcessName -ErrorAction SilentlyContinue
        if ($nginxProcesses) {
            Write-Host "Stopping existing Nginx processes..." -ForegroundColor Yellow
            $nginxProcesses | Stop-Process -Force
            Start-Sleep -Seconds 2  # Give it time to stop
        }
    } catch {
        Write-Host "Warning: Could not stop existing Nginx processes: $_" -ForegroundColor Yellow
    }
    
    # Build full paths - Join-Path only takes 2 arguments, so we need to chain them
    $nginxBasePath = Join-Path $PSScriptRoot $NginxPath
    $nginxExePath = Join-Path $nginxBasePath $config.NginxExe
    $configPath = Join-Path $nginxBasePath $ConfigFile
    
    if (-not (Test-Path $nginxExePath)) {
        Write-Host "Nginx executable not found at: $nginxExePath" -ForegroundColor Red
        return $null
    }
    
    if (-not (Test-Path $configPath)) {
        Write-Host "Nginx config file not found at: $configPath" -ForegroundColor Red
        return $null
    }
    
    try {
        # Change to Nginx directory to ensure relative paths in config work
        $originalLocation = Get-Location
        $nginxDir = Split-Path -Parent $nginxExePath
        Set-Location $nginxDir
        
        # Test Nginx configuration first
        $testResult = & $nginxExePath -t -c $configPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Nginx configuration test failed:" -ForegroundColor Red
            $testResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            return $null
        }
        
        # Start Nginx
        $process = Start-Process -FilePath $nginxExePath -ArgumentList "-c `"$configPath`"" -PassThru -NoNewWindow -ErrorAction Stop
        
        # Wait a moment for Nginx to start
        Start-Sleep -Seconds 2
        
        # Check if Nginx is running
        if ($process.HasExited -and $process.ExitCode -ne 0) {
            Write-Host "Failed to start Nginx. Exit code: $($process.ExitCode)" -ForegroundColor Red
            return $null
        }
        
        Write-Host "Nginx started with PID: $($process.Id)" -ForegroundColor Green
        return $process
    } catch {
        Write-Host "Failed to start Nginx: $_" -ForegroundColor Red
        return $null
    } finally {
        if ($originalLocation) { Set-Location $originalLocation }
    }
}

function Stop-Nginx {
    param (
        [switch]$Force = $false
    )
    
    try {
        $nginxProcesses = Get-Process -Name $config.NginxProcessName -ErrorAction SilentlyContinue
        if ($nginxProcesses) {
            Write-Host "Stopping Nginx..." -ForegroundColor Yellow
            $nginxProcesses | Stop-Process -Force:$Force
            Start-Sleep -Seconds 1  # Give it time to stop
            
            # Verify Nginx is stopped
            $nginxProcesses = Get-Process -Name $config.NginxProcessName -ErrorAction SilentlyContinue
            if ($nginxProcesses) {
                Write-Host "Warning: Some Nginx processes are still running" -ForegroundColor Red
                return $false
            }
            
            Write-Host "Nginx stopped successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "No Nginx processes found" -ForegroundColor Gray
            return $true
        }
    } catch {
        Write-Host "Error stopping Nginx: $_" -ForegroundColor Red
        return $false
    }
}

function Wait-ForService {
    param (
        [string]$Url,
        [string]$Method = 'HEAD',
        [int]$Timeout = 60
    )
    
    $startTime = Get-Date
    $success = $false
    
    Write-Host "Checking $Url " -NoNewline
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $Timeout) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $success = $true
                break
            }
        } catch {
            # Try with GET if HEAD fails
            try {
                $response = Invoke-WebRequest -Uri $Url -Method $Method -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $success = $true
                    break
                }
            } catch {
                # Service not ready yet
            }
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
    
    if ($success) {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [TIMEOUT]" -ForegroundColor Red
    }
    
    return $success
}

# Function to stop processes using a specific port
function Stop-ProcessesOnPort {
    param (
        [int]$Port
    )
    
    Write-Host "Checking for processes using port $Port..." -ForegroundColor Yellow
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                Where-Object { $_.State -eq 'Listen' } | 
                Select-Object -ExpandProperty OwningProcess -Unique | 
                ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
    
    if ($processes) {
        Write-Host "Found $(@($processes).Count) process(es) using port $Port. Stopping..." -ForegroundColor Yellow
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2  # Give processes time to shut down
    } else {
        Write-Host "No processes found using port $Port" -ForegroundColor Green
    }
}

# Main execution
Show-Header

# Stop any processes using required ports
Stop-ProcessesOnPort -Port $config.BackendPort
Stop-ProcessesOnPort -Port $config.FrontendPort

# Additional check for Node.js processes that might be using the port
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "Found $($nodeProcesses.Count) Node.js process(es). Stopping..." -ForegroundColor Yellow
    $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start services
$backend = Start-Backend -BackendPath $config.BackendPath -Port $config.BackendPort
if (-not $backend) {
    Write-Host "Failed to start backend. Exiting." -ForegroundColor Red
    exit 1
}

# Wait for backend to start
Write-Host "`n=== Starting Backend ===" -ForegroundColor Cyan
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # Give backend more time to initialize

# Check if backend is responding
$healthCheckUrl = "$($config.BackendUrl)$($config.HealthCheckEndpoint)"
Write-Host "Checking backend at $healthCheckUrl" -ForegroundColor Cyan

$backendHealthy = $false
$backendStatus = "Not Responding"
$backendVersion = "Unknown"
$backendEnv = "Unknown"

try {
    $response = Invoke-RestMethod -Uri $healthCheckUrl -Method Get -ErrorAction Stop -TimeoutSec 10
    $backendHealthy = $response.status -eq 'ok'  # Updated from 'healthy' to 'ok' to match the API response
    $backendStatus = $response.status
    $backendVersion = $response.version
    $backendEnv = $response.environment
} catch {
    Write-Host "Error checking backend status: $_" -ForegroundColor Red
}

if (-not $backendHealthy) {
    Write-Host ""
    Write-Host "=== Backend Status ===" -ForegroundColor Red
    Write-Host "Status:      $backendStatus"
    Write-Host "Environment: $backendEnv"
    Write-Host "Version:     $backendVersion"
    Write-Host ""
    Write-Host "Backend is not responding correctly. Possible issues:" -ForegroundColor Red
    Write-Host "1. The backend may have failed to start"
    Write-Host "2. The backend might be running on a different port"
    Write-Host "3. There might be a configuration error"
    Write-Host ""
    Write-Host "Check the logs at $PSScriptRoot\logs\casestrainer.log for errors" -ForegroundColor Yellow
    Write-Host "Backend did not start properly. Check the logs for errors." -ForegroundColor Red
    exit 1
} else {
    Write-Host ""
    Write-Host "=== Backend Status ===" -ForegroundColor Green
    Write-Host "Status:      $backendStatus"
}

# Enhanced health check function
function Test-WebEndpoint {
    param (
        [string]$Url,
        [int]$Timeout = 10,
        [int]$RetryInterval = 2,
        [int]$MaxRetries = 10,
        [string]$Description = "endpoint"
    )
    
    $retryCount = 0
    $success = $false
    
    Write-Host "`n=== Verifying $Description ===" -ForegroundColor Cyan
    Write-Host "URL: $Url"
    
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Head -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
            if ($response.StatusCode -in @(200, 301, 302, 403, 404)) {
                Write-Host "[$($response.StatusCode)] $($response.StatusDescription)" -ForegroundColor Green
                $success = $true
                break
            }
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($statusCode) {
                Write-Host "[$statusCode] $($_.Exception.Response.StatusDescription)" -ForegroundColor Green
                $success = $true
                break
            }
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
        
        $retryCount++
        if ($retryCount -lt $MaxRetries) {
            Start-Sleep -Seconds $RetryInterval
        }
    } while ($retryCount -lt $MaxRetries)
    
    if (-not $success) {
        Write-Host "`nWarning: Could not verify $Description at $Url" -ForegroundColor Yellow
    }
    
    return $success
}

# Check Nginx status with enhanced verification
$nginxHealthy = $false
$nginxStatus = "Not Started"

if ($envConfig.StartNginx) {
    $nginxHealthy = Test-WebEndpoint -Url $config.NginxUrl -Description "Nginx"
    $nginxStatus = if ($nginxHealthy) { "Running" } else { "Not Responding" }
}

# Start frontend server if configured
$frontendHealthy = $false
$frontendStatus = "Not Started"
$frontend = $null

if ($envConfig.StartFrontend) {
    $frontend = Start-Frontend -FrontendPath $config.FrontendPath -Port $config.FrontendPort
    if (-not $frontend) {
        Write-Host "Failed to start frontend. Check the logs for errors." -ForegroundColor Red
    }
    $frontendUrl = $config.FrontendUrl
    $frontendHealthy = Test-WebEndpoint -Url $frontendUrl -Description "Frontend"
    $frontendStatus = if ($frontendHealthy) { "Running" } else { "Not Responding" }
}

Write-Host ""
Write-Host "=== Frontend Status ===" -ForegroundColor $(if ($frontendHealthy) { 'Green' } else { 'Red' })
Write-Host "Status:  $frontendStatus"
Write-Host "URL:     $($config.FrontendUrl)"
Write-Host ""

if (-not $frontendHealthy -and $envConfig.StartFrontend) {
    Write-Host "Frontend did not start properly. Check the logs for errors." -ForegroundColor Yellow
}

# Show status
Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Development Environment Status" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Backend:  $($config.BackendUrl)" -ForegroundColor $(if ($backendHealthy) { 'Green' } else { 'Red' })
Write-Host "  Status:   $backendStatus"
Write-Host "  Env:      $backendEnv"
Write-Host "  Version:  $backendVersion"
Write-Host ""
Write-Host "  Nginx:    $($config.NginxUrl)" -ForegroundColor $(if ($nginxHealthy) { 'Green' } else { 'Red' })
Write-Host "  Status:   $nginxStatus"
Write-Host ""
Write-Host "  Frontend: $($config.FrontendUrl)" -ForegroundColor $(if ($frontendHealthy) { 'Green' } else { 'Red' })
Write-Host "  Status:   $frontendStatus"
Write-Host ""

$allServicesHealthy = $backendHealthy -and $nginxHealthy -and $frontendHealthy

if ($allServicesHealthy) {
    Write-Host "  All services started successfully!" -ForegroundColor Green
} else {
    Write-Host "  Some services did not start properly. Check the logs for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

# Open browser to the appropriate URL with better fallback logic
$browserUrl = if ($nginxHealthy -and $envConfig.StartNginx) {
    $url = $config.NginxUrl.TrimEnd('/') + "/casestrainer/"
    Write-Host "`nOpening browser to Nginx URL: $url" -ForegroundColor Cyan
    $url
} elseif ($frontendHealthy -and $envConfig.StartFrontend) {
    $url = "$($config.FrontendUrl)"
    Write-Host "`nOpening browser to Frontend URL: $url" -ForegroundColor Cyan
    $url
} else {
    $url = $config.BackendUrl
    Write-Host "`nOpening browser to Backend URL: $url (fallback)" -ForegroundColor Yellow
    $url
}

# Only open browser if we're not in a headless environment
if (-not $env:CI -and -not $env:TF_BUILD) {
    try {
        Start-Process $browserUrl
    } catch {
        Write-Host "Warning: Could not open browser automatically. Please open $browserUrl manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "Running in CI/CD environment. Please open $browserUrl in your browser." -ForegroundColor Cyan
}

# Keep script running until Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    
    if ($nginx) {
        $nginxStopped = Stop-Nginx -Force
        if ($nginxStopped) {
            Write-Host "Nginx stopped" -ForegroundColor Green
        } else {
            Write-Host "Warning: Failed to stop Nginx" -ForegroundColor Red
        }
    }
    
    if ($backend) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Backend stopped" -ForegroundColor Green
    }
    
    if ($frontend) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Frontend stopped" -ForegroundColor Green
    }
    
    Write-Host "All services stopped." -ForegroundColor Green
}

# Add a pause to keep the window open
Write-Host "`nPress any key to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
