@echo off
echo ===================================================
echo CaseStrainer Nginx Port Update
echo ===================================================
echo.

:: Check Docker status
echo Checking Docker status...
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Docker does not appear to be running.
    echo The Docker Nginx container may not be accessible.
    echo.
    echo Would you like to continue anyway? (Y/N)
    set /p CONTINUE=
    if /i "%CONTINUE%" neq "Y" (
        echo Operation cancelled by user.
        pause
        exit /b 1
    )
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

:: Display current Nginx configuration
echo.
echo Current Nginx configuration:
docker exec docker-nginx-1 cat /etc/nginx/conf.d/casestrainer.conf | findstr proxy_pass

:: Update Nginx configuration to use port 5000 instead of 5001
echo.
echo Updating Nginx configuration to use port 5000...
docker exec docker-nginx-1 sh -c "sed -i 's/10.158.120.151:5001/10.158.120.151:5000/g' /etc/nginx/conf.d/casestrainer.conf"

:: Display updated Nginx configuration
echo.
echo Updated Nginx configuration:
docker exec docker-nginx-1 cat /etc/nginx/conf.d/casestrainer.conf | findstr proxy_pass

:: Reload Nginx configuration
echo.
echo Reloading Nginx configuration...
docker exec docker-nginx-1 nginx -s reload

echo.
echo Nginx configuration updated to use port 5000.
echo CaseStrainer should now be accessible at https://wolf.law.uw.edu/casestrainer/
echo.

pause
