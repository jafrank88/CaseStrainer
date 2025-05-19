@echo off
setlocal EnableDelayedExpansion

REM Logging setup
set LOGFILE=logs\deploy.log
set ERRLOG=logs\deploy_error.log

REM Timestamp for this run
for /f "tokens=1-4 delims=/ " %%a in ("%date% %time%") do set NOW=%%a-%%b-%%c_%%d

echo ===================================================
echo =================================================== >> %LOGFILE%
echo CaseStrainer Production Start Script (Unified Vue.js + API)
echo CaseStrainer Production Start Script (Unified Vue.js + API) >> %LOGFILE%
echo Started at %NOW%
echo Started at %NOW% >> %LOGFILE%
echo ===================================================
echo =================================================== >> %LOGFILE%
echo.
echo. >> %LOGFILE%

REM Clear previous logs for a fresh start
if exist %LOGFILE% del %LOGFILE%
if exist %ERRLOG% del %ERRLOG%

REM Set environment variables
set FLASK_APP=src/app.py
set HOST=0.0.0.0
set PORT=5000
set FLASK_ENV=production
set FLASK_DEBUG=0
set USE_WAITRESS=True

REM Create required directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Ensure Flask startup log is cleared
set FLASK_LOG=logs\flask_startup.log
if exist %FLASK_LOG% del %FLASK_LOG%

REM Pull latest code from GitHub before starting
 echo Pulling latest code from GitHub...
 git pull origin main
 if %errorLevel% neq 0 (
     echo WARNING: Failed to pull latest code from GitHub.
     echo Please check your network connection or resolve merge conflicts.
     pause
 )

REM Step 1: Stop any existing processes
 echo Step 1: Stopping existing processes...
 echo.

REM Stop Windows Nginx if running
 echo Checking for Windows Nginx...
 tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
 if !ERRORLEVEL! == 0 (
     echo Stopping Windows Nginx...
     taskkill /F /IM nginx.exe
     echo Windows Nginx stopped.
 ) else (
     echo Windows Nginx is not running.
 )

REM Check if port 5000 is already in use
 echo Checking if port 5000 is in use...
 netstat -ano | findstr :5000 | findstr LISTENING
 if !ERRORLEVEL! == 0 (
     echo Port 5000 is in use. Attempting to kill the process...
     for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
         echo Killing process with PID %%a
         taskkill /F /PID %%a
     )
     echo Process killed.
     timeout /t 2 /nobreak >nul
 ) else (
     echo Port 5000 is available.
 )

REM Stop any running Flask (CaseStrainer) processes
 echo Checking for Flask (CaseStrainer) processes...
 for /f "tokens=2 delims==" %%a in ('wmic process where "CommandLine like '%%app_final_vue.py%%' and Name='python.exe'" get ProcessId /value 2^>nul ^| findstr ProcessId') do (
     set PID=%%a
     echo Found Flask process with PID !PID! running app_final_vue.py. Killing it...
     taskkill /F /PID !PID!
 )
 for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
     echo Killing python process using port 5000 with PID %%a
     taskkill /F /PID %%a
 )
 echo Flask (CaseStrainer) processes stopped if any were running.

REM Step 1: Stop any existing processes
echo Step 1: Stopping existing processes...
echo.

REM Stop Windows Nginx if running
echo Checking for Windows Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if !ERRORLEVEL! == 0 (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
)

REM Stop Python server if running
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if !ERRORLEVEL! == 0 (
    echo Stopping existing Python server...
    taskkill /F /IM python.exe
)

