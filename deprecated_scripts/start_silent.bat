@echo off
setlocal enabledelayedexpansion

:: Silent Startup Script for CaseStrainer
:: =====================================

:: Set working directory to script location
cd /d "%~dp0"

:: Read ports from config.ini
for /f "tokens=1,2 delims==" %%A in ('findstr /B /I "DEV_BACKEND_PORT DEV_FRONTEND_PORT" config.ini') do (
    if /i "%%A"=="DEV_BACKEND_PORT" set DEV_BACKEND_PORT=%%B
    if /i "%%A"=="DEV_FRONTEND_PORT" set DEV_FRONTEND_PORT=%%B
)

:: Set default ports if not found in config.ini
if not defined DEV_BACKEND_PORT set DEV_BACKEND_PORT=5001
if not defined DEV_FRONTEND_PORT set DEV_FRONTEND_PORT=3000

echo [*] Using ports from config.ini:
echo     - Backend: %DEV_BACKEND_PORT%
echo     - Frontend: %DEV_FRONTEND_PORT%

echo [*] Stopping any existing processes...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

:: Create required directories if they don't exist
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"
if not exist "casestrainer_sessions" mkdir "casestrainer_sessions"

echo [*] Updating Nginx configuration with ports from config.ini...
powershell -Command "(Get-Content 'nginx-1.27.5\conf\nginx.conf') -replace 'proxy_pass http://127.0.0.1:5001/', 'proxy_pass http://127.0.0.1:%DEV_BACKEND_PORT%/' | Set-Content 'nginx-1.27.5\conf\nginx.conf'"
powershell -Command "(Get-Content 'nginx-1.27.5\conf\nginx.conf') -replace 'proxy_pass http://127.0.0.1:3000/', 'proxy_pass http://127.0.0.1:%DEV_FRONTEND_PORT%/' | Set-Content 'nginx-1.27.5\conf\nginx.conf'"

echo [*] Starting Nginx...
cd /d "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5"
start "" /B nginx.exe -p . -c conf\nginx.conf
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Nginx. Check nginx-1.27.5\logs\error.log for details.
    echo [DEBUG] Attempting to run with full path...
    "C:\Windows\System32\cmd.exe" /c "cd /d "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5" && nginx.exe -p . -c conf\nginx.conf"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Nginx failed to start with full path. Please check the logs.
        exit /b 1
    )
)
cd /d "%~dp0"
echo [✓] Nginx started successfully

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=production
set HOST=0.0.0.0
set PORT=%DEV_BACKEND_PORT%
set THREADS=10
set USE_CHEROOT=True

echo [*] Starting Flask application...
start "" /B cmd /c "python -m flask run --host=%HOST% --port=%PORT% --with-threads > logs\flask.log 2>&1"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Flask application
    exit /b 1
)

echo [*] Starting Vite development server...
set VUE_DIR=casestrainer-vue-new

if not exist "%VUE_DIR%" (
    echo [ERROR] %VUE_DIR% directory not found
    echo [INFO] Current directory: %CD%
    dir /b
    exit /b 1
)

echo [*] Using Vite directory: %VUE_DIR%

:: Store the current directory
set CURRENT_DIR=%CD%

:: Change to the VUE_DIR
cd /d "%CURRENT_DIR%\%VUE_DIR%"

:: Check if package.json exists
if not exist "package.json" (
    echo [ERROR] package.json not found in %VUE_DIR%
    cd /d "%CURRENT_DIR%"
    exit /b 1
)

echo [*] Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install npm dependencies
    cd /d "%CURRENT_DIR%"
    exit /b 1
)

:: Return to the original directory
cd /d "%CURRENT_DIR%"



:: Check if port is in use
netstat -ano | find ":%DEV_FRONTEND_PORT%" | find "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Port %DEV_FRONTEND_PORT% is already in use
    echo [INFO] Trying to find the process using the port...
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%DEV_FRONTEND_PORT%" ^| find "LISTENING"') do (
        tasklist /FI "PID eq %%a"
    )
    echo [INFO] You may need to terminate the process using the port
)

:: Start Vite in a new window for better error visibility
echo [*] Starting Vite on port %DEV_FRONTEND_PORT%...
start "Vite Dev Server" /B cmd /k "cd /d "%CURRENT_DIR%\%VUE_DIR%" && echo Starting Vite on port %DEV_FRONTEND_PORT%... && npm run dev -- --port %DEV_FRONTEND_PORT%"

echo [*] Waiting for Vite to start...
timeout /t 5 >nul

:: Give it some time to start
timeout /t 5 >nul

cd ..

:: Check if Vite is running
tasklist /FI "IMAGENAME eq node.exe" | find /I "node" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Vite process is running
    echo [*] Vite should be available at: http://localhost:%VITE_PORT%
) else (
    echo [WARNING] Vite might not have started properly. Check the Vite window for errors.
    echo [INFO] You can also try starting Vite manually: cd %VUE_DIR% && npm run dev -- --port %VITE_PORT%
)

echo [*] Nginx is configured to proxy requests to: http://localhost:%VITE_PORT%

:: Brief pause to allow services to start
timeout /t 5 >nul

:: Check service status
echo.
echo [*] Service Status:
echo -------------------

tasklist /FI "IMAGENAME eq nginx.exe" | find /I "nginx.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Nginx is running
) else (
    echo [✗] Nginx is not running
)

tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Flask is running
) else (
    echo [✗] Flask is not running
)

tasklist /FI "IMAGENAME eq node.exe" | find /I "node.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Vite is running
) else (
    echo [✗] Vite is not running
)

echo.
echo [*] Application URLs:
echo --------------------
echo     - Local Backend:  http://localhost:%DEV_BACKEND_PORT%
echo     - Local Frontend: http://localhost:%DEV_FRONTEND_PORT%
echo     - External:       https://wolf.law.uw.edu/casestrainer/
echo     - API Endpoint:   http://localhost:%DEV_BACKEND_PORT%/api/
echo.
echo [*] Logs are available in the 'logs' directory
echo [*] Press any key to stop services and exit...
pause >nul

echo [*] Stopping services...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo [*] Services stopped.
