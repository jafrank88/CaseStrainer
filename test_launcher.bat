@echo off
echo Testing launcher.ps1...
echo.

REM Test if PowerShell is available
powershell -Command "Write-Host 'PowerShell is available'" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available
    pause
    exit /b 1
)

REM Test if launcher.ps1 exists
if not exist "launcher.ps1" (
    echo ERROR: launcher.ps1 not found
    pause
    exit /b 1
)

echo launcher.ps1 file exists
echo.

REM Test launcher help
echo Testing launcher help...
powershell -ExecutionPolicy Bypass -Command "& '.\launcher.ps1' -Help" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: launcher.ps1 help failed
    pause
    exit /b 1
)

echo.
echo launcher.ps1 help test completed successfully
pause 