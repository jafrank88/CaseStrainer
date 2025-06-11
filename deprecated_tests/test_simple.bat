@echo off
setlocal enabledelayedexpansion

echo Testing basic initialization...

:: Set up basic variables like the main script
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "CONFIG_FILE=%SCRIPT_DIR%config.ini"

:: Create directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

:: Set up log file
set "dt=%date:~-4%%date:~3,2%%date:~0,2%"
set "tm=%time:~0,2%%time:~3,2%%time:~6,2%"
set "tm=%tm: =0%"
set "LOG_FILE=%LOG_DIR%\test_%dt%_%tm%.log"

echo SCRIPT_DIR: %SCRIPT_DIR%
echo LOG_DIR: %LOG_DIR%
echo LOG_FILE: %LOG_FILE%
echo CONFIG_FILE: %CONFIG_FILE%

:: Test the log function
call :test_log_message "Testing log function" "INFO"

:: Test config creation
call :test_config

echo.
echo Test completed. Check if log file was created: %LOG_FILE%
if exist "%LOG_FILE%" (
    echo Log file exists! Contents:
    type "%LOG_FILE%"
) else (
    echo Log file was not created.
)

pause
exit /b 0

:test_log_message
    set "message=%~1"
    set "level=%~2"
    if not defined level set "level=INFO"
    
    echo [%level%] %message%
    echo %date% %time% [%level%] %message% >> "%LOG_FILE%" 2>nul
    exit /b 0

:test_config
    if not exist "%CONFIG_FILE%" (
        echo Creating test config...
        (
            echo SSL_CERT_PATH=D:/CaseStrainer/ssl/WolfCertBundle.crt
            echo SSL_KEY_PATH=D:/CaseStrainer/ssl/wolf.law.uw.edu.key
            echo DEV_BACKEND_PORT=5000
        ) > "%CONFIG_FILE%"
    )
    
    echo Loading config...
    for /f "usebackq tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        if not "%%a"=="" (
            set "%%a=%%b"
            echo Loaded: %%a=%%b
        )
    )
    
    echo SSL_CERT_PATH: %SSL_CERT_PATH%
    echo SSL_KEY_PATH: %SSL_KEY_PATH%
    echo DEV_BACKEND_PORT: %DEV_BACKEND_PORT%
    exit /b 0