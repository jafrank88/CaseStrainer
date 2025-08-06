@echo off
setlocal enabledelayedexpansion

echo === Docker Recovery Script for CaseStrainer ===
echo.

if "%1"=="-CheckOnly" goto :CheckOnly
if "%1"=="-Quick" goto :Quick
if "%1"=="-Full" goto :Full
if "%1"=="-Emergency" goto :Emergency

echo Usage:
echo   docker_recovery.bat -CheckOnly    # Run diagnostics only
echo   docker_recovery.bat -Quick        # Quick recovery (restart containers)
echo   docker_recovery.bat -Full         # Full recovery (restart Docker)
echo   docker_recovery.bat -Emergency    # Emergency recovery (reset everything)
echo.
echo Recommended approach:
echo 1. Start with -CheckOnly to diagnose the issue
echo 2. Try -Quick for minor issues
echo 3. Use -Full for persistent problems
echo 4. Use -Emergency as a last resort
goto :end

:CheckOnly
echo Running diagnostics...
echo.
echo Testing Docker responsiveness...
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker is responsive
) else (
    echo ✗ Docker is unresponsive
)

echo.
echo Container Status:
docker ps -a

echo.
echo Resource Usage:
docker stats --no-stream

echo.
echo ✓ Diagnostics completed
goto :end

:Quick
echo Performing quick recovery...
echo.
echo 1. Stopping casestrainer containers...
for /f "tokens=*" %%i in ('docker ps -q --filter "name=casestrainer"') do (
    docker stop %%i
)

echo.
echo 2. Starting containers...
docker-compose -f docker-compose.prod.yml up -d

echo.
echo ✓ Quick recovery completed
goto :end

:Full
echo Performing full recovery...
echo.
echo 1. Stopping all containers...
docker stop $(docker ps -q) 2>nul

echo.
echo 2. Cleaning up Docker resources...
docker container prune -f 2>nul
docker system prune -f 2>nul

echo.
echo 3. Restarting Docker Desktop...
taskkill /f /im "Docker Desktop.exe" 2>nul
timeout /t 10 /nobreak >nul
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo 4. Waiting for Docker to start...
set /a timeout=120
set /a elapsed=0
:wait_loop
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker is ready
    goto :start_app
)
timeout /t 5 /nobreak >nul
set /a elapsed+=5
echo Waiting... (!elapsed!/!timeout! seconds)
if !elapsed! geq !timeout! (
    echo ✗ Docker failed to start within timeout
    goto :end
)
goto :wait_loop

:start_app
echo.
echo 5. Starting application...
docker-compose -f docker-compose.prod.yml up -d --build

echo.
echo ✓ Full recovery completed
goto :end

:Emergency
echo Performing emergency recovery...
echo.
echo 1. Stopping all containers...
docker stop $(docker ps -q) 2>nul

echo.
echo 2. Cleaning all Docker resources...
docker container prune -f 2>nul
docker image prune -f 2>nul
docker volume prune -f 2>nul
docker network prune -f 2>nul
docker system prune -af 2>nul

echo.
echo 3. Restarting Docker Desktop...
taskkill /f /im "Docker Desktop.exe" 2>nul
timeout /t 15 /nobreak >nul
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo 4. Waiting for Docker to start...
set /a timeout=180
set /a elapsed=0
:emergency_wait_loop
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker is ready
    goto :rebuild_app
)
timeout /t 10 /nobreak >nul
set /a elapsed+=10
echo Waiting... (!elapsed!/!timeout! seconds)
if !elapsed! geq !timeout! (
    echo ✗ Docker failed to start within timeout
    echo You may need to restart your computer
    goto :end
)
goto :emergency_wait_loop

:rebuild_app
echo.
echo 5. Rebuilding application...
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

echo.
echo ✓ Emergency recovery completed
goto :end

:end
echo.
pause 