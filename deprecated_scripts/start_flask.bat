@echo off
setlocal enabledelayedexpansion

:: Set up logging
set "LOG_FILE=%~dp0flask.log"
echo [%DATE% %TIME%] Starting Flask application > "%LOG_FILE%"

:: Function to log messages
:log
echo [%DATE% %TIME%] %* >> "%LOG_FILE%"
echo [%TIME%] %*
goto :eof

:: Set environment variables
set "FLASK_APP=src\app_final_vue.py"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "PORT=5000"

:: Log startup info
call :log Starting Flask application

:: Activate virtual environment
call .venv\Scripts\activate

:: Start Flask application
call :log Starting Flask application on 0.0.0.0:%PORT%
python -m flask run --host=0.0.0.0 --port=%PORT%

if %ERRORLEVEL% NEQ 0 (
    call :log ERROR: Failed to start Flask application
    exit /b 1
) else (
    call :log Flask application started successfully
)

exit /b 0
call :log FLASK_APP=%FLASK_APP%
call :log FLASK_ENV=%FLASK_ENV%
call :log PORT=%PORT%

:: Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log [ERROR] Python is not in PATH
    pause
    exit /b 1
)

:: Check if Flask is installed
python -c "import flask" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log [ERROR] Flask is not installed. Please install it with: pip install flask
    pause
    exit /b 1
)

:: Check if the Flask app file exists
if not exist "%FLASK_APP%" (
    call :log [ERROR] Flask app not found: %FLASK_APP%
    call :log [INFO] Current directory: %CD%
    pause
    exit /b 1
)

call :log [OK] Found Flask app: %FLASK_APP%

:: Start Flask
call :log [INFO] Starting Flask server...
python -m flask run --port=%PORT% --host=0.0.0.0 --no-debugger --no-reload --with-threads

call :log [INFO] Flask server stopped
pause
