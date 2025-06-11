@echo off
setlocal enabledelayedexpansion

:: Set the working directory to the script's directory
cd /d "%~dp0"

:: Navigate to the Vue.js project directory
cd casestrainer-vue-new

echo Installing dependencies...
npm install

if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Starting Vue.js development server...
start "Vue.js Dev Server" cmd /k "npm run dev"

echo Vue.js development server is starting...
echo It should be available at: http://localhost:5173
echo.
pause
