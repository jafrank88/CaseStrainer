@echo off
echo ===================================================
echo Starting CaseStrainer with Reverse Proxy...
echo ===================================================
echo.

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

REM Check if port 8080 is already in use
echo Checking if port 8080 is in use...
netstat -ano | findstr :8080 | findstr LISTENING
if "%ERRORLEVEL%"=="0" (
    echo Port 8080 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
) else (
    echo Port 8080 is available.
)

REM Start the Flask application with Vue.js integration on port 5000 with host 0.0.0.0
echo Starting Flask application with Vue.js integration on port 5000 with host 0.0.0.0...
cd "%~dp0"

REM Set environment variable to use Cheroot
SET USE_CHEROOT=True

REM Start the CaseStrainer application in a new window
start "CaseStrainer" cmd /c "IF EXIST ".venv\Scripts\python.exe" (call .venv\Scripts\activate.bat && python app_final_vue.py --host=0.0.0.0 --port=5000 --use-cheroot) ELSE (python app_final_vue.py --host=0.0.0.0 --port=5000 --use-cheroot)"

REM Wait for the CaseStrainer application to start
echo Waiting for CaseStrainer to start...
timeout /t 5 /nobreak

REM Start the reverse proxy in this window
echo Starting reverse proxy on port 8080...
IF EXIST ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    python reverse_proxy.py --proxy-port=8080
) ELSE (
    python reverse_proxy.py --proxy-port=8080
)

echo.
echo Reverse proxy stopped.
echo.
echo If you need to restart the application, run this script again.
