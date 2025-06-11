@echo off
setlocal enabledelayedexpansion

:: CaseStrainer Production Server Launcher
:: Full-featured deployment with all configuration options

:: Set up logging
set "LOG_FILE=%~dp0deployment.log"
echo [%DATE% %TIME%] Starting CaseStrainer deployment > "%LOG_FILE%"

:: Function to log messages
:log
echo [%DATE% %TIME%] %* >> "%LOG_FILE%"
echo %*
goto :eof

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

:: Display banner
echo.
echo ================================================
echo    CaseStrainer Production Server
echo    Target: https://wolf.law.uw.edu/casestrainer
echo ================================================
echo Time: %DATE% %TIME%
echo.

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log [ERROR] Please run as administrator
    call :log This is required for production deployment with SSL
    pause
    exit /b 1
)

:: Initialize all base paths
set "CASESTRAINER_DIR=%~dp0"
set "BACKEND_DIR=%CASESTRAINER_DIR%src"
set "FRONTEND_DIR=%CASESTRAINER_DIR%casestrainer-vue-new"
set "NGINX_DIR=%CASESTRAINER_DIR%nginx-1.27.5"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx_production.conf"
set "NGINX_LOGS=%NGINX_DIR%\logs"
set "BUILD_LOG=%TEMP%\casestrainer_build.log"

:: Display paths for debugging
call :log [DEBUG] CASESTRAINER_DIR: %CASESTRAINER_DIR%
call :log [DEBUG] BACKEND_DIR: %BACKEND_DIR%
call :log [DEBUG] FRONTEND_DIR: %FRONTEND_DIR%
call :log [DEBUG] NGINX_DIR: %NGINX_DIR%
call :log [DEBUG] NGINX_EXE: %NGINX_EXE%
call :log [DEBUG] NGINX_CONF: %NGINX_CONF%
call :log [DEBUG] Current directory: %CD%
call :log [DEBUG] Looking for app_final_vue.py in: %BACKEND_DIR%\app_final_vue.py

