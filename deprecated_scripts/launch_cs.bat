@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Launcher
:: Can be run from any directory
:: ===================================================

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: If run from a different directory, change to the script's directory
cd /d "%SCRIPT_DIR%" 2>nul || (
    echo [ERROR] Failed to change to script directory: %SCRIPT_DIR%
    pause
    exit /b 1
)

:: Verify run_cs.bat exists in the same directory
if not exist "run_cs.bat" (
    echo [ERROR] Could not find run_cs.bat in the current directory
    echo [INFO] Current directory: %CD%
    pause
    exit /b 1
)

:: Run the main script
echo [INFO] Launching CaseStrainer from: %CD%
echo.

call "run_cs.bat"
set "EXIT_CODE=!ERRORLEVEL!"

if %EXIT_CODE% neq 0 (
    echo [ERROR] CaseStrainer exited with error code %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
