@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Startup Script (No Pause Version)
REM ===================================================

REM Set working directory to script location
cd /d "%~dp0"

REM Kill all Python processes to prevent conflicts
echo Stopping all Python processes...
taskkill /f /im python.exe >nul 2>&1

REM Create required directories if they don't exist
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"
if not exist "casestrainer_sessions" mkdir "casestrainer_sessions"

REM Stop any running instances
echo Stopping any running instances...
taskkill /f /im python.exe /fi "WINDOWTITLE eq CaseStrainer Backend" >nul 2>&1
taskkill /f /im nginx.exe >nul 2>&1

REM Start Nginx
echo Starting Nginx...
start "" /B "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe" -p "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5" -c "conf\nginx.conf"

REM Set environment variables
echo Starting Flask application...
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=production
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_CHEROOT=True

REM Start Flask application
start "CaseStrainer Backend" /B cmd /c "python -m flask run --host=%HOST% --port=%PORT% --with-threads"

echo.
echo ===================================================
echo CaseStrainer is now running in the background.
echo Access the application at: http://localhost:5000
echo ===================================================
echo.

exit /b 0

echo.
echo ===================================================
echo CaseStrainer is now running in the background.
echo ===================================================
echo.
echo Access the application at: https://wolf.law.uw.edu/casestrainer/

echo.
echo ===================================================
echo Checking if application is running on port 5000...
echo ===================================================
netstat -ano | findstr :5000

echo.
echo If no output is shown above, the application is not running on port 5000.
echo Check the logs in the 'logs' directory for any errors.
echo Local development: http://127.0.0.1:5000
echo.
echo To stop the application, run: taskkill /f /im nginx.exe /im python.exe
echo ===================================================
