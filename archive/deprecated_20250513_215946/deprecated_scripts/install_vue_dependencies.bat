@echo off
echo ===================================================
echo CaseStrainer Vue.js Dependencies Installation
echo ===================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script is not running as Administrator.
    echo Some features like installing system packages may not work properly.
    echo.
    echo Continuing automatically...
    timeout /t 2 /nobreak >nul
)

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in the PATH.
    echo Please install Python 3.8 or higher.
    exit /b 1
)
echo Python is installed. Proceeding...

REM Install Python dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies.
    exit /b 1
)
echo Python dependencies installed successfully.

REM Check if Node.js is installed
echo.
echo Checking Node.js installation...
where npm >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Node.js is not installed or not in the PATH.
    echo The Vue.js frontend cannot be built without Node.js.
    echo.
    echo Would you like to:
    echo 1. Continue without Node.js (you'll need to install it later)
    echo 2. Exit and install Node.js manually
    echo.
    set /p NODE_CHOICE=Enter your choice (1 or 2): 
    
    if "%NODE_CHOICE%"=="2" (
        echo.
        echo Please download and install Node.js from https://nodejs.org/
        echo Then run this script again.
        exit /b 1
    )
    
    echo.
    echo Continuing without Node.js. You'll need to install it later to build the Vue.js frontend.
) else (
    echo Node.js is installed. Proceeding...
    
    REM Check npm version
    for /f "tokens=1,2,3 delims=." %%a in ('npm --version') do (
        set NPM_MAJOR=%%a
        set NPM_MINOR=%%b
    )
    
    if %NPM_MAJOR% LSS 6 (
        echo WARNING: npm version is less than 6.0.0
        echo You may encounter issues building the Vue.js frontend.
        echo Consider upgrading npm: npm install -g npm@latest
    )
    
    REM Install Vue CLI globally
    echo.
    echo Installing Vue CLI globally...
    npm install -g @vue/cli
    if %errorLevel% neq 0 (
        echo WARNING: Failed to install Vue CLI globally.
        echo You may encounter issues building the Vue.js frontend.
    ) else (
        echo Vue CLI installed successfully.
    )
)

REM Create necessary directories
echo.
echo Creating necessary directories...
if not exist "static" mkdir "static"
if not exist "static\vue" mkdir "static\vue"
echo Directories created successfully.

REM Check Docker installation
echo.
echo Checking Docker installation...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Docker is not installed or not running.
    echo The application may not be accessible through the Nginx proxy.
    echo.
    echo Please install Docker Desktop if you need to use the Nginx proxy.
) else (
    echo Docker is installed. Proceeding...
    
    REM Check if Docker is running
    docker ps >nul 2>&1
    if %errorLevel% neq 0 (
        echo WARNING: Docker is installed but not running.
        echo Starting Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Waiting for Docker to start (30 seconds)...
        timeout /t 30 /nobreak >nul
    )
    
    REM Check Nginx container
    echo Checking Nginx container...
    docker ps | findstr nginx >nul 2>&1
    if %errorLevel% neq 0 (
        echo WARNING: Nginx container is not running.
        echo.
        echo Would you like to:
        echo 1. Start the Nginx container (if it exists)
        echo 2. Continue without starting the Nginx container
        echo.
        set /p NGINX_CHOICE=Enter your choice (1 or 2): 
        
        if "%NGINX_CHOICE%"=="1" (
            echo.
            echo Starting Nginx container...
            docker start docker-nginx-1 >nul 2>&1
            if %errorLevel% neq 0 (
                echo ERROR: Failed to start Nginx container.
                echo The container may not exist or there might be an issue with Docker.
            ) else {
                echo Nginx container started successfully.
            }
        )
    ) else {
        echo Nginx container is running.
    }
)

echo.
echo ===================================================
echo Installation completed!
echo ===================================================
echo.
echo Next steps:
echo 1. Build the Vue.js frontend:
echo    .\build_and_deploy_vue.bat
echo.
echo 2. Start the application:
echo    .\start_vue.bat
echo.
echo The application will be accessible at:
echo - Local: http://127.0.0.1:5000
echo - External: https://wolf.law.uw.edu/casestrainer/
echo.

pause
