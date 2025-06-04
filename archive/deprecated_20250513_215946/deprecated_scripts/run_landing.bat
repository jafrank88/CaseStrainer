@echo off
echo Starting CaseStrainer with simple landing page...

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 | findstr LISTENING >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Try to activate the virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the application
echo Starting CaseStrainer on port 5000...
python app_simple_landing.py

pause
