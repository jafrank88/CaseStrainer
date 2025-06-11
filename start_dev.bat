@echo off
setlocal enabledelayedexpansion

@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Development Environment
:: ===================================================
:: Usage:
::   start_dev.bat      - Start services normally
::   start_dev.bat --restart  - Restart services
:: ===================================================

:: Call main function and then show status
goto main

:end_script
call :show_status

:: Log completion
call :log "==================================================="
call :log "Development environment startup completed at: %TIME%"
call :log "==================================================="

:: Keep the window open if not in restart mode
if "%RESTART_MODE%"=="0" (
    pause
)

exit /b 0

:: ===================================================
:: Configuration
:: ===================================================
:: This script starts the CaseStrainer development environment
:: including both the Flask backend and Vue.js frontend
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "FLASK_APP=src/app_final_vue.py"
set "FLASK_ENV=development"
set "FLASK_DEBUG=1"
set "FLASK_RUN_PORT=5000"
set "FLASK_RUN_HOST=0.0.0.0"
set "VUE_DEV_PORT=5173"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\dev_%TIMESTAMP%.log"

:: Function to log messages
:log
set "MESSAGE=%~1"
echo [%TIME%] %MESSAGE%
(
echo [%TIME%] %MESSAGE%
) >> "%LOG_FILE%"
goto :eof

:: Redirect output to log file
call :log "Starting CaseStrainer Development Environment"
call :log "Log file: %LOG_FILE%"

:: Set window title
title CaseStrainer Development Environment

:: Set colors
color 0A
mode con:cols=100 lines=30

:: Clear screen
cls

echo ===================================================
echo    Starting CaseStrainer Development Environment
echo    %DATE% %TIME%
echo ===================================================
echo Log file: %LOG_FILE%
echo ===================================================
echo.

echo ===================================================
echo    Starting CaseStrainer Development Environment
echo ===================================================
echo.

:: Function to check if a process is running
:check_running
set "PID="
for /f "tokens=2 delims=: " %%a in ('tasklist /FI "IMAGENAME eq %1" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    set "PID=%%a"
)
if defined PID (
    echo [INFO] Process %1 is running with PID !PID!
    exit /b 1
) else (
    echo [INFO] Process %1 is not running
    exit /b 0
)

call :log "[1/4] Stopping any running processes..."
echo ===================================================

:: Function to stop process by name
:stop_process
set "PROCESS=%~1"
set "FRIENDLY_NAME=%~2"
if "%FRIENDLY_NAME%"=="" set "FRIENDLY_NAME=%PROCESS%"

call :log "Stopping %FRIENDLY_NAME% processes..."
tasklist /FI "IMAGENAME eq %PROCESS%" | find /I "%PROCESS%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    taskkill /F /IM %PROCESS% /T >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        call :log "[SUCCESS] Stopped %FRIENDLY_NAME%"
    ) else (
        call :log "[WARNING] Failed to stop %FRIENDLY_NAME% (may require admin rights)"
    )
) else (
    call :log "[INFO] No %FRIENDLY_NAME% processes found"
)
goto :eof

:: Stop processes
call :stop_process python.exe "Python"
call :stop_process node.exe "Node.js"
call :stop_process nginx.exe "Nginx"

:: Wait for processes to terminate
call :log "Waiting for processes to terminate..."
for /l %%i in (1,1,3) do (
    set /a "seconds=4-%%i"
    call :log "Waiting %%i/3 seconds..."
    timeout /t 1 /nobreak >nul
    
    :: Check if any processes are still running
    set "processes_running=0"
    for %%p in (python.exe node.exe nginx.exe) do (
        tasklist /FI "IMAGENAME eq %%p" 2>nul | find /I "%%p" >nul
        if !ERRORLEVEL! EQU 0 set "processes_running=1"
    )
    
    if "!processes_running!"=="0" (
        call :log "All processes have been terminated"
        goto :processes_stopped
    )
)

:processes_stopped

echo.
echo [2/4] Starting Flask backend...
echo ===================================================

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not in PATH. Please ensure Python is installed and in your PATH.
    pause
    exit /b 1
)

