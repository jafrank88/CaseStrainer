@echo off
:: CI Health Check Script for CaseStrainer
:: This script runs in the CI environment to verify all services are running

setlocal enabledelayedexpansion

:: Configuration
set SERVICE_HOST=host.docker.internal  # This works in GitHub Actions
set SERVICE_TIMEOUT=60
set INITIAL_DELAY=45  # Increased initial delay to ensure services are fully started

:: For local testing, you can override the host
if not "%CI%"=="true" (
    set SERVICE_HOST=localhost
)

echo =======================================
echo 🏥 CaseStrainer CI Health Check
echo =======================================
echo Environment: %CI%
echo Service Host: %SERVICE_HOST%
echo Timeout: %SERVICE_TIMEOUT%s
echo =======================================

:: Install required packages
echo.
echo 📦 Installing required packages...
python -m pip install --quiet --upgrade pip
pip install --quiet requests

:: Run the health check
echo.
echo 🚀 Running health checks...
python scripts/ci_health_check.py
set EXIT_CODE=!ERRORLEVEL!

:: Print final status
echo.
if !EXIT_CODE! equ 0 (
    echo ✅ All services are healthy!
) else (
    echo ❌ Health check failed
)

exit /b !EXIT_CODE!
