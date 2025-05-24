@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Commit, Push, and Deploy Script
REM USAGE: Double-click or run from the CaseStrainer root directory.
REM LOG: All output is logged to casestrainer_deploy.log
REM REQUIREMENTS: Node.js, npm, Python 3.x, git, Docker, PowerShell
REM TROUBLESHOOTING: Check casestrainer_deploy.log for errors.
REM Exit code 0 = success, nonzero = failure.
REM ===================================================

set LOGFILE=casestrainer_deploy.log

REM === Tool Checks ===
where node >nul 2>&1 || (echo [ERROR] Node.js is not installed!
echo [ERROR] Node.js is not installed! >> %LOGFILE%
exit /b 1)
where npm >nul 2>&1 || (echo [ERROR] npm is not installed!
echo [ERROR] npm is not installed! >> %LOGFILE%
exit /b 1)
where python >nul 2>&1 || (echo [ERROR] Python is not installed!
echo [ERROR] Python is not installed! >> %LOGFILE%
exit /b 1)
where git >nul 2>&1 || (echo [ERROR] git is not installed!
echo [ERROR] git is not installed! >> %LOGFILE%
exit /b 1)
where docker >nul 2>&1 || (echo [ERROR] Docker is not installed!
echo [ERROR] Docker is not installed! >> %LOGFILE%
exit /b 1)
where powershell >nul 2>&1 || (echo [ERROR] PowerShell is not installed!
echo [ERROR] PowerShell is not installed! >> %LOGFILE%
exit /b 1)

REM === Log Start ===
echo =================================================== >> %LOGFILE%
echo [%DATE% %TIME%] Starting Commit/Push/Deploy >> %LOGFILE%
REM ================================================
REM CaseStrainer Commit, Push, and Deploy Script
REM ================================================
REM This script commits changes, pushes to main, and redeploys using the latest deployment logic from start_casestrainer.bat
REM ================================================

REM === Ensure pre-commit hooks are up-to-date and clean ===
pre-commit autoupdate
pre-commit clean
pre-commit install

REM Step 1: Commit all changes
echo Adding all changes to git...
git add -A
set /p commitmsg="Enter commit message: "
echo Running pre-commit checks on all files...
pre-commit run --all-files
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pre-commit checks failed. Please fix the issues above before committing.
echo [ERROR] Pre-commit checks failed. Please fix the issues above before committing. >> %LOGFILE%
    exit /b 1
)
echo Pre-commit checks passed. Proceeding with commit...
echo Committing changes...
git commit -m "%commitmsg%"

REM Step 2: Push to remote repository
echo Pushing to remote repository...
git push origin main

REM Step 3: Stop any running Nginx instances to avoid conflicts
taskkill /F /IM nginx.exe >nul 2>&1

REM Step 4: Ensure required directories exist
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Step 5: Start CaseStrainer using the main startup script (handles build, cache, encoding, and all checks)
call start_casestrainer.bat

REM Step 6: Ensure port 5000 is available and kill any conflicting processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Port 5000 in use by PID %%a. Killing process...
    taskkill /F /PID %%a
)

REM Step 7: Activate Python venv and start backend with correct host/port
call C:\Users\jafrank\venv_casestrainer\Scripts\activate.bat
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set THREADS=4

start "CaseStrainer Backend" cmd /k "python src\app_final_vue.py --use-waitress --host=%HOST% --port=%PORT% --threads=%THREADS% & echo. & echo Backend process ended. Press any key to close. & pause"

REM Step 8: Start Nginx
set NGINX_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5
set NGINX_CONFIG=%NGINX_DIR%\conf\casestrainer.conf
cd /d "%NGINX_DIR%"
echo Starting Nginx with config: %NGINX_CONFIG%
start nginx.exe -c "%NGINX_CONFIG%"
cd /d "%~dp0"

REM Step 9: Verify Flask is running
timeout /t 5 >nul
netstat -ano | findstr :5000 | findstr LISTENING
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Flask did not start or port 5000 is not listening.
    echo To diagnose, run the following commands in your terminal:
    echo -----------------------------------------------
    echo set FLASK_APP=src/app_final_vue.py
    echo set FLASK_ENV=production
    echo python -m flask run --host=0.0.0.0 --port=5000
    echo -----------------------------------------------
    echo This will show any error messages directly.
    echo If you see missing dependency errors, run:
    echo     pip install -r requirements.txt
    echo If port 5000 is in use, check for processes and kill them as needed.
    echo.
    pause
) else (
    echo Flask is running on port 5000. Deployment appears successful.
    pause
)
