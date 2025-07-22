@echo off
set NGINX_DIR=%~dp0nginx
cd /d %NGINX_DIR%
start "" nginx.exe -p %NGINX_DIR% -c conf/nginx.conf

REM Wait a moment for Nginx to start
timeout /t 2 >nul

echo Checking if Nginx is running...
tasklist /fi "imagename eq nginx.exe" | find "nginx.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo Nginx started successfully.
    echo You can access the application at: http://localhost/casestrainer/
) else (
    echo Failed to start Nginx. Please check the error logs in %NGINX_DIR%\logs\error.log
    pause
)
