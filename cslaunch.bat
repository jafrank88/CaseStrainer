@echo off
echo CaseStrainer Deployment Manager
echo ================================
echo.

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell is not available in the system path.
    echo Please install PowerShell and ensure it's in your system path.
    pause
    exit /b 1
)

:: Run the cslaunch.ps1 script with the provided arguments
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\cslaunch.ps1" %*

:: Check if the script executed successfully
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while running the deployment script.
    echo Please check the error messages above for details.
    pause
    exit /b 1
)

exit /b 0
