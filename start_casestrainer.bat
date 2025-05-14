@echo off
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
    python src/app_final_vue.py --host=%HOST% --port=%PORT% --use-cheroot
)

pause