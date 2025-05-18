@echo off
echo ===================================================
echo Starting CaseStrainer Vue.js Interface...
echo ===================================================
echo.

REM Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 5000 is already in use.
    echo Stopping any processes using port 5000...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
)

REM Kill any existing Python processes
echo Stopping any existing Python processes...
taskkill /f /im python.exe >nul 2>&1

REM Set environment variables
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_WAITRESS=True"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"

REM Navigate to project root
cd /d "%~dp0.."

REM Start the application
echo Starting CaseStrainer Vue.js Interface on port 5000...
python src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production

echo.
echo CaseStrainer Vue.js Interface stopped.
echo.
echo Access the application at: http://localhost:5000
echo.