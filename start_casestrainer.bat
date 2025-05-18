@echo off
setlocal enabledelayedexpansion

REM === CONFIGURATION ===
set NGINX_DIR=%~dp0nginx-1.27.5
set PROD_CONF=%NGINX_DIR%\conf\nginx.conf
set TEST_CONF=%NGINX_DIR%\conf\nginx_test.conf
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_CHEROOT=True

REM === CHOOSE NGINX CONFIGURATION ===
set NGINX_CONFIG=%PROD_CONF%
if /i "%1"=="test" set NGINX_CONFIG=%TEST_CONF%

REM === STOP EXISTING NGINX ===
echo Checking for running Nginx...
tasklist | find /i "nginx.exe" >nul 2>&1
if %errorlevel%==0 (
    echo Stopping existing Nginx instance...
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit
    timeout /t 2 >nul
    cd /d "%~dp0"
)

REM === STOP EXISTING BACKEND ===
echo Stopping any running CaseStrainer backend processes...
tasklist /fi "imagename eq python.exe" /fo csv | findstr /i "python.exe" > temp_processes.txt
for /f "tokens=1,2 delims=," %%a in (temp_processes.txt) do (
    set "process=%%a"
    set process=!process:"=!
    set "pid=%%b"
    set pid=!pid:"=! 
    wmic process where "ProcessId=!pid!" get CommandLine | findstr /i "app_final_vue.py" > nul
    if !errorlevel! equ 0 (
        echo Stopping backend process with PID: !pid!
        taskkill /f /pid !pid! > nul 2>&1
    )
)
del temp_processes.txt > nul 2>&1

REM === START BACKEND ===
echo Starting CaseStrainer backend on port %PORT% ...
start "CaseStrainer Backend" cmd /c "set FLASK_APP=%FLASK_APP% && set HOST=%HOST% && set PORT=%PORT% && set THREADS=%THREADS% && set USE_CHEROOT=%USE_CHEROOT% && python -m flask run --host=%HOST% --port=%PORT%"

REM === START NGINX ===
echo Starting Nginx with config: %NGINX_CONFIG%
cd /d "%NGINX_DIR%"
start "Nginx" nginx.exe -c "%NGINX_CONFIG%"
cd /d "%~dp0"

echo =============================================
echo   CaseStrainer backend and Nginx started!
echo =============================================
pause
endlocal

echo ===================================================
echo CaseStrainer Startup Script
echo ===================================================
echo.

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_CHEROOT=True

:: Create required directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

:: Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 5000 is already in use.
    echo Stopping any processes using port 5000...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
)

:: Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Check if development mode is requested
if "%1"=="dev" (
    echo Starting in DEVELOPMENT mode...
    set FLASK_ENV=development
    set FLASK_DEBUG=1
    python -m flask run --host=%HOST% --port=%PORT%
) else (
    echo Starting in PRODUCTION mode...
    set FLASK_ENV=production
    echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
    echo Local access will be available at: http://127.0.0.1:5000
    echo.
    python src/app_final_vue.py --host=%HOST% --port=%PORT%
)

pause