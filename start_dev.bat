@echo off
setlocal EnableDelayedExpansion

REM === CaseStrainer DEV Startup Script (Unified Vue.js + API) ===
REM This script is for local development and testing only.

REM Logging setup (dev: logs to console, not file)
REM Timestamp for this run
for /f "tokens=1-4 delims=/ " %%a in ("%date% %time%") do set NOW=%%a-%%b-%%c_%%d

echo ===================================================
echo CaseStrainer DEV Startup Script (Unified Vue.js + API)
echo Started at %NOW%
echo ===================================================
echo.

REM Set environment variables (development mode)
set FLASK_APP=src/app.py
set HOST=127.0.0.1
set PORT=5000
set FLASK_ENV=development
set FLASK_DEBUG=1
set USE_WAITRESS=False
set THREADS=2
set NGINX_DIR=%~dp0nginx-1.27.5
set DEV_CONF=%NGINX_DIR%\conf\nginx_test.conf

REM Create required directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Check if Vue frontend is built
if not exist casestrainer-vue\dist (
    echo.
    echo WARNING: Vue.js frontend build not found!
    echo The CaseStrainer web interface will NOT work until the Vue frontend is built.
    echo To build the frontend, open a terminal in the 'casestrainer-vue' directory and run:
    echo     npm install
    echo     npm run build
    echo After building, restart this batch file.
    echo.
)

REM Step 1: Stop any existing processes
echo Step 1: Stopping existing processes...
echo.

REM Stop Windows Nginx if running
echo Checking for Windows Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if !ERRORLEVEL! == 0 (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
    echo Windows Nginx stopped.
) else (
    echo Windows Nginx is not running.
)

REM Check if port 5000 is already in use
echo Checking if port 5000 is in use...
netstat -ano | findstr :5000 | findstr LISTENING
if !ERRORLEVEL! == 0 (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
    timeout /t 2 /nobreak >nul
) else (
    echo Port 5000 is available.
)

REM Stop any running Flask (CaseStrainer) processes
REM Only kill python.exe processes running app.py or using port 5000

echo Checking for Flask (CaseStrainer) processes...
REM Find python processes running app.py
for /f "tokens=2 delims==" %%a in ('wmic process where "CommandLine like '%%app.py%%' and Name='python.exe'" get ProcessId /value 2^>nul ^| findstr ProcessId') do (
    set PID=%%a
    echo Found Flask process with PID !PID! running app.py. Killing it...
    taskkill /F /PID !PID!
)
REM Also check for python.exe using port 5000 (in case of alternate launches)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing python process using port 5000 with PID %%a
    taskkill /F /PID %%a
)
echo Flask (CaseStrainer) processes stopped if any were running.

REM Step 2: Start backend in DEV mode
echo Starting CaseStrainer backend (Unified Vue.js + API) in DEV mode on port %PORT% ...
start "CaseStrainer Backend DEV" cmd /c "set FLASK_APP=%FLASK_APP% && set FLASK_ENV=development && set FLASK_DEBUG=1 && set HOST=%HOST% && set PORT=%PORT% && python -m flask run --host=%HOST% --port=%PORT%"

REM Step 3: Start Nginx (DEV CONFIG)
echo Starting Nginx (DEV) with config: %DEV_CONF%
cd /d "%NGINX_DIR%"
start "Nginx DEV" nginx.exe -c "%DEV_CONF%"
cd /d "%~dp0"

echo =============================================
echo   CaseStrainer DEV backend and Nginx started!
echo =============================================
pause
endlocal
