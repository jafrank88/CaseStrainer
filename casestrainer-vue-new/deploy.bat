@echo off
echo ========================================
echo  CaseStrainer Vue.js Deployment Script
echo ========================================
echo.

:: Check if PowerShell is available
powershell -NoProfile -Command "exit 0"
if %ERRORLEVEL% NEQ 0 (
    echo Error: PowerShell is required to run this script.
    pause
    exit /b 1
)

:: Default target directory (relative to script location)
set "DEFAULT_TARGET=..\..\static\vue"

:: Check if target directory was provided as an argument
if "%~1" NEQ "" (
    set "TARGET_DIR=%~1"
) else (
    set "TARGET_DIR=%DEFAULT_TARGET%"
)

echo Deploying to: %TARGET_DIR%
echo.

:: Run the deployment script with PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1" -TargetDir "%TARGET_DIR%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Deployment failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Deployment completed successfully!
pause
