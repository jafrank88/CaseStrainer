@echo off
echo Starting CaseStrainer for Nginx...

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Kill any Python processes that might be using port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing process with PID %%a
    taskkill /F /PID %%a 2>nul
)

REM Activate the virtual environment and run the application
echo Starting CaseStrainer on port 5000...
call .venv\Scripts\activate.bat
python app_nginx_compatible.py --host=0.0.0.0 --port=5000

pause
