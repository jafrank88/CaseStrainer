@echo off
setlocal enabledelayedexpansion

:: CaseStrainer Production Deployment
:: Clean version without encoding corruption

echo.
echo ================================================
echo    CaseStrainer Production Deployment
echo    Target: https://wolf.law.uw.edu/casestrainer
echo ================================================
echo Time: %DATE% %TIME%
echo.

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Please run as administrator
    echo This is required for production deployment
    pause
    exit /b 1
)

:: Define base paths
set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "BACKEND_DIR=%CASESTRAINER_DIR%\src"
set "FRONTEND_DIR=%CASESTRAINER_DIR%\casestrainer-vue-new"

echo [INFO] Working directory: %CASESTRAINER_DIR%
cd /d "%CASESTRAINER_DIR%"

:: Load production configuration
echo [STEP 1] Loading production configuration...
if exist "config.env" (
    echo [INFO] Reading configuration from config.env...
    for /f "usebackq tokens=1,2 delims==" %%a in ("config.env") do (
        set "%%a=%%b"
    )
) else (
    echo [WARNING] config.env not found, using fallback values
    set "SSL_CERT_PATH=D:\CaseStrainer\ssl\WolfCertBundle.crt"
    set "SSL_KEY_PATH=D:\CaseStrainer\ssl\wolf.law.uw.edu.key"
    set "PROD_BACKEND_PORT=5002"
    set "SERVER_NAME=wolf.law.uw.edu"
    set "SERVER_IP=128.208.154.3"
    set "NGINX_DIR=nginx-1.27.5"
)

set "NGINX_FULL_DIR=%CASESTRAINER_DIR%\%NGINX_DIR%"
set "APP_PATH=/casestrainer"

:: Fix SSL paths for Windows
set "SSL_CERT_PATH=%SSL_CERT_PATH:/=\%"
set "SSL_KEY_PATH=%SSL_KEY_PATH:/=\%"

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
echo [STEP 3] Preparing Vue production build...
cd /d "%FRONTEND_DIR%"

if not exist "dist\index.html" (
    echo [INFO] Production build not found, building Vue app...
    if exist "package.json" (
        echo [INFO] Running production build: npm run build
        call npm run build
        if !errorlevel! neq 0 (
            echo [ERROR] Vue production build failed
            pause
            exit /b 1
        )
        echo [SUCCESS] Vue production build completed
    ) else (
        echo [ERROR] Vue project not found
        pause
        exit /b 1
    )
) else (
    echo [OK] Production build exists
)

:: Configure Vue build for subpath
echo [INFO] Configuring Vue build for /casestrainer path...
if exist "dist\index.html" (
    powershell -Command "(Get-Content 'dist\index.html') -replace '=\"/', '=\"/casestrainer/' | Set-Content 'dist\index.html'"
    echo [OK] Vue build configured for subpath deployment
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

:: Wait for Flask
echo [INFO] Waiting for Flask to initialize...
timeout /t 8 /nobreak

:: Verify Flask
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Flask production server running on port %PROD_BACKEND_PORT%
) else (
    echo [ERROR] Flask failed to start
    echo Check the Flask window for errors
    pause
    exit /b 1
)
echo.

:: Configure Nginx for production
echo [STEP 7] Configuring Nginx for production deployment...
cd /d "%NGINX_FULL_DIR%"

if not exist "nginx.exe" (
    echo [ERROR] nginx.exe not found in %NGINX_FULL_DIR%
    pause
    exit /b 1
)

:: Create production Nginx configuration
echo [INFO] Creating production Nginx configuration...
set "NGINX_CONF=conf\nginx_production.conf"

echo # CaseStrainer Production Configuration > "%NGINX_CONF%"
echo # For https://wolf.law.uw.edu/casestrainer >> "%NGINX_CONF%"
echo # Generated: %DATE% %TIME% >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo worker_processes 1; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo events { >> "%NGINX_CONF%"
echo     worker_connections 1024; >> "%NGINX_CONF%"
echo } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo http { >> "%NGINX_CONF%"
echo     include       mime.types; >> "%NGINX_CONF%"
echo     default_type  application/octet-stream; >> "%NGINX_CONF%"
echo     sendfile        on; >> "%NGINX_CONF%"
echo     keepalive_timeout  65; >> "%NGINX_CONF%"
echo     client_max_body_size 50M; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # Gzip compression >> "%NGINX_CONF%"
echo     gzip on; >> "%NGINX_CONF%"
echo     gzip_vary on; >> "%NGINX_CONF%"
echo     gzip_min_length 1024; >> "%NGINX_CONF%"
echo     gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # HTTP redirect to HTTPS >> "%NGINX_CONF%"
echo     server { >> "%NGINX_CONF%"
echo         listen 80; >> "%NGINX_CONF%"
echo         server_name %SERVER_NAME%; >> "%NGINX_CONF%"
echo         return 301 https://%%server_name%%request_uri; >> "%NGINX_CONF%"
echo     } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo     # HTTPS server >> "%NGINX_CONF%"
echo     server { >> "%NGINX_CONF%"
echo         listen 443 ssl; >> "%NGINX_CONF%"
echo         server_name %SERVER_NAME%; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # SSL certificates >> "%NGINX_CONF%"
echo         ssl_certificate "%SSL_CERT_PATH%"; >> "%NGINX_CONF%"
echo         ssl_certificate_key "%SSL_KEY_PATH%"; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # SSL settings >> "%NGINX_CONF%"
echo         ssl_protocols TLSv1.2 TLSv1.3; >> "%NGINX_CONF%"
echo         ssl_ciphers HIGH:!aNULL:!MD5; >> "%NGINX_CONF%"
echo         ssl_prefer_server_ciphers on; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Security headers >> "%NGINX_CONF%"
echo         add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always; >> "%NGINX_CONF%"
echo         add_header X-Frame-Options SAMEORIGIN always; >> "%NGINX_CONF%"
echo         add_header X-Content-Type-Options nosniff always; >> "%NGINX_CONF%"
echo         add_header X-XSS-Protection "1; mode=block" always; >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # CaseStrainer application >> "%NGINX_CONF%"
echo         location %APP_PATH%/ { >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR:\=/%/dist/"; >> "%NGINX_CONF%"
echo             try_files %%uri %%uri/ %APP_PATH%/index.html; >> "%NGINX_CONF%"
echo             index index.html; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Vue assets >> "%NGINX_CONF%"
echo         location /assets/ { >> "%NGINX_CONF%"
echo             alias "%FRONTEND_DIR:\=/%/dist/assets/"; >> "%NGINX_CONF%"
echo             expires 1y; >> "%NGINX_CONF%"
echo             add_header Cache-Control "public, immutable"; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # API proxy to Flask backend >> "%NGINX_CONF%"
echo         location %APP_PATH%/api/ { >> "%NGINX_CONF%"
echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/; >> "%NGINX_CONF%"
echo             proxy_set_header Host %%host; >> "%NGINX_CONF%"
echo             proxy_set_header X-Real-IP %%remote_addr; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-For %%proxy_add_x_forwarded_for; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Proto %%scheme; >> "%NGINX_CONF%"
echo             proxy_set_header X-Forwarded-Host %%server_name; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo. >> "%NGINX_CONF%"
echo         # Health check >> "%NGINX_CONF%"
echo         location /health { >> "%NGINX_CONF%"
echo             access_log off; >> "%NGINX_CONF%"
echo             return 200 "healthy\n"; >> "%NGINX_CONF%"
echo             add_header Content-Type text/plain; >> "%NGINX_CONF%"
echo         } >> "%NGINX_CONF%"
echo     } >> "%NGINX_CONF%"
echo } >> "%NGINX_CONF%"

echo [SUCCESS] Production Nginx configuration created
echo.

:: Start Nginx with production configuration
echo [STEP 8] Starting Nginx production server...
start "CaseStrainer_Production_Nginx" nginx.exe -c "%NGINX_CONF%"
timeout /t 3 /nobreak

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
echo Production URL: https://%SERVER_NAME%%APP_PATH%
echo Backend API:    https://%SERVER_NAME%%APP_PATH%/api/
echo Health Check:   https://%SERVER_NAME%/health
echo Server IP:      %SERVER_IP%
echo.
echo [INFO] Services running:
echo   - Flask Backend: Port %PROD_BACKEND_PORT% (production mode)
echo   - Nginx Server:  Ports 80/443 (SSL enabled with real certificates)
echo.
echo [SUCCESS] CaseStrainer is live at https://%SERVER_NAME%%APP_PATH%
echo.
echo Press any key to stop all services...
pause >nul

:: Production cleanup
echo.
echo [INFO] Stopping production services...

echo [INFO] Stopping Nginx...
taskkill /IM nginx.exe /F >nul 2>&1

echo [INFO] Stopping Flask...
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PROD_BACKEND_PORT% " ^| findstr "LISTENING"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo [SUCCESS] Production services stopped
echo.
pause