@echo off
echo ===================================================
echo CaseStrainer Startup Script (Simplified Version)
echo ===================================================
echo.

echo Stopping any Windows Nginx instances...
taskkill /f /im nginx.exe >nul 2>&1

echo Stopping any existing Python processes...
taskkill /f /im python.exe >nul 2>&1

echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo Port 5000 is already in use. Attempting to free it...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo Starting CaseStrainer on port 5000...
echo External access: https://wolf.law.uw.edu/casestrainer/
echo Local access: http://127.0.0.1:5000
echo.

python run_production.py --host 0.0.0.0 --port 5000

echo.
echo CaseStrainer has been stopped.
echo.
pause
