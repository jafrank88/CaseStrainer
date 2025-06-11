@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Server Status Check
:: ===================================================
:: Checks if required servers are running before tests
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%test_logs"
set "MAX_RETRIES=3"
set "RETRY_DELAY=5"

:: Server endpoints to check
set "FLASK_SERVER=http://localhost:5000/health"
set "NGINX_SERVER=http://localhost"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\server_check_%TIMESTAMP%.log"

echo ===================================================
echo CaseStrainer Server Status Check
echo ===================================================
echo Log file: %LOG_FILE%
echo.

(
echo ===================================================
echo [%TIMESTAMP%] Starting server status check
echo ===================================================
) >> "%LOG_FILE%"

:: Check Flask server
echo [%TIME%] Checking Flask Backend at %FLASK_SERVER%...
echo [%TIME%] Checking Flask Backend at %FLASK_SERVER%... >> "%LOG_FILE%"

set "FLASK_RUNNING=0"
for /l %%i in (1,1,%MAX_RETRIES%) do (
    powershell -Command "try { $response = Invoke-WebRequest -Uri '%FLASK_SERVER%' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop; exit 0 } catch { exit 1 }"
    if !errorlevel! EQU 0 (
        echo [%TIME%] Flask Backend is running and responsive.
        echo [%TIME%] Flask Backend is running and responsive. >> "%LOG_FILE%"
        set "FLASK_RUNNING=1"
        goto :check_nginx
    ) else (
        echo [%TIME%] Flask Backend not ready (attempt %%i of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds...
        echo [%TIME%] Flask Backend not ready (attempt %%i of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds... >> "%LOG_FILE%"
        if %%i LSS %MAX_RETRIES% timeout /t %RETRY_DELAY% >nul
    )
)

:check_nginx
echo.
echo [%TIME%] Checking Nginx at %NGINX_SERVER%...
echo. >> "%LOG_FILE%"
echo [%TIME%] Checking Nginx at %NGINX_SERVER%... >> "%LOG_FILE%"

set "NGINX_RUNNING=0"
for /l %%i in (1,1,%MAX_RETRIES%) do (
    powershell -Command "try { $response = Invoke-WebRequest -Uri '%NGINX_SERVER%' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop; exit 0 } catch { exit 1 }"
    if !errorlevel! EQU 0 (
        echo [%TIME%] Nginx is running and responsive.
        echo [%TIME%] Nginx is running and responsive. >> "%LOG_FILE%"
        set "NGINX_RUNNING=1"
        goto :check_complete
    ) else (
        echo [%TIME%] Nginx not ready (attempt %%i of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds...
        echo [%TIME%] Nginx not ready (attempt %%i of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds... >> "%LOG_FILE%"
        if %%i LSS %MAX_RETRIES% timeout /t %RETRY_DELAY% >nul
    )
)

:check_complete
echo.
echo ===================================================
echo Server Status Summary
echo ===================================================
if %FLASK_RUNNING% EQU 1 (
    echo [✓] Flask Backend: RUNNING
) else (
    echo [✗] Flask Backend: NOT RUNNING
)

if %NGINX_RUNNING% EQU 1 (
    echo [✓] Nginx: RUNNING
) else (
    echo [✗] Nginx: NOT RUNNING
)

echo.
echo ===================================================
if %FLASK_RUNNING% EQU 1 if %NGINX_RUNNING% EQU 1 (
    echo [✓] All required servers are running.
    echo [i] You can now run the test suite.
    set "EXIT_CODE=0"
) else (
    echo [✗] Some required servers are not running.
    echo [i] Please start the required servers and try again.
    set "EXIT_CODE=1"
)
echo ===================================================

(
echo.
echo ===================================================
echo [%TIME%] Server check completed with status: %EXIT_CODE%
echo ===================================================
) >> "%LOG_FILE%"

exit /b %EXIT_CODE%
