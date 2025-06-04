@echo off
echo ===================================================
echo CaseStrainer Vue.js Startup Script (Simple Version)
echo ===================================================
echo.

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
echo Starting CaseStrainer with Vue.js frontend on port 5000...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000
echo.

:: Use the correct host parameter (0.0.0.0 to listen on all interfaces)
set "HOST=0.0.0.0"
set "PORT=5000"

:: Use the full path to app_final_vue.py to ensure it works correctly
cd /d "%~dp0"
python app_final_vue.py --host 0.0.0.0 --port 5000

echo.
echo CaseStrainer stopped.
echo Press any key to exit...
pause > nul
