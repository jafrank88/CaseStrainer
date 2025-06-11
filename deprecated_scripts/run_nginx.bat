@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: Complete Nginx Setup for CaseStrainer
:: Run this after Flask is already started
:: ===================================================

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Please run as administrator
    pause
    exit /b 1
)

:: Define paths
set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "FRONTEND_DIR=%CASESTRAINER_DIR%\casestrainer-vue-new"
set "NGINX_DIR=%CASESTRAINER_DIR%\nginx-1.27.5"

echo.
echo ===================================================
echo  Complete Nginx Setup for CaseStrainer
echo ===================================================
echo Time: %DATE% %TIME%
echo.

:: Load configuration
cd /d "%CASESTRAINER_DIR%"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SSL_CERT_PATH"') do set "SSL_CERT_PATH=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SSL_KEY_PATH"') do set "SSL_KEY_PATH=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SERVER_NAME"') do set "SERVER_NAME=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "PROD_BACKEND_PORT"') do set "PROD_BACKEND_PORT=%%b"

echo [CONFIG] Server: %SERVER_NAME%
echo [CONFIG] Backend Port: %PROD_BACKEND_PORT%
echo [CONFIG] SSL Cert: %SSL_CERT_PATH%
echo [CONFIG] SSL Key: %SSL_KEY_PATH%
echo.

:: Verify Flask is still running
echo [CHECK] Verifying Flask is still running...
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Flask is not running on port %PROD_BACKEND_PORT%
    echo [INFO] Please start Flask first using the debug script
    pause
    exit /b 1
)
echo [OK] Flask is running on port %PROD_BACKEND_PORT%
echo.

:: Stop any existing Nginx
echo [CLEANUP] Stopping any existing Nginx processes...
taskkill /F /IM nginx.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Create Nginx configuration
echo [NGINX] Creating Nginx configuration...
cd /d "%NGINX_DIR%"

set "NGINX_CONFIG=%NGINX_DIR%\conf\casestrainer_production.conf"
set "FRONTEND_DIST_UNIX=%FRONTEND_DIR:\=/%/dist"

echo [INFO] Config file: %NGINX_CONFIG%
echo [INFO] Frontend path: %FRONTEND_DIST_UNIX%

(
    echo # CaseStrainer Production Configuration
    echo # Generated: %DATE% %TIME%
    echo.
    echo worker_processes 1;
    echo error_log logs/error.log warn;
    echo.
    echo events {
    echo     worker_connections 1024;
    echo }
    echo.
    echo http {
    echo     include mime.types;
    echo     default_type application/octet-stream;
    echo     sendfile on;
    echo     keepalive_timeout 65;
    echo.
    echo     # Logging
    echo     access_log logs/access.log;
    echo.
    echo     # HTTP to HTTPS redirect
    echo     server {
    echo         listen 80;
    echo         server_name %SERVER_NAME% localhost;
            echo         return 301 https://$server_name$request_uri;
    echo     }
    echo.
    echo     # HTTPS server
    echo     server {
    echo         listen 443 ssl;
    echo         server_name %SERVER_NAME% localhost;
    echo.
    echo         # SSL Configuration
    echo         ssl_certificate "%SSL_CERT_PATH:\=/%";
    echo         ssl_certificate_key "%SSL_KEY_PATH:\=/%";
    echo         ssl_session_cache shared:SSL:1m;
    echo         ssl_session_timeout 10m;
    echo.
    echo         # Security headers
    echo         add_header X-Frame-Options SAMEORIGIN;
    echo         add_header X-Content-Type-Options nosniff;
    echo.
    echo         # Root redirect to CaseStrainer
    echo         location = / {
    echo             return 301 /casestrainer/;
    echo         }
    echo.
    echo         # Serve Vue static files
    echo         location /casestrainer/ {
    echo             alias "%FRONTEND_DIST_UNIX%/";
            echo             try_files $uri $uri/ @fallback;
    echo             expires 1h;
    echo             add_header Cache-Control "public";
    echo         }
    echo.
    echo         # Fallback for Vue Router ^(single page app^)
    echo         location @fallback {
    echo             rewrite ^/casestrainer/.*$ /casestrainer/index.html last;
    echo         }
    echo.
    echo         # API proxy to Flask backend
    echo         location /casestrainer/api/ {
    echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/api/;
    echo             proxy_set_header Host $host;
    echo             proxy_set_header X-Real-IP $remote_addr;
    echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    echo             proxy_set_header X-Forwarded-Proto $scheme;
    echo             proxy_connect_timeout 30;
    echo             proxy_send_timeout 30;
    echo             proxy_read_timeout 30;
    echo         }
    echo.
    echo         # Health check endpoint
    echo         location /health {
    echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/health;
    echo             access_log off;
    echo         }
    echo.
    echo         # Static assets with longer cache
    echo         location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    echo             alias "%FRONTEND_DIST_UNIX%/";
    echo             expires 1y;
    echo             add_header Cache-Control "public, immutable";
    echo         }
    echo     }
    echo }
) > "%NGINX_CONFIG%"

