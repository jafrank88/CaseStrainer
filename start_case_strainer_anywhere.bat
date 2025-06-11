@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Launcher - Works from any directory
:: ===================================================
:: This script starts the CaseStrainer application
:: ===================================================

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Change to the script directory
pushd "%SCRIPT_DIR%"

:: Check if start_casestrainer.bat exists
if not exist "start_casestrainer.bat" (
    echo Error: Could not find start_casestrainer.bat in the script directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting CaseStrainer from: %CD%
echo Please wait, this may take a moment...

:: Start the application and keep the window open
start "CaseStrainer" cmd /k ""%CD%\start_casestrainer.bat""

:: Return to the original directory
popd

exit /b 0