:: Verify backend directory exists
if not exist "%BACKEND_DIR%" (
    call :log [ERROR] Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

:: Verify frontend directory exists
if not exist "%FRONTEND_DIR%" (
    call :log [ERROR] Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

:: Read configuration from config.ini
for /f "tokens=1,2 delims==" %%A in ('type "%~dp0config.ini" ^| findstr /v "^;" ^| findstr /v "^$"') do (
    set "%%A=%%B"
)

:: Set paths
set "FRONTEND_DIR=%~dp0casestrainer-vue-new"
set "BACKEND_DIR=%~dp0"
set "NGINX_DIR=%~dp0%NGINX_DIR%"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx_production.conf"
set "LOG_DIR=%~dp0logs"
set "BUILD_LOG=%LOG_DIR%\build.log"
set "NGINX_LOG=%LOG_DIR%\nginx.log"
set "FLASK_LOG=%LOG_DIR%\flask.log"
set "HOST=0.0.0.0"

cd /d "%CASESTRAINER_DIR%"

:: Load configuration from environment variables or set defaults
echo [%DATE% %TIME%] Loading production configuration...

:: SSL Configuration - Use paths from config.ini or fall back to default locations
if not defined SSL_CERT_PATH set "SSL_CERT_PATH=%CASESTRAINER_DIR%\ssl\WolfCertBundle.crt"
if not defined SSL_KEY_PATH set "SSL_KEY_PATH=%CASESTRAINER_DIR%\ssl\wolf.law.uw.edu.key"

:: Development Environment
set "DEV_BACKEND_PORT=5001"
set "DEV_FRONTEND_PORT=5000"

:: Production Environment - Ensure backend runs on port 5000 as per deployment requirements
set "PROD_BACKEND_PORT=5000"
set "PROD_FRONTEND_PORT=80"

:: Server Configuration
set "SERVER_NAME=wolf.law.uw.edu"
set "SERVER_IP=128.208.154.3"
set "NGINX_DIR=nginx-1.27.5"

:: Paths
set "STATIC_FILES_PATH=./static"
set "LOG_DIR=./logs"

:: Nginx Worker Configuration
set "WORKER_PROCESSES=1"
set "WORKER_CONNECTIONS=1024"

:: Timeouts (in seconds)
set "KEEPALIVE_TIMEOUT=300"
set "PROXY_CONNECT_TIMEOUT=60"
set "PROXY_SEND_TIMEOUT=60"
set "PROXY_READ_TIMEOUT=300"

:: Rate Limiting
set "RATE_LIMIT_ZONE_SIZE=10m"
set "RATE_LIMIT_GENERAL=10r/s"
set "RATE_LIMIT_API=50r/s"

:: Gzip Settings
set "GZIP_MIN_LENGTH=10240"
set "GZIP_TYPES=text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript"

:: SSL Configuration
set "SSL_PROTOCOLS=TLSv1.2 TLSv1.3"
set "SSL_CIPHERS=ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"
set "SSL_SESSION_TIMEOUT=1d"
set "SSL_SESSION_CACHE=shared:SSL:50m"

:: Security Headers
set "HSTS_MAX_AGE=63072000"
set "CSP_DEFAULT_SRC='self' https://wolf.law.uw.edu"
set "CSP_SCRIPT_SRC='self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net"
set "CSP_STYLE_SRC='self' 'unsafe-inline' https://cdn.jsdelivr.net"
set "CSP_IMG_SRC='self' data:"
set "CSP_FONT_SRC='self' data: https://cdn.jsdelivr.net"
set "CSP_CONNECT_SRC='self' https://wolf.law.uw.edu wss:"

:: File Upload Settings
set "CLIENT_MAX_BODY_SIZE=50M"

:: Set full paths
set "NGINX_FULL_DIR=%SCRIPT_DIR%\%NGINX_DIR%"
set "NGINX_EXE=%NGINX_FULL_DIR%\nginx.exe"
set "APP_PATH=/casestrainer"

call :log [CONFIG] Server: %SERVER_NAME% (%SERVER_IP%)
call :log [CONFIG] Backend Port: %PROD_BACKEND_PORT%
call :log [CONFIG] SSL Cert: %SSL_CERT_PATH%
call :log [CONFIG] SSL Key: %SSL_KEY_PATH%
call :log [CONFIG] Nginx Dir: %NGINX_FULL_DIR%
echo.

:: Check SSL certificates
call :log [STEP 2] Verifying SSL certificates...
if exist "%SSL_CERT_PATH%" (
    call :log [OK] SSL certificate found: %SSL_CERT_PATH%
) else (
    call :log [ERROR] SSL certificate not found: %SSL_CERT_PATH%
    call :log Please ensure the SSL certificate is in the correct location
    pause
    exit /b 1
)

if exist "%SSL_KEY_PATH%" (
    call :log [OK] SSL key found: %SSL_KEY_PATH%
) else (
    call :log [ERROR] SSL key not found: %SSL_KEY_PATH%
    call :log Please ensure the SSL key is in the correct location
    pause
    exit /b 1
)
echo.

:: Build Vue.js for production
call :log [STEP 3] Building Vue.js application for production...

:: Check frontend directory
call :log [INFO] Checking frontend directory: %FRONTEND_DIR%
if not exist "%FRONTEND_DIR%" (
    call :log [ERROR] Frontend directory not found: %FRONTEND_DIR%
    call :log [INFO] Current directory: %CD%
    call :log [INFO] Available directories:
    dir /b /a:d >> "%LOG_FILE%" 2>&1
    call :log [INFO] Check %LOG_FILE% for detailed error information
    pause
    exit /b 1
)

:: Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :log [ERROR] Node.js is not installed or not in PATH
    call :log [INFO] Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :log [ERROR] npm is not installed or not in PATH
    call :log [INFO] Please install Node.js which includes npm
    pause
    exit /b 1
)

:: Build Vue.js frontend if needed
call :log [INFO] Building Vue.js frontend...
if not exist "%FRONTEND_DIR%\package.json" (
    call :log [ERROR] package.json not found in %FRONTEND_DIR%
    call :log [INFO] Make sure the frontend directory is properly set up
    call :log [INFO] Current directory: %CD%
    dir "%FRONTEND_DIR%" >> "%LOG_FILE%" 2>&1
    call :log [INFO] Check %LOG_FILE% for detailed error information
    pause
    exit /b 1
)

pushd "%FRONTEND_DIR%"

:: Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    call :log [%TIME%] Installing npm dependencies...
    call npm install --no-fund --no-audit --prefer-offline
    if !errorlevel! neq 0 (
        call :log [ERROR] npm install failed with error code !errorlevel!
        if exist "%BUILD_LOG%" type "%BUILD_LOG%" >> "%LOG_FILE%" 2>&1
        popd
        pause
        exit /b 1
    )
    call :log [%TIME%] npm dependencies installed successfully
) else (
    call :log [%TIME%] Using existing node_modules
)

