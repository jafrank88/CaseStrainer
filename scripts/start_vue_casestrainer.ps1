# CaseStrainer Vue.js PowerShell Startup Script
Write-Host "===================================================
CaseStrainer Vue.js Startup Script for Production
===================================================" -ForegroundColor Cyan

# Set the current directory to the script directory
Set-Location $PSScriptRoot

# Check local IP address
Write-Host "Checking local IP address..." -ForegroundColor Green
$localIP = "127.0.0.1"
$ipInfo = Get-NetIPAddress | Where-Object { $_.IPAddress -like "10.158.*" -and $_.AddressFamily -eq "IPv4" }
if ($ipInfo) {
    $localIP = $ipInfo.IPAddress
    Write-Host "Found local IP: $localIP" -ForegroundColor Green
}

# Stop any Windows Nginx instances
Write-Host "Checking for Windows Nginx..." -ForegroundColor Green
$nginxProcess = Get-Process -Name nginx -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Write-Host "Stopping Windows Nginx..." -ForegroundColor Yellow
    Stop-Process -Name nginx -Force
    Write-Host "Windows Nginx stopped." -ForegroundColor Green
} else {
    Write-Host "Windows Nginx is not running." -ForegroundColor Green
}

# Check if port 5000 is available
Write-Host "Checking if port 5000 is available..." -ForegroundColor Green
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port 5000 is already in use." -ForegroundColor Yellow
    Write-Host "Stopping any processes using port 5000..." -ForegroundColor Yellow
    
    foreach ($process in $portInUse) {
        $processId = $process.OwningProcess
        Write-Host "Killing process with PID: $processId" -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 2
}

# Kill any existing Python processes
Write-Host "Stopping any existing Python processes..." -ForegroundColor Green
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force

# Find Python executable
Write-Host "Looking for Python executable..." -ForegroundColor Green
$pythonPath = $null

# Check for Python in virtual environment
if (Test-Path ".venv\Scripts\python.exe") {
    $pythonPath = (Resolve-Path ".venv\Scripts\python.exe").Path
    Write-Host "Found Python in virtual environment: $pythonPath" -ForegroundColor Green
} else {
    # Try to find Python in PATH
    try {
        $pythonPath = (Get-Command python -ErrorAction Stop).Source
        Write-Host "Found Python in PATH: $pythonPath" -ForegroundColor Green
    } catch {
        # Check common installation directories
        $commonPaths = @(
            "C:\Python311\python.exe",
            "C:\Python310\python.exe",
            "C:\Python39\python.exe",
            "C:\Program Files\Python311\python.exe",
            "C:\Program Files\Python310\python.exe",
            "C:\Program Files\Python39\python.exe"
        )
        
        foreach ($path in $commonPaths) {
            if (Test-Path $path) {
                $pythonPath = $path
                Write-Host "Found Python at: $pythonPath" -ForegroundColor Green
                break
            }
        }
    }
}

if (-not $pythonPath) {
    Write-Host "ERROR: Python executable not found. Please install Python or ensure it's in your PATH." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# Start CaseStrainer with Vue.js frontend
Write-Host "
Starting CaseStrainer with Vue.js frontend on port 5000...
External access will be available at: https://wolf.law.uw.edu/casestrainer/
Local access will be available at: http://127.0.0.1:5000
" -ForegroundColor Cyan

# Set environment variables
$env:HOST = "0.0.0.0"
$env:PORT = "5000"
$env:USE_CHEROOT = "True"

# Get the full path to app_final_vue.py
$appPath = (Resolve-Path "app_final_vue.py").Path
Write-Host "Starting application from: $appPath" -ForegroundColor Green

# Start the application
try {
    & $pythonPath $appPath --host 0.0.0.0 --port 5000
} catch {
    Write-Host "ERROR: Failed to start CaseStrainer: $_" -ForegroundColor Red
}

Write-Host "CaseStrainer stopped." -ForegroundColor Yellow
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
