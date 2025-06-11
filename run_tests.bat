@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Test Runner
:: ===================================================
:: USAGE: run_tests.bat [test_name]
::   - If no test_name is provided, all tests will run
::   - Example: run_tests.bat api
:: ===================================================

:: Set up paths
set "SCRIPT_DIR=%~dp0"
set "TEST_DIR=%SCRIPT_DIR%tests"
set "LOG_DIR=%SCRIPT_DIR%test_logs"
set "PYTHON=python"
set "REQUIREMENTS=requirements-test.txt"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Set log file with timestamp
for /f "tokens=2 delims==. " %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOG_FILE=%LOG_DIR%\test_results_%TIMESTAMP%.log"

echo [%TIME%] Starting test suite > "%LOG_FILE%"
(
echo ===================================================
echo CaseStrainer Test Runner
echo ===================================================
echo Log file: %LOG_FILE%
echo.
) >> "%LOG_FILE%"

echo ===================================================
echo CaseStrainer Test Runner
echo ===================================================
echo Log file: %LOG_FILE%
echo.

:: Function to run a test and log the result
:run_test
set "TEST_NAME=%~1"
set "TEST_SCRIPT=tests\\%TEST_NAME%.py"
set "TEST_LOG=%LOG_DIR%\\%TEST_NAME%_%TIMESTAMP%.log"

echo [%TIME%] Running test: %TEST_NAME%
echo [%TIME%] Test log: %TEST_LOG%
(
echo [%TIME%] Running test: %TEST_NAME%
echo [%TIME%] Test log: %TEST_LOG%
) >> "%LOG_FILE%"

%PYTHON% "%TEST_SCRIPT%" > "%TEST_LOG%" 2>&1
set "TEST_RESULT=!ERRORLEVEL!"

if !TEST_RESULT! EQU 0 (
    echo [%TIME%] PASS: %TEST_NAME%
    (
    echo [%TIME%] PASS: %TEST_NAME%
    ) >> "%LOG_FILE%"
) else (
    echo [%TIME%] FAIL: %TEST_NAME% (Code: !TEST_RESULT!)
    echo [%TIME%] Check %TEST_LOG% for details
    (
    echo [%TIME%] FAIL: %TEST_NAME% (Code: !TEST_RESULT!)
    echo [%TIME%] Check %TEST_LOG% for details
    ) >> "%LOG_FILE%"
)

echo.
echo. >> "%LOG_FILE%"
goto :eof

:: Main test execution
if "%~1"=="" (
    echo [%TIME%] No specific test specified. Running all tests.
    echo [%TIME%] No specific test specified. Running all tests. >> "%LOG_FILE%"
    
    :: Run API tests
    call :run_test test_api_endpoints
    call :run_test test_citation_verification
    call :run_test test_flask_app
    call :run_test test_backend_api
    call :run_test test_email
    
    echo [%TIME%] All tests completed. See %LOG_FILE% for details.
    echo [%TIME%] All tests completed. See %LOG_FILE% for details. >> "%LOG_FILE%"
) else (
    :: Run specific test
    call :run_test %~1
    
    echo [%TIME%] Test completed. See %LOG_FILE% for details.
    echo [%TIME%] Test completed. See %LOG_FILE% for details. >> "%LOG_FILE%"
)

echo ===================================================
echo Test execution complete
echo ===================================================
(
echo ===================================================
echo Test execution complete
echo ===================================================
) >> "%LOG_FILE%"

endlocal
