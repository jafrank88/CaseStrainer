# CaseStrainer Vue.js PowerShell Startup Script
Write-Host "===================================================
CaseStrainer Vue.js Startup Script
===================================================" -ForegroundColor Cyan

# Set the current directory to the script directory
Set-Location $PSScriptRoot

# Function to check and kill processes on port 5000
function Stop-Port5000 {
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
}

# Function to find Python executable
function Find-PythonExecutable {
    Write-Host "Looking for Python executable..." -ForegroundColor Green
    
    # Check common locations
    $pythonExes = @(
        ".venv\Scripts\python.exe",
        "C:\Python313\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe",
        "C:\Program Files\Python39\python.exe",
        "C:\Users\jafrank\AppData\Local\Programs\Python\Python313\python.exe",
        "C:\Users\jafrank\AppData\Local\Programs\Python\Python311\python.exe",
        "C:\Users\jafrank\AppData\Local\Programs\Python\Python310\python.exe",
        "C:\Users\jafrank\AppData\Local\Programs\Python\Python39\python.exe"
    )

    foreach ($exe in $pythonExes) {
        if (Test-Path $exe) {
            Write-Host "Found Python executable: $exe" -ForegroundColor Green
            return $exe
        }
    }

    # Try to find Python in PATH
    try {
        $pythonExe = (Get-Command python -ErrorAction Stop).Source
        Write-Host "Found Python in PATH: $pythonExe" -ForegroundColor Green
        return $pythonExe
    } catch {
        Write-Host "Python not found in PATH or in common locations." -ForegroundColor Red
        Write-Host "Please install Python and try again." -ForegroundColor Red
        return $null
    }
}

# Function to check for Windows Nginx
function Stop-WindowsNginx {
    Write-Host "Checking for Windows Nginx..." -ForegroundColor Green
    $nginxProcess = Get-Process -Name nginx -ErrorAction SilentlyContinue
    if ($nginxProcess) {
        Write-Host "Stopping Windows Nginx..." -ForegroundColor Yellow
        Stop-Process -Name nginx -Force
        Write-Host "Windows Nginx stopped." -ForegroundColor Green
    } else {
        Write-Host "Windows Nginx is not running." -ForegroundColor Green
    }
}

# Main execution
try {
    # Stop any processes on port 5000
    Stop-Port5000

    # Stop Windows Nginx if running
    Stop-WindowsNginx

    # Find Python executable
    $pythonExe = Find-PythonExecutable
    if (-not $pythonExe) {
        throw "Python executable not found"
    }

    # Set environment variables
    $env:HOST = "0.0.0.0"
    $env:PORT = "5000"
    $env:USE_WAITRESS = "True"
    $env:FLASK_ENV = "production"
    $env:APPLICATION_ROOT = "/casestrainer"

    # Start the application
    Write-Host "
Starting CaseStrainer with Vue.js frontend on port 5000...
External access will be available at: https://wolf.law.uw.edu/casestrainer/
Local access will be available at: http://0.0.0.0:5000
" -ForegroundColor Cyan

    # Get the full path to run_production.py
    $appPath = Join-Path -Path $PSScriptRoot -ChildPath "..\src\run_production.py"
    if (-not (Test-Path $appPath)) {
        throw "run_production.py not found at: $appPath"
    }

    Write-Host "Starting application from: $appPath" -ForegroundColor Green
    & $pythonExe $appPath --host 0.0.0.0 --port 5000 --env production --threads 10 --url-prefix /casestrainer

} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "CaseStrainer stopped." -ForegroundColor Yellow
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 