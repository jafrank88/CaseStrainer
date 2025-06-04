@echo off
setlocal enabledelayedexpansion

REM Set the project root directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

REM Set up log directory
set "LOG_DIR=%PROJECT_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\casestrainer_prod_%DATE:/=-%_%TIME::=-%.log"

REM Function to log messages
:log
    echo [%DATE% %TIME%] %* | findstr /v "^[0-9]"
    echo [%DATE% %TIME%] %* >> "%LOG_FILE%" 2>&1
goto :eof

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1

REM Build the frontend if needed
if not exist "%PROJECT_ROOT%static\vue\index.html" (
    call :log "Frontend not built. Building now..."
    call "%PROJECT_ROOT%build_frontend.bat"
    if errorlevel 1 (
        call :log "Error: Failed to build frontend"
        exit /b 1
    )
)

REM Start the production server
call :log "Starting production server..."
python -c "import logging; logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s'); from src.app_final_vue import app; app.run(host='0.0.0.0', port=5000, debug=False)"