:: Check if required Python modules are installed
echo [INFO] Checking Python dependencies...
python -c "import flask" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Required Python packages not found. Installing...
    pip install -r requirements.txt
)

:: Start Flask backend in a new window
if "%RESTART_MODE%"=="1" (
    call :log "Restarting Flask backend..."
) else (
    call :log "Starting Flask backend..."
)
start "Flask Backend" cmd /k "@echo off && title Flask Backend && echo [Flask Backend] Starting... && cd /d %~dp0 && python src/app_final_vue.py || echo [ERROR] Failed to start Flask backend && pause"

:: Wait for Flask to start
echo [INFO] Waiting for Flask to start (this may take a moment)...
set "flask_started=0"
for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    curl -s -f -o nul http://localhost:5000/health
    if !ERRORLEVEL! EQU 0 (
        set "flask_started=1"
        echo [SUCCESS] Flask backend is running at http://localhost:5000
        goto :flask_running
    )
    echo [INFO] Waiting for Flask to start... (Attempt %%i/10)
)

if "!flask_started!"=="0" (
    echo [ERROR] Flask backend failed to start. Please check the Flask console for errors.
    echo [INFO] You may need to manually start the Flask backend with: python src/app_final_vue.py
    set /p continue=Continue with Vue.js startup? [y/N] 
    if /i not "!continue!"=="y" (
        exit /b 1
    )
)

:flask_running

echo.
echo [3/4] Starting Vue.js development server...
echo ===================================================

:: Check if Node.js and npm are available
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not in PATH. Please ensure Node.js is installed and in your PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not in PATH. Please ensure Node.js is installed and in your PATH.
    pause
    exit /b 1
)

:: Check if in the correct directory
if not exist "casestrainer-vue-new\package.json" (
    echo [ERROR] Could not find Vue.js project in casestrainer-vue-new directory
    pause
    exit /b 1
)

:: Install dependencies if node_modules doesn't exist
if not exist "casestrainer-vue-new\node_modules" (
    echo [INFO] Installing Vue.js dependencies (this may take a few minutes)...
    cd casestrainer-vue-new
    call npm install
    cd ..
)

:: Start Vue dev server in a new window
if "%RESTART_MODE%"=="1" (
    call :log "Restarting Vue.js development server..."
) else (
    call :log "Starting Vue.js development server..."
)

:: Change to Vue directory and start dev server
cd /d "%~dp0casestrainer-vue-new"

:: Check if node_modules exists, if not run npm install
if not exist "node_modules" (
    call :log "Node modules not found. Running npm install..."
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        call :log "[ERROR] Failed to install npm dependencies"
        goto :eof
    )
)

:: Start Vue dev server in a new window
start "Vue Dev Server" cmd /k "@echo off && title Vue Dev Server && echo [Vue Dev] Starting... && cd /d "%~dp0casestrainer-vue-new" && npm run dev || (echo [ERROR] Failed to start Vue dev server && pause)"

:: Change back to script directory
cd /d "%~dp0"

:: Wait for Vue dev server to start
echo [INFO] Waiting for Vue dev server to start (this may take a moment)...
set "vue_started=0"
for /l %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    curl -s -f -o nul http://localhost:5173/
    if !ERRORLEVEL! EQU 0 (
        set "vue_started=1"
        echo [SUCCESS] Vue dev server is running at http://localhost:5173
        goto :vue_running
    )
    echo [INFO] Waiting for Vue dev server to start... (Attempt %%i/15)
)

if "!vue_started!"=="0" (
    echo [WARNING] Vue dev server might not be ready yet. Please check the Vue console for errors.
    echo [INFO] You can access it later at http://localhost:5173
)

:vue_running

call :log "[4/4] Opening application in browser..."
echo ===================================================

:: Open the application in the default browser
start "" http://localhost:%VUE_DEV_PORT%/

