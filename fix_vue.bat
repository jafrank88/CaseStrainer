@echo off

:: ============================================
:: fix_vue.bat - CaseStrainer Vue.js Development Setup
:: 
:: This script sets up the Vue.js development environment using Vite.
:: Last updated: 2025-06-06
:: ============================================

:: Set error handling
setlocal enabledelayedexpansion

:: Change to the script's directory
cd /d "%~dp0"

:: Check if we're in the correct directory
if not exist "casestrainer-vue-new" (
    echo Error: casestrainer-vue-new directory not found!
    echo Please run this script from the CaseStrainer root directory.
    pause
    exit /b 1
)

:: Clean up old build artifacts
echo Cleaning up build artifacts...
if exist "casestrainer-vue-new\node_modules" rmdir /s /q "casestrainer-vue-new\node_modules"
if exist "casestrainer-vue-new\dist" rmdir /s /q "casestrainer-vue-new\dist"
if exist "casestrainer-vue-new\.vite" rmdir /s /q "casestrainer-vue-new\.vite"
if exist "casestrainer-vue-new\package-lock.json" del "casestrainer-vue-new\package-lock.json"

:: Change to the Vue.js project directory
cd "casestrainer-vue-new"

:: Install dependencies
echo Installing dependencies...
call npm install
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies. Please check the error above.
    pause
    exit /b 1
)

:: Start the Vite development server
echo Starting Vite development server...
start "Vue Dev Server (Vite)" cmd /k "npm run dev"

:: Provide information to the user
echo.
echo ============================================
echo Development server is starting...
echo.
echo The application should be available at:
echo http://localhost:5173/
echo.
echo If the browser doesn't open automatically,
echo please open the URL above manually.
echo ============================================
echo.

endlocal
