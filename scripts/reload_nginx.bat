@echo off
echo Reloading Nginx configuration...
cd /d "%~dp0\..\nginx"
nginx.exe -s reload
if %errorlevel% equ 0 (
    echo Nginx configuration reloaded successfully.
) else (
    echo Failed to reload Nginx configuration.
)
pause
