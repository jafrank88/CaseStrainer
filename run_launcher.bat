@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: CaseStrainer Launcher
:: ===================================================
:: This script can be run from any directory
:: ===================================================

:: Get the directory where this script is located
set "LAUNCHER_PATH=%~f0"
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Set console window title
title CaseStrainer Launcher

:: Set console window size
mode con:cols=100 lines=25

:: Function to log messages with timestamp
:log
echo [%TIME%] %~1
goto :eof

:: Function to display the menu
:show_menu
cls
echo ===================================================
echo   CaseStrainer Launcher
echo ===================================================
echo   Location: %SCRIPT_DIR:~0,80%
echo   Time: %DATE% %TIME:~0,8%
echo ===================================================
echo.
echo   1. Launch Control Panel (Interactive Menu)
echo   2. Start All Services
echo   3. Stop All Services
echo   4. Exit
echo.
goto :eof

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    cls
    echo ===================================================
    echo   ERROR: Python not found
    echo ===================================================
    echo.
    echo Python is not in your system PATH.
    echo Please install Python and ensure it's in your PATH.
    echo.
    pause
    exit /b 1
)

:: Ensure we have required directories
if not exist "%SCRIPT_DIR%" (
    cls
    echo ===================================================
    echo   ERROR: Invalid script directory
    echo ===================================================
    echo.
    echo Could not determine script directory.
    echo.
    echo Launcher path: %LAUNCHER_PATH%
    echo.
    pause
    exit /b 1
)

:: Main menu loop
:start
call :show_menu
set "choice="
set /p "choice=Enter your choice (1-4): "

if "%choice%"=="" (
    echo.
    echo Please enter a choice (1-4)
    timeout /t 2 >nul
    goto :start
)

if "%choice%"=="1" (
    if exist "%SCRIPT_DIR%\launch_app.bat" (
        echo.
        echo Launching CaseStrainer Control Panel...
        echo Script directory: %SCRIPT_DIR%
        echo.
        
        cd /d "%SCRIPT_DIR%"
        start "CaseStrainer Control Panel" cmd /k ""%SCRIPT_DIR%\launch_app.bat""
        timeout /t 2 /nobreak >nul
    ) else (
        cls
        echo ===================================================
        echo   ERROR: Missing launch_app.bat
        echo ===================================================
        echo.
        echo Could not find: %SCRIPT_DIR%\launch_app.bat
        echo.
        echo Current directory: %CD%
        echo.
        echo Directory contents:
        dir /b
        echo.
        pause
    )
    goto :start
) else if "%choice%"=="2" (
    if exist "%SCRIPT_DIR%\launch_app.bat" (
        cls
        echo ===================================================
        echo   Starting All Services
        echo ===================================================
        echo.
        echo Please wait while services start...
        echo.
        
        cd /d "%SCRIPT_DIR%"
        "%SCRIPT_DIR%\launch_app.bat" 2
        timeout /t 2 /nobreak >nul
    ) else (
        cls
        echo ===================================================
        echo   ERROR: Missing launch_app.bat
        echo ===================================================
        echo.
        echo Could not find: %SCRIPT_DIR%\launch_app.bat
        echo.
        pause
    )
    goto :start
) else if "%choice%"=="3" (
    if exist "%SCRIPT_DIR%\launch_app.bat" (
        cls
        echo ===================================================
        echo   Stopping All Services
        echo ===================================================
        echo.
        echo Please wait while services stop...
        echo.
        
        cd /d "%SCRIPT_DIR%"
        "%SCRIPT_DIR%\launch_app.bat" 3
        timeout /t 2 /nobreak >nul
    ) else (
        cls
        echo ===================================================
        echo   ERROR: Missing launch_app.bat
        echo ===================================================
        echo.
        echo Could not find: %SCRIPT_DIR%\launch_app.bat
        echo.
        pause
    )
    goto :start
) else if "%choice%"=="4" (
    cls
    echo ===================================================
    echo   Exiting CaseStrainer Launcher
    echo ===================================================
    echo.
    echo Thank you for using CaseStrainer!
    echo.
    timeout /t 2 /nobreak >nul
    exit /b 0
) else (
    echo.
    echo Invalid choice: %choice%
    echo Please enter a number between 1 and 4
    timeout /t 2 /nobreak >nul
    goto :start
)
