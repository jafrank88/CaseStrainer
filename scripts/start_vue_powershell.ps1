# CaseStrainer Vue.js PowerShell Startup Script
Write-Host "===================================================
CaseStrainer Vue.js Startup Script
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

# Find Python executable in the virtual environment
$pythonPath = Join-Path -Path $PSScriptRoot -ChildPath ".venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "Found Python executable: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "Python executable not found at: $pythonPath" -ForegroundColor Red
    Write-Host "Please make sure the virtual environment is properly set up." -ForegroundColor Red
    exit
}

# Find app_final_vue.py
$appPath = Join-Path -Path $PSScriptRoot -ChildPath "app_final_vue.py"
if (Test-Path $appPath) {
    Write-Host "Found app_final_vue.py: $appPath" -ForegroundColor Green
} else {
    Write-Host "app_final_vue.py not found at: $appPath" -ForegroundColor Red
    exit
}

# Start the application
Write-Host "Starting CaseStrainer Vue.js frontend on port 5000..." -ForegroundColor Cyan
Write-Host "External access will be available at: https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Cyan
Write-Host "Local access will be available at: http://127.0.0.1:5000" -ForegroundColor Cyan

# Use Start-Process to run the Python executable with the app_final_vue.py script
Start-Process -FilePath $pythonPath -ArgumentList "$appPath --host=0.0.0.0 --port=5000" -NoNewWindow -Wait
