@echo off
setlocal

:: Stop any running Python processes
taskkill /f /im python.exe >nul 2>&1

:: Set environment variables
set FLASK_APP=src\app_final_vue.py
set FLASK_ENV=production
set FLASK_DEBUG=0
set PORT=5000

:: Activate virtual environment and start Flask
call .venv\Scripts\activate.bat

:: Start Flask
python -m flask run --host=0.0.0.0 --port=%PORT% --no-debugger --no-reload

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start Flask application
    pause
    exit /b 1
)

exit /b 0
