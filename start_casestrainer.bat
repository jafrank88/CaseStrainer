@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Startup Script
REM USAGE: Double-click or run from the CaseStrainer root directory.
REM LOG: All output is logged to casestrainer_deploy.log
REM REQUIREMENTS: Node.js, npm, Python 3.x, git, Docker, PowerShell
REM TROUBLESHOOTING: Check casestrainer_deploy.log for errors.
REM Exit code 0 = success, nonzero = failure.
REM ===================================================

set LOGFILE=casestrainer_deploy.log

REM === Tool Checks ===
where node >nul 2>&1 || (echo [ERROR] Node.js is not installed! | tee -a %LOGFILE% & exit /b 1)
where npm >nul 2>&1 || (echo [ERROR] npm is not installed! | tee -a %LOGFILE% & exit /b 1)
where python >nul 2>&1 || (echo [ERROR] Python is not installed! | tee -a %LOGFILE% & exit /b 1)
where git >nul 2>&1 || (echo [ERROR] git is not installed! | tee -a %LOGFILE% & exit /b 1)
where docker >nul 2>&1 || (echo [ERROR] Docker is not installed! | tee -a %LOGFILE% & exit /b 1)
where powershell >nul 2>&1 || (echo [ERROR] PowerShell is not installed! | tee -a %LOGFILE% & exit /b 1)

REM === Log Start ===
echo =================================================== >> %LOGFILE%
echo [%DATE% %TIME%] Starting CaseStrainer >> %LOGFILE%

REM === Relaunch in CMD if running in PowerShell (but only once) ===
if defined PSModulePath (
    if not defined CASESTRAINER_CMD (
        set CASESTRAINER_CMD=1
        echo Detected PowerShell. Relaunching in cmd.exe...
        cmd /c "%~f0" %*
        exit /b
    )
)

REM === Activate Python venv ===
call C:\Users\jafrank\venv_casestrainer\Scripts\activate.bat
set FLASK_APP=src/app_final_vue.py

REM ===================================================
REM CaseStrainer Startup Script
REM ===================================================
REM
REM USAGE:
REM   Double-click or run this script from the CaseStrainer root directory.
REM
REM DESCRIPTION:
REM   This is the ONLY supported script for starting or restarting CaseStrainer.
REM   - Stops any conflicting Windows Nginx instances
REM   - Verifies Docker and Docker Nginx container status (if relevant)
REM   - Ensures required directories exist
REM   - Builds Vue.js frontend if needed
REM   - Ensures port 5000 is available and kills any conflicting processes
REM   - Starts CaseStrainer with proper host (0.0.0.0) and port (5000) settings
REM
REM   All other batch files are deprecated and should not be used for normal workflow.
REM ===================================================

REM === CONFIGURATION ===

REM === Directory Creation ===
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM === Vue Build Check and Auto-Build with Checksum ===
echo Checking Vue.js source for changes...
pushd casestrainer-vue

REM === Clear Vue/Node build cache ===
if exist node_modules\.cache (
    echo Deleting node_modules\.cache ...
    rmdir /s /q node_modules\.cache
)

REM === Convert all .vue files to UTF-8 (without BOM) ===
powershell -Command "Get-ChildItem -Recurse -Filter *.vue | ForEach-Object { $c = Get-Content $_.FullName; [System.IO.File]::WriteAllLines($_.FullName, $c, (New-Object System.Text.UTF8Encoding($false))) }"

REM === Find duplicate EnhancedValidator.vue files ===
dir /s /b EnhancedValidator.vue

REM Concatenate all relevant files and compute hash
(for /r %%f in (*.vue *.js *.json) do type "%%f") > all_vue_files.tmp
certutil -hashfile all_vue_files.tmp SHA256 > current_vue_checksum.txt
del all_vue_files.tmp

