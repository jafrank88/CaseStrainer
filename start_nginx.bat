@echo off
setlocal enabledelayedexpansion

:: Set paths
set "NGINX_DIR=%~dp0nginx-1.27.5"
set "CONFIG_FILE=%~dp0nginx-http.conf"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click on the script and select 'Run as administrator'.
    pause
    exit /b 1
)

echo Stopping any running Nginx instances...
taskkill /F /IM nginx.exe >nul 2>&1

echo Starting Nginx...
"%NGINX_EXE%" -c "%CONFIG_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo Nginx started successfully.
    echo Access the application at: http://localhost/casestrainer/
) else (
    echo Failed to start Nginx. Check the error log:
    echo %NGINX_DIR%\logs\error.log
)

echo.
pause
