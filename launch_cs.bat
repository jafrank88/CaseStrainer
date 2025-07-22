@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Launch Control
:: ===================================================
:: This script provides a menu to start/stop CaseStrainer services
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "NGINX_DIR=%SCRIPT_DIR%nginx"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx.conf"
set "FLASK_APP=app_final_vue.py"
set "FLASK_PORT=5000"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value 2^>nul') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\launch_cs_%TIMESTAMP%.log"

:: Function to log messages
:log
set "MESSAGE=%~1"
echo [%TIME%] %MESSAGE%
(
echo [%TIME%] %MESSAGE%
) >> "%LOG_FILE%" 2>nul
goto :eof

:: Function to check if a process is running
:is_running
set "PROCESS=%~1"
tasklist | find /i "%PROCESS%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    exit /b 0
) else (
    exit /b 1
)

:: Function to check if a port is in use
:port_in_use
set "PORT=%~1"
netstat -ano | find ":%PORT%" | find "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    exit /b 0
) else (
    exit /b 1
)

:: Function to start services
:start_services
call :log "Starting CaseStrainer services..."

:: Start Flask backend
call :log "Starting Flask backend..."
start "CaseStrainer Backend" cmd /k "cd /d "%SCRIPT_DIR%" && python -m waitress --port=%FLASK_PORT% %FLASK_APP%"

:: Start Nginx
call :log "Starting Nginx..."
if exist "%NGINX_EXE%" (
    "%NGINX_EXE" -c "%NGINX_CONF%"
    if %ERRORLEVEL% EQU 0 (
        call :log "Nginx started successfully"
    ) else (
        call :log "ERROR: Failed to start Nginx"
    )
) else (
    call :log "ERROR: Nginx not found at %NGINX_EXE%"
)

timeout /t 2 /nobreak >nul
call :check_status

echo.
echo Press any key to return to the main menu...
pause >nul
goto :menu

:: Function to stop services
:stop_services
call :log "Stopping CaseStrainer services..."

:: Stop Nginx
call :log "Stopping Nginx..."
if exist "%NGINX_EXE%" (
    "%NGINX_EXE" -s stop
    call :log "Nginx stop command sent"
)

:: Stop Python processes
call :log "Stopping Python processes..."
taskkill /F /IM python.exe /T >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :log "Python processes stopped"
) else (
    call :log "No Python processes found or failed to stop"
)

timeout /t 2 /nobreak >nul
call :check_status

echo.
echo Press any key to return to the main menu...
pause >nul
goto :menu

:: Function to check service status
:check_status
call :log "Checking service status..."

set "NGINX_RUNNING=0"
set "FLASK_RUNNING=0"

:: Check Nginx
call :is_running "nginx.exe"
if %ERRORLEVEL% EQU 0 (
    set "NGINX_RUNNING=1"
    call :log "Nginx is running"
) else (
    call :log "Nginx is not running"
)

:: Check Flask
call :port_in_use "%FLASK_PORT%"
if %ERRORLEVEL% EQU 0 (
    set "FLASK_RUNNING=1"
    call :log "Flask is running on port %FLASK_PORT%"
) else (
    call :log "Flask is not running on port %FLASK_PORT%"
)

goto :eof

:: Function to show service status
:show_status
cls
echo ===================================================
echo   CaseStrainer Service Status
   echo ===================================================
echo.

call :check_status >nul

if %NGINX_RUNNING% EQU 1 (
    echo [RUNNING] Nginx web server
) else (
    echo [STOPPED] Nginx web server
)

if %FLASK_RUNNING% EQU 1 (
    echo [RUNNING] Flask backend (port %FLASK_PORT%)
) else (
    echo [STOPPED] Flask backend (port %FLASK_PORT%)
)

echo.
echo Log file: %LOG_FILE%
echo.
echo ===================================================
goto :eof

:: Main menu
:menu
call :show_status

echo.
echo ===================================================
echo   CaseStrainer Launch Control
   echo ===================================================
echo.
echo   1. Start All Services
echo   2. Stop All Services
echo   3. Restart All Services
echo   4. Check Status
echo   5. View Logs
   echo   6. Open in Browser
   echo   7. Exit

echo.
set /p "CHOICE=Enter your choice (1-7): "

echo.
if "%CHOICE%"=="1" (
    call :start_services
) else if "%CHOICE%"=="2" (
    call :stop_services
) else if "%CHOICE%"=="3" (
    call :stop_services
    timeout /t 2 /nobreak >nul
    call :start_services
) else if "%CHOICE%"=="4" (
    call :show_status
    echo.
    echo Press any key to return to the main menu...
    pause >nul
    goto :menu
) else if "%CHOICE%"=="5" (
    if exist "%LOG_FILE%" (
        notepad "%LOG_FILE%"
    ) else (
        echo No log file found at: %LOG_FILE%
        timeout /t 2 /nobreak >nul
    )
    goto :menu
) else if "%CHOICE%"=="6" (
    start "" "http://localhost/casestrainer/"
    goto :menu
) else if "%CHOICE%"=="7" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    timeout /t 1 /nobreak >nul
    goto :menu
)
