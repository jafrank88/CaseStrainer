@echo off
echo Starting CaseStrainer with Vue.js frontend...

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Kill any Python processes that might be using port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING 2^>nul') do (
    echo Killing process with PID %%a
    taskkill /F /PID %%a 2>nul
)

REM Start the application using the full path to Python
echo Starting CaseStrainer on port 5000...
"%~dp0.venv\Scripts\python.exe" "%~dp0app_final_vue_simple.py" --host=0.0.0.0 --port=5000

pause
