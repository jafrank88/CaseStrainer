@echo off
echo Setting up Vue.js development environment...
echo ==========================================

REM Check if Docker is running
docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Clean up any existing containers
echo.
echo Cleaning up any existing containers...
docker stop vue-dev 2>nul
docker rm vue-dev 2>nul

REM Start the development container
echo.
echo Starting Vue.js development server...
echo This may take a few minutes on first run...
echo.
echo Once the server starts, you can access the app at:
echo http://localhost:5173
echo.

docker run -it --rm ^
  --name vue-dev ^
  -v "%CD%\casestrainer-vue-new:/app" ^
  -w /app ^
  -p 5173:5173 ^
  node:18-alpine ^
  sh -c "npm install && npm run dev -- --host"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start the development server.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
