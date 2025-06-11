@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Test Runner with Server Status Check
:: ===================================================
:: This script checks server status before running tests
:: and ensures all required services are running.
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "PYTHON=python"
set "TEST_SCRIPT=%SCRIPT_DIR%tests\test_smoke.py"
set "LOG_DIR=%SCRIPT_DIR%test_logs"
set "MAX_RETRIES=5"
set "RETRY_DELAY=5"  

:: Server endpoints to check
set "FLASK_SERVER=http://localhost:5000/health"
set "NGINX_SERVER=http://localhost"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\test_run_%TIMESTAMP%.log"

:: Function to log messages
echo =================================================== > "%LOG_FILE%"
echo [%TIMESTAMP%] Starting test run >> "%LOG_FILE%"

echo ===================================================
echo CaseStrainer Test Runner with Server Status Check
echo ===================================================
echo Log file: %LOG_FILE%
echo.

:: Function to check if a server is responding
:check_server
setlocal enabledelayedexpansion
set "URL=%~1"
set "SERVICE_NAME=%~2"
set "RETRY_COUNT=0"

:retry_server_check
echo [%TIME%] Checking %SERVICE_NAME% at %URL%...
echo [%TIME%] Checking %SERVICE_NAME% at %URL%... >> "%LOG_FILE%"

powershell -Command "try { $response = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop; exit 0 } catch { exit 1 }"
set "STATUS=!ERRORLEVEL!"

if !STATUS! EQU 0 (
    echo [%TIME%] %SERVICE_NAME% is running and responsive.
    echo [%TIME%] %SERVICE_NAME% is running and responsive. >> "%LOG_FILE%"
    endlocal & exit /b 0
) else (
    set /a "RETRY_COUNT+=1"
    
    if !RETRY_COUNT! GEQ %MAX_RETRIES% (
        echo [%TIME%] ERROR: Failed to connect to %SERVICE_NAME% after %MAX_RETRIES% attempts.
        echo [%TIME%] ERROR: Failed to connect to %SERVICE_NAME% after %MAX_RETRIES% attempts. >> "%LOG_FILE%"
        endlocal & exit /b 1
    )
    
    echo [%TIME%] %SERVICE_NAME% not ready (attempt !RETRY_COUNT! of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds...
    echo [%TIME%] %SERVICE_NAME% not ready (attempt !RETRY_COUNT! of %MAX_RETRIES%). Retrying in %RETRY_DELAY% seconds... >> "%LOG_FILE%"
    
    timeout /t %RETRY_DELAY% >nul
    goto :retry_server_check
)
endlocal

echo [%TIME%] Starting server status check...
echo [%TIME%] Starting server status check... >> "%LOG_FILE%"

:: Check Flask server
call :check_server "%FLASK_SERVER%" "Flask Backend"
if !ERRORLEVEL! NEQ 0 (
    echo [%TIME%] ERROR: Flask server is not running. Please start the server and try again.
    echo [%TIME%] ERROR: Flask server is not running. Please start the server and try again. >> "%LOG_FILE%"
    goto :error_exit
)

:: Check Nginx server
call :check_server "%NGINX_SERVER%" "Nginx"
if !ERRORLEVEL! NEQ 0 (
    echo [%TIME%] WARNING: Nginx server is not running. Some tests may fail.
    echo [%TIME%] WARNING: Nginx server is not running. Some tests may fail. >> "%LOG_FILE%"
    set "NGINX_RUNNING=0"
) else (
    set "NGINX_RUNNING=1"
)

echo [%TIME%] All required servers are running. Starting tests...
echo [%TIME%] All required servers are running. Starting tests... >> "%LOG_FILE%"
echo.

:: Run the tests
echo [%TIME%] Running tests...
echo [%TIME%] Running tests... >> "%LOG_FILE%"
%PYTHON% -m pytest "%TEST_SCRIPT%" -v >> "%LOG_FILE%" 2>&1
set "TEST_RESULT=!ERRORLEVEL!"

if !TEST_RESULT! EQU 0 (
    echo [%TIME%] PASS: All tests completed successfully.
    echo [%TIME%] PASS: All tests completed successfully. >> "%LOG_FILE%"
) else (
    echo [%TIME%] FAIL: Some tests failed. See %LOG_FILE% for details.
    echo [%TIME%] FAIL: Some tests failed. >> "%LOG_FILE%"
)

goto :end_script

:error_exit
echo [%TIME%] ERROR: Server check failed. Tests will not run.
echo [%TIME%] ERROR: Server check failed. Tests will not run. >> "%LOG_FILE%"
set "TEST_RESULT=1"

:end_script
echo.
echo ===================================================
echo Test execution complete - %DATE% %TIME%
echo Log file: %LOG_FILE%
echo ===================================================
(
echo.
echo ===================================================
echo Test execution complete - %DATE% %TIME%
echo Log file: %LOG_FILE%
echo ===================================================
) >> "%LOG_FILE%"

exit /b %TEST_RESULT%

endlocal
