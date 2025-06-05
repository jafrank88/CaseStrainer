@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Production Startup Script
REM USAGE: Double-click or run from the CaseStrainer root directory.
REM LOG: All output is logged to casestrainer_deploy.log
REM REQUIREMENTS: Node.js, npm, Python 3.x, git, Docker, PowerShell
REM TROUBLESHOOTING: Check casestrainer_deploy.log for errors.
REM Exit code 0 = success, nonzero = failure.
REM ===================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "LOG_DIR=logs"
set "LOGFILE=%LOG_DIR%\casestrainer_%DATE:/=-%_%TIME::=-%.log"
set "ENV_FILE=.env.production"

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

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

REM === Activate Python Virtual Environment ===
if exist ".venv\Scripts\activate" (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate
) else (
    echo Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    
    echo Installing required Python packages...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

REM === Set Environment Variables ===
if exist "%ENV_FILE%" (
    echo Loading environment variables from %ENV_FILE%
    for /f "usebackq tokens=*" %%i in ("%ENV_FILE%") do (
        for /f "tokens=1* delims==" %%a in ("%%i") do (
            if not "%%a"=="" if not "%%a"=="#" if not "%%a"=="" set "%%a=%%b"
        )
    )
) else (
    echo Warning: %ENV_FILE% not found. Using default settings. >> "%LOGFILE%"
)

REM === Activate Python venv ===
call C:\Users\jafrank\venv_casestrainer\Scripts\activate.bat

REM Set required environment variables if not already set
if "%FLASK_APP%"=="" set FLASK_APP=src/app_final_vue.py
if "%FLASK_ENV%"=="" set FLASK_ENV=production
if "%SECRET_KEY%"=="" set SECRET_KEY=insecure-secret-key-change-in-production

echo Environment: %FLASK_ENV% >> "%LOGFILE%"

REM === Directory Creation ===
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM === Vue Build Check and Auto-Build with Checksum ===
echo Checking Vue.js source for changes...
pushd casestrainer-vue-new

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

REM === CREATE TEMPORARY SCRIPT FOR BACKEND ===
echo @echo off > start_backend.bat
echo call .venv\Scripts\activate >> start_backend.bat
echo set FLASK_APP=src.app_final_vue:app >> start_backend.bat

REM === START BACKEND WITH WAITRESS ===
if "%DEBUG_MODE%"=="True" (
    echo [DEBUG] Starting backend in DEBUG mode...
    echo set FLASK_DEBUG=1 >> start_backend.bat
    echo set FLASK_ENV=development >> start_backend.bat
echo set FLASK_DEBUG=1 >> start_backend.bat
echo python -m flask run --host=%HOST% --port=%PORT% >> start_backend.bat
    start "CaseStrainer Backend (Debug)" cmd /k "start_backend.bat & echo. & echo Backend process ended. Press any key to close... & pause"
) else if "%USE_CHEROOT%"=="True" (
    echo Starting backend with CherryPy...
    echo python -m waitress --host=%HOST% --port=%PORT% --threads=%THREADS% src.app_final_vue:app >> start_backend.bat
    start "CaseStrainer Backend" cmd /k "start_backend.bat & echo. & echo Backend process ended. Press any key to close... & pause"
) else (
    echo Starting backend with Waitress...
    echo python -m waitress --host=%HOST% --port=%PORT% --threads=%THREADS% src.app_final_vue:app >> start_backend.bat
    start "CaseStrainer Backend" cmd /k "start_backend.bat & echo. & echo Backend process ended. Press any key to close... & pause"
)

REM === Start Nginx ===
echo [%TIME%] Starting Nginx...
if exist "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" (
    "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" -c "%SCRIPT_DIR%nginx.conf"
) else (
    start "" /B nginx.exe -c "%SCRIPT_DIR%nginx.conf"
)

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
set DEBUG_MODE=False

REM Check for debug flag
if "%1"=="--debug" (
    set DEBUG_MODE=True
    shift
)

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

:: Set PYTHONPATH to include the project root directory
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

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
    py -3.13 -m waitress --host=%HOST% --port=%PORT% --threads=%THREADS% src.app_final_vue:app
)

pause