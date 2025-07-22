@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Production Start Script
:: ===================================================
:: This script starts the CaseStrainer application in production mode
:: For development, use start_development.bat instead
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "NGINX_DIR=%SCRIPT_DIR%nginx"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx.conf"
set "FLASK_APP=app_final_vue.py"
set "FLASK_RUN_HOST=0.0.0.0"

:: Default to production environment if not specified
if "%1"=="" (
    set "ENV=production"
) else (
    set "ENV=%1"
)

:: Set environment-specific variables
if /i "%ENV%"=="development" (
    set "FLASK_ENV=development"
    set "FLASK_RUN_PORT=5001"
    set "FLASK_DEBUG=1"
    set "LOG_LEVEL=DEBUG"
) else (
    set "FLASK_ENV=production"
    set "FLASK_RUN_PORT=5000"
    set "FLASK_DEBUG=0"
    set "LOG_LEVEL=INFO"
)

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\casestrainer_%TIMESTAMP%.log"

:: Function to log messages
:log
set "MESSAGE=%~1"
echo [%TIME%] %MESSAGE%
(
echo [%TIME%] %MESSAGE%
) >> "%LOG_FILE%"
goto :eof

:: Redirect output to log file
echo Starting CaseStrainer at %TIME%... > "%LOG_FILE%"
echo Log file: %LOG_FILE% >> "%LOG_FILE%"

:: Display initial message
echo [%TIME%] Starting CaseStrainer...
echo [%TIME%] Log file: %LOG_FILE%

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :log "ERROR: This script requires administrator privileges."
    call :log "Please right-click on the script and select 'Run as administrator'."
    pause
    exit /b 1
)

:: Kill any existing Python and Nginx processes
call :log "Stopping any existing Python and Nginx processes..."
:: Stop any existing processes
call :log "Stopping any existing processes..."
taskkill /F /IM nginx.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1

:: Wait for processes to terminate
timeout /t 2 /nobreak >nul

:: Check if backend port is available
call :log "Checking if port %PROD_BACKEND_PORT% is available..."
netstat -ano | find ":%PROD_BACKEND_PORT%" | find "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :log "Port %PROD_BACKEND_PORT% is in use. Attempting to free..."
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%PROD_BACKEND_PORT%" ^| find "LISTENING"') do (
        call :log "Killing process using port %PROD_BACKEND_PORT% (PID: %%a)"
        taskkill /F /PID %%a >nul 2>&1
    )
)

:: Create required directories
call :log "Creating required directories..."
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%BACKEND_DIR%\uploads" mkdir "%BACKEND_DIR%\uploads"
if not exist "%BACKEND_DIR%\casestrainer_sessions" mkdir "%BACKEND_DIR%\casestrainer_sessions"

:: Activate Python virtual environment
call :log "Activating Python virtual environment..."
if not exist "%VENV_ACTIVATE%" (
    call :error "Virtual environment not found at %VENV_ACTIVATE%"
)
call "%VENV_ACTIVATE%"

:: Install Python dependencies
call :log "Installing Python dependencies..."
python -m pip install --upgrade pip
if exist "%BACKEND_DIR%\requirements.txt" (
    python -m pip install -r "%BACKEND_DIR%\requirements.txt"
) else (
    call :log "Warning: requirements.txt not found in %BACKEND_DIR%"
)

