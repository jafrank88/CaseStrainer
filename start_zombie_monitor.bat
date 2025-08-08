@echo off
echo Starting Docker Zombie Process Monitor...

REM Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo PowerShell not found. Cannot start zombie monitor.
    pause
    exit /b 1
)

REM Start zombie monitor in background
powershell -NoProfile -ExecutionPolicy Bypass -File "docker_zombie_monitor.ps1" -Verbose

pause