:: Build the Vue.js application with a timeout
call :log [%TIME%] Starting Vue.js build...
call :log [%TIME%] Build log: %BUILD_LOG%

:: Create a temporary batch file to run the build with a timeout
set "BUILD_SCRIPT=%TEMP%\vue_build_%RANDOM%.bat"
echo @echo off > "%BUILD_SCRIPT%"
echo echo [%%TIME%%] Starting npm run build... >> "%BUILD_SCRIPT%"
echo call npm run build -- --debug >> "%BUILD_SCRIPT%"
echo echo [%%TIME%%] Build completed with errorlevel: %%errorlevel%% >> "%BUILD_SCRIPT%"
echo exit /b %%errorlevel%% >> "%BUILD_SCRIPT%"

:: Run the build with a 30-second timeout
set "STARTTIME=%TIME%"
call :log [%TIME%] Build started at %STARTTIME%
call "%SystemRoot%\System32\timeout.exe" /t 30 /nobreak
if !errorlevel! equ 1 (
    call :log [ERROR] Build timed out after 30 seconds
    if exist "%BUILD_SCRIPT%" del "%BUILD_SCRIPT%"
    popd
    pause
    exit /b 1
)

call "%BUILD_SCRIPT%" > "%BUILD_LOG%" 2>&1
set BUILD_RESULT=!errorlevel!

if exist "%BUILD_SCRIPT%" del "%BUILD_SCRIPT%"

if !BUILD_RESULT! neq 0 (
    call :log [ERROR] Vue.js build failed with error code !BUILD_RESULT!
    call :log [INFO] Build log contents:
    if exist "%BUILD_LOG%" type "%BUILD_LOG%" >> "%LOG_FILE%" 2>&1
    popd
    pause
    exit /b 1
)

call :log [%TIME%] Vue.js build completed successfully

popd
call :log [OK] Vue.js application built successfully
call :log [INFO] Production files are in: %FRONTEND_DIR%\dist

:: Configure Vue build for subpath
call :log [INFO] Configuring Vue build for subpath deployment...
cd /d "%FRONTEND_DIR%"
if exist "dist\index.html" (
    powershell -Command "(Get-Content 'dist\index.html') -replace '=\"/', '=\"/casestrainer/' | Set-Content 'dist\index.html'" 2>nul
    if !errorlevel! equ 0 (
        call :log [OK] Vue build configured for /casestrainer path
    ) else (
        call :log [WARNING] Could not modify Vue build paths automatically
    )
)
cd /d "%CASESTRAINER_DIR%"
echo.

:: Check Flask backend
call :log [STEP 4] Checking Flask backend...
set "FLASK_APP=%BACKEND_DIR%\app_final_vue.py"

:: Check if file exists using multiple methods
if not exist "%FLASK_APP%" (
    call :log [ERROR] Flask app not found at: %FLASK_APP%
    call :log [INFO] Current directory: %CD%
    call :log [INFO] Directory listing of src:
    dir "%BACKEND_DIR%" /b | findstr /i "app_final" >> "%LOG_FILE%" 2>&1
    
    :: Try alternative path in case of OneDrive issues
    set "FLASK_APP=src\app_final_vue.py"
    if exist "%FLASK_APP%" (
        call :log [WARNING] Found Flask app using alternative path: %FLASK_APP%
    ) else (
        call :log [ERROR] Flask app not found at alternative path either: %FLASK_APP%
        call :log [INFO] Check %LOG_FILE% for detailed error information
        pause
        exit /b 1
    )
) 

call :log [OK] Using Flask app: %FLASK_APP%
set "FLASK_APP_PATH=%FLASK_APP%"

echo.

:: Stop existing services
call :log [STEP 5] Stopping existing services...

:: Stop existing Flask
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Stopping existing Flask on port %PROD_BACKEND_PORT%...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PROD_BACKEND_PORT% " ^| findstr "LISTENING"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

