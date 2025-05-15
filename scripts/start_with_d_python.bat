@echo off
echo ===================================================
echo CaseStrainer Vue.js Startup Script (D:\Python)
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

REM Set environment variables
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_CHEROOT=True"

REM Start the CaseStrainer Vue.js frontend using D:\Python\python.exe
echo Starting CaseStrainer Vue.js frontend on port 5000...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000

REM Use the Python executable at D:\Python\python.exe
D:\Python\python.exe "%~dp0app_final_vue.py" --host=0.0.0.0 --port=5000

echo.
echo CaseStrainer stopped.
