@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: Manual CaseStrainer Deployment
:: Bypasses the problematic network verification
:: ===================================================

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ===================================================
    echo   ADMINISTRATOR PRIVILEGES REQUIRED
    echo ===================================================
    echo Please right-click this script and "Run as administrator"
    pause
    exit /b 1
)

:: Define paths
set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "BACKEND_DIR=%CASESTRAINER_DIR%\src"
set "FRONTEND_DIR=%CASESTRAINER_DIR%\casestrainer-vue-new"
set "NGINX_DIR=%CASESTRAINER_DIR%\nginx-1.27.5"

echo.
echo ===================================================
echo  Manual CaseStrainer Deployment
echo ===================================================
echo Time: %DATE% %TIME%
echo.

:: Change to CaseStrainer directory
cd /d "%CASESTRAINER_DIR%"
echo [INFO] Working directory: %CD%
echo.

:: Load configuration manually
echo [STEP 1] Loading configuration...
if not exist "config.ini" (
    echo [ERROR] config.ini not found
    pause
    exit /b 1
)

:: Extract key config values
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SSL_CERT_PATH"') do set "SSL_CERT_PATH=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SSL_KEY_PATH"') do set "SSL_KEY_PATH=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "SERVER_NAME"') do set "SERVER_NAME=%%b"
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "PROD_BACKEND_PORT"') do set "PROD_BACKEND_PORT=%%b"

echo [OK] SSL Certificate: %SSL_CERT_PATH%
echo [OK] SSL Key: %SSL_KEY_PATH%
echo [OK] Server: %SERVER_NAME%
echo [OK] Backend Port: %PROD_BACKEND_PORT%
echo.

:: Choose deployment mode manually
echo [STEP 2] Choose Deployment Mode:
echo.
echo 1. FLASK STATIC MODE
echo    - Serves Vue files directly from Flask
echo    - Single server process
echo    - Recommended for production
echo.
echo 2. NGINX STATIC MODE  
echo    - Nginx serves static files + proxies API
echo    - Best performance with your SSL setup
echo    - Recommended for your configuration
echo.
echo 3. DEVELOPMENT SERVER MODE
echo    - Vue dev server with hot reloading
echo    - Good for development
echo.
set /p "deploy_choice=Enter your choice (1, 2, or 3): "

if "%deploy_choice%"=="1" (
    set "DEPLOYMENT_MODE=flask-static"
    echo [SELECTED] Flask Static Mode
) else if "%deploy_choice%"=="2" (
    set "DEPLOYMENT_MODE=nginx-static"
    echo [SELECTED] Nginx Static Mode
) else if "%deploy_choice%"=="3" (
    set "DEPLOYMENT_MODE=dev-server"
    echo [SELECTED] Development Server Mode
) else (
    echo [ERROR] Invalid choice, defaulting to Nginx Static
    set "DEPLOYMENT_MODE=nginx-static"
)
echo.

:: Execute deployment based on choice
if "%DEPLOYMENT_MODE%"=="nginx-static" (
    call :deploy_nginx_mode
) else if "%DEPLOYMENT_MODE%"=="flask-static" (
    call :deploy_flask_mode
) else (
    call :deploy_dev_mode
)

echo.
echo ===================================================
echo [COMPLETED] Manual deployment finished
echo ===================================================
echo.
echo Access your application at:
echo https://%SERVER_NAME%/casestrainer/
echo.
echo Press any key to exit...
pause >nul
exit /b 0

:: ===================================================
:: DEPLOYMENT FUNCTIONS
:: ===================================================

:deploy_nginx_mode
    echo [STEP 3] Nginx Static Deployment
    echo.
    
    echo [3.1] Building Vue application...
    cd /d "%FRONTEND_DIR%"
    
    if not exist "node_modules" (
        echo [INFO] Installing npm dependencies...
        npm install
        if %ERRORLEVEL% neq 0 (
            echo [ERROR] npm install failed
            pause
            exit /b 1
        )
    )
    
    echo [INFO] Building production Vue app...
    set "NODE_ENV=production"
    npm run build
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Vue build failed
        pause
        exit /b 1
    )
    
    if not exist "dist\index.html" (
        echo [ERROR] Build output not found
        pause
        exit /b 1
    )
    echo [OK] Vue build completed
    
    echo [3.2] Starting Flask backend...
    cd /d "%BACKEND_DIR%"
    
    start "CaseStrainer_Flask" cmd /c "python app_final_vue.py --port=%PROD_BACKEND_PORT% --host=0.0.0.0"
    
    echo [INFO] Waiting for Flask to start...
    timeout /t 10 /nobreak >nul
    
    netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] Flask backend started on port %PROD_BACKEND_PORT%
    ) else (
        echo [WARNING] Flask may not have started properly
    )
    
    echo [3.3] Configuring Nginx...
    cd /d "%NGINX_DIR%"
    
    :: Create simple nginx config
    set "NGINX_CONFIG=%NGINX_DIR%\conf\casestrainer.conf"
    call :create_nginx_config
    
    echo [3.4] Starting Nginx...
    nginx.exe -t -c "%NGINX_CONFIG%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Nginx config test failed
        pause
        exit /b 1
    )
    
    start "CaseStrainer_Nginx" nginx.exe -c "%NGINX_CONFIG%"
    
    echo [INFO] Waiting for Nginx to start...
    timeout /t 5 /nobreak >nul
    
    tasklist | findstr "nginx.exe" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] Nginx started successfully
    ) else (
        echo [WARNING] Nginx may not have started
    )
    
    exit /b 0

:create_nginx_config
    set "FRONTEND_DIST_UNIX=%FRONTEND_DIR:\=/%/dist"
    
    (
        echo worker_processes 1;
        echo events { worker_connections 1024; }
        echo http {
        echo     include mime.types;
        echo     default_type application/octet-stream;
        echo.
        echo     server {
        echo         listen 80;
        echo         server_name %SERVER_NAME% localhost;
        echo         return 301 https://$server_name$request_uri;
        echo     }
        echo.
        echo     server {
        echo         listen 443 ssl;
        echo         server_name %SERVER_NAME% localhost;
        echo.
        echo         ssl_certificate "%SSL_CERT_PATH:\=/%";
        echo         ssl_certificate_key "%SSL_KEY_PATH:\=/%";
        echo.
        echo         location = / {
        echo             return 301 /casestrainer/;
        echo         }
        echo.
        echo         location /casestrainer/ {
        echo             alias "%FRONTEND_DIST_UNIX%/";
        echo             try_files $uri $uri/ /index.html;
        echo         }
        echo.
        echo         location /casestrainer/api/ {
        echo             proxy_pass http://127.0.0.1:%PROD_BACKEND_PORT%/api/;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo     }
        echo }
    ) > "%NGINX_CONFIG%"
    exit /b 0

:deploy_flask_mode
    echo [STEP 3] Flask Static Deployment
    echo [INFO] This mode serves Vue files directly from Flask
    echo [ERROR] Flask static mode not implemented in manual version
    echo [INFO] Please use Nginx mode or fix the main script
    pause
    exit /b 1

:deploy_dev_mode
    echo [STEP 3] Development Server Deployment  
    echo [ERROR] Dev server mode not implemented in manual version
    echo [INFO] Please use Nginx mode or fix the main script
    pause
    exit /b 1