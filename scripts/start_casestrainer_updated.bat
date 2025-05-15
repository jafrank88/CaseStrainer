@echo off
echo Starting CaseStrainer with updated configuration...

REM Check and stop any Windows Nginx instances
echo Checking for Windows Nginx instances...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
) else (
    echo No Windows Nginx instances found.
)

REM Check if Docker is running
echo Checking Docker status...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Docker does not appear to be running. Nginx proxy may not be available.
) else (
    echo Docker is running. Checking Nginx container...
    docker ps | find "docker-nginx-1" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Docker Nginx container not found. External access may not work.
    ) else (
        echo Docker Nginx container is running.
    )
)

REM Check if port 5001 is in use and kill any conflicting processes
echo Checking if port 5000 is available...
netstat -ano | find ":5000" | find "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":5000" ^| find "LISTENING"') do (
        echo Killing process using port 5000 (PID: %%a)...
        taskkill /F /PID %%a
    )
) else (
    echo Port 5000 is available.
)

REM Kill any running Python processes
echo Stopping any running Python instances...
taskkill /F /IM python.exe 2>NUL

REM Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul

REM Start CaseStrainer with the correct host and port
echo Starting CaseStrainer application...
python app_final_vue.py --host=0.0.0.0 --port=5000

echo CaseStrainer startup complete.
