@echo off
setlocal enabledelayedexpansion

echo [DEBUG] Script started

:: Configuration
echo [DEBUG] Setting up configuration...
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"

:: Create log directory if it doesn't exist
if not exist "%LOG_DIR%" (
    echo [DEBUG] Creating log directory: %LOG_DIR%
    mkdir "%LOG_DIR%"
) else (
    echo [DEBUG] Log directory exists: %LOG_DIR%
)

:: Simple test to see if we can write to the log directory
echo [DEBUG] Testing log directory write access...
echo Test log entry > "%LOG_DIR%\test_write.log"
if exist "%LOG_DIR%\test_write.log" (
    echo [DEBUG] Successfully wrote to log directory
    del "%LOG_DIR%\test_write.log"
) else (
    echo [ERROR] Failed to write to log directory: %LOG_DIR%
    pause
    exit /b 1
)

echo [DEBUG] Script completed successfully
pause
