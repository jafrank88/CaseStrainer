@echo off
echo ===================================================
echo CaseStrainer Vue.js Startup Script
echo ===================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script is not running as Administrator.
    echo Some features like starting services may not work properly.
    echo.
    echo Continuing automatically...
    timeout /t 2 /nobreak >nul
)

REM Check local IP address
echo Checking local IP address...
set "LOCAL_IP=127.0.0.1"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address" ^| findstr /c:"10.158"') do (
    set "LOCAL_IP=%%a"
    set "LOCAL_IP=!LOCAL_IP:~1!"
    echo Found local IP: !LOCAL_IP!
)

REM Stop any Windows Nginx instances (should be stopped to avoid conflicts)
echo Stopping any Windows Nginx instances...
taskkill /f /im nginx.exe >nul 2>&1

REM Check Docker status
echo Checking Docker status...
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Docker does not appear to be running.
    echo The Docker Nginx container may not be accessible.
    echo.
    echo Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start (30 seconds)...
    timeout /t 30 /nobreak >nul
)

REM Check Docker Nginx container
echo Checking Docker Nginx container...
docker ps | findstr nginx >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Docker Nginx container not found.
    echo External access through https://wolf.law.uw.edu/casestrainer/ may not work.
    echo.
    echo Attempting to start Docker Nginx container automatically...
    docker start docker-nginx-1 >nul 2>&1
    timeout /t 5 /nobreak >nul
    
    docker ps | findstr nginx >nul 2>&1
    if %errorLevel% neq 0 (
        echo Failed to start Docker Nginx container.
        echo You may need to start it manually using: docker start docker-nginx-1
    ) else (
        echo Docker Nginx container started successfully.
    )
)

REM Check if port 5000 is available
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

REM Kill any existing Python processes
echo Stopping any existing Python processes...
taskkill /f /im python.exe >nul 2>&1

REM Start CaseStrainer with Vue.js frontend
echo.
echo Starting CaseStrainer with Vue.js frontend on port 5000 (required for Docker Nginx proxy)...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000
echo.

REM Use the correct host parameter (0.0.0.0 to listen on all interfaces)
REM Setting environment variables to ensure app_vue.py uses the correct settings
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_CHEROOT=True"

REM Start the application
python "%~dp0\app_vue.py" --host 0.0.0.0 --port 5000

echo.
if %errorLevel% neq 0 (
    echo ERROR: Failed to start CaseStrainer.
    echo Check the error messages above for more information.
) else (
    echo CaseStrainer stopped.
)

pause
