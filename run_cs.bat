@echo off
setlocal enabledelayedexpansion

:: CaseStrainer Production Server Launcher
:: Full-featured deployment with all configuration options

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

:: Set this to 1 to enable debug output
set "DEBUG=0"

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
    echo [ERROR] Please run as administrator
    echo This is required for production deployment with SSL
    pause
    exit /b 1
)

:: Define base paths (relative to script location)
set "BACKEND_DIR=%SCRIPT_DIR%\src"
set "FRONTEND_DIR=%SCRIPT_DIR%\casestrainer-vue-new"
set "CASESTRAINER_DIR=%SCRIPT_DIR%"

echo [INFO] Working directory: %CASESTRAINER_DIR%
cd /d "%CASESTRAINER_DIR%"

:: Load configuration from environment variables or set defaults
echo [STEP 1] Loading production configuration...

:: SSL Certificate Paths (configurable via environment variables)
if "%SSL_CERT_PATH%"=="" set "SSL_CERT_PATH=%SCRIPT_DIR%\ssl\WolfCertBundle.crt"
if "%SSL_KEY_PATH%"=="" set "SSL_KEY_PATH=%SCRIPT_DIR%\ssl\wolf.law.uw.edu.key"

:: Development Environment
set "DEV_BACKEND_PORT=5001"
set "DEV_FRONTEND_PORT=5000"

:: Production Environment
set "PROD_BACKEND_PORT=5002"
set "PROD_FRONTEND_PORT=5000"

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

echo [CONFIG] Server: %SERVER_NAME% (%SERVER_IP%)
echo [CONFIG] Backend Port: %PROD_BACKEND_PORT%
echo [CONFIG] SSL Cert: %SSL_CERT_PATH%
echo [CONFIG] SSL Key: %SSL_KEY_PATH%
echo [CONFIG] Nginx Dir: %NGINX_FULL_DIR%
echo.

:: Check SSL certificates
echo [STEP 2] Verifying SSL certificates...
if exist "%SSL_CERT_PATH%" (
    echo [OK] SSL certificate found: %SSL_CERT_PATH%
) else (
    echo [ERROR] SSL certificate not found: %SSL_CERT_PATH%
    echo Please ensure the SSL certificate is in the correct location
    pause
    exit /b 1
)

if exist "%SSL_KEY_PATH%" (
    echo [OK] SSL key found: %SSL_KEY_PATH%
) else (
    echo [ERROR] SSL key not found: %SSL_KEY_PATH%
    echo Please ensure the SSL key is in the correct location
    pause
    exit /b 1
)
echo.

:: Check Vue production build
echo [STEP 3] Checking Vue production build...
if not exist "%FRONTEND_DIR%\dist\index.html" (
    echo [WARNING] Vue production build not found, building now...
    cd /d "%FRONTEND_DIR%"
    if exist "package.json" (
        echo [INFO] Running npm run build...
        call npm run build
        if !errorlevel! neq 0 (
            echo [ERROR] Vue production build failed
            pause
            exit /b 1
        )
        echo [SUCCESS] Vue production build completed
    ) else (
        echo [ERROR] Vue project not found in %FRONTEND_DIR%
        pause
        exit /b 1
    )
    cd /d "%CASESTRAINER_DIR%"
) else (
    echo [OK] Vue production build exists
)

:: Configure Vue build for subpath
echo [INFO] Configuring Vue build for subpath deployment...
cd /d "%FRONTEND_DIR%"
if exist "dist\index.html" (
    powershell -Command "(Get-Content 'dist\index.html') -replace '=\"/', '=\"/casestrainer/' | Set-Content 'dist\index.html'" 2>nul
    if !errorlevel! equ 0 (
        echo [OK] Vue build configured for /casestrainer path
    ) else (
        echo [WARNING] Could not modify Vue build paths automatically
    )
)
cd /d "%CASESTRAINER_DIR%"
echo.

