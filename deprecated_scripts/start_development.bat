@echo off
setlocal enabledelayedexpansion

REM Set the project root directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

REM Set up log directory
set "LOG_DIR=%PROJECT_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\casestrainer_%DATE:/=-%_%TIME::=-%.log"

REM Function to log messages
:log
    echo [%DATE% %TIME%] %* | findstr /v "^[0-9]"
    echo [%DATE% %TIME%] %* >> "%LOG_FILE%" 2>&1
goto :eof

REM Kill any existing Python and Node processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

REM Start the backend server
call :log "Starting backend server..."
start "CaseStrainer Backend" /MIN cmd /c "python -c "import logging; logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s'); from src.app_final_vue import app; app.run(host='0.0.0.0', port=5000, debug=True)" 2>&1 | findstr /v "GET /favicon.ico""

REM Wait for backend to start
call :log "Waiting for backend to start..."
timeout /t 5 >nul

REM Start the frontend development server
cd "%PROJECT_ROOT%casestrainer-vue-new"
call :log "Starting frontend development server..."
start "CaseStrainer Frontend" cmd /c "npm run dev"

call :log "Development environment started successfully!"
call :log "Backend: http://localhost:5000"
call :log "Frontend: http://localhost:5173"
call :log ""
call :log "Press any key to stop all services..."
pause >nul

taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

call :log "All services stopped."
