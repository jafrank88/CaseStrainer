@echo off
echo Stopping any running Python instances...
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im python3.exe /t >nul 2>&1

echo Starting CaseStrainer...
set FLASK_APP=src.app_final_vue
set FLASK_ENV=production
set HOST=0.0.0.0
set PORT=5000
set THREADS=4

start "CaseStrainer" cmd /k "cd /d %~dp0 && python -m flask run --host=%HOST% --port=%PORT% --with-threads --reload"

echo CaseStrainer is starting...
timeout /t 5 >nul
start http://localhost:%PORT%/casestrainer
