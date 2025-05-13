@echo off
echo Starting CaseStrainer with proper settings for Nginx proxy...

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
set "USE_CHEROOT=True"

REM Start the application with the correct settings
echo Starting CaseStrainer on port 5000 with host 0.0.0.0...
cd /d "%~dp0"
python app_simple.py --host=0.0.0.0 --port=5000

echo CaseStrainer stopped.
