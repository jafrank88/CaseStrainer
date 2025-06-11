@echo off
setlocal enabledelayedexpansion

:: ===========================================
:: CaseStrainer Test Runner
:: ===========================================
:: This script runs comprehensive tests for the CaseStrainer application
:: including both Flask backend and Nginx proxy tests.
::
:: Usage: run_tests.bat [--unit] [--integration] [--all] [--help]
::   --unit       : Run only unit tests
::   --integration: Run only integration tests
::   --all        : Run all tests (default)
::   --help       : Show this help message
:: ===========================================

:: Configuration
set "PROJECT_ROOT=%~dp0"
set "FLASK_APP=src\app_final_vue.py"
set "FLASK_ENV=testing"
set "PYTHONPATH=%PROJECT_ROOT%src;%PYTHONPATH%"
set "PORT=5000"
set "HOST=0.0.0.0"
set "NGINX_EXE=%PROJECT_ROOT%nginx-1.27.5\nginx.exe"
set "NGINX_CONF=%PROJECT_ROOT%nginx-test.conf"
set "NGINX_DIR=%PROJECT_ROOT%nginx-1.27.5"
set "TEST_FILE=%PROJECT_ROOT%test_files\test.pdf"
set "VENV_ACTIVATE=%PROJECT_ROOT%.venv\Scripts\activate"

:: Parse command line arguments
set "RUN_UNIT=0"
set "RUN_INTEGRATION=0"
set "SHOW_HELP=0"

:parse_args
if "%~1"=="" goto args_done
if "%~1"=="--unit" set RUN_UNIT=1
if "%~1"=="--integration" set RUN_INTEGRATION=1
if "%~1"=="--all" set RUN_UNIT=1 & set RUN_INTEGRATION=1
if "%~1"=="--help" set SHOW_HELP=1
shift
goto parse_args
:args_done

:: Show help if requested
if "%SHOW_HELP%"=="1" (
    echo.
    echo CaseStrainer Test Runner
    echo =========================
    echo.
    echo Usage: run_tests.bat [options]
    echo.
    echo Options:
    echo   --unit        Run only unit tests
    echo   --integration Run only integration tests
    echo   --all         Run all tests (default)
    echo   --help        Show this help message
    echo.
    exit /b 0
)

:: Default to all tests if none specified
if "%RUN_UNIT%%RUN_INTEGRATION%"=="00" (
    set RUN_UNIT=1
    set RUN_INTEGRATION=1
)

:: Log file setup
set "LOG_DIR=%PROJECT_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\test_%date:/=_%_%time::=%.log"
set "LOG_FILE=%LOG_FILE: =0%"

:: Initialize log file
echo [%DATE% %TIME%] Starting CaseStrainer Tests > "%LOG_FILE%"

:: Function to log messages
:log
echo [%TIME%] %* | findstr /v "^[0-9]"
echo [%DATE% %TIME%] %* >> "%LOG_FILE%" 2>&1
goto :eof

:: Error handler
:error
    call :log "ERROR: %~1"
    echo.
    echo Test failed! Check the log file for details:
    echo %LOG_FILE%
    pause
    exit /b 1

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[WARNING] Not running as administrator"
    call :log "[WARNING] Some tests may fail without admin privileges"
    timeout /t 2 >nul
)

:: Stop any existing services
call :log "[INFO] Stopping any existing services..."
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

:: Verify Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :log [ERROR] Python is not in PATH
    pause
    exit /b 1
)

:: Verify Nginx exists
if not exist "%NGINX_EXE%" (
    call :log [ERROR] Nginx not found at: %NGINX_EXE%
    pause
    exit /b 1
)

:: Verify test file exists
if not exist "%TEST_FILE%" (
    call :log [WARNING] Test file not found: %TEST_FILE%
    call :log [INFO] Creating a simple test file...
    echo This is a test PDF file with a citation to 410 U.S. 113 > test_files\test.txt
    ren test_files\test.txt test.pdf
    if not exist "%TEST_FILE%" (
        call :log [ERROR] Failed to create test file
        pause
        exit /b 1
    )
)

:: Change to script directory
cd /d "%~dp0"

:: Start Flask backend
call :log [INFO] Starting Flask backend...
start "CaseStrainer Backend" cmd /k "title CaseStrainer Backend && set FLASK_APP=%FLASK_APP% && set FLASK_ENV=%FLASK_ENV% && python -m flask run --host=%HOST% --port=%PORT%"

:: Wait for backend to start
call :log [INFO] Waiting for backend to start...
set "started=0"
for /l %%i in (1,1,30) do (
    timeout /t 1 >nul
    netstat -ano | find ":%PORT%" | find "LISTENING" >nul
    if !errorlevel! equ 0 (
        set started=1
        call :log [SUCCESS] Backend is running on port %PORT%
        goto start_nginx
    )
    call :log [INFO] Waiting for backend to start (%%i/30)...
)

call :log [ERROR] Backend failed to start within 30 seconds
pause
exit /b 1

:start_nginx
:: Start Nginx
call :log [INFO] Starting Nginx...
start "CaseStrainer Nginx" cmd /k "title CaseStrainer Nginx && "%NGINX_EXE%" -c "%NGINX_CONF%" -p "%NGINX_DIR%" && pause"

:: Wait for Nginx to start
timeout /t 2 /nobreak >nul

:: Run tests
call :log [INFO] Running comprehensive API tests...
python test_all_endpoints.py
set "test_result=!errorlevel!"

:: Display test results
if !test_result! EQU 0 (
    call :log [SUCCESS] All tests passed!
) else (
    call :log [ERROR] Some tests failed with error code !test_result!
)

:: Stop services
call :log [INFO] Stopping services...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

call :log [INFO] All services stopped.
call :log ============================================

if !test_result! NEQ 0 (
    pause
    exit /b !test_result!
)

pause
