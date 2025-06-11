@echo off
echo ===================================================
echo FLEXIBLE DEPLOYMENT: CaseStrainer (Dev/Prod)
echo ===================================================
echo.

REM Check if Windows Nginx is running and stop it
echo Checking for Windows Nginx...
set NGINX_PATH=C:\Users\jafrank\Downloads\nginx-1.27.5\nginx-1.27.5\nginx.exe

if exist "%NGINX_PATH%" (
    tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo Stopping Windows Nginx...
        taskkill /F /IM nginx.exe
        echo Windows Nginx stopped.
    ) else (
        echo Windows Nginx is not running.
    )
) else (
    echo Windows Nginx not found at expected path. Checking for any nginx processes...
    tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo Found nginx.exe process. Stopping it...
        taskkill /F /IM nginx.exe
    )
)

REM Check if port 5000 is already in use
echo Checking if port 5000 is in use...
netstat -ano | findstr :5000 | findstr LISTENING >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    
    REM Verify port was freed
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr :5000 | findstr LISTENING >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        echo WARNING: Failed to free port 5000. Please close the application using this port manually.
        
        REM Try one more approach - use the Windows Resource Monitor technique
        echo Trying alternative method to free port 5000...
        for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
            echo Found process using port 5000: PID %%a
            taskkill /F /PID %%a >nul 2>&1
            if "%ERRORLEVEL%"=="0" (
                echo Successfully terminated process with PID %%a
            ) else (
                echo Failed to terminate process with PID %%a
            )
        )
        
        REM Check one more time
        timeout /t 2 /nobreak >nul
        netstat -ano | findstr :5000 | findstr LISTENING >nul 2>&1
        if "%ERRORLEVEL%"=="0" (
            echo WARNING: Still unable to free port 5000.
            echo Press any key to continue anyway or CTRL+C to abort...
            pause >nul
        ) else (
            echo Port 5000 is now available.
        )
    ) else (
        echo Port 5000 is now available.
    )
) else (
    echo Port 5000 is available.
)

REM Verify Docker is running and Docker Nginx container is active
echo Checking if Docker is running...
docker ps >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo Docker is running. Checking Docker Nginx container...
    docker ps | findstr "docker-nginx-1" >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        echo Docker Nginx container is running.
        echo Restarting Docker Nginx container to ensure it picks up the latest changes...
        docker restart casestrainer-nginx
        echo Docker Nginx container restarted.
    ) else (
        echo WARNING: Docker Nginx container not found or not running.
        echo This will prevent external access to CaseStrainer through https://wolf.law.uw.edu/casestrainer/
        echo.
        echo Press any key to continue anyway or CTRL+C to abort...
        pause >nul
    )
) else (
    echo WARNING: Docker is not running. The Docker Nginx container will not be accessible.
    echo This will prevent external access to CaseStrainer through https://wolf.law.uw.edu/casestrainer/
    echo.
    echo Press any key to continue anyway or CTRL+C to abort...
    pause >nul
)

REM Create required directories
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"
if not exist "src\flask_session" mkdir "src\flask_session"

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
SET USE_WAITRESS=True
SET APPLICATION_ROOT=/casestrainer

REM Check if development mode is requested
if "%1"=="dev" (
    echo Starting in DEVELOPMENT mode...
    SET FLASK_ENV=development
    SET FLASK_DEBUG=1
    
    REM Try different Python installations in order of preference
    IF EXIST ".venv\Scripts\python.exe" (
        echo Using Python from virtual environment
        call .venv\Scripts\activate.bat
        python -m flask run --host=0.0.0.0 --port=5000
    ) ELSE (
        python -m flask run --host=0.0.0.0 --port=5000
    )
) else (
    echo Starting in PRODUCTION mode...
    SET FLASK_ENV=production
    SET FLASK_DEBUG=0
    echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
    echo Local access will be available at: http://127.0.0.1:5000/
    echo.
    
    REM Try different Python installations in order of preference
    IF EXIST ".venv\Scripts\python.exe" (
        echo Using Python from virtual environment
        call .venv\Scripts\activate.bat
        python src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
    ) ELSE IF EXIST "D:\Python\python.exe" (
        echo Using Python from D:\Python
        "D:\Python\python.exe" src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
    ) ELSE IF EXIST "C:\Python313\python.exe" (
        echo Using Python from C:\Python313
        "C:\Python313\python.exe" src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
    ) ELSE (
        echo Python not found, trying system Python
        python src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress --env=production
    )
)

echo.
echo CaseStrainer stopped.
echo.
echo If you need to restart the application, run this script again.
echo External access URL: https://wolf.law.uw.edu/casestrainer/
echo.
