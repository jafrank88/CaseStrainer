@echo off
setlocal enabledelayedexpansion

echo [DEBUG] Starting debug launcher...
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Script directory: %~dp0

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [DEBUG] Changing to directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

echo [DEBUG] Current directory is now: %CD%

:: Check if start_casestrainer.bat exists
if exist "start_casestrainer.bat" (
    echo [DEBUG] Found start_casestrainer.bat
    echo [DEBUG] Starting CaseStrainer...
    
    :: Run the script directly in the current window
    call "%CD%\start_casestrainer.bat"
) else (
    echo [ERROR] Could not find start_casestrainer.bat
    echo [ERROR] Looked in: %CD%
    dir /b
)

echo [DEBUG] Launcher finished
pause