REM Step 1.5: Build the Vue.js frontend if source files are newer than dist
pushd casestrainer-vue
if not exist "package.json" (
    echo ERROR: package.json not found in casestrainer-vue. Cannot build frontend.
    popd
    goto vue_build_fail
)
where npm >nul 2>nul
if not !ERRORLEVEL! == 0 (
    echo ERROR: npm is not installed or not in PATH. Please install Node.js and npm.
    popd
    goto vue_build_fail
)
REM Find newest file in src and dist, suppress 'File Not Found' errors
set "NEWESTSRC="
for /f "delims=" %%F in ('dir /b /s /a-d src 2^>nul') do set "NEWESTSRC=%%F"
if not defined NEWESTSRC (
    echo ERROR: No source files found in casestrainer-vue\src. Cannot build frontend.
    popd
    goto vue_build_fail
)
set "NEWESTDIST="
if exist dist (
    for /f "delims=" %%F in ('dir /b /s /a-d dist 2^>nul') do set "NEWESTDIST=%%F"
)
if not defined NEWESTDIST (
    echo No frontend build found. Building Vue.js frontend...
    call npm install
    call npm audit fix
    call npm run build
) else (
    for %%I in ("%NEWESTSRC%") do set "SRCDATE=%%~tI"
    for %%I in ("%NEWESTDIST%") do set "DISTDATE=%%~tI"
    if "%SRCDATE%" GTR "%DISTDATE%" (
        echo Source files have changed since last build. Rebuilding Vue.js frontend...
        call npm install
        call npm audit fix
        call npm run build
    ) else (
        echo Vue.js frontend is up to date. Skipping build.
    )
)
popd
goto after_vue_build
:vue_build_fail
echo Failed to build Vue.js frontend. Exiting.
exit /b 1
:after_vue_build

REM Step 2: Start the Flask application
echo.
echo Step 2: Starting Flask application...
echo.

REM Start the Flask application in a new window
echo Starting Flask application on port 5000...
REM Redirect output to logs\flask_startup.log
start "CaseStrainer Flask" cmd /c "python src\app_final_vue.py --host=%HOST% --port=%PORT% --use-waitress --env=production > %FLASK_LOG% 2>&1"

REM Wait for Flask to start
echo Waiting for Flask application to start...
timeout /t 5 /nobreak >nul

REM Check if Flask started and port 5000 is listening
netstat -ano | findstr :5000 | findstr LISTENING >nul
if not "%ERRORLEVEL%"=="0" (
    echo ERROR: Flask did not start or port 5000 is not listening!
    if exist logs\flask_startup.log (
        echo ===== Flask Startup Log =====
        type logs\flask_startup.log
        echo ============================
    ) else (
        echo No Flask startup log found. Try running the Flask command manually for more details.
    )
    pause
    exit /b 1
) else (
    echo Flask is running on port 5000.
)

REM Step 3: Start Nginx
echo.
echo Step 3: Starting Nginx...
echo.

REM Ensure required Nginx directories exist
if not exist "nginx-1.27.5\logs" mkdir "nginx-1.27.5\logs"
if not exist "nginx-1.27.5\temp" mkdir "nginx-1.27.5\temp"
if not exist "nginx-1.27.5\temp\client_body_temp" mkdir "nginx-1.27.5\temp\client_body_temp"
if not exist "nginx-1.27.5\temp\fastcgi_temp" mkdir "nginx-1.27.5\temp\fastcgi_temp"
if not exist "nginx-1.27.5\temp\proxy_temp" mkdir "nginx-1.27.5\temp\proxy_temp"
if not exist "nginx-1.27.5\temp\scgi_temp" mkdir "nginx-1.27.5\temp\scgi_temp"
if not exist "nginx-1.27.5\temp\uwsgi_temp" mkdir "nginx-1.27.5\temp\uwsgi_temp"
cd "nginx-1.27.5"
echo Starting Windows Nginx...
"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe" -c "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\conf\nginx.conf"

REM Wait for Nginx to start
ping 127.0.0.1 -n 3 >nul
cd "%~dp0"

REM Health check: check if Flask app is reachable
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:5000/' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { Write-Output 'ERROR' }" | findstr 200 >nul
if not "%ERRORLEVEL%"=="0" (
    echo ERROR: Flask app is not reachable at http://localhost:5000/
    echo Check Flask logs and configuration.
    pause
)

REM Health check: check if Nginx proxy is reachable
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost/casestrainer/' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { Write-Output 'ERROR' }" | findstr 200 >nul
if not "%ERRORLEVEL%"=="0" (
    echo ERROR: Nginx proxy is not reachable at http://localhost/casestrainer/
    echo Check Nginx logs and configuration.
    pause
)

echo.
echo ===================================================
echo CaseStrainer deployment complete!
echo ===================================================
echo.
echo The application is now accessible at:
echo - External: https://wolf.law.uw.edu/casestrainer/
echo - Local: http://localhost/casestrainer/
echo.
echo Press any key to exit this script (the application will continue running)...
pause >nul
