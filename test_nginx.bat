@chcp 65001 >nul 2>&1
@echo off
setlocal enabledelayedexpansion

:: Quick Nginx Fix - Since Flask is already running
echo.
echo ================================================
echo     Quick Nginx Startup (Flask already running)
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

cd /d "%CASESTRAINER_DIR%"

:: Load config.env
echo [INFO] Loading config.env...
for /f "usebackq tokens=1,2 delims==" %%a in ("config.env") do (
    set "%%a=%%b"
)

echo [INFO] Flask is already running on port %PROD_BACKEND_PORT%
echo [INFO] Starting Nginx to complete the deployment...

cd /d "%NGINX_DIR%"

:: Create minimal working Nginx config
echo [INFO] Creating Nginx configuration...
set "NGINX_CONF=conf\nginx_production.conf"

(
    echo worker_processes 1;
    echo events { worker_connections 1024; }
    echo http {
    echo     include mime.types;
    echo     default_type application/octet-stream;
    echo     sendfile on;
    echo     keepalive_timeout 65;
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
    echo         ssl_certificate %SSL_CERT_PATH%;
    echo         ssl_certificate_key %SSL_KEY_PATH%;
    echo.
    echo         # CaseStrainer app
    echo         location /casestrainer/ {
    echo             alias %FRONTEND_DIR:\=/%/dist/;
    echo             try_files $uri $uri/ /casestrainer/index.html;
    echo             index index.html;
    echo         }
    echo.
    echo         # API proxy
    echo         location /casestrainer/api/ {
    echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/;
    echo             proxy_set_header Host $host;
    echo             proxy_set_header X-Real-IP $remote_addr;
    echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    echo             proxy_set_header X-Forwarded-Proto $scheme;
    echo         }
    echo     }
    echo }
) > "%NGINX_CONF%"

echo [SUCCESS] Nginx config created

:: Start Nginx
echo [INFO] Starting Nginx...
start "CaseStrainer_Nginx" nginx.exe -c "%NGINX_CONF%"
timeout /t 3

:: Check if it started
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Nginx is now running!
    echo.
    echo ================================================
    echo   CaseStrainer should now be accessible at:
    echo   https://wolf.law.uw.edu/casestrainer/
    echo ================================================
) else (
    echo [ERROR] Nginx failed to start
    echo [INFO] Check the SSL certificate paths in config.env
    if exist "logs\error.log" (
        echo [ERROR LOG]
        type "logs\error.log"
    )
)

echo.
pause