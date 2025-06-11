@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Clean Startup Script
REM ===================================================

:init
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [%TIME%] ===================================
echo [%TIME%] Starting CaseStrainer Deployment
echo [%TIME%] ===================================

REM Check for required commands
where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ERROR: npm is not in PATH. Please install Node.js and npm.
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [%TIME%] ERROR: Python is not in PATH. Please install Python 3.7 or higher.
        exit /b 1
    )
)

REM Stop any running processes
echo [%TIME%] Stopping any running instances...
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im python3.exe /t >nul 2>&1
taskkill /f /im nginx.exe /t >nul 2>&1

REM Wait a moment for processes to stop
echo [%TIME%] Waiting for processes to terminate...
timeout /t 3 /nobreak >nul

REM Set environment variables
echo [%TIME%] Setting up environment...
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=production
set HOST=0.0.0.0
set PORT=5000
set THREADS=4

REM Add the project root to PYTHONPATH
set PYTHONPATH=%CD%;%PYTHONPATH%

REM Create required directories
echo [%TIME%] Creating required directories...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Install Python dependencies
echo [%TIME%] Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] WARNING: Failed to install some Python dependencies. Trying to continue...
    echo [%TIME%] This might be expected if some packages are local or not available on PyPI
)

REM Install the local package in development mode
echo [%TIME%] Installing local package in development mode...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] WARNING: Failed to install local package in development mode.
    echo [%TIME%] Trying to continue anyway...
)

REM Install and build Vue.js frontend
echo [%TIME%] Installing Node.js dependencies...
cd casestrainer-vue-new
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ERROR: Failed to install Node.js dependencies
    exit /b 1
)

echo [%TIME%] Building Vue.js frontend...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ERROR: Failed to build Vue.js frontend
    exit /b 1
)
cd ..

REM Start the application
echo [%TIME%] ===================================
REM Start Nginx
echo [%TIME%] Starting Nginx...
if exist "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" (
    "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" -c "%SCRIPT_DIR%nginx.conf"
) else (
    start "" /B nginx.exe -c "%SCRIPT_DIR%nginx.conf"
)
echo [%TIME%] ===================================

echo [%TIME%] Application will be available at: http://%HOST%:%PORT%
echo [%TIME%] Press Ctrl+C to stop the server

REM Start the application in the current window
python src/app_final_vue.py --host=%HOST% --port=%PORT% --debug=1

if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ERROR: Failed to start CaseStrainer
    exit /b 1
)

goto :eof

REM Verify the server started
timeout /t 5 /nobreak >nul
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [%TIME%] CaseStrainer is running in the background.
    echo [%TIME%] Access the application at: http://localhost:%PORT%/casestrainer
    echo [%TIME%] To stop the server, use: taskkill /f /im python.exe
) else (
    echo [%TIME%] ERROR: Failed to start CaseStrainer
    echo [%TIME%] Check the logs in the logs/ directory for more information
    exit /b 1
)

timeout /t 2 /nobreak >nul
