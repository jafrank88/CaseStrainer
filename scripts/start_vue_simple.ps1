# CaseStrainer PowerShell Startup Script
Write-Host "Starting CaseStrainer with simplified Vue.js frontend..." -ForegroundColor Green

# Set the current directory to the script directory
Set-Location $PSScriptRoot

# Stop any running Python processes using port 5000
$processes = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($processes) {
    Write-Host "Port 5000 is in use. Attempting to kill the process..." -ForegroundColor Yellow
    foreach ($process in $processes) {
        Stop-Process -Id $process -Force
        Write-Host "Killed process with PID $process" -ForegroundColor Yellow
    }
} else {
    Write-Host "Port 5000 is available." -ForegroundColor Green
}

# Find Python executable
$pythonPath = $null

# Check for Python in virtual environment
if (Test-Path ".venv\Scripts\python.exe") {
    $pythonPath = ".\.venv\Scripts\python.exe"
    Write-Host "Using Python from virtual environment: $pythonPath" -ForegroundColor Green
} else {
    # Check for Python in PATH
    try {
        $pythonPath = (Get-Command python -ErrorAction Stop).Source
        Write-Host "Using Python from PATH: $pythonPath" -ForegroundColor Green
    } catch {
        # Check for Python in common installation directories
        $commonPaths = @(
            "C:\Python311\python.exe",
            "C:\Python310\python.exe",
            "C:\Python39\python.exe",
            "C:\Python38\python.exe",
            "C:\Program Files\Python311\python.exe",
            "C:\Program Files\Python310\python.exe",
            "C:\Program Files\Python39\python.exe",
            "C:\Program Files\Python38\python.exe"
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
    Write-Host "Python not found. Please install Python and try again." -ForegroundColor Red
    exit 1
}

# Start the application
Write-Host "Starting CaseStrainer on port 5000 with host 0.0.0.0..." -ForegroundColor Green
try {
    & $pythonPath "app_final_vue_simple.py" --host=0.0.0.0 --port=5000
} catch {
    Write-Host "Error starting CaseStrainer: $_" -ForegroundColor Red
}

Write-Host "CaseStrainer stopped." -ForegroundColor Yellow
