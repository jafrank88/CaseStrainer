@echo off
echo Creating a clean Vue.js development environment...
echo ===============================================

REM Create a clean directory
set "CLEAN_DIR=%~dp0casestrainer-vue-clean"

REM Remove existing directory if it exists
if exist "%CLEAN_DIR%" (
    echo Removing existing directory...
    rmdir /s /q "%CLEAN_DIR%"
)

echo Creating new Vue.js project...
call npx create-vue@latest "%CLEAN_DIR%" --default --force

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to create Vue.js project.
    pause
    exit /b 1
)

REM Change to the project directory
cd /d "%CLEAN_DIR%"

echo.
echo Installing dependencies...
call npm install

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting development server...
echo.
echo The application should open automatically in your browser.
echo If it doesn't, please visit: http://localhost:5173
echo.

call npm run dev

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    pause
    exit /b 1
)

pause
