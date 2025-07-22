@echo off
setlocal enabledelayedexpansion

echo [DEBUG] Script started
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Script directory: %~dp0

:: Configuration
echo [DEBUG] Setting up configuration...
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "NGINX_DIR=%SCRIPT_DIR%nginx"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx.conf"
set "FLASK_APP=app_final_vue.py"
set "FLASK_ENV=production"
set "FLASK_RUN_PORT=5000"
set "FLASK_RUN_HOST=0.0.0.0"

echo [DEBUG] Configuration set:
echo [DEBUG]   SCRIPT_DIR = %SCRIPT_DIR%
echo [DEBUG]   LOG_DIR = %LOG_DIR%
echo [DEBUG]   NGINX_DIR = %NGINX_DIR%
echo [DEBUG]   NGINX_CONF = %NGINX_CONF%

:: Create log directory if it doesn't exist
echo [DEBUG] Checking log directory...
if not exist "%LOG_DIR%" (
    echo [DEBUG] Creating log directory: %LOG_DIR%
    mkdir "%LOG_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create log directory
        pause
        exit /b 1
    )
) else (
    echo [DEBUG] Log directory exists: %LOG_DIR%
)

:: Set log file with timestamp
echo [DEBUG] Setting up log file...
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value 2^>nul') do set "dt=%%a"
if not defined dt (
    echo [WARNING] Could not get timestamp from wmic, using alternative method
    set "dt=%date:~-4%%date:~3,2%%date:~0,2%%time:~0,2%%time:~3,2%%time:~6,2%"
    set "dt=%dt: =0%"
)
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\casestrainer_%TIMESTAMP%.log"

echo [DEBUG] Log file: %LOG_FILE%

:: Function to log messages
:log
set "MESSAGE=%~1"
echo [%TIME%] %MESSAGE%
(
echo [%TIME%] %MESSAGE%
) >> "%LOG_FILE%" 2>nul
if errorlevel 1 (
    echo [ERROR] Failed to write to log file: %LOG_FILE%
    echo [ERROR] Please check directory permissions
    pause
    exit /b 1
)
goto :eof

:: Test log function
echo [DEBUG] Testing log function...
call :log "Test log entry"

:: Check if running as administrator
echo [DEBUG] Checking for administrator privileges...
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] This script requires administrator privileges.
    echo [ERROR] Please right-click on the script and select 'Run as administrator'.
    pause
    exit /b 1
)

echo [DEBUG] Administrator privileges confirmed

:: If we get here, the script is working
call :log "Debug script ran successfully"
echo.
echo =======================================
echo DEBUG SCRIPT COMPLETED SUCCESSFULLY
echo =======================================
echo.
pause
