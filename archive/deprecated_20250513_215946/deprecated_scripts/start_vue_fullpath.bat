@echo off
echo ===================================================
echo CaseStrainer Vue.js Startup Script
echo ===================================================
echo.

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

REM Start the CaseStrainer Vue.js frontend using the full path to the Python executable
echo Starting CaseStrainer Vue.js frontend on port 5000...
cd /d "%~dp0"

REM Use the full path to the Python executable
"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\.venv\Scripts\python.exe" "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\app_final_vue.py" --host=0.0.0.0 --port=5000

echo.
echo CaseStrainer stopped.
