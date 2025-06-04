@echo off
setlocal enabledelayedexpansion
echo ===================================================
echo CaseStrainer Vue.js Startup Script for Production
echo ===================================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script is not running as Administrator.
    echo Some features like starting services may not work properly.
    echo.
    echo Continuing automatically...
    timeout /t 2 /nobreak >nul
)

:: Check local IP address
echo Checking local IP address...
set "LOCAL_IP=127.0.0.1"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address" ^| findstr /c:"10.158"') do (
    set "LOCAL_IP=%%a"
    set "LOCAL_IP=!LOCAL_IP:~1!"
    echo Found local IP: !LOCAL_IP!
)

:: Stop any Windows Nginx instances (should be stopped to avoid conflicts)
echo Stopping any Windows Nginx instances...
taskkill /f /im nginx.exe >nul 2>&1

:: Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 5000 is already in use.
    echo Stopping any processes using port 5000...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
)

:: Kill any existing Python processes
echo Stopping any existing Python processes...
taskkill /f /im python.exe >nul 2>&1

:: Start CaseStrainer with Vue.js frontend
echo.
echo Starting CaseStrainer with Vue.js frontend on port 5000 (required for Docker Nginx proxy)...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000
echo.

:: Use the correct host parameter (0.0.0.0 to listen on all interfaces)
:: Setting environment variables to ensure the app uses the correct settings
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_CHEROOT=True"

:: Use run_vue_production.py to build the Vue.js frontend and start the application
python "c:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\run_vue_production.py" --host 0.0.0.0 --port 5000

echo.
if %errorLevel% neq 0 (
    echo ERROR: CaseStrainer failed to start properly.
    echo Please check the error messages above.
) else (
    echo CaseStrainer stopped successfully.
)

echo.
echo Press any key to exit...
pause > nul
