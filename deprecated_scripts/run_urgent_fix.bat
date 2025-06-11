@echo off
:: Emergency file replacement for corrupted run_cs.bat

echo ================================================
echo    Emergency run_cs.bat File Replacement
echo ================================================

cd /d "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"

:: Backup the corrupted file
echo [STEP 1] Backing up corrupted file...
if exist "run_cs.bat" (
    copy "run_cs.bat" "run_cs_corrupted_backup.bat" >nul
    echo [OK] Backup created: run_cs_corrupted_backup.bat
)

:: Delete the corrupted file completely
echo [STEP 2] Removing corrupted file...
del "run_cs.bat" 2>nul
echo [OK] Corrupted file deleted

:: Create new clean file using PowerShell (most reliable)
echo [STEP 3] Creating new clean file...
powershell -Command "& {
$content = @'
@echo off
setlocal enabledelayedexpansion

:: CaseStrainer Production Launcher - Emergency Clean Version

echo.
echo ================================================
echo    CaseStrainer Production Deployment
echo    Target: https://wolf.law.uw.edu/casestrainer  
echo ================================================

:: Check admin
net session >nul 2>&1
if %%ERRORLEVEL%% neq 0 (
    echo [ERROR] Please run as administrator
    pause
    exit /b 1
)

set CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer
set NGINX_DIR=%%CASESTRAINER_DIR%%\nginx-1.27.5
set FRONTEND_DIR=%%CASESTRAINER_DIR%%\casestrainer-vue-new

cd /d %%CASESTRAINER_DIR%%

:: Load config
echo [INFO] Loading configuration...
set SSL_CERT_PATH=D:\CaseStrainer\ssl\WolfCertBundle.crt
set SSL_KEY_PATH=D:\CaseStrainer\ssl\wolf.law.uw.edu.key
set PROD_BACKEND_PORT=5002
set SERVER_NAME=wolf.law.uw.edu

echo [CONFIG] Backend Port: %%PROD_BACKEND_PORT%%
echo [CONFIG] SSL Cert: %%SSL_CERT_PATH%%

:: Check Flask is running
echo [INFO] Checking if Flask is running on port %%PROD_BACKEND_PORT%%...
netstat -ano | findstr :%%PROD_BACKEND_PORT%% | findstr LISTENING >nul
if %%ERRORLEVEL%% equ 0 (
    echo [OK] Flask is already running
) else (
    echo [ERROR] Flask is not running - start it first
    pause
    exit /b 1
)

:: Stop existing Nginx
echo [INFO] Stopping existing Nginx...
taskkill /IM nginx.exe /F >nul 2>&1

:: Start Nginx with simple config
cd /d %%NGINX_DIR%%

echo [INFO] Creating simple Nginx config...
echo worker_processes 1; > conf\simple.conf
echo events { worker_connections 1024; } >> conf\simple.conf
echo http { >> conf\simple.conf
echo   include mime.types; >> conf\simple.conf
echo   server { >> conf\simple.conf
echo     listen 80; >> conf\simple.conf
echo     server_name wolf.law.uw.edu; >> conf\simple.conf
echo     return 301 https://^^server_name^^request_uri; >> conf\simple.conf
echo   } >> conf\simple.conf
echo   server { >> conf\simple.conf
echo     listen 443 ssl; >> conf\simple.conf
echo     server_name wolf.law.uw.edu; >> conf\simple.conf
echo     ssl_certificate \"D:\CaseStrainer\ssl\WolfCertBundle.crt\"; >> conf\simple.conf
echo     ssl_certificate_key \"D:\CaseStrainer\ssl\wolf.law.uw.edu.key\"; >> conf\simple.conf
echo     location /casestrainer/ { >> conf\simple.conf
echo       alias \"%%FRONTEND_DIR:\=/%%/dist/\"; >> conf\simple.conf
echo       try_files ^^uri ^^uri/ /casestrainer/index.html; >> conf\simple.conf
echo     } >> conf\simple.conf
echo     location /assets/ { >> conf\simple.conf
echo       alias \"%%FRONTEND_DIR:\=/%%/dist/assets/\"; >> conf\simple.conf
echo     } >> conf\simple.conf
echo     location /casestrainer/api/ { >> conf\simple.conf
echo       proxy_pass http://127.0.0.1:%%PROD_BACKEND_PORT%%/; >> conf\simple.conf
echo     } >> conf\simple.conf
echo   } >> conf\simple.conf
echo } >> conf\simple.conf

echo [INFO] Starting Nginx...
start nginx.exe -c conf\simple.conf

timeout /t 3

tasklist | findstr nginx.exe >nul
if %%ERRORLEVEL%% equ 0 (
    echo [SUCCESS] Nginx started successfully!
    echo.
    echo CaseStrainer is now live at:
    echo https://wolf.law.uw.edu/casestrainer/
    echo.
) else (
    echo [ERROR] Nginx failed to start
)

pause
'@

$content | Out-File -FilePath 'run_cs.bat' -Encoding ASCII -NoNewline
}"

if exist "run_cs.bat" (
    echo [SUCCESS] New clean file created
) else (
    echo [ERROR] Failed to create new file
    pause
    exit /b 1
)

:: Test the new file
echo [STEP 4] Testing new file...
echo [INFO] First few lines of new file:
type "run_cs.bat" | more +1 | findstr /n "^" | head -5

echo.
echo ================================================
echo File replacement complete!
echo.
echo Next steps:
echo 1. Run: run_cs.bat
echo 2. It should work without corruption errors
echo ================================================
pause