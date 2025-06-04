@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Test
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if requests is installed
pip show requests >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing requests package...
    pip install requests
    echo Requests installed.
)

REM Start the log monitor if it's not already running
tasklist /fi "windowtitle eq CaseStrainer Log Monitor" | find "cmd.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Starting log monitor...
    start "CaseStrainer Log Monitor" cmd /k "python log_monitor.py"
    echo Log monitor started in a new window.
    timeout /t 2 >nul
)

REM Run the test script
echo Running Enhanced Validator tests with real briefs...
python test_enhanced_validator.py

echo.
echo Test completed. Check the log monitor window for detailed results.
echo.
pause
