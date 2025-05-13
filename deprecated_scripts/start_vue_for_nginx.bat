@echo off
echo Starting CaseStrainer with Vue.js frontend for Nginx...

REM Check if Windows Nginx is running and stop it
echo Checking for Windows Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
    echo Windows Nginx stopped.
) else (
    echo Windows Nginx is not running.
)

REM Check if port 5000 is already in use
echo Checking if port 5000 is in use...
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

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Start the Flask application with Vue.js integration on port 5000 with host 0.0.0.0
echo Starting Flask application with Vue.js integration on port 5000 with host 0.0.0.0...
python app_final_vue.py --host=0.0.0.0 --port=5000

echo.
echo CaseStrainer stopped.