echo [OK] Nginx configuration created
echo.

:: Test Nginx configuration
echo [TEST] Testing Nginx configuration...
nginx.exe -t -c "%NGINX_CONFIG%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Nginx configuration test failed
    echo [INFO] Check the configuration file: %NGINX_CONFIG%
    pause
    exit /b 1
)
echo [OK] Nginx configuration is valid
echo.

:: Start Nginx
echo [START] Starting Nginx server...

:: Create Nginx startup script with logging
set "NGINX_SCRIPT=%TEMP%\start_nginx.bat"
(
    echo @echo off
    echo setlocal enabledelayedexpansion
    echo title CaseStrainer Nginx Server - HTTPS
    echo echo ============================================
    echo echo  CaseStrainer Nginx Server
    echo echo ============================================
    echo echo Config: %NGINX_CONFIG%
    echo echo HTTPS Port: 443
    echo echo HTTP Port: 80 ^(redirects to HTTPS^)
    echo echo Time: %%TIME%%
    echo echo ============================================
    echo echo.
    echo cd /d "%NGINX_DIR%"
    echo echo [NGINX] Starting with config: %NGINX_CONFIG%
    echo nginx.exe -c "%NGINX_CONFIG%"
    echo echo [NGINX] Nginx process started
    echo echo [NGINX] Check logs in: logs/error.log and logs/access.log
    echo echo [NGINX] Press Ctrl+C to stop Nginx
    echo echo.
    echo timeout /t -1
) > "%NGINX_SCRIPT%"

start "Nginx_Server" cmd /c "%NGINX_SCRIPT%"

echo [INFO] Waiting for Nginx to start...
timeout /t 5 /nobreak

:: Verify Nginx started
echo [VERIFY] Checking Nginx startup...
tasklist | findstr "nginx.exe" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Nginx process is running
) else (
    echo [ERROR] Nginx process not found
    echo [INFO] Check the Nginx window for error messages
    pause
    exit /b 1
)

:: Check HTTPS port
netstat -ano | findstr ":443 " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] HTTPS port 443 is active
) else (
    echo [WARNING] Port 443 not detected - may take a moment
)

:: Check HTTP port
netstat -ano | findstr ":80 " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] HTTP port 80 is active (redirects to HTTPS)
) else (
    echo [WARNING] Port 80 not detected
)

echo.
echo ===================================================
echo  CASESTRAINER DEPLOYMENT COMPLETED!
echo ===================================================
echo.
echo Services Status:
echo [RUNNING] Flask Backend: Port %PROD_BACKEND_PORT%
echo [RUNNING] Nginx HTTPS: Port 443
echo [RUNNING] Nginx HTTP: Port 80 (redirects)
echo.
echo Access URLs:
echo [PRIMARY] https://%SERVER_NAME%/casestrainer/
echo [LOCAL]   https://localhost/casestrainer/
echo [DIRECT]  http://localhost:%PROD_BACKEND_PORT% (Flask only)
echo.
echo Configuration Files:
echo [NGINX]   %NGINX_CONFIG%
echo [VUE]     %FRONTEND_DIR%\dist\
echo [FLASK]   %BACKEND_DIR%\app_final_vue.py
echo.
echo Logs:
echo [NGINX]   %NGINX_DIR%\logs\error.log
echo [NGINX]   %NGINX_DIR%\logs\access.log
echo.
echo Next Steps:
echo 1. Test local access: https://localhost/casestrainer/
echo 2. Test external access: https://%SERVER_NAME%/casestrainer/
echo 3. Ensure DNS points to this server's public IP
echo 4. Verify firewall allows ports 80 and 443
echo.
echo Press any key to open the application...
pause >nul

echo [INFO] Opening CaseStrainer application...
start "" "https://%SERVER_NAME%/casestrainer/"

echo.
echo Deployment complete! Both Flask and Nginx windows will remain open.
echo Close them manually when you're done testing.
pause