:: Show completion message
echo.
echo ===================================================
echo      Development environment is ready!
echo ===================================================
echo.
echo [ACCESS LINKS]
echo - Frontend: http://localhost:%VUE_DEV_PORT%
echo - Backend API: http://localhost:%FLASK_RUN_PORT%
echo - Backend Health: http://localhost:%FLASK_RUN_PORT%/health
echo.
echo [CONSOLE WINDOWS]
- Flask Backend: Check for any Python/Flask errors
- Vue Dev Server: Check for any Vue.js compilation errors
echo.
echo [TROUBLESHOOTING]
- If the page doesn't load, check the console windows for errors
- Make sure all required services are running
- Check if ports %FLASK_RUN_PORT% and %VUE_DEV_PORT% are not in use by other applications
echo.
echo ===================================================
echo [INFO] Log file: %LOG_FILE%
echo [INFO] You can close this window at any time.
echo [INFO] To stop all services, close the Flask and Vue console windows.
echo ===================================================

:: Log completion
call :log "Development environment started successfully"
call :log "Frontend: http://localhost:%VUE_DEV_PORT%"
call :log "Backend API: http://localhost:%FLASK_RUN_PORT%"

:: Keep the window open
pause >nul
goto :eof

:: ===================================================
:: Helper Functions
:: ===================================================

:check_flask_status
set "FLASK_RUNNING=0"
curl -s -f -o nul http://localhost:%FLASK_RUN_PORT%/health
if %ERRORLEVEL% EQU 0 set "FLASK_RUNNING=1"
exit /b 0

:check_vue_status
set "VUE_RUNNING=0"
curl -s -f -o nul http://localhost:%VUE_DEV_PORT%
if %ERRORLEVEL% EQU 0 set "VUE_RUNNING=1"
exit /b 0

:show_status
call :log "=== Current Status ==="

:: Check Flask status
call :check_flask_status
if "!FLASK_RUNNING!"=="1" (
    call :log "[STATUS] Flask Backend: RUNNING on http://localhost:%FLASK_RUN_PORT%"
    netstat -ano | find ":%FLASK_RUN_PORT%"
) else (
    call :log "[STATUS] Flask Backend: NOT RUNNING"
)

:: Check Vue status
call :check_vue_status
if "!VUE_RUNNING!"=="1" (
    call :log "[STATUS] Vue Dev Server: RUNNING on http://localhost:%VUE_DEV_PORT%"
    netstat -ano | find ":%VUE_DEV_PORT%"
) else (
    call :log "[STATUS] Vue Dev Server: NOT RUNNING"
)

echo.
echo [INFO] To stop all services, close the Flask and Vue console windows.
echo [INFO] To restart, simply run this script again.
echo.
goto :eof

:: ===================================================
:: Main Execution
:: ===================================================

:main
:: Check for restart mode
if "%~1"=="--restart" (
    call :log "=== Restarting CaseStrainer Development Environment ==="
    set "RESTART_MODE=1"
) else (
    call :log "=== Starting CaseStrainer Development Environment ==="
    set "RESTART_MODE=0"
)

:check_port
set "PORT=%~1"
set "SERVICE=%~2"
call :log "Checking if port %PORT% is available for %SERVICE%..."
netstat -ano | find ":%PORT% " >nul
if %ERRORLEVEL% EQU 0 (
    call :log "[WARNING] Port %PORT% is in use by another process"
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%PORT% " ^| find "LISTENING"') do (
        set "PID=%%a"
        call :log "[WARNING] Process using port %PORT%: PID=!PID!"
        tasklist /FI "PID eq !PID!" 2>nul | findstr /B /C:"Image Name" /C:"========" /C:"chrome" /C:"node" /C:"python"
    )
    exit /b 1
) else (
    call :log "[SUCCESS] Port %PORT% is available"
    exit /b 0
)
goto :eof

:check_python_module
set "MODULE=%~1"
python -c "import %MODULE%" 2>nul
if %ERRORLEVEL% NEQ 0 (
    call :log "[WARNING] Python module %MODULE% not found"
    exit /b 1
) else (
    call :log "[SUCCESS] Python module %MODULE% is available"
    exit /b 0
)
goto :eof
