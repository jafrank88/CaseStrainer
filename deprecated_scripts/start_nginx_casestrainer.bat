@echo off
setlocal

set NGINX_PATH=%~dp0nginx-1.27.5\nginx.exe
set NGINX_CONFIG=%~dp0nginx-1.27.5\conf\casestrainer.conf
set NGINX_DIR=%~dp0nginx-1.27.5

echo Stopping any running Nginx instances...
taskkill /f /im nginx.exe >nul 2>&1

echo Starting Nginx with CaseStrainer configuration...
cd /d "%NGINX_DIR%"
"%NGINX_PATH%" -c "%NGINX_CONFIG%" -p "%NGINX_DIR%"

if %ERRORLEVEL% EQU 0 (
    echo Nginx started successfully
    echo Access the application at: https://wolf.law.uw.edu/casestrainer/
) else (
    echo Failed to start Nginx
    echo Check the error logs at: %NGINX_DIR%\logs\casestrainer_error.log
)

endlocal
