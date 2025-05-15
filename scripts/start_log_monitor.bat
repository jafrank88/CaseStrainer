@echo off
echo ===================================================
echo CaseStrainer Log Monitor
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if colorama is installed
pip show colorama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing colorama package...
    pip install colorama
    echo Colorama installed.
)

REM Start the log monitor in a new window
start cmd /k "python log_monitor.py"

echo Log monitor started in a new window.
echo.
echo You can now test the Enhanced Validator while monitoring the logs.
echo.
