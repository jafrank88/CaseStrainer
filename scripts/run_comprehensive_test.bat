@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Comprehensive Test
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if required packages are installed
echo Checking required packages...

REM Check for requests
pip show requests >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing requests package...
    pip install requests
    echo Requests installed.
)

REM Check for matplotlib
pip show matplotlib >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing matplotlib package...
    pip install matplotlib
    echo Matplotlib installed.
)

REM Check for tabulate
pip show tabulate >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing tabulate package...
    pip install tabulate
    echo Tabulate installed.
)

REM Create results directory if it doesn't exist
if not exist "results" mkdir "results"

REM Start the log monitor if it's not already running
tasklist /fi "windowtitle eq CaseStrainer Log Monitor" | find "cmd.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Starting log monitor...
    start "CaseStrainer Log Monitor" cmd /k "python log_monitor.py"
    echo Log monitor started in a new window.
    timeout /t 2 >nul
)

REM Run the comprehensive test script
echo Running comprehensive Enhanced Validator tests...
python comprehensive_validator_test.py

echo.
echo Test completed. Check the results directory for detailed reports.
echo.
pause
