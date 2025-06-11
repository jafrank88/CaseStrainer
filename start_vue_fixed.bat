@echo off
echo Starting Vue.js development server on port 5173...
echo ===========================================

REM Change to the Vue project directory
cd /d "%~dp0casestrainer-vue-new"

REM Kill any running Node.js processes
echo Stopping any running Node.js processes...
taskkill /F /IM node.exe >nul 2>&1

REM Wait a moment for processes to close
timeout /t 2 /nobreak >nul

REM Start the development server with the fixed config
echo Starting Vite development server...
echo.
echo The application should automatically open in your browser at:
echo http://localhost:5173
echo.

call npx vite --config vite.fixed.config.js

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