:: Build Vue.js frontend
if exist "%FRONTEND_DIR%" (
    call :log "Building Vue.js frontend..."
    pushd "%FRONTEND_DIR%"
    
    :: Clear Vue/Node build cache
    if exist "node_modules\.cache" (
        call :log "Clearing Vue build cache..."
        rmdir /s /q "node_modules\.cache"
    )
    
    :: Install npm dependencies
    if not exist "node_modules" (
        call :log "Installing npm dependencies..."
        call npm install
        if %ERRORLEVEL% NEQ 0 call :error "npm install failed"
    )
    
    :: Build Vue app
    call :log "Building Vue application..."
    call npm run build
    if %ERRORLEVEL% NEQ 0 call :error "Vue build failed"
    
    :: Copy built files to static directory
    call :log "Copying built files to static directory..."
    if not exist "%BACKEND_DIR%\static" mkdir "%BACKEND_DIR%\static"
    xcopy /Y /E /I /Q "%FRONTEND_DIR%\dist\*" "%BACKEND_DIR%\static\"
    
    popd
else
    call :log "Warning: Vue.js frontend directory not found at %FRONTEND_DIR%"
    call :log "Skipping frontend build. Using existing static files if available."
fi

:: Configure Nginx
call :log "Configuring Nginx..."
if not exist "%NGINX_DIR%\logs" mkdir "%NGINX_DIR%\logs"
if not exist "%NGINX_DIR%\conf" mkdir "%NGINX_DIR%\conf"

:: Create Nginx configuration
echo Configuring Nginx...
(
echo worker_processes 1;
echo;
echo events {
echo     worker_connections 1024;
echo }
echo;
echo http {
echo     include       mime.types;
echo     default_type  application/octet-stream;
echo     sendfile      on;
echo     keepalive_timeout  65;
echo     client_max_body_size 100M;
echo     server_tokens off;
echo     gzip on;
echo     gzip_types text/plain text/css application/json application/javascript application/x-javascript text/xml application/xml application/xml+rss text/javascript;
echo;
echo     # HTTP server - redirect to HTTPS
echo     server {
echo         listen       80;
echo         server_name  wolf.law.uw.edu localhost 127.0.0.1;
echo         return 301 https://$host$request_uri;
echo     }
echo;
echo     # HTTPS server
echo     server {
echo         listen       443 ssl http2;
echo         server_name  wolf.law.uw.edu localhost 127.0.0.1;
echo;
echo         ssl_certificate      D:/CaseStrainer/ssl/WolfCertBundle.crt;
echo         ssl_certificate_key  D:/CaseStrainer/ssl/wolf.law.uw.edu.key;
echo         ssl_session_cache    shared:SSL:1m;
echo         ssl_session_timeout  5m;
echo         ssl_ciphers  HIGH:!aNULL:!MD5;
echo         ssl_prefer_server_ciphers  on;
echo;
echo         # Security headers
echo         add_header X-Content-Type-Options nosniff;
echo         add_header X-Frame-Options SAMEORIGIN;
echo         add_header X-XSS-Protection "1; mode=block";
echo         add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
echo;
echo         # Logging
echo         access_log  logs/casestrainer_access.log;
echo         error_log   logs/casestrainer_error.log;
echo;
echo         # Handle /casestrainer/
echo         location /casestrainer/ {
echo             alias "%BACKEND_DIR%/static/";
echo             try_files $uri $uri/ /casestrainer/index.html;
echo             expires -1;
echo             add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate";
echo             add_header X-Content-Type-Options nosniff;
echo             add_header X-Frame-Options SAMEORIGIN;
echo             add_header X-XSS-Protection "1; mode=block";
echo         }
echo;
echo         # API proxy
echo         location /casestrainer/api/ {
echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo             proxy_set_header X-Forwarded-Prefix /casestrainer;
echo             proxy_set_header X-Forwarded-Port $server_port;
echo             proxy_http_version 1.1;
echo             proxy_set_header Upgrade $http_upgrade;
echo             proxy_set_header Connection "upgrade";
echo             proxy_read_timeout 300s;
echo             proxy_connect_timeout 75s;
echo         }
echo     }
echo }
) > "%NGINX_CONF%"

if %ERRORLEVEL% NEQ 0 call :error "Failed to create Nginx configuration"

:: Start Nginx
call :log "Starting Nginx..."
"%NGINX_EXE%" -c "%NGINX_CONF%"
if %ERRORLEVEL% NEQ 0 call :error "Failed to start Nginx"

:: Start Flask backend
call :log "Starting Flask backend on port %PROD_BACKEND_PORT%..."
start "CaseStrainer Backend" /MIN cmd /c "%VENV_ACTIVATE% && python "%FLASK_APP%" --host=0.0.0.0 --port=%PROD_BACKEND_PORT%"

:: Verify services
call :log "Verifying services..."
timeout /t 5 /nobreak >nul

tasklist /FI "IMAGENAME eq nginx.exe" | find "nginx.exe" >nul
if %ERRORLEVEL% NEQ 0 call :error "Nginx failed to start"

tasklist /FI "IMAGENAME eq python.exe" | find "python" >nul
if %ERRORLEVEL% NEQ 0 call :error "Flask backend failed to start"

:: Final status
call :log ""
call :log "==================================================="
call :log "CaseStrainer Deployment Successful!"
call :log "- Backend: http://localhost:%PROD_BACKEND_PORT%"
call :log "- Frontend: https://wolf.law.uw.edu/casestrainer"
call :log "- Logs: %LOGFILE%"
call :log "==================================================="
call :log ""

goto :eof

:cleanup
call :log "Cleaning up..."
taskkill /F /IM nginx.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
exit /b 1

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM === Tool Checks ===
where python >nul 2>&1 || (echo [ERROR] Python is not installed! | tee -a %LOGFILE% & exit /b 1)
where powershell >nul 2>&1 || (echo [WARNING] PowerShell is not installed! Some features may be limited. | tee -a %LOGFILE%)

REM === Log Start ===
echo =================================================== >> %LOGFILE%
echo [%DATE% %TIME%] Starting CaseStrainer >> %LOGFILE%

REM === Check if running as administrator ===
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Not running as administrator. Some operations might fail.
    echo [WARNING] For full functionality, please run this script as administrator.
)
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

