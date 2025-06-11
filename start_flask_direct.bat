@echo off
setlocal enabledelayedexpansion

:: Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Change to the script directory
cd /d "%SCRIPT_DIR%"

echo ===== Starting CaseStrainer =====
echo Directory: %CD%
echo Python version:
py --version
echo ===============================

:: Set environment variables
set FLASK_APP=app_final_vue.py
set FLASK_ENV=production
set FLASK_RUN_PORT=5000
set FLASK_RUN_HOST=0.0.0.0

echo.
echo Starting Flask application...
echo.

:: Run the Flask application using py launcher
py -m flask run --host=0.0.0.0 --port=5000

echo.
echo ===============================
echo Flask application has exited.
echo ===============================
pause
