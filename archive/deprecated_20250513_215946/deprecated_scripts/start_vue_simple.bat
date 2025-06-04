@echo off
echo Starting CaseStrainer with simplified Vue.js frontend...

REM Stop any running Python instances
echo Stopping any running Python instances...
taskkill /F /IM python.exe 2>nul

REM Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 | findstr LISTENING
if "%ERRORLEVEL%"=="0" (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
) else (
    echo Port 5000 is available.
)

REM Set environment variables
set "HOST=0.0.0.0"
set "PORT=5000"

REM Start the application with the correct settings
echo Starting CaseStrainer on port 5000 with host 0.0.0.0...
cd /d "%~dp0"

REM Check if Python is in the PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Using Python from PATH
    python app_final_vue_simple.py --host=0.0.0.0 --port=5000
) else (
    echo Python not found in PATH, checking virtual environment...
    if exist ".venv\Scripts\python.exe" (
        echo Using Python from virtual environment
        .venv\Scripts\python.exe app_final_vue_simple.py --host=0.0.0.0 --port=5000
    ) else (
        echo Python not found. Please install Python and try again.
        exit /b 1
    )
)

echo CaseStrainer stopped.