:: Stop existing Nginx
echo [INFO] Stopping existing Nginx...
taskkill /IM nginx.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [OK] Existing services stopped
echo.

:: Start Flask backend
echo [STEP 6] Starting Flask backend for production...
cd /d "%BACKEND_DIR%"

set "FLASK_SCRIPT=%TEMP%\casestrainer_prod_flask.bat"
echo @echo off > "%FLASK_SCRIPT%"
echo title CaseStrainer Production Flask - Port %PROD_BACKEND_PORT% >> "%FLASK_SCRIPT%"
echo echo ============================================ >> "%FLASK_SCRIPT%"
echo echo  CaseStrainer Production Backend >> "%FLASK_SCRIPT%"
echo echo ============================================ >> "%FLASK_SCRIPT%"

call :log [INFO] Starting Flask with: %FLASK_APP_PATH%
start "Flask Backend" cmd /c "%FLASK_SCRIPT%"
timeout /t 5 /nobreak >nul

:: Check if Flask started successfully
tasklist /FI "WINDOWTITLE eq Flask Backend*" 2>nul | find /i "cmd.exe" >nul
if %ERRORLEVEL% EQU 0 (
    call :log [OK] Flask backend started successfully on port %PROD_BACKEND_PORT%
) else (
    call :log [ERROR] Failed to start Flask backend
    call :log [INFO] Check %LOG_FILE% for error details
    pause
    exit /b 1
)

:: Clean up the temporary script
if exist "%FLASK_SCRIPT%" del "%FLASK_SCRIPT%"

:: Wait for Flask to start
echo [INFO] Waiting for Flask to initialize...
set "FLASK_READY=0"
for /L %%i in (1,1,15) do (
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
    if !errorlevel! equ 0 (
        set "FLASK_READY=1"
        goto :flask_started
    )
    if %%i equ 5 echo [INFO] Still waiting for Flask... (%%i/15)
    if %%i equ 10 echo [INFO] Flask taking longer than expected... (%%i/15)
)

:flask_started
if %FLASK_READY% equ 1 (
    echo [SUCCESS] Flask production server running on port %PROD_BACKEND_PORT%
) else (
    echo [ERROR] Flask failed to start within 15 seconds
    echo Check the Flask window for error messages
    pause
    exit /b 1
)
echo.

:: Configure Nginx for production
echo [STEP 7] Configuring Nginx for production deployment...
cd /d "%NGINX_FULL_DIR%"

:: Check if Nginx is installed
if not exist "%NGINX_EXE%" (
    echo [ERROR] Nginx not found at: %NGINX_EXE%
    echo [INFO] Please ensure Nginx is installed in: %NGINX_FULL_DIR%
    pause
    exit /b 1
)
echo [OK] Found Nginx at: %NGINX_EXE%

:: Create production Nginx configuration
echo [INFO] Creating enterprise-grade Nginx configuration...
if not exist "%NGINX_DIR%\conf" mkdir "%NGINX_DIR%\conf"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx_production.conf"

:: Remove existing config file if it exists
if exist "%NGINX_CONF%" del /f /q "%NGINX_CONF%"

:: Verify we can write to the config directory
echo. > "%NGINX_CONF%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Cannot write to Nginx config file: %NGINX_CONF%
    echo [ERROR] Please check directory permissions and try again
    pause
    exit /b 1
)

echo [DEBUG] Will write Nginx config to: %NGINX_CONF%

