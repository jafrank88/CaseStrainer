@echo off
echo ===================================================
echo CaseStrainer Nginx Configuration Update
echo ===================================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script is not running as Administrator.
    echo Some features may not work properly.
    echo.
    echo Continuing automatically...
    timeout /t 2 /nobreak >nul
)

:: Check Docker status
echo Checking Docker status...
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Docker does not appear to be running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: Check if Nginx container is running
echo Checking Nginx container status...
docker ps | findstr nginx >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Nginx container is not running.
    echo Attempting to start the Nginx container...
    docker start docker-nginx-1 >nul 2>&1
    
    if %errorLevel% neq 0 (
        echo ERROR: Failed to start Nginx container.
        echo Please start it manually with: docker start docker-nginx-1
        pause
        exit /b 1
    ) else (
        echo Nginx container started successfully.
    )
)

:: Update Nginx configuration to use port 5000 instead of 5001
echo.
echo Updating Nginx configuration to use port 5000...
docker exec docker-nginx-1 sh -c "sed -i 's/10.158.120.151:5001/10.158.120.151:5000/g' /etc/nginx/conf.d/casestrainer.conf" >nul 2>&1

:: Add X-Forwarded-Prefix header to Nginx configuration
echo Adding X-Forwarded-Prefix header to Nginx configuration...
docker exec docker-nginx-1 sh -c "grep -q 'X-Forwarded-Prefix' /etc/nginx/conf.d/casestrainer.conf || sed -i '/X-Forwarded-Proto/a\        proxy_set_header X-Forwarded-Prefix /casestrainer;' /etc/nginx/conf.d/casestrainer.conf" >nul 2>&1

if %errorLevel% neq 0 (
    echo ERROR: Failed to update Nginx configuration.
    echo Please update it manually by changing port 5001 to 5000 in the Nginx configuration.
    pause
    exit /b 1
)

:: Reload Nginx configuration
echo Reloading Nginx configuration...
docker exec docker-nginx-1 nginx -s reload >nul 2>&1

if %errorLevel% neq 0 (
    echo ERROR: Failed to reload Nginx configuration.
    echo Please reload it manually with: docker exec docker-nginx-1 nginx -s reload
    pause
    exit /b 1
)

echo.
echo Nginx configuration updated successfully!
echo CaseStrainer should now be accessible at https://wolf.law.uw.edu/casestrainer/
echo.

pause
