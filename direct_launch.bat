@echo off
setlocal enabledelayedexpansion

:: Get the script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Change to the script directory
cd /d "%SCRIPT_DIR%"

echo ===== Starting CaseStrainer =====
echo Directory: %CD%
echo ===============================
echo.

:: Run the main script directly
call start_casestrainer.bat

:: Keep the window open
echo.
echo ===============================
echo CaseStrainer has exited.
echo ===============================
pause