:: Check Flask backend
echo [STEP 4] Checking Flask backend...
if exist "%BACKEND_DIR%\app_final_vue.py" (
    echo [OK] Flask app found
) else (
    echo [ERROR] Flask app not found: %BACKEND_DIR%\app_final_vue.py
    pause
    exit /b 1
)
echo.

:: Stop existing services
echo [STEP 5] Stopping existing services...

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
echo echo Server: %SERVER_NAME% >> "%FLASK_SCRIPT%"
echo echo Port: %PROD_BACKEND_PORT% >> "%FLASK_SCRIPT%"
echo echo Mode: Production >> "%FLASK_SCRIPT%"
echo echo Time: %%TIME%% >> "%FLASK_SCRIPT%"
echo echo ============================================ >> "%FLASK_SCRIPT%"
echo echo. >> "%FLASK_SCRIPT%"
echo cd /d "%BACKEND_DIR%" >> "%FLASK_SCRIPT%"
echo set FLASK_ENV=production >> "%FLASK_SCRIPT%"
echo set FLASK_DEBUG=0 >> "%FLASK_SCRIPT%"
echo python app_final_vue.py --port=%PROD_BACKEND_PORT% --host=127.0.0.1 >> "%FLASK_SCRIPT%"
echo echo. >> "%FLASK_SCRIPT%"
echo echo [FLASK] Production server ended >> "%FLASK_SCRIPT%"
echo pause >> "%FLASK_SCRIPT%"

start "CaseStrainer_Production_Flask" cmd /c "%FLASK_SCRIPT%"
echo [INFO] Flask starting in production mode...

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
set "NGINX_CONF=conf\nginx_production.conf"

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
echo         location %APP_PATH%/ { >> "%NGINX_CONF%"
echo             limit_req zone=general burst=20 nodelay; >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR%\\dist"; >> "%NGINX_CONF%"
echo             try_files $uri $uri/ %APP_PATH%/index.html; >> "%NGINX_CONF%"
echo             index index.html; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Static assets >> "%NGINX_CONF%"
echo         location /assets/ { >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR%\\dist/assets/"; >> "%NGINX_CONF%"
echo             expires 1y; >> "%NGINX_CONF%"
echo             add_header Cache-Control "public, immutable"; >> "%NGINX_CONF%"
echo             access_log off; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # API proxy to Flask backend >> "%NGINX_CONF%"
echo         location %APP_PATH%/api/ { >> "%NGINX_CONF%"
echo             limit_req zone=api burst=100 nodelay; >> "%NGINX_CONF%"
echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%; >> "%NGINX_CONF%"
echo             proxy_set_header Host $host; >> "%NGINX_CONF%"
echo             proxy_set_header X-Real-IP $remote_addr; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Proto $scheme; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Host $server_name; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Prefix /casestrainer; >> "%NGINX_CONF%"
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

:: Check if port is available
:check_ports
for /f "tokens=1,2,3,4,5" %%a in ('netstat -ano ^| findstr ":80 \":443 "') do (
    if not "%%e"=="" (
        echo [WARNING] Port conflict detected: Port %%a (PID: %%e)
        echo [INFO] Attempting to terminate conflicting process...
        taskkill /F /PID %%e >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            echo [INFO] Successfully terminated process %%e
        ) else (
            echo [ERROR] Failed to terminate process %%e
            echo [ERROR] Please close the application using port %%a and try again
            pause
            exit /b 1
        )
    )
)

:: Start Nginx
echo [INFO] Starting Nginx...
"%NGINX_EXE%" -c "%NGINX_CONF%" -t
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Nginx configuration test failed
    pause
    exit /b 1
)

start "" /B "%NGINX_EXE%" -c "%NGINX_CONF%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to start Nginx
    echo [INFO] Checking for existing Nginx processes...
    tasklist /FI "IMAGENAME eq nginx.exe"
    pause
    exit /b 1
)

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