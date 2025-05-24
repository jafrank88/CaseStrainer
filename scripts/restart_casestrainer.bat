@echo off
REM ===================================================
REM DEPRECATED SCRIPT
REM ===================================================
REM This script is no longer supported.
REM Please use start_casestrainer.bat for all startup and restart operations.
REM ===================================================
setlocal enabledelayedexpansion

echo ===================================================
echo CaseStrainer Restart Script
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

:: Stop any running CaseStrainer processes
echo Stopping any running CaseStrainer processes...
tasklist /fi "imagename eq python.exe" /fo csv | findstr /i "python.exe" > temp_processes.txt
for /f "tokens=1,2 delims=," %%a in (temp_processes.txt) do (
    set "process=%%a"
    set process=!process:"=!
    set "pid=%%b"
    set pid=!pid:"=!
    
    :: Check if this process is running app_final_vue.py
    wmic process where "ProcessId=!pid!" get CommandLine | findstr /i "app_final_vue.py" > nul
    if !errorlevel! equ 0 (
        echo Stopping CaseStrainer process with PID: !pid!
        taskkill /f /pid !pid! > nul 2>&1
        if !errorlevel! equ 0 (
            echo Successfully stopped process.
        ) else (
            echo Failed to stop process.
        )
    )
)
del temp_processes.txt > nul 2>&1

:: Check if port 5000 is still in use
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 > nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 5000 is still in use.
    echo Stopping any processes using port 5000...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a > nul 2>&1
    )
    
    timeout /t 2 /nobreak > nul
)

:: Clear log files
echo Clearing old log files...
if exist logs\citation_verification.log (
    echo Backing up old citation_verification.log...
    copy logs\citation_verification.log logs\citation_verification.log.bak > nul
    echo > logs\citation_verification.log
)
if exist logs\casestrainer.log (
    echo Backing up old casestrainer.log...
    copy logs\casestrainer.log logs\casestrainer.log.bak > nul
    echo > logs\casestrainer.log
)

:: Install/update dependencies
echo Checking and updating dependencies...
pip install -r requirements.txt

:: Move to the correct directory
cd /d %~dp0\..

:: Check if development mode is requested
if "%1"=="dev" (
    echo Starting in DEVELOPMENT mode...
    set FLASK_ENV=development
    set FLASK_DEBUG=1
    echo Starting CaseStrainer in development mode...
    start "CaseStrainer Dev" cmd /c "python -m flask run --host=%HOST% --port=%PORT%"
) else (
    echo Starting in PRODUCTION mode...
    set FLASK_ENV=production
    echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
    echo Local access will be available at: http://127.0.0.1:5000
    echo.
    echo Starting CaseStrainer in production mode...
    start "CaseStrainer Production" cmd /c "python src/app_final_vue.py --host=%HOST% --port=%PORT%"
)

echo.
echo CaseStrainer has been restarted.
echo You can view the logs in the logs directory.
echo.
echo To stop CaseStrainer, close the command window or run:
echo   taskkill /fi "windowtitle eq CaseStrainer*" /f
echo.

endlocal
