@echo off

:: Stop Windows Nginx if running
taskkill /F /IM nginx.exe 2>nul

:: Verify Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

:: Stop existing containers
echo Stopping existing containers...
docker-compose down

:: Build and start containers
echo Starting Docker containers...
docker-compose build
docker-compose up -d

:: Verify containers are running
echo Verifying containers are running...
docker-compose ps

:: Verify Nginx configuration
echo Verifying Nginx configuration...
docker-compose exec nginx nginx -t
if %errorlevel% neq 0 (
    echo Nginx configuration test failed. Please check nginx.conf.
    exit /b 1
)

echo Nginx proxy configuration updated successfully.
echo Application should now be accessible at https://wolf.law.uw.edu/casestrainer/
