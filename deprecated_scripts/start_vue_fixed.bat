@echo off
echo Starting CaseStrainer with Vue.js frontend...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python and try again.
    exit /b 1
)

REM Check if port 5000 is already in use
netstat -ano | findstr :5000 >nul
if %ERRORLEVEL% equ 0 (
    echo Port 5000 is already in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        taskkill /F /PID %%a
        if %ERRORLEVEL% equ 0 (
            echo Successfully killed process using port 5000.
        ) else (
            echo Failed to kill process. Please close the application using port 5000 manually.
            exit /b 1
        )
    )
)

REM Set the Flask app environment variables
set FLASK_APP=app_vue_fixed.py
set FLASK_ENV=production

REM Get the full path to the app_vue_fixed.py file
set APP_PATH=%~dp0app_vue_fixed.py

REM Start the Flask application
echo Starting CaseStrainer on http://127.0.0.1:5000
echo For external access, use https://wolf.law.uw.edu/casestrainer/
python "%APP_PATH%" --host=0.0.0.0 --port=5000

pause
