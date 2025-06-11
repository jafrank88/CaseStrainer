@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Stop Script
:: Stops all CaseStrainer services
:: ===================================================

:: Set script directory and change to it
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Initialize logging
set "LOG_DIR=logs"
set "TIMESTAMP=%DATE:/=-%_%TIME::=-%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOGFILE=%LOG_DIR%\casestrainer_stop_%TIMESTAMP%.log"

:: Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo =================================================== > "%LOGFILE%"
echo [%DATE% %TIME%] Stopping CaseStrainer Services >> "%LOGFILE%"

echo [%TIME%] Stopping CaseStrainer services...

:: Stop Nginx
echo [%TIME%] Stopping Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" | find "nginx.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [%TIME%] Found running Nginx process. Stopping...
    taskkill /F /IM nginx.exe /T >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [%TIME%] Successfully stopped Nginx
    ) else (
        echo [%TIME%] [WARNING] Failed to stop Nginx. It may already be stopped.
    )
) else (
    echo [%TIME%] Nginx is not running
)

:: Stop Python processes (Flask backend)
echo [%TIME%] Stopping Python backend...
tasklist /FI "IMAGENAME eq python.exe" | find "python" >nul
if %ERRORLEVEL% EQU 0 (
    echo [%TIME%] Found running Python process. Stopping...
    taskkill /F /IM python.exe /T >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [%TIME%] Successfully stopped Python backend
    ) else (
        echo [%TIME%] [WARNING] Failed to stop Python backend. It may already be stopped.
    )
) else (
    echo [%TIME%] Python backend is not running
)

echo [%TIME%] All CaseStrainer services have been stopped
echo [%TIME%] Log file: %LOGFILE%
echo ===================================================

pause
