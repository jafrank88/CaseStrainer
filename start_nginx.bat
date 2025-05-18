@echo off
setlocal

REM === CONFIGURATION ===
set NGINX_DIR=%~dp0nginx-1.27.5
set PROD_CONF=%NGINX_DIR%\conf\nginx.conf
set TEST_CONF=%NGINX_DIR%\conf\nginx_test.conf

REM === CHOOSE CONFIGURATION ===
set CONFIG=%PROD_CONF%
if /i "%1"=="test" set CONFIG=%TEST_CONF%

echo.
echo ============================================
echo   Starting Nginx with config:
echo   %CONFIG%
echo ============================================
echo.

REM === STOP ANY RUNNING NGINX ===
cd /d "%NGINX_DIR%"
tasklist | find /i "nginx.exe" >nul 2>&1
if %errorlevel%==0 (
    echo Stopping existing Nginx instance...
    nginx.exe -s quit
    timeout /t 2 >nul
)

REM === START NGINX ===
nginx.exe -c "%CONFIG%"
if %errorlevel%==0 (
    echo Nginx started successfully.
) else (
    echo ERROR: Nginx failed to start. Check logs in %NGINX_DIR%\logs\error.log
)

pause
endlocal
