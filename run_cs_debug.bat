@chcp 65001 >nul 2>&1
@echo off
setlocal enabledelayedexpansion

:: Debug CaseStrainer Deployment Status
:: Check if services are running and diagnose issues

echo.
echo ================================================
echo    CaseStrainer Deployment Diagnostic
echo ================================================
echo Time: %DATE% %TIME%
echo.

:: Define paths from your setup
set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "NGINX_DIR=%CASESTRAINER_DIR%\nginx-1.27.5"

echo [STEP 1] Checking Flask Backend Status...
echo.

:: Check if Flask is running on port 5002
netstat -ano | findstr ":5002 " | findstr "LISTENING"
if %ERRORLEVEL% equ 0 (
    echo [OK] Flask is listening on port 5002
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5002 " ^| findstr "LISTENING"') do (
        echo [INFO] Flask process ID: %%a
    )
) else (
    echo [ERROR] Flask is NOT running on port 5002
    echo [DEBUG] Checking what's on port 5002...
    netstat -ano | findstr ":5002"
    if %ERRORLEVEL% neq 0 (
        echo [INFO] Nothing is listening on port 5002
    )
)

echo.
echo [STEP 2] Checking Nginx Status...
echo.

:: Check if Nginx process is running
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo [OK] Nginx process is running
    tasklist /FI "IMAGENAME eq nginx.exe"
) else (
    echo [ERROR] Nginx process is NOT running
)

:: Check if ports 80 and 443 are listening
echo.
echo [INFO] Checking web server ports...
netstat -ano | findstr ":80 " | findstr "LISTENING"
if %ERRORLEVEL% equ 0 (
    echo [OK] Something is listening on port 80
) else (
    echo [WARNING] Nothing listening on port 80
)

netstat -ano | findstr ":443 " | findstr "LISTENING"
if %ERRORLEVEL% equ 0 (
    echo [OK] Something is listening on port 443 (HTTPS)
) else (
    echo [WARNING] Nothing listening on port 443 (HTTPS)
)

echo.
echo [STEP 3] Checking Configuration Files...
echo.

:: Check if config.env exists
if exist "%CASESTRAINER_DIR%\config.env" (
    echo [OK] config.env found
    echo [INFO] Backend port from config:
    findstr "PROD_BACKEND_PORT" "%CASESTRAINER_DIR%\config.env"
) else (
    echo [WARNING] config.env not found in %CASESTRAINER_DIR%
)

:: Check if Nginx directory exists
if exist "%NGINX_DIR%" (
    echo [OK] Nginx directory found: %NGINX_DIR%
    if exist "%NGINX_DIR%\nginx.exe" (
        echo [OK] nginx.exe found
    ) else (
        echo [ERROR] nginx.exe not found in %NGINX_DIR%
    )
) else (
    echo [ERROR] Nginx directory not found: %NGINX_DIR%
)

:: Check if Nginx config was created
if exist "%NGINX_DIR%\conf\nginx_production.conf" (
    echo [OK] Production Nginx config found
) else (
    echo [WARNING] Production Nginx config not found
)

echo.
echo [STEP 4] Checking SSL Certificates...
echo.

:: Check SSL certificate paths from config
if exist "%CASESTRAINER_DIR%\config.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("%CASESTRAINER_DIR%\config.env") do (
        if "%%a"=="SSL_CERT_PATH" set "SSL_CERT_PATH=%%b"
        if "%%a"=="SSL_KEY_PATH" set "SSL_KEY_PATH=%%b"
    )
    
    if defined SSL_CERT_PATH (
        echo [INFO] SSL Cert Path: !SSL_CERT_PATH!
        if exist "!SSL_CERT_PATH!" (
            echo [OK] SSL certificate found
        ) else (
            echo [ERROR] SSL certificate NOT found at !SSL_CERT_PATH!
        )
    )
    
    if defined SSL_KEY_PATH (
        echo [INFO] SSL Key Path: !SSL_KEY_PATH!
        if exist "!SSL_KEY_PATH!" (
            echo [OK] SSL key found
        ) else (
            echo [ERROR] SSL key NOT found at !SSL_KEY_PATH!
        )
    )
)

echo.
echo [STEP 5] Network Connectivity Test...
echo.

:: Test local connectivity
echo [INFO] Testing local connection to Flask backend...
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://127.0.0.1:5002/ 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Local Flask backend responded
) else (
    echo [WARNING] Could not connect to local Flask backend
    echo [INFO] This might be normal if Flask isn't running
)

echo.
echo [INFO] Testing external domain resolution...
nslookup wolf.law.uw.edu
echo.

echo.
echo ================================================
echo              Diagnostic Summary
echo ================================================
echo.
echo [NEXT STEPS]
echo 1. If Flask is not running: Start the deployment script
echo 2. If Nginx is not running: Check nginx error logs
echo 3. If SSL certs are missing: Verify certificate paths
echo 4. If ports aren't listening: Check firewall settings
echo 5. If domain doesn't resolve: Check DNS configuration
echo.
echo [LOGS TO CHECK]
if exist "%NGINX_DIR%\logs\error.log" (
    echo - Nginx Error Log: %NGINX_DIR%\logs\error.log
) else (
    echo - Nginx Error Log: Not found (check %NGINX_DIR%\logs\)
)
echo - Flask Window: Check the Flask console window for errors
echo.
echo Press any key to exit...
pause >nul