REM Compare with previous checksum
if exist vue_checksum.txt (
    fc /b current_vue_checksum.txt vue_checksum.txt > nul
    if errorlevel 1 (
        echo Vue source changed, rebuilding...
        if not exist node_modules (
            echo Running npm install...
            call npm install
            if errorlevel 1 (
                echo ERROR: npm install failed. Please check npm logs.
                pause
                popd
                exit /b 1
            )
        )
        call npm run build
        if errorlevel 1 (
            echo ERROR: npm run build failed. Please check npm logs.
            pause
            popd
            exit /b 1
        )
        copy /y current_vue_checksum.txt vue_checksum.txt > nul
    ) else (
        echo Vue source unchanged, skipping build.
    )
) else (
    echo No previous checksum, building Vue frontend...
    if not exist node_modules (
        echo Running npm install...
        call npm install
        if errorlevel 1 (
            echo ERROR: npm install failed. Please check npm logs.
            pause
            popd
            exit /b 1
        )
    )
    call npm run build
    if errorlevel 1 (
        echo ERROR: npm run build failed. Please check npm logs.
        pause
        popd
        exit /b 1
    )
    copy /y current_vue_checksum.txt vue_checksum.txt > nul
)
del current_vue_checksum.txt
popd

REM === Log Cleanup (Optional) ===
if exist logs\deploy.log del logs\deploy.log
if exist logs\deploy_error.log del logs\deploy_error.log

set NGINX_DIR=%~dp0nginx-1.27.5
set PROD_CONF=%NGINX_DIR%\conf\nginx.conf
set TEST_CONF=%NGINX_DIR%\conf\nginx_test.conf
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_CHEROOT=True

REM === CHOOSE NGINX CONFIGURATION ===
set NGINX_CONFIG=%PROD_CONF%
if /i "%1"=="test" set NGINX_CONFIG=%TEST_CONF%

REM === STOP EXISTING NGINX ===
echo Checking for running Nginx...
tasklist | find /i "nginx.exe" >nul 2>&1
if %errorlevel%==0 (
    echo Stopping existing Nginx instance...
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit
    timeout /t 2 >nul
    cd /d "%~dp0"
)

REM === STOP EXISTING BACKEND ===
echo Stopping any running CaseStrainer backend processes...
tasklist /fi "imagename eq python.exe" /fo csv | findstr /i "python.exe" > temp_processes.txt
for /f "tokens=1,2 delims=," %%a in (temp_processes.txt) do (
    set "process=%%a"
    set process=!process:"=!
    set "pid=%%b"
    set pid=!pid:"=! 
    wmic process where "ProcessId=!pid!" get CommandLine | findstr /i "app.py" > nul
    if !errorlevel! equ 0 (
        echo Stopping backend process with PID: !pid!
        taskkill /f /pid !pid! > nul 2>&1
    )
)
del temp_processes.txt > nul 2>&1

REM === START BACKEND WITH WAITRESS ===
echo Starting CaseStrainer backend (Unified Vue.js + API) on port %PORT% with Waitress...
REM Start backend in a new window and keep it open after exit
start "CaseStrainer Backend" cmd /k "python src\app_final_vue.py --use-waitress --host=%HOST% --port=%PORT% --threads=%THREADS% & echo. & echo Backend process ended. Press any key to close. & pause"

REM === START NGINX ===
echo Starting Nginx with config: %NGINX_CONFIG%
cd /d "%NGINX_DIR%"
REM Start Nginx in a new window and keep it open after exit
start "Nginx" cmd /k "nginx.exe -c "%NGINX_CONFIG%" & echo. & echo Nginx process ended. Press any key to close. & pause"
cd /d "%~dp0"

echo =============================================
echo   CaseStrainer backend and Nginx started!
echo =============================================
pause
endlocal

echo ===================================================
echo CaseStrainer Startup Script
echo ===================================================
echo.

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_CHEROOT=True

:: Create required directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

:: Check if port 5000 is available
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 5000 is already in use.
    echo Stopping any processes using port 5000...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo Killing process with PID: %%a
        taskkill /f /pid %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
)

:: Install/update dependencies
echo Installing dependencies...
py -3.13 -m pip install -r requirements.txt

:: Check if development mode is requested
if "%1"=="dev" (
    echo Starting in DEVELOPMENT mode...
    set FLASK_ENV=development
    set FLASK_DEBUG=1
    py -3.13 -m flask run --host=%HOST% --port=%PORT%
) else (
    echo Starting in PRODUCTION mode...
    set FLASK_ENV=production
    echo External access will be available at: https://wolf.law.uw.edu/casestrainer/
    echo Local access will be available at: http://127.0.0.1:5000
    echo.
    py -3.13 src/app_final_vue.py --host=%HOST% --port=%PORT%
)

pause