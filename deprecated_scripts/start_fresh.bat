@echo off
setlocal enabledelayedexpansion

:: Simple startup script for CaseStrainer
:: 1. Start the Flask backend
:: 2. Start Nginx with the simple configuration

echo [%TIME%] Starting CaseStrainer with fresh configuration...

:: Set paths
set "FLASK_APP=src\app_final_vue.py"
set "NGINX_PATH=%~dp0nginx-1.27.5\nginx.exe"
set "NGINX_CONFIG=%~dp0nginx-simple.conf"
set "NGINX_DIR=%~dp0nginx-1.27.5"

:: Check if Nginx exists
if not exist "%NGINX_PATH%" (
    echo [ERROR] Nginx not found at: %NGINX_PATH%
    pause
    exit /b 1
)

:: Check if Nginx config exists
if not exist "%NGINX_CONFIG%" (
    echo [ERROR] Nginx config not found at: %NGINX_CONFIG%
    pause
    exit /b 1
)

:: Kill any existing Nginx and Python processes
echo [%TIME%] Stopping any existing processes...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

:: Start Flask backend in a new window
echo [%TIME%] Starting Flask backend...
start "Flask Backend" cmd /k "set FLASK_APP=%FLASK_APP% && set FLASK_ENV=production && python -m flask run --host=0.0.0.0 --port=5000"

:: Wait a moment for Flask to start
timeout /t 5 /nobreak >nul

:: Start Nginx in a new window
echo [%TIME%] Starting Nginx with simple configuration...
start "Nginx" cmd /k ""%NGINX_PATH%" -c "%NGINX_CONFIG%" -p "%NGINX_DIR%" && pause"

echo [%TIME%] CaseStrainer should now be running at: https://localhost/casestrainer/
echo [%TIME%] Press any key to stop all services and exit...
pause >nul

:: Clean up
echo [%TIME%] Stopping services...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo [%TIME%] All services stopped.