echo # CaseStrainer Production Configuration > "%NGINX_CONF%"
echo # Enterprise grade deployment for %SERVER_NAME% >> "%NGINX_CONF%"
echo # Generated: %DATE% %TIME% >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo worker_processes %WORKER_PROCESSES%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo events { >> "%NGINX_CONF%"
echo     worker_connections %WORKER_CONNECTIONS%; >> "%NGINX_CONF%"
echo } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo http { >> "%NGINX_CONF%"
echo     include       mime.types; >> "%NGINX_CONF%"
echo     default_type  application/octet-stream; >> "%NGINX_CONF%"
echo     sendfile        on; >> "%NGINX_CONF%"
echo     keepalive_timeout  %KEEPALIVE_TIMEOUT%; >> "%NGINX_CONF%"
echo     client_max_body_size %CLIENT_MAX_BODY_SIZE%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # Rate limiting zones >> "%NGINX_CONF%"
echo     limit_req_zone $binary_remote_addr zone=general:%RATE_LIMIT_ZONE_SIZE% rate=%RATE_LIMIT_GENERAL%; >> "%NGINX_CONF%"
echo     limit_req_zone $binary_remote_addr zone=api:%RATE_LIMIT_ZONE_SIZE% rate=%RATE_LIMIT_API%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # Gzip compression >> "%NGINX_CONF%"
echo     gzip on; >> "%NGINX_CONF%"
echo     gzip_vary on; >> "%NGINX_CONF%"
echo     gzip_min_length %GZIP_MIN_LENGTH%; >> "%NGINX_CONF%"
echo     gzip_types %GZIP_TYPES%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # SSL Configuration >> "%NGINX_CONF%"
echo     ssl_protocols %SSL_PROTOCOLS%; >> "%NGINX_CONF%"
echo     ssl_ciphers %SSL_CIPHERS%; >> "%NGINX_CONF%"
echo     ssl_prefer_server_ciphers on; >> "%NGINX_CONF%"
echo     ssl_session_timeout %SSL_SESSION_TIMEOUT%; >> "%NGINX_CONF%"
echo     ssl_session_cache %SSL_SESSION_CACHE%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # HTTP redirect to HTTPS >> "%NGINX_CONF%"
echo     server { >> "%NGINX_CONF%"
echo         listen 80; >> "%NGINX_CONF%"
echo         server_name %SERVER_NAME%; >> "%NGINX_CONF%"
echo         return 301 https://$host$request_uri; >> "%NGINX_CONF%"
echo     } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # HTTPS server >> "%NGINX_CONF%"
echo     server { >> "%NGINX_CONF%"
echo         listen 443 ssl http2; >> "%NGINX_CONF%"
echo         server_name %SERVER_NAME%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # SSL certificates >> "%NGINX_CONF%"
echo         ssl_certificate "%SSL_CERT_PATH%"; >> "%NGINX_CONF%"
echo         ssl_certificate_key "%SSL_KEY_PATH%"; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Security headers >> "%NGINX_CONF%"
echo         add_header Strict-Transport-Security "max-age=%HSTS_MAX_AGE%; includeSubDomains" always; >> "%NGINX_CONF%"
echo         add_header X-Frame-Options SAMEORIGIN always; >> "%NGINX_CONF%"
echo         add_header X-Content-Type-Options nosniff always; >> "%NGINX_CONF%"
echo         add_header X-XSS-Protection "1; mode=block" always; >> "%NGINX_CONF%"
echo         add_header Content-Security-Policy "default-src %CSP_DEFAULT_SRC%; script-src %CSP_SCRIPT_SRC%; style-src %CSP_STYLE_SRC%; img-src %CSP_IMG_SRC%; font-src %CSP_FONT_SRC%; connect-src %CSP_CONNECT_SRC%" always; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Proxy settings >> "%NGINX_CONF%"
echo         proxy_connect_timeout %PROXY_CONNECT_TIMEOUT%; >> "%NGINX_CONF%"
echo         proxy_send_timeout %PROXY_SEND_TIMEOUT%; >> "%NGINX_CONF%"
echo         proxy_read_timeout %PROXY_READ_TIMEOUT%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"

echo         # CaseStrainer application >> "%NGINX_CONF%"
echo         location ^~ /casestrainer/ { >> "%NGINX_CONF%"
echo             limit_req zone=general burst=20 nodelay; >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR%/dist/"; >> "%NGINX_CONF%"
echo             try_files $uri $uri/ /casestrainer/index.html; >> "%NGINX_CONF%"
echo             index index.html; >> "%NGINX_CONF%"

echo             # Security headers >> "%NGINX_CONF%"
echo             add_header X-Frame-Options "SAMEORIGIN" always; >> "%NGINX_CONF%"
echo             add_header X-Content-Type-Options "nosniff" always; >> "%NGINX_CONF%"
echo             add_header X-XSS-Protection "1; mode=block" always; >> "%NGINX_CONF%"
echo             add_header Referrer-Policy "no-referrer-when-downgrade" always; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"

echo         # Static assets >> "%NGINX_CONF%"
echo         location ^~ /casestrainer/assets/ { >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR%/dist/assets/"; >> "%NGINX_CONF%"
echo             expires 1y; >> "%NGINX_CONF%"
echo             add_header Cache-Control "public, immutable"; >> "%NGINX_CONF%"
echo             access_log off; >> "%NGINX_CONF%"

echo             # Security headers >> "%NGINX_CONF%"
echo             add_header X-Content-Type-Options "nosniff" always; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"

echo         # API proxy to Flask backend >> "%NGINX_CONF%"
echo         location ^~ /casestrainer/api/ { >> "%NGINX_CONF%"
echo             limit_req zone=api burst=100 nodelay; >> "%NGINX_CONF%"
echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT/; >> "%NGINX_CONF%"
echo             proxy_http_version 1.1; >> "%NGINX_CONF%"
echo             proxy_set_header Host $http_host; >> "%NGINX_CONF%"
echo             proxy_set_header X-Real-IP $remote_addr; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Proto $scheme; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Host $server_name; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Prefix /casestrainer; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Port $server_port; >> "%NGINX_CONF%"
echo             proxy_set_header Connection ''; >> "%NGINX_CONF%"
echo             proxy_redirect off; >> "%NGINX_CONF%"
echo             proxy_buffering off; >> "%NGINX_CONF%"
echo             proxy_read_timeout 300s; >> "%NGINX_CONF%"
echo             proxy_connect_timeout 75s; >> "%NGINX_CONF%"
echo             proxy_send_timeout 300s; >> "%NGINX_CONF%"
echo             proxy_request_buffering off; >> "%NGINX_CONF%"
echo             proxy_set_header X-Script-Name /casestrainer; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Health check endpoint >> "%NGINX_CONF%"
echo         location /health { >> "%NGINX_CONF%"
echo             access_log off; >> "%NGINX_CONF%"
echo             return 200 "healthy\n"; >> "%NGINX_CONF%"
echo             add_header Content-Type text/plain; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Favicon >> "%NGINX_CONF%"
echo         location /favicon.ico { >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR%\\dist\\favicon.ico"; >> "%NGINX_CONF%"
echo             access_log off; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo     } >> "%NGINX_CONF%"
echo } >> "%NGINX_CONF%"

echo [SUCCESS] Enterprise Nginx configuration created
echo.

:: Stop any running Nginx instances
echo [INFO] Stopping any running Nginx instances...
taskkill /F /IM nginx.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: Verify Nginx configuration
echo [INFO] Verifying Nginx configuration...
pushd "%NGINX_DIR%"
"%NGINX_EXE%" -t -c "conf\nginx_production.conf"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Nginx configuration test failed
    echo [INFO] Please check the Nginx configuration file: %NGINX_DIR%\conf\nginx_production.conf
    popd
    pause
    exit /b 1
)

:: Start Nginx
echo [INFO] Starting Nginx...
start "" /B "%NGINX_EXE%" -c "conf\nginx_production.conf"
popd

:: Verify Nginx is running
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq nginx.exe" | find "nginx.exe" >nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to start Nginx
    echo [INFO] Please check the Nginx error log: %NGINX_DIR%\logs\error.log
    pause
    exit /b 1
)

echo [SUCCESS] Nginx started successfully

:: Create and start Nginx log viewer
echo [INFO] Starting Nginx log viewer...
set "LOG_SCRIPT=%TEMP%\casestrainer_nginx_logs.bat"
echo @echo off > "%LOG_SCRIPT%"
echo title CaseStrainer Nginx Logs >> "%LOG_SCRIPT%"
echo echo ============================================ >> "%LOG_SCRIPT%"
echo echo  CaseStrainer Nginx Log Viewer >> "%LOG_SCRIPT%"
echo echo ============================================ >> "%LOG_SCRIPT%"
echo echo Log File: %NGINX_FULL_DIR%\logs\error.log >> "%LOG_SCRIPT%"
echo echo ============================================ >> "%LOG_SCRIPT%"
echo echo. >> "%LOG_SCRIPT%"
echo if not exist "%NGINX_FULL_DIR%\logs\error.log" ( >> "%LOG_SCRIPT%"
echo     echo [INFO] Waiting for Nginx to create log file... >> "%LOG_SCRIPT%"
echo     timeout /t 2 /nobreak ^>nul >> "%LOG_SCRIPT%"
echo ) >> "%LOG_SCRIPT%"
echo powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -Path '%NGINX_FULL_DIR%\logs\error.log' -Wait -Tail 50" >> "%LOG_SCRIPT%"
echo echo. >> "%LOG_SCRIPT%"
echo echo [NGINX] Log viewer ended >> "%LOG_SCRIPT%"
echo pause >> "%LOG_SCRIPT%"

start "CaseStrainer_Nginx_Logs" cmd /c "%LOG_SCRIPT%"

:: Verify Nginx
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Nginx production server is running
) else (
    echo [ERROR] Nginx failed to start
    echo Check logs: %NGINX_FULL_DIR%\logs\error.log
    pause
    exit /b 1
)
echo.

:: Final production status
echo ================================================
echo     CaseStrainer Production Deployment Complete
echo ================================================
echo.
echo [STATUS] Service Status:
echo.

:: Check Flask backend status
echo [BACKEND] Flask Application:
netstat -ano | findstr ":%PROD_BACKEND_PORT%" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PROD_BACKEND_PORT%" ^| findstr "LISTENING"') do (
        set "FLASK_PID=%%a"
        for /f "tokens=1,2 delims= " %%b in ('tasklist /FI "PID eq !FLASK_PID!" /FO LIST ^| findstr "Image"') do (
            set "FLASK_IMAGE=%%c"
        )
        echo   Status:    RUNNING (PID: !FLASK_PID! - !FLASK_IMAGE!)
    )
) else (
    echo   Status:    NOT RUNNING
)
echo   Port:      %PROD_BACKEND_PORT%
echo   URL:       http://localhost:%PROD_BACKEND_PORT%/api/

