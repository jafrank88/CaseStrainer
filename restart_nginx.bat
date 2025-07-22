@echo off
echo Stopping Nginx...
taskkill /F /IM nginx.exe

echo Starting Nginx...
start "" "nginx\nginx.exe"

echo Nginx restarted successfully.
pause
