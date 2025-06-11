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
python --version
echo ===============================
echo.

:: Set environment variables
echo Setting up environment...
set FLASK_APP=src.app_final_vue
set FLASK_ENV=production
set FLASK_RUN_PORT=5000
set FLASK_RUN_HOST=0.0.0.0

:: Install required packages if needed
echo.
echo Checking Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting Flask application...
echo.

:: Add src to PYTHONPATH
set PYTHONPATH=%SCRIPT_DIR%

:: Run the Flask application using python directly
echo Running: python -m flask run --host=0.0.0.0 --port=5000
python -m flask run --host=0.0.0.0 --port=5000

echo.
echo ===============================
echo Flask application has exited.
echo ===============================
pause
