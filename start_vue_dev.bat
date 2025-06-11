@echo off
echo Starting Vue.js Development Environment...

REM Check if Docker is running
docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Building and starting Docker containers...
cd /d "%~dp0casestrainer-vue-new"
docker-compose up --build -d

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to start Docker containers.
    echo Please check if Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Vue.js Development Server is starting...
echo ========================================
echo.
echo Once the build is complete, you can access the application at:
echo http://localhost:5173
echo.
echo To stop the development server, run: docker-compose down
echo.

REM Open the application in the default browser
start http://localhost:5173

pause
