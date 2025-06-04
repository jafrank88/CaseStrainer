@echo off
echo ===================================================
echo Starting CaseStrainer with Enhanced Validator...
echo ===================================================
echo.

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

REM Verify Docker is running (required for Docker Nginx container)
echo Checking if Docker is running...
docker ps >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo Docker is running.
) else (
    echo WARNING: Docker may not be running. The Docker Nginx container might not be accessible.
    echo This could prevent external access to CaseStrainer through https://wolf.law.uw.edu/casestrainer/
    echo.
    echo Press any key to continue anyway or CTRL+C to abort...
    pause >nul
)

REM Start the Flask application with Enhanced Validator on port 5000 with host 0.0.0.0
echo Starting Flask application with Enhanced Validator on port 5000 with host 0.0.0.0...
cd "%~dp0"

REM Set environment variable to use Cheroot
SET USE_CHEROOT=True

REM Try different Python installations in order of preference
IF EXIST ".venv\Scripts\python.exe" (
    echo Using Python from virtual environment
    call .venv\Scripts\activate.bat
    python app_final_fixed.py --host=0.0.0.0 --port=5000 --use-cheroot
) ELSE IF EXIST "D:\Python\python.exe" (
    echo Using Python from D:\Python
    "D:\Python\python.exe" app_final_fixed.py --host=0.0.0.0 --port=5000 --use-cheroot
) ELSE IF EXIST "C:\Python313\python.exe" (
    echo Using Python from C:\Python313
    "C:\Python313\python.exe" app_final_fixed.py --host=0.0.0.0 --port=5000 --use-cheroot
) ELSE (
    echo Python not found, trying system Python
    python app_final_fixed.py --host=0.0.0.0 --port=5000 --use-cheroot
)

echo.
echo CaseStrainer stopped.
echo.
echo If you need to restart the application, run this script again.