REM Navigate to Vue project directory
pushd "casestrainer-vue-new"

echo ===== Building Vue Frontend =====

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: npm install failed. Please check npm logs.
        pause
        popd
        exit /b 1
    )
)

REM Always build the Vue app in production mode
echo Building Vue frontend for production...
call npm run build
if errorlevel 1 (
    echo ERROR: npm run build failed. Please check npm logs.
    pause
    popd
    exit /b 1
)

popd

echo Vue frontend built successfully.

REM === Log Cleanup (Optional) ===
if exist logs\deploy.log del logs\deploy.log
if exist logs\deploy_error.log del logs\deploy_error.log

set NGINX_DIR=%~dp0nginx
set PROD_CONF=%NGINX_DIR%\conf\nginx.conf
set TEST_CONF=%NGINX_DIR%\conf\nginx_test.conf
set FLASK_APP=src/app_final_vue.py
REM === Configuration ===
set HOST=0.0.0.0
set PORT=5000
set THREADS=10
set USE_WAITRESS=True
set DEBUG_MODE=False

REM Check for debug flag
if "%1"=="--debug" (
    set DEBUG_MODE=True
    shift
)

REM === Stop any existing Nginx instances ===
echo [%TIME%] Stopping any running Nginx instances...
tasklist | find /i "nginx.exe" >nul 2>&1
if %errorlevel%==0 (
    echo Stopping existing Nginx instances...
    taskkill /f /im nginx.exe >nul 2>&1
    timeout /t 2 >nul
)

REM === Stop any existing Python backend processes ===
echo [%TIME%] Stopping any running backend processes...
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do (
    tasklist /fi "PID eq %%i" /fo csv | findstr /i "app.py" >nul
    if !errorlevel! equ 0 (
        echo Stopping backend process with PID: %%i
        taskkill /f /pid %%i >nul 2>&1
    )
)

REM === Create required directories ===
echo [%TIME%] Setting up directories...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "uploads" mkdir "uploads"
if not exist "casestrainer_sessions" mkdir "casestrainer_sessions"

REM === Check if port 5000 is available ===
echo [%TIME%] Checking if port 5000 is available...
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

REM === Install/update dependencies ===
echo [%TIME%] Installing/updating Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM === Start the backend ===
echo [%TIME%] Starting backend...
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

if "%DEBUG_MODE%"=="True" (
    echo [INFO] Starting in DEBUG mode...
    set FLASK_APP=src/app_final_vue.py
    set FLASK_ENV=development
    set FLASK_DEBUG=1
    start "CaseStrainer Backend (Debug)" cmd /k "python -m flask run --host=%HOST% --port=%PORT% & echo. & echo Backend process ended. Press any key to close... & pause"
) else (
    echo [INFO] Starting in PRODUCTION mode...
    if "%USE_WAITRESS%"=="True" (
        start "CaseStrainer Backend" cmd /k "python -m waitress --host=%HOST% --port=%PORT% --threads=%THREADS% src.app_final_vue:app & echo. & echo Backend process ended. Press any key to close... & pause"
    ) else (
        start "CaseStrainer Backend" cmd /k "python -m waitress --host=%HOST% --port=%PORT% --threads=%THREADS% src.app_final_vue:app & echo. & echo Backend process ended. Press any key to close... & pause"
    )
)

REM === Start Nginx ===
echo [%TIME%] Starting Nginx...

if not exist "%NGINX_DIR%\nginx.exe" (
    echo [ERROR] Nginx executable not found at: %NGINX_DIR%\nginx.exe
    pause
    exit /b 1
)

