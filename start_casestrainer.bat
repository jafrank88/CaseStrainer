@echo off
echo.
echo ============================================================
echo   CaseStrainer - One Click Start with Monitoring
echo ============================================================
echo.
echo Starting CaseStrainer with automatic monitoring setup...
echo.
echo Features:
echo - Automatic Docker monitoring (every 60 seconds)
echo - Docker auto-restart if it crashes
echo - System startup configuration (survives reboots)
echo - Web interface ready when done
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges - Full features enabled
) else (
    echo [NOTE] Running without admin - Monitoring will work at login
)

echo.
echo ============================================================
echo.

REM Launch cslaunch which automatically sets up monitoring
powershell -ExecutionPolicy Bypass -File ".\cslaunch.ps1"

echo.
echo ============================================================
echo   CaseStrainer is Running!
echo ============================================================
echo.
echo Monitoring Status:
echo - Docker daemon: Being monitored every 60 seconds
echo - Auto-restart: Enabled if Docker crashes
echo - System startup: Configured
echo.
echo Access CaseStrainer:
echo - Main: https://wolf.law.uw.edu/casestrainer/
echo - API:  https://wolf.law.uw.edu/casestrainer/api/
echo.
echo View Logs:
echo - Docker status: logs\docker_daemon_monitor.log
echo - Docker events: logs\docker_events.log
echo.
echo Press any key to exit...
pause >nul
