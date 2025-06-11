@echo off
setlocal enabledelayedexpansion

:: Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Change to the script directory
cd /d "%SCRIPT_DIR%"

echo ===== Starting CaseStrainer in Production Mode =====
echo Directory: %CD%
echo ===================================================
echo.

:: Set environment variables
echo Setting up environment...
set FLASK_APP=src.app_final_vue
set FLASK_ENV=production
set FLASK_RUN_PORT=5000
set FLASK_RUN_HOST=0.0.0.0
set PYTHONPATH=%SCRIPT_DIR%

:: Kill any existing Nginx and Python processes
echo Stopping any existing services...
taskkill /F /IM nginx.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

:: Start Nginx
echo.
echo Starting Nginx...
start "Nginx" cmd /k ""%SCRIPT_DIR%\nginx-1.27.5\nginx.exe" -c "%SCRIPT_DIR%\nginx-case-strainer.conf" && echo Nginx started successfully. Press any key to close... && pause >nul"

:: Wait for Nginx to start
timeout /t 2 /nobreak >nul

echo.
echo Starting CaseStrainer backend...
start "CaseStrainer Backend" cmd /k "cd /d "%SCRIPT_DIR%" && python -m waitress --host=0.0.0.0 --port=5000 -w 4 "src.app_final_vue:create_app()""

echo.
echo ===================================================
echo   CaseStrainer is now running in production mode!
echo ===================================================
echo.
echo Access the application at:
echo - Local: http://localhost/casestrainer/
echo - Network: https://wolf.law.uw.edu/casestrainer/
echo.
echo Press any key to stop all services and exit...
pause >nul

echo.
echo Stopping all services...
taskkill /F /IM nginx.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
echo All services have been stopped.

exit /b 0
