@echo off
:: Health check script for CaseStrainer CI/CD pipeline
:: Ensures all services are available before running health checks

setlocal enabledelayedexpansion

:: Configuration
set BASE_URL=http://localhost:5000
set REDIS_URL=redis://localhost:6379/0
set TIMEOUT=60

:: Print header
echo =======================================
echo 🏥 CaseStrainer Health Check
:: Print system information
echo OS: %OS% %PROCESSOR_ARCHITECTURE%
echo Python: %PYTHON_VERSION%
echo =======================================

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python is not in PATH
    exit /b 1
)

:: Install required packages if not already installed
python -m pip install --quiet --upgrade pip
python -m pip install --quiet requests redis rq psutil

:: Wait for Redis to be available
echo.
echo ⏳ Waiting for Redis to be available...
call scripts\wait-for-it.sh -t %TIMEOUT% localhost:6379
if %ERRORLEVEL% neq 0 (
    echo ❌ Redis is not available after %TIMEOUT% seconds
    exit /b 1
)
echo ✅ Redis is available

:: Wait for API to be available
echo.
echo ⏳ Waiting for API to be available...
call scripts\wait-for-it.sh -t %TIMEOUT% localhost:5000
if %ERRORLEVEL% neq 0 (
    echo ❌ API is not available after %TIMEOUT% seconds
    exit /b 1
)
echo ✅ API is available

:: Run health check
echo.
echo 🚀 Running health checks...
set HEALTH_CHECK_CMD=python check_health.py

:: Run with retries
set MAX_RETRIES=3
set RETRY_DELAY=5

for /l %%i in (1, 1, %MAX_RETRIES%) do (
    echo.
    echo 🔍 Health check attempt %%i of %MAX_RETRIES%
    
    %HEALTH_CHECK_CMD%
    set EXIT_CODE=!ERRORLEVEL!
    
    if !EXIT_CODE! equ 0 (
        echo.
        echo ✅ Health check passed
        exit /b 0
    ) else if !EXIT_CODE! equ 1 (
        echo ⚠️ Health check warning (degraded)
        if "%%i" neq "%MAX_RETRIES%" (
            echo Waiting %RETRY_DELAY% seconds before retry...
            timeout /t %RETRY_DELAY% >nul
        )
    ) else (
        echo ❌ Health check failed with error code !EXIT_CODE!
        if "%%i" neq "%MAX_RETRIES%" (
            echo Waiting %RETRY_DELAY% seconds before retry...
            timeout /t %RETRY_DELAY% >nul
        )
    )
)

:: If we get here, all retries failed
echo.
echo ❌ Health check failed after %MAX_RETRIES% attempts
exit /b 1
