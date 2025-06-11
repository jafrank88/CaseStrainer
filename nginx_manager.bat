@echo off
setlocal enabledelayedexpansion

:: Configuration
set "NGINX_DIR=%~dp0nginx-1.27.5"
set "CONFIG_FILE=%~dp0nginx-case-strainer.conf"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click on the script and select 'Run as administrator'.
    pause
    exit /b 1
)

:menu
cls
echo ===================================================
echo   Nginx Manager for CaseStrainer
echo ===================================================
echo   1. Start Nginx
echo   2. Stop Nginx
echo   3. Restart Nginx
echo   4. Check Nginx status
echo   5. Test Nginx configuration
echo   6. View error log
echo   7. View access log
echo   8. Exit
echo.
set /p "choice=Enter your choice (1-8): "

echo.

if "%choice%"=="1" (
    echo Starting Nginx...
    "%NGINX_EXE%" -c "%CONFIG_FILE%"
    if !ERRORLEVEL! EQU 0 (
        echo Nginx started successfully.
    ) else (
        echo Failed to start Nginx. Check error log for details.
    )
    pause
    goto menu
) else if "%choice%"=="2" (
    echo Stopping Nginx...
    taskkill /F /IM nginx.exe >nul 2>&1
    echo Nginx stopped.
    pause
    goto menu
) else if "%choice%"=="3" (
    echo Restarting Nginx...
    taskkill /F /IM nginx.exe >nul 2>&1
    "%NGINX_EXE%" -c "%CONFIG_FILE%"
    if !ERRORLEVEL! EQU 0 (
        echo Nginx restarted successfully.
    else
        echo Failed to restart Nginx. Check error log for details.
    )
    pause
    goto menu
) else if "%choice%"=="4" (
    echo Nginx processes:
    tasklist /FI "IMAGENAME eq nginx.exe"
    pause
    goto menu
) else if "%choice%"=="5" (
    echo Testing Nginx configuration...
    "%NGINX_EXE%" -t -c "%CONFIG_FILE%"
    pause
    goto menu
) else if "%choice%"=="6" (
    if exist "%NGINX_DIR%\logs\error.log" (
        notepad "%NGINX_DIR%\logs\error.log"
    ) else (
        echo Error log not found at: %NGINX_DIR%\logs\error.log
    )
    pause
    goto menu
) else if "%choice%"=="7" (
    if exist "%NGINX_DIR%\logs\access.log" (
        notepad "%NGINX_DIR%\logs\access.log"
    ) else (
        echo Access log not found at: %NGINX_DIR%\logs\access.log
    )
    pause
    goto menu
) else if "%choice%"=="8" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto menu
)
