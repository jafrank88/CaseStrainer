@echo off
setlocal enabledelayedexpansion

:: ===========================================
:: CaseStrainer Simple Launcher
:: ===========================================
:: Starts the Flask backend and Nginx with minimal configuration
:: ===========================================

:: Set console title
title CaseStrainer Simple Launcher

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%src"
set "FLASK_APP=app_final_vue.py"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "PORT=5000"
set "HOST=0.0.0.0"
set "NGINX_EXE=%SCRIPT_DIR%nginx-1.27.5\nginx.exe"
set "NGINX_CONF=%SCRIPT_DIR%nginx-simple.conf"
set "NGINX_DIR=%SCRIPT_DIR%nginx-1.27.5"

:: Log file setup
set "LOG_DIR=%SCRIPT_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\casestrainer_%date:/=%.log"
echo [%TIME%] Starting CaseStrainer >> "%LOG_FILE%"

:: Function to log messages
:log
echo [%DATE% %TIME%] %* >> "%LOG_FILE%"
echo [%TIME%] %*
goto :eof

:: Display banner
call :log ============================================
call :log    CaseStrainer Simple Launcher
call :log    Starting at: %DATE% %TIME%
call :log ============================================

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log [WARNING] Not running as administrator
    call :log [WARNING] Some features may require admin privileges
    timeout /t 2 >nul
)

:: Stop any existing services
call :log [INFO] Stopping any existing services...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

:: Verify Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :log [ERROR] Python is not in PATH
    pause
    exit /b 1
)

:: Verify Nginx exists
if not exist "%NGINX_EXE%" (
    call :log [ERROR] Nginx not found at: %NGINX_EXE%
    pause
    exit /b 1
)

:: Change to backend directory
cd /d "%BACKEND_DIR%"
if %ERRORLEVEL% NEQ 0 (
    call :log [ERROR] Failed to change to backend directory: %BACKEND_DIR%
    pause
    exit /b 1
)

:: Start Flask backend
call :log [INFO] Starting Flask backend...
start "CaseStrainer Backend" cmd /k "title CaseStrainer Backend && set FLASK_APP=%FLASK_APP% && set FLASK_ENV=%FLASK_ENV% && set FLASK_DEBUG=%FLASK_DEBUG% && python -m flask run --host=%HOST% --port=%PORT%"

:: Wait for backend to start
timeout /t 5 /nobreak >nul

:: Start Nginx
call :log [INFO] Starting Nginx...
cd /d "%SCRIPT_DIR%"
start "CaseStrainer Nginx" cmd /k "title CaseStrainer Nginx && "%NGINX_EXE%" -c "%NGINX_CONF%" -p "%NGINX_DIR%" && pause"

:: Verify services
call :log [INFO] Verifying services...

timeout /t 2 /nobreak >nul

tasklist | findstr /i "nginx.exe" >nul
if %ERRORLEVEL% EQU 0 (
    call :log [SUCCESS] Nginx is running
) else (
    call :log [ERROR] Nginx failed to start
)

tasklist | findstr /i "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    call :log [SUCCESS] Python/Flask is running
) else (
    call :log [ERROR] Python/Flask failed to start
)

:: Display completion message
call :log ============================================
call :log    CaseStrainer Services Started
call :log ============================================
call :log [INFO] Backend: http://%HOST%:%PORT%
call :log [INFO] Frontend: https://localhost/casestrainer/
call :log [INFO] Press Ctrl+C in this window to stop services
call :log ============================================

:: Wait for user to stop the services
pause

:: Clean up
call :log [INFO] Stopping services...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

call :log [INFO] All services stopped.
call :log ============================================

pause
