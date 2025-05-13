@echo off
echo ===================================================
echo CaseStrainer Vue.js Startup Script (System Python)
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

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Set environment variables
set "HOST=0.0.0.0"
set "PORT=5000"
set "USE_CHEROOT=True"

REM Unset any PYTHON_PATH environment variable that might be causing issues
set "PYTHON_PATH="

REM Start the CaseStrainer Vue.js frontend using the system Python
echo Starting CaseStrainer Vue.js frontend on port 5000...
echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
echo Local access will be available at: http://127.0.0.1:5000

REM Try to find Python in the PATH
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Found Python in PATH
    python app_final_vue.py --host=0.0.0.0 --port=5000
) else (
    echo Python not found in PATH, checking common locations...
    
    if exist "C:\Python313\python.exe" (
        echo Found Python at C:\Python313\python.exe
        "C:\Python313\python.exe" app_final_vue.py --host=0.0.0.0 --port=5000
    ) else if exist ".venv\Scripts\python.exe" (
        echo Found Python in virtual environment
        call .venv\Scripts\activate.bat
        python app_final_vue.py --host=0.0.0.0 --port=5000
    ) else (
        echo Python not found. Please install Python and try again.
        exit /b 1
    )
)

echo.
echo CaseStrainer stopped.
