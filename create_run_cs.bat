@echo off
:: Create a working run_cs.bat using simple echo commands

echo Creating new run_cs.bat file...
cd /d "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"

:: Delete old file
del run_cs.bat 2>nul

:: Create new file line by line with echo
echo @echo off > run_cs.bat
echo setlocal enabledelayedexpansion >> run_cs.bat
echo. >> run_cs.bat
echo :: CaseStrainer Production Launcher >> run_cs.bat
echo. >> run_cs.bat
echo echo. >> run_cs.bat
echo echo ================================================ >> run_cs.bat
echo echo    CaseStrainer Production Deployment >> run_cs.bat
echo echo    Target: https://wolf.law.uw.edu/casestrainer >> run_cs.bat
echo echo ================================================ >> run_cs.bat
echo. >> run_cs.bat
echo :: Check admin >> run_cs.bat
echo net session ^>nul 2^>^&1 >> run_cs.bat
echo if %%ERRORLEVEL%% neq 0 ^( >> run_cs.bat
echo     echo [ERROR] Please run as administrator >> run_cs.bat
echo     pause >> run_cs.bat
echo     exit /b 1 >> run_cs.bat
echo ^) >> run_cs.bat
echo. >> run_cs.bat
echo set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer" >> run_cs.bat
echo set "NGINX_DIR=%%CASESTRAINER_DIR%%\nginx-1.27.5" >> run_cs.bat
echo set "FRONTEND_DIR=%%CASESTRAINER_DIR%%\casestrainer-vue-new" >> run_cs.bat
echo set "PROD_BACKEND_PORT=5002" >> run_cs.bat
echo set "SSL_CERT_PATH=D:\CaseStrainer\ssl\WolfCertBundle.crt" >> run_cs.bat
echo set "SSL_KEY_PATH=D:\CaseStrainer\ssl\wolf.law.uw.edu.key" >> run_cs.bat
echo. >> run_cs.bat
echo cd /d "%%CASESTRAINER_DIR%%" >> run_cs.bat
echo. >> run_cs.bat
echo echo [CONFIG] Backend Port: %%PROD_BACKEND_PORT%% >> run_cs.bat
echo echo [CONFIG] SSL Cert: %%SSL_CERT_PATH%% >> run_cs.bat
echo echo [CONFIG] Frontend: %%FRONTEND_DIR%% >> run_cs.bat
echo. >> run_cs.bat
echo :: Check Flask is running >> run_cs.bat
echo echo [INFO] Checking if Flask is running... >> run_cs.bat
echo netstat -ano ^| findstr :%%PROD_BACKEND_PORT%% ^| findstr LISTENING ^>nul >> run_cs.bat
echo if %%ERRORLEVEL%% equ 0 ^( >> run_cs.bat
echo     echo [OK] Flask is running on port %%PROD_BACKEND_PORT%% >> run_cs.bat
echo ^) else ^( >> run_cs.bat
echo     echo [ERROR] Flask is not running - start it first >> run_cs.bat
echo     pause >> run_cs.bat
echo     exit /b 1 >> run_cs.bat
echo ^) >> run_cs.bat
echo. >> run_cs.bat
echo :: Stop existing Nginx >> run_cs.bat
echo echo [INFO] Stopping existing Nginx... >> run_cs.bat
echo taskkill /IM nginx.exe /F ^>nul 2^>^&1 >> run_cs.bat
echo. >> run_cs.bat
echo :: Create simple Nginx config >> run_cs.bat
echo cd /d "%%NGINX_DIR%%" >> run_cs.bat
echo echo [INFO] Creating Nginx configuration... >> run_cs.bat
echo. >> run_cs.bat
echo echo worker_processes 1; ^> conf\simple.conf >> run_cs.bat
echo echo events { worker_connections 1024; } ^>^> conf\simple.conf >> run_cs.bat
echo echo http { ^>^> conf\simple.conf >> run_cs.bat
echo echo   include mime.types; ^>^> conf\simple.conf >> run_cs.bat
echo echo   server { ^>^> conf\simple.conf >> run_cs.bat
echo echo     listen 80; ^>^> conf\simple.conf >> run_cs.bat
echo echo     server_name wolf.law.uw.edu; ^>^> conf\simple.conf >> run_cs.bat
echo echo     return 301 https://^^^^server_name^^^^request_uri; ^>^> conf\simple.conf >> run_cs.bat
echo echo   } ^>^> conf\simple.conf >> run_cs.bat
echo echo   server { ^>^> conf\simple.conf >> run_cs.bat
echo echo     listen 443 ssl; ^>^> conf\simple.conf >> run_cs.bat
echo echo     server_name wolf.law.uw.edu; ^>^> conf\simple.conf >> run_cs.bat
echo echo     ssl_certificate "%%SSL_CERT_PATH%%"; ^>^> conf\simple.conf >> run_cs.bat
echo echo     ssl_certificate_key "%%SSL_KEY_PATH%%"; ^>^> conf\simple.conf >> run_cs.bat
echo echo     location /casestrainer/ { ^>^> conf\simple.conf >> run_cs.bat
echo echo       alias "%%FRONTEND_DIR:\=/%%/dist/"; ^>^> conf\simple.conf >> run_cs.bat
echo echo       try_files ^^^^uri ^^^^uri/ /casestrainer/index.html; ^>^> conf\simple.conf >> run_cs.bat
echo echo     } ^>^> conf\simple.conf >> run_cs.bat
echo echo     location /assets/ { ^>^> conf\simple.conf >> run_cs.bat
echo echo       alias "%%FRONTEND_DIR:\=/%%/dist/assets/"; ^>^> conf\simple.conf >> run_cs.bat
echo echo     } ^>^> conf\simple.conf >> run_cs.bat
echo echo     location /casestrainer/api/ { ^>^> conf\simple.conf >> run_cs.bat
echo echo       proxy_pass http://127.0.0.1:%%PROD_BACKEND_PORT%%/; ^>^> conf\simple.conf >> run_cs.bat
echo echo       proxy_set_header Host ^^^^host; ^>^> conf\simple.conf >> run_cs.bat
echo echo     } ^>^> conf\simple.conf >> run_cs.bat
echo echo   } ^>^> conf\simple.conf >> run_cs.bat
echo echo } ^>^> conf\simple.conf >> run_cs.bat
echo. >> run_cs.bat
echo :: Start Nginx >> run_cs.bat
echo echo [INFO] Starting Nginx... >> run_cs.bat
echo start nginx.exe -c conf\simple.conf >> run_cs.bat
echo timeout /t 3 >> run_cs.bat
echo. >> run_cs.bat
echo :: Check if Nginx started >> run_cs.bat
echo tasklist ^| findstr nginx.exe ^>nul >> run_cs.bat
echo if %%ERRORLEVEL%% equ 0 ^( >> run_cs.bat
echo     echo [SUCCESS] Nginx started successfully! >> run_cs.bat
echo     echo. >> run_cs.bat
echo     echo CaseStrainer is now live at: >> run_cs.bat
echo     echo https://wolf.law.uw.edu/casestrainer/ >> run_cs.bat
echo     echo. >> run_cs.bat
echo ^) else ^( >> run_cs.bat
echo     echo [ERROR] Nginx failed to start >> run_cs.bat
echo     echo Check logs in nginx-1.27.5\logs\ >> run_cs.bat
echo ^) >> run_cs.bat
echo. >> run_cs.bat
echo pause >> run_cs.bat

echo.
echo ================================================
echo New run_cs.bat file created successfully!
echo ================================================
echo.
echo Now testing the file...
echo.

:: Show first few lines to verify
echo [TEST] First 5 lines of new file:
echo ----------------------------------------
type run_cs.bat | more +1 | findstr /n "^" | head -5
echo ----------------------------------------
echo.

echo File created! You can now run: run_cs.bat
pause