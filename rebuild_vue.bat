@echo off
setlocal enabledelayedexpansion

echo Cleaning up previous build artifacts...

REM Navigate to Vue project directory
cd /d "%~dp0casestrainer-vue-new"

REM Remove node_modules and package-lock.json
if exist node_modules (
    echo Removing node_modules...
    rmdir /s /q node_modules
)

if exist package-lock.json (
    echo Removing package-lock.json...
    del /f package-lock.json
)

echo Cleaning npm cache...
npm cache clean --force

echo Installing dependencies...
npm install

if %ERRORLEVEL% NEQ 0 (
    echo Error during npm install. Please check the error messages above.
    exit /b %ERRORLEVEL%
)

echo Building Vue application...
npm run build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================
    echo Vue.js build completed successfully!
    echo ===============================================
) else (
    echo.
    echo ===============================================
    echo Error during Vue.js build. Please check the logs.
    echo ===============================================
    exit /b %ERRORLEVEL%
)

endlocal
