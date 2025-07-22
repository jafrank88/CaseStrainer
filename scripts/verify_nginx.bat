@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM Nginx Configuration Verification Script
REM ===================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo [%TIME%] ===================================
echo [%TIME%] Verifying Nginx Configuration
echo [%TIME%] ===================================

REM Check if Nginx is running
tasklist /FI "IMAGENAME eq nginx.exe" | find /I "nginx.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [%TIME%] Nginx is already running. Stopping it...
    taskkill /F /IM nginx.exe /T >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Check if nginx.conf exists
if not exist "nginx.conf" (
    echo [%TIME%] ERROR: nginx.conf not found in the current directory.
    exit /b 1
)

REM Verify Nginx configuration
echo [%TIME%] Verifying Nginx configuration...
if exist "nginx\nginx.exe" (
    "nginx\nginx.exe" -t -c "%CD%\nginx.conf"
) else (
    nginx -t -c "%CD%\nginx.conf"
)

if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ERROR: Nginx configuration test failed. Please check the configuration.
    exit /b 1
)

echo [%TIME%] Nginx configuration test is successful.
echo [%TIME%] ===================================
echo [%TIME%] To start Nginx, run:
echo [%TIME%]   nginx -c "%CD%\nginx.conf"

exit /b 0
