# CaseStrainer Vue.js PowerShell Startup Script
Write-Host "===================================================
CaseStrainer Vue.js Startup Script (Direct)
===================================================" -ForegroundColor Cyan

# Set the current directory to the script directory
Set-Location $PSScriptRoot

# Check if port 5000 is available
Write-Host "Checking if port 5000 is available..." -ForegroundColor Green
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 5000 is in use. Attempting to kill the process..." -ForegroundColor Yellow
    foreach ($process in $portInUse) {
        $processId = $process.OwningProcess
        Write-Host "Killing process with PID: $processId" -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "Port 5000 is available." -ForegroundColor Green
}

# Try to find Python executable directly
$pythonExes = @(
    "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\.venv\Scripts\python.exe",
    "C:\Python313\python.exe",
    "C:\Python\python.exe",
    "C:\Users\jafrank\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Users\jafrank\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\jafrank\AppData\Local\Programs\Python\Python310\python.exe",
    "C:\Users\jafrank\AppData\Local\Programs\Python\Python39\python.exe"
)

$pythonExe = $null
foreach ($exe in $pythonExes) {
    if (Test-Path $exe) {
        $pythonExe = $exe
        Write-Host "Found Python executable: $pythonExe" -ForegroundColor Green
        break
    }
}

if (-not $pythonExe) {
    # Try to find Python in PATH
    try {
        $pythonExe = (Get-Command python -ErrorAction Stop).Source
        Write-Host "Found Python in PATH: $pythonExe" -ForegroundColor Green
    } catch {
        Write-Host "Python not found in PATH or in common locations." -ForegroundColor Red
        Write-Host "Please install Python and try again." -ForegroundColor Red
        exit
    }
}

# Check if app_final_vue.py exists
$appPath = Join-Path -Path $PSScriptRoot -ChildPath "app_final_vue.py"
if (Test-Path $appPath) {
    Write-Host "Found app_final_vue.py: $appPath" -ForegroundColor Green
} else {
    # Try app_final_vue_simple.py as fallback
    $appPath = Join-Path -Path $PSScriptRoot -ChildPath "app_final_vue_simple.py"
    if (Test-Path $appPath) {
        Write-Host "Found app_final_vue_simple.py: $appPath" -ForegroundColor Green
    } else {
        Write-Host "Neither app_final_vue.py nor app_final_vue_simple.py found." -ForegroundColor Red
        exit
    }
}

# Start the application
Write-Host "Starting CaseStrainer Vue.js frontend on port 5000..." -ForegroundColor Cyan
Write-Host "External access will be available at: https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Cyan
Write-Host "Local access will be available at: http://127.0.0.1:5000" -ForegroundColor Cyan

# Set environment variables
$env:HOST = "0.0.0.0"
$env:PORT = "5000"
$env:USE_CHEROOT = "True"

# Run the Python application
& $pythonExe $appPath --host=0.0.0.0 --port=5000
