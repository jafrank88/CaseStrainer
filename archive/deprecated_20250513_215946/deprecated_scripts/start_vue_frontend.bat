@echo off
echo Starting CaseStrainer Vue.js frontend...

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

REM Start the CaseStrainer Vue.js frontend
echo Starting CaseStrainer Vue.js frontend on port 5000...
cd /d "%~dp0"
python run_vue_frontend.py --host=0.0.0.0 --port=5000

echo.
echo CaseStrainer stopped.
