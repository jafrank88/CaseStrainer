@echo off
echo Starting Vue.js development server...
echo =================================

REM Change to the Vue project directory
cd /d "%~dp0casestrainer-vue-new"

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules\vite" (
    echo Installing dependencies...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting development server...
echo.
echo Once the server starts, you can access the app at:
echo http://localhost:5173
echo.

REM Start the development server with explicit host and port
call npx vite --host 0.0.0.0 --port 5173

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    pause
    exit /b 1
)

pause
