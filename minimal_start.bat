@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Minimal Start Script - Testing Only
echo ===================================

echo [1] Current directory: %CD%
echo [2] Script directory: %~dp0

:: Basic configuration
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "LOG_FILE=%LOG_DIR%\minimal_test.log"

echo [3] Creating log directory if it doesn't exist...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [4] Testing log file write access...
echo Test log entry at %TIME% > "%LOG_FILE%"
if exist "%LOG_FILE%" (
    echo [SUCCESS] Successfully wrote to log file: %LOG_FILE%
) else (
    echo [ERROR] Failed to write to log file: %LOG_FILE%
    pause
    exit /b 1
)

echo [5] Testing administrator privileges...
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] This script requires administrator privileges.
    echo [ERROR] Please right-click on the script and select 'Run as administrator'.
    pause
    exit /b 1
)

echo [6] Administrator privileges confirmed

echo.
echo ===================================
echo Minimal test completed successfully!
echo ===================================
echo.
pause
