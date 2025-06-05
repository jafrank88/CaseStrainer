@chcp 65001 >nul 2>&1
@echo off
setlocal enabledelayedexpansion

:: Fixed CaseStrainer Nginx Deployment
:: Addresses SSL path and configuration syntax issues

echo.
echo ================================================
echo     Fixed CaseStrainer Nginx Deployment
echo ================================================

:: Check admin
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Please run as administrator
    pause
    exit /b 1
)

set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "NGINX_DIR=%CASESTRAINER_DIR%\nginx-1.27.5"
set "FRONTEND_DIR=%CASESTRAINER_DIR%\casestrainer-vue-new"
set "BACKEND_DIR=%CASESTRAINER_DIR%\src"

cd /d "%CASESTRAINER_DIR%"

:: Load config with path fixes
echo [STEP 1] Loading and fixing configuration...
if exist "config.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("config.env") do (
        set "%%a=%%b"
    )
) else (
    echo [ERROR] config.env not found
    pause
    exit /b 1
)

:: Fix SSL paths - convert D:/ to D:\ format
set "SSL_CERT_PATH=!SSL_CERT_PATH:/=\!"
set "SSL_KEY_PATH=!SSL_KEY_PATH:/=\!"

echo [CONFIG] SSL Cert: !SSL_CERT_PATH!
echo [CONFIG] SSL Key: !SSL_KEY_PATH!
echo [CONFIG] Backend Port: %PROD_BACKEND_PORT%

:: Verify SSL certificates exist
echo [STEP 2] Verifying SSL certificates...
if not exist "!SSL_CERT_PATH!" (
    echo [ERROR] SSL certificate not found: !SSL_CERT_PATH!
    echo [INFO] Please check the path and ensure the certificate exists
    pause
    exit /b 1
)

if not exist "!SSL_KEY_PATH!" (
    echo [ERROR] SSL key not found: !SSL_KEY_PATH!
    echo [INFO] Please check the path and ensure the key exists
    pause
    exit /b 1
)

echo [OK] SSL certificates verified

:: Check Vue build
echo [STEP 3] Checking Vue build...
if not exist "%FRONTEND_DIR%\dist\index.html" (
    echo [ERROR] Vue dist folder not found
    echo [INFO] Please run 'npm run build' in the Vue project first
    pause
    exit /b 1
)

echo [OK] Vue build found

:: Stop any existing Nginx
echo [STEP 4] Stopping existing Nginx...
taskkill /IM nginx.exe /F >nul 2>&1

cd /d "%NGINX_DIR%"

:: Create corrected Nginx configuration
echo [STEP 5] Creating corrected Nginx configuration...
set "NGINX_CONF=conf\nginx_production.conf"

(
    echo # CaseStrainer Production Configuration - Fixed
    echo # Generated: %DATE% %TIME%
    echo.
    echo worker_processes 1;
    echo.
    echo events {
    echo     worker_connections 1024;
    echo }
    echo.
    echo http {
    echo     include       mime.types;
    echo     default_type  application/octet-stream;
    echo     sendfile        on;
    echo     keepalive_timeout  65;
    echo     client_max_body_size 50M;
    echo.
    echo     # Gzip compression
    echo     gzip on;
    echo     gzip_vary on;
    echo     gzip_min_length 1024;
    echo     gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    echo.
    echo     # HTTP redirect to HTTPS
    echo     server {
    echo         listen 80;
    echo         server_name wolf.law.uw.edu;
    echo         return 301 https://$server_name$request_uri;
    echo     }
    echo.
    echo     # HTTPS server
    echo     server {
    echo         listen 443 ssl;
    echo         server_name wolf.law.uw.edu;
    echo.
    echo         # SSL certificates - using corrected paths
    echo         ssl_certificate "!SSL_CERT_PATH!";
    echo         ssl_certificate_key "!SSL_KEY_PATH!";
    echo.
    echo         # SSL settings
    echo         ssl_protocols TLSv1.2 TLSv1.3;
    echo         ssl_ciphers HIGH:!aNULL:!MD5;
    echo         ssl_prefer_server_ciphers on;
    echo.
    echo         # Security headers
    echo         add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    echo         add_header X-Frame-Options SAMEORIGIN always;
    echo         add_header X-Content-Type-Options nosniff always;
    echo         add_header X-XSS-Protection "1; mode=block" always;
    echo.
    echo         # CaseStrainer application - corrected alias syntax
    echo         location /casestrainer/ {
    echo             alias "%FRONTEND_DIR:\=/%/dist/";
    echo             try_files $uri $uri/ /casestrainer/index.html;
    echo             index index.html;
    echo         }
    echo.
    echo         # Static assets - direct serve from dist
    echo         location /assets/ {
    echo             alias "%FRONTEND_DIR:\=/%/dist/assets/";
    echo             expires 1y;
    echo             add_header Cache-Control "public, immutable";
    echo         }
    echo.
    echo         # API proxy to Flask backend
    echo         location /casestrainer/api/ {
    echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/;
    echo             proxy_set_header Host $host;
    echo             proxy_set_header X-Real-IP $remote_addr;
    echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    echo             proxy_set_header X-Forwarded-Proto $scheme;
    echo             proxy_set_header X-Forwarded-Host $server_name;
    echo         }
    echo.
    echo         # Health check
    echo         location /health {
    echo             access_log off;
    echo             return 200 "healthy\n";
    echo             add_header Content-Type text/plain;
    echo         }
    echo.
    echo         # Favicon
    echo         location /favicon.ico {
    echo             alias "%FRONTEND_DIR:\=/%/dist/favicon.ico";
    echo             access_log off;
    echo         }
    echo     }
    echo }
) > "%NGINX_CONF%"

echo [SUCCESS] Nginx configuration created

:: Test configuration syntax
echo [STEP 6] Testing Nginx configuration...
nginx.exe -t -c "%NGINX_CONF%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Nginx configuration test failed
    echo [INFO] Check the syntax errors above
    pause
    exit /b 1
)

echo [OK] Nginx configuration is valid

:: Start Nginx
echo [STEP 7] Starting Nginx...
start "CaseStrainer_Nginx_Fixed" nginx.exe -c "%NGINX_CONF%"
timeout /t 3

:: Verify Nginx started
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Nginx is running!
    
    :: Check if listening on correct ports
    netstat -ano | findstr ":80 " | findstr "LISTENING" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] HTTP port 80 is listening
    )
    
    netstat -ano | findstr ":443 " | findstr "LISTENING" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] HTTPS port 443 is listening
    )
    
    echo.
    echo ================================================
    echo         Deployment Complete!
    echo ================================================
    echo.
    echo CaseStrainer URLs:
    echo - Main App: https://wolf.law.uw.edu/casestrainer/
    echo - Health:   https://wolf.law.uw.edu/health
    echo - API:      https://wolf.law.uw.edu/casestrainer/api/
    echo.
    echo Backend Flask: http://127.0.0.1:%PROD_BACKEND_PORT%
    echo.
    echo [INFO] Services running:
    echo - Flask: Port %PROD_BACKEND_PORT% (PID from earlier diagnostic)
    echo - Nginx: Ports 80/443 with real SSL certificates
    echo.
    
) else (
    echo [ERROR] Nginx failed to start
    echo [INFO] Check error log for details:
    if exist "logs\error.log" (
        echo.
        echo [RECENT ERRORS]
        powershell -Command "Get-Content 'logs\error.log' | Select-Object -Last 10"
    )
    pause
    exit /b 1
)

echo Press any key to continue (Nginx will keep running)...
pause >nul