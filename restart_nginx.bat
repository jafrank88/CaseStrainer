@echo off
echo Stopping Nginx...
taskkill /F /IM nginx.exe

echo Starting Nginx...
start "" "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe"

echo Nginx restarted successfully.
pause
