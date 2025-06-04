@echo off
REM Script to set up CaseStrainer environment variables

echo Setting up CaseStrainer environment...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Run the Python setup script
python scripts/setup_env.py

REM Pause to show any messages
pause
