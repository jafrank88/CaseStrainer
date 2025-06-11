@echo off
setlocal enabledelayedexpansion

:: ============================================
:: debug_flask.bat - Start Flask server in debug mode
::
:: Usage: debug_flask.bat [port]
::   port: Optional port number (default: 5000)
:: ============================================

:: Set default values
set PORT=5000
set HOST=0.0.0.0
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONPATH=%~dp0src;%PYTHONPATH%

:: Check for custom port
if not "%1"=="" (
    set PORT=%1
)

echo ============================================
echo  Starting Flask Server in Debug Mode
echo ============================================
echo Host: %HOST%
echo Port: %PORT%
echo Python: %PYTHON_HOME%\python.exe
echo ============================================

:: Kill any existing Python processes on the same port
echo Checking for processes on port %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% "') do (
    echo Terminating process with PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: Start Flask server
echo.
echo Starting Flask development server...
echo Press Ctrl+C to stop the server
python -m flask run --host=%HOST% --port=%PORT% --debugger --reload

:: If we get here, the server was stopped
echo.
echo ============================================
echo  Flask server has stopped
echo ============================================
pause
