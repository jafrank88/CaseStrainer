@echo off
echo Setting up Vue.js development environment...
echo =========================================

REM Change to the Vue project directory
cd /d "%~dp0casestrainer-vue-new"

REM Clean up any previous installations
echo Cleaning up previous installations...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

REM Install dependencies
echo Installing dependencies...
call npm install

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Start the development server
echo.
echo Starting development server...
echo The application should open automatically in your browser.
echo If it doesn't, please visit: http://localhost:5173
echo.

call npx vite --host 0.0.0.0 --port 5173

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
