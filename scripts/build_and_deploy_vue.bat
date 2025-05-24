@echo off
REM ===================================================
REM CaseStrainer Vue.js Build and Deploy Script
REM ===================================================
REM
REM USAGE:
REM   Run this script to build and deploy the Vue.js frontend for production.
REM   Should be executed after making changes to the frontend code.
REM   This script will:
REM     - Check for Node.js and npm
REM     - Install dependencies if needed
REM     - Build the Vue.js frontend
REM     - Copy the built files to the appropriate static directory
REM ===================================================
echo ===================================================
echo CaseStrainer Vue.js Build and Deploy Script
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

REM Navigate to the Vue.js project directory
cd /d "%~dp0\..\casestrainer-vue"

REM Install dependencies
echo Installing dependencies...
call D:\node\node.exe D:\node\node_modules\npm\bin\npm-cli.js install
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

REM Build the Vue.js frontend
echo.
echo Building Vue.js frontend for production...
call D:\node\node.exe D:\node\node_modules\npm\bin\npm-cli.js run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed.
    exit /b 1
)

REM Create the static/vue directory if it doesn't exist
echo.
echo Creating static/vue directory...
cd /d "%~dp0\.."
if not exist "src\static\vue" mkdir "src\static\vue"

REM Copy the built files to the static/vue directory
echo Copying built files to static/vue directory...
xcopy /E /Y "%~dp0\..\casestrainer-vue\dist\*" "%~dp0\..\src\static\vue\"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to copy built files.
    exit /b 1
)

echo.
echo ===================================================
echo Vue.js frontend built and deployed successfully!
echo ===================================================
echo.
echo To start the application with the Vue.js frontend, run:
echo.
echo   python app_vue.py --host=0.0.0.0 --port=5000
echo.
echo The application will be accessible at:
echo   - Local: http://127.0.0.1:5000
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
