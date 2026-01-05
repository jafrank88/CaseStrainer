@echo off
:: Setup Docker Service - Requests admin privileges and runs the PowerShell script
echo ========================================
echo Setting up Docker Auto-Restart Service
echo ========================================
echo.

:: Check if already running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrator privileges
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -File "D:\dev\casestrainer\Create-DockerService.ps1"
) else (
    echo [INFO] Requesting Administrator privileges...
    echo.
    powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File D:\dev\casestrainer\Create-DockerService.ps1' -Verb RunAs"
)

echo.
pause
