@echo off
echo ===================================================
echo CaseStrainer Complete Deployment Script
echo ===================================================
echo.

REM Set environment variables
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set FLASK_ENV=production
set FLASK_DEBUG=0
set USE_WAITRESS=True

REM Create required directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Step 1: Stop any existing processes
echo Step 1: Stopping existing processes...
echo.

REM Stop Windows Nginx if running
echo Checking for Windows Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
    echo Windows Nginx stopped.
) else (
    echo Windows Nginx is not running.
)

REM Check if port 5000 is already in use
echo Checking if port 5000 is in use...
netstat -ano | findstr :5000 | findstr LISTENING
if "%ERRORLEVEL%"=="0" (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
    timeout /t 2 /nobreak >nul
) else (
    echo Port 5000 is available.
)

REM Stop any Python processes
echo Checking for Python processes...
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Python processes...
    taskkill /F /IM python.exe
    echo Python processes stopped.
) else (
    echo No Python processes running.
)

REM Step 2: Start the Flask application
echo.
echo Step 2: Starting Flask application...
echo.

REM Start the Flask application in a new window
echo Starting Flask application on port 5000...
start "CaseStrainer Flask" cmd /c "python src\app_final_vue.py --host=%HOST% --port=%PORT% --use-waitress --env=production"

REM Wait for Flask to start
echo Waiting for Flask application to start...
timeout /t 5 /nobreak >nul

REM Step 3: Start Nginx
echo.
echo Step 3: Starting Nginx...
echo.

REM Start Windows Nginx
echo Starting Windows Nginx...
cd "%~dp0"
start "" "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe"

echo.
echo ===================================================
echo CaseStrainer deployment complete!
echo ===================================================
echo.
echo The application is now accessible at:
echo - External: https://wolf.law.uw.edu/casestrainer/
echo - Local: http://localhost/casestrainer/
echo.
echo Press any key to exit this script (the application will continue running)...
pause >nul
