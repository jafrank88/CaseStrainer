@echo off
echo Stopping any running Node.js processes...
echo ===================================

taskkill /F /IM node.exe >nul 2>&1

REM Wait a moment for processes to close
timeout /t 2 /nobreak >nul

echo.
echo Starting Vue.js development server...
echo ================================

REM Change to the Vue project directory
cd /d "%~dp0casestrainer-vue-new"

REM Start the development server with explicit host and port
echo Starting Vite development server...
echo.
echo Once the server starts, you can access the app at:
echo http://localhost:5173
echo.

call npx vite --host 0.0.0.0 --port 5173

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    pause
    exit /b 1
)

pause
