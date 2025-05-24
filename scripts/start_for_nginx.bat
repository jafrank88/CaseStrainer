@echo off
REM ===================================================
REM DEPRECATED SCRIPT
REM ===================================================
REM This script is no longer supported.
REM Please use start_casestrainer.bat for all startup and restart operations.
REM ===================================================
echo ===================================================
echo Starting CaseStrainer for Nginx proxy access...
echo ===================================================
echo.

REM Check if Windows Nginx is running and stop it
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
) else (
    echo Port 5000 is available.
)

REM Verify Docker is running (required for Docker Nginx container)
echo Checking if Docker is running...
docker ps >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo Docker is running.
) else (
    echo WARNING: Docker may not be running. The Docker Nginx container might not be accessible.
    echo This could prevent external access to CaseStrainer through https://wolf.law.uw.edu/casestrainer/
    echo.
    echo Press any key to continue anyway or CTRL+C to abort...
    pause >nul
)

REM Start the Flask application with Vue.js integration on port 5000 with host 0.0.0.0
echo Starting Flask application with Vue.js integration on port 5000 with host 0.0.0.0...
cd "%~dp0"

REM Set environment variables
SET USE_WAITRESS=True
SET FLASK_ENV=production
SET FLASK_DEBUG=0

REM Navigate to the project root directory
cd "%~dp0.."

REM Try different Python installations in order of preference
IF EXIST ".venv\Scripts\python.exe" (
    echo Using Python from virtual environment
    call .venv\Scripts\activate.bat
    python src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
) ELSE IF EXIST "D:\Python\python.exe" (
    echo Using Python from D:\Python
    "D:\Python\python.exe" src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-cheroot
) ELSE IF EXIST "C:\Python313\python.exe" (
    echo Using Python from C:\Python313
    "C:\Python313\python.exe" src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-cheroot
) ELSE (
    echo Python not found, trying system Python
    python src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
)

echo.
echo CaseStrainer stopped.
echo.
echo If you need to restart the application, run this script again.
echo External access URL: https://wolf.law.uw.edu/casestrainer/
echo.
