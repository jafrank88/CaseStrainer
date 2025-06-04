@echo off
REM Script to test CaseStrainer environment configuration

echo Testing CaseStrainer environment configuration...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Install python-dotenv if not installed
pip install python-dotenv --quiet

REM Run the Python test script
python scripts/test_env.py

REM Pause to show any messages
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo For help with setup, run: scripts\setup_env.bat
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
pause