:: Check Nginx status
echo.
echo [FRONTEND] Nginx Server:
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo   Status:    RUNNING
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80 " ^| findstr "LISTENING"') do (
        set "NGINX_PID=%%a"
    )
    if defined NGINX_PID (
        echo   PID:       %NGINX_PID%
    )
) else (
    echo   Status:    NOT RUNNING
)
echo   Ports:     80 (HTTP), 443 (HTTPS)
echo   Config:    %NGINX_CONF%

:: Check port 80 and 443 status
echo.
echo [PORTS] Port Status:
for %%p in (80 443) do (
    netstat -ano | findstr ":%%p" | findstr "LISTENING" >nul
    if !errorlevel! equ 0 (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr "LISTENING"') do (
            set "PORT_PID=%%a"
            for /f "tokens=1,2 delims= " %%b in ('tasklist /FI "PID eq !PORT_PID!" /FO LIST ^| findstr "Image"') do (
                set "PORT_IMAGE=%%c"
            )
            echo   Port %%p:   IN USE by !PORT_IMAGE! (PID: !PORT_PID!)
            set "PORT_FOUND=true"
        )
    ) else (
        echo   Port %%p:   AVAILABLE
    )
)

echo.
echo [ACCESS] Production URLs:
echo   Main App: https://%SERVER_NAME%%APP_PATH%/
echo   API:      https://%SERVER_NAME%%APP_PATH%/api/
echo   Health:   https://%SERVER_NAME%/health
echo.
echo [INFO] Server Details:
echo   Server IP: %SERVER_IP%
echo   Frontend:  Ports 80/443 (Nginx with SSL)
echo   Backend:   Port %PROD_BACKEND_PORT% (Flask)

echo.
echo [INFO] Enterprise Features Enabled:
echo   - SSL/TLS with strong ciphers
echo   - HTTP/2 support
echo   - Rate limiting (%RATE_LIMIT_GENERAL% general, %RATE_LIMIT_API% API)
echo   - Security headers (HSTS, CSP, XSS protection)
echo   - Gzip compression
echo   - Static asset caching
echo   - Request timeouts and limits

echo.
echo [INFO] Press any key to close this window...
pause >nul
echo.
echo [SUCCESS] CaseStrainer is live at https://%SERVER_NAME%%APP_PATH%/
echo.
echo Both Flask and Nginx are running in separate windows.
echo Monitor their console windows for logs and status.
echo.
echo Press any key to exit this launcher (services will continue running)...
pause >nul

echo.
echo [INFO] Deployment launcher exiting - services continue running
echo [INFO] To stop services: Close Flask and Nginx console windows
echo.