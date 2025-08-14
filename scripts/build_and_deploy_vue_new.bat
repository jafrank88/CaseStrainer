@echo off
REM ===================================================
REM CaseStrainer Vue.js Build and Deploy Script (Updated for casestrainer-vue-new)
REM ===================================================
REM
REM USAGE:
REM   Run this script to build and deploy the Vue.js frontend for production.
REM   Should be executed after making changes to the frontend code.
REM   This script will:
REM     - Check for Node.js and npm
REM     - Run the deploy.ps1 script in casestrainer-vue-new
REM     - Ensure the static/vue directory is properly populated
REM ===================================================
echo ===================================================
echo CaseStrainer Vue.js Build and Deploy Script
echo (Updated for casestrainer-vue-new)
echo ===================================================
echo.

REM Check if Node.js and npm are available
if not exist "D:\node\node.exe" (
    echo ERROR: Node.js executable not found at D:\node\node.exe
    echo Please ensure Node.js is installed at the correct location.
    exit /b 1
)

if not exist "D:\node\node_modules\npm\bin\npm-cli.js" (
    echo ERROR: npm not found at D:\node\node_modules\npm\bin\npm-cli.js
    echo Please ensure npm is installed at the correct location.
    exit /b 1
)

echo Node.js and npm are installed. Proceeding with build...
echo.

REM Run the deploy.ps1 script in casestrainer-vue-new
echo Running deploy.ps1 from casestrainer-vue-new...
cd /d "%~dp0\..\casestrainer-vue-new"
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Frontend build and deployment failed.
    exit /b 1
)

echo.
echo ===================================================
echo Vue.js frontend built and deployed successfully!
echo ===================================================
echo.
echo The built frontend has been copied to: %~dp0\..\static\vue
echo.
echo To start the application with the Vue.js frontend, run:
echo.
echo   D:\Python\python.exe src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress
echo.
echo The application will be accessible at:
echo   - Local: http://127.0.0.1:5000/casestrainer/
echo   - External: https://wolf.law.uw.edu/casestrainer/
echo.

REM Ask if the user wants to start the application
set /p START_APP=Do you want to start the application now? (Y/N): 
if /i "%START_APP%"=="Y" (
    echo.
    echo Starting CaseStrainer with Vue.js frontend...
    cd /d "%~dp0\.."
    D:\Python\python.exe src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress
) else (
    echo.
    echo You can start the application later by running:
    echo   D:\Python\python.exe src\app_final_vue.py --host=0.0.0.0 --port=5000 --use-waitress
)

pause