if not exist "%NGINX_CONF%" (
    echo [ERROR] Nginx config file not found at: %NGINX_CONF%
    pause
    exit /b 1
)

echo [INFO] Using Nginx from: %NGINX_DIR%\nginx.exe
echo [INFO] Using config file: %NGINX_CONF%

REM Test Nginx configuration
"%NGINX_DIR%\nginx.exe" -t -c "%NGINX_CONF%" -p "%NGINX_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Nginx configuration test failed. Please check the configuration.
    pause
    exit /b 1
)

REM Start Nginx
start "Nginx" cmd /k "cd /d "%NGINX_DIR%" && nginx.exe -c "%NGINX_CONF%" -p "%NGINX_DIR%" & echo. & echo Nginx process ended. Press any key to close. & pause"

REM === Verify services ===
timeout /t 2 /nobreak >nul

echo.
echo =============================================
echo   CaseStrainer Services Started!
echo =============================================
echo.
echo [INFO] Backend is running on http://%HOST%:%PORT%
echo [INFO] External access: https://wolf.law.uw.edu/casestrainer/
echo [INFO] Local access: http://localhost:5000
echo.
echo [INFO] Logs are available in the 'logs' directory
echo.

REM === Check services status ===
echo [%TIME%] Verifying services...

echo.
echo === Nginx Status ===
tasklist | find /i "nginx.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Nginx is running
) else (
    echo [ERROR] Nginx failed to start!
)

echo.
echo === Backend Status ===
tasklist | find /i "python.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is running
) else (
    echo [ERROR] Backend failed to start!
)

echo.
echo =============================================
echo   Running Automated Tests...
echo =============================================
echo.

:: Set test result tracking
set "ALL_TESTS_PASSED=true"
set "TEST_LOG=%LOG_DIR%\test_results_%TIMESTAMP%.log"

echo [%TIME%] Starting automated tests... > "%TEST_LOG%"
echo [INFO] Test log: %TEST_LOG%"

:: Test 1: Check Flask health endpoint
echo.
echo === Testing Flask Health Endpoint ===
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000/health' -UseBasicParsing -TimeoutSec 5; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Flask health check passed
    echo [%TIME%] SUCCESS: Flask health check passed >> "%TEST_LOG%"
) else (
    echo [ERROR] Flask health check failed
    echo [%TIME%] ERROR: Flask health check failed >> "%TEST_LOG%"
    set "ALL_TESTS_PASSED=false"
)

:: Test 2: Check Nginx homepage
echo.
echo === Testing Nginx Homepage ===
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost' -UseBasicParsing -TimeoutSec 5 -MaximumRedirection 0 -ErrorAction SilentlyContinue; if ($response.StatusCode -eq 301 -or $response.StatusCode -eq 302) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Nginx is redirecting to HTTPS (expected)
    echo [%TIME%] SUCCESS: Nginx homepage check passed >> "%TEST_LOG%"
) else (
    echo [ERROR] Nginx homepage check failed
    echo [%TIME%] ERROR: Nginx homepage check failed >> "%TEST_LOG%"
    set "ALL_TESTS_PASSED=false"
)

:: Test 3: Check application endpoint
echo.
echo === Testing Application Endpoint ===
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000' -UseBasicParsing -TimeoutSec 10; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Application endpoint is accessible
    echo [%TIME%] SUCCESS: Application endpoint check passed >> "%TEST_LOG%"
) else (
    echo [WARNING] Application endpoint check failed (this might be expected if authentication is required)
    echo [%TIME%] WARNING: Application endpoint check failed >> "%TEST_LOG%"
    :: Don't fail the build for this check as it might require authentication
)

:: Display test summary
echo.
echo =============================================
echo   Test Results Summary
echo =============================================
type "%TEST_LOG%"
echo =============================================

if "%ALL_TESTS_PASSED%"=="true" (
    echo [SUCCESS] All critical tests passed!
) else (
    echo [WARNING] Some tests failed. Check the test log for details.
)

echo.
echo =============================================
echo   Startup Complete!
echo =============================================
echo.
echo If you encounter any issues, please check:
echo 1. Nginx error log: %NGINX_DIR%\logs\error.log
echo 2. Application log: %LOG_DIR%\casestrainer_*.log
echo 3. Test log: %TEST_LOG%
echo.

REM Keep the window open
pause

endlocal