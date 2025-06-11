@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Control Panel
:: ===================================================
:: This script can be run from any directory
:: ===================================================

:: Set console window title
title CaseStrainer Control Panel

:: Set console window size
mode con:cols=100 lines=30

:: Get the directory where this script is located
set "SCRIPT_PATH=%~f0"
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"  :: Remove trailing backslash

:: Display script location
call :log "Script path: %SCRIPT_PATH%"
call :log "Script directory: %SCRIPT_DIR%"

:: Initialize error level
set "ERROR_LEVEL=0"

:: Ensure we have required directories
if not exist "%SCRIPT_DIR%" (
    call :log "ERROR: Could not determine script directory"
    pause
    exit /b 1
)

:: Change to script directory for consistent operation
cd /d "%SCRIPT_DIR%"
call :log "Working directory: %CD%"

:: Check for command line arguments
if not "%~1"=="" (
    if "%~1"=="1" (
        call :start_services
    ) else if "%~1"=="2" (
        call :stop_services
    )
    exit /b 0
)

:: ===================================================
:: CaseStrainer Launch Application
:: ===================================================
:: Main control panel for CaseStrainer services
:: ===================================================

:: Configuration
set "LOG_DIR=%SCRIPT_DIR%\logs"
set "NGINX_DIR=%SCRIPT_DIR%\nginx-1.27.5"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx.conf"
set "FLASK_APP=app_final_vue.py"
set "FLASK_PORT=5000"
set "APP_URL=http://localhost/casestrainer/"

:: Log configuration
call :log "Configuration:"
call :log "  Log directory: %LOG_DIR%"
call :log "  Nginx directory: %NGINX_DIR%"
call :log "  Nginx executable: %NGINX_EXE%"
call :log "  Nginx config: %NGINX_CONF%"
call :log "  Flask app: %FLASK_APP%"
call :log "  Flask port: %FLASK_PORT%"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

:: Verify Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not in your system PATH. Please install Python and ensure it's in your PATH.
    exit /b 1
)

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value 2^>nul') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\launch_app_%TIMESTAMP%.log"

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
set "FLASK_APP_PATH=%SCRIPT_DIR%\src\app_final_vue.py"
call :log "Starting Flask backend on port %FLASK_PORT%..."
call :log "Looking for Flask app at: %FLASK_APP_PATH%"

if exist "%FLASK_APP_PATH%" (
    call :log "Found Flask app, starting Waitress server..."
    
    set "PYTHON_CMD=python -c "from src.app_final_vue import create_app; app = create_app(); import waitress; waitress.serve(app, host='0.0.0.0', port=%FLASK_PORT%)""
    call :log "Command: %PYTHON_CMD%"
    
    start "CaseStrainer Backend" cmd /k "cd /d "%SCRIPT_DIR%" && set PYTHONPATH=%SCRIPT_DIR% && %PYTHON_CMD%"
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: Failed to start Flask backend (Error: !ERRORLEVEL!)"
        set "ERROR_LEVEL=1"
    ) else (
        call :log "Flask backend started successfully on port %FLASK_PORT%"
    )
) else (
    call :log "ERROR: Could not find Flask app at: %FLASK_APP_PATH%"
    call :log "Current directory: %CD%"
    call :log "Contents of src directory:"
    dir "%SCRIPT_DIR%\src\" 2>nul || echo Directory not found: %SCRIPT_DIR%\src
    set "ERROR_LEVEL=1"
)

:: Start Nginx
call :log "Starting Nginx..."
if exist "%NGINX_EXE%" (
    call :log "Nginx executable found at: %NGINX_EXE%"
    
    :: Verify Nginx configuration
    call :log "Verifying Nginx configuration..."
    "%NGINX_EXE%" -t -c "%NGINX_CONF%" -p "%NGINX_DIR%"
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: Nginx configuration test failed"
        set "ERROR_LEVEL=1"
        goto :skip_nginx_start
    )
    
    :: Stop any running Nginx instances first
    call :log "Stopping any running Nginx instances..."
    tasklist | find /i "nginx.exe" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        taskkill /F /IM nginx.exe >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
    
    :: Start Nginx
    call :log "Starting Nginx with config: %NGINX_CONF%"
    start "Nginx" /D"%NGINX_DIR%" "%NGINX_EXE%" -c "%NGINX_CONF%" -p "%NGINX_DIR%"
    
    :: Check if Nginx started successfully
    timeout /t 2 /nobreak >nul
    tasklist | find /i "nginx.exe" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        call :log "Nginx started successfully"
    ) else (
        call :log "ERROR: Failed to start Nginx"
        call :log "Checking Nginx error log..."
        if exist "%NGINX_DIR%\logs\error.log" (
            type "%NGINX_DIR%\logs\error.log"
        )
        set "ERROR_LEVEL=1"
    )
) else (
    call :log "ERROR: Nginx not found at: %NGINX_EXE%"
    call :log "Current directory: %CD%"
    call :log "Contents of nginx directory:"
    dir "%NGINX_DIR%" 2>nul || echo Directory not found: %NGINX_DIR%
    set "ERROR_LEVEL=1"
)
:skip_nginx_start

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
set "NGINX_RUNNING=0"
set "FLASK_RUNNING=0"

:: Check Nginx
call :is_running "nginx.exe"
if %ERRORLEVEL% EQU 0 (
    set "NGINX_RUNNING=1"
) 

:: Check Flask
call :port_in_use "%FLASK_PORT%"
if %ERRORLEVEL% EQU 0 (
    set "FLASK_RUNNING=1"
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

:: Function to open logs
:open_logs
if exist "%LOG_FILE%" (
    notepad "%LOG_FILE%"
) else (
    echo No log file found at: %LOG_FILE%
    timeout /t 2 /nobreak >nul
)
goto :menu

:: Function to open in browser
:open_browser
start "" "%APP_URL%"
goto :menu

:: Function to show help
:show_help
cls
echo ===================================================
echo   CaseStrainer - Help
   echo ===================================================
echo.
echo 1. Start All Services:
   echo    - Launches Flask backend with Waitress
   echo    - Starts Nginx web server
   echo    - Configures reverse proxy

echo.
echo 2. Stop All Services:
   echo    - Stops Nginx gracefully
   echo    - Terminates Python processes

echo.
echo 3. Restart All Services:
   echo    - Stops and then starts all services

echo.
echo 4. Check Status:
   echo    - Shows running services
   echo    - Displays port information

echo.
echo 5. View Logs:
   echo    - Opens the current log file

echo.
echo 6. Open in Browser:
   echo    - Launches the application in your default browser

echo.
echo 7. Exit:
   echo    - Closes this menu

echo.
pause
goto :menu

:: Main menu
:menu
cls
echo ===================================================
echo   CaseStrainer Control Panel
echo ===================================================
echo   Directory: %CD%
echo   Log: %LOG_FILE%
echo ===================================================
echo.
echo   1. Start All Services
echo   2. Stop All Services
echo   3. Check Status
echo   4. View Logs
echo   5. Open in Browser
echo   6. Help
echo   7. Exit
echo.
set "choice="
set /p choice=Enter your choice (1-7): 

if "%choice%"=="" (
    echo Please enter a valid choice.
    timeout /t 2 /nobreak >nul
    goto :menu
) else if "%choice%"=="1" (
    call :start_services
    goto :menu
) else if "%choice%"=="2" (
    call :stop_services
    goto :menu
) else if "%choice%"=="3" (
    call :show_status
    echo.
    pause
    goto :menu
) else if "%choice%"=="4" (
    call :open_logs
    goto :menu
) else if "%choice%"=="5" (
    call :open_browser
    goto :menu
) else if "%choice%"=="6" (
    call :show_help
    pause
    goto :menu
) else if "%choice%"=="7" (
    exit /b 0
) else (
    echo Invalid choice: %choice%. Please enter a number between 1 and 7.
    timeout /t 2 /nobreak >nul
    goto :menu
)

goto :menu

:error_handling
echo.
echo An error occurred:
   echo %ERROR_MESSAGE%
echo.
echo Press any key to return to the main menu...
pause >nul
goto :menu
