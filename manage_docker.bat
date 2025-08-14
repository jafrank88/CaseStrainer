@echo off
setlocal enabledelayedexpansion

:: CaseStrainer Docker Management Script
:: This script provides an interactive menu to manage Docker for CaseStrainer

:menu
cls
echo ===========================================
echo     CaseStrainer Docker Management
echo ===========================================
echo.
echo 1. Start Docker (Linux Containers)
echo 2. Start Docker (Windows Containers)
echo 3. Stop Docker
echo 4. Restart Docker
echo 5. Check Docker Status
echo 6. Repair Docker Installation
echo 7. Clean Docker System
echo 8. View Docker Logs
echo 9. Exit
echo.
set /p choice=Enter your choice (1-9): 

goto option!choice!

:option1
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action switch-mode -Mode linux
if %ERRORLEVEL% neq 0 (
    echo Failed to switch to Linux containers
    pause
    goto menu
)
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action start
goto menu

:option2
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action switch-mode -Mode windows
if %ERRORLEVEL% neq 0 (
    echo Failed to switch to Windows containers
    pause
    goto menu
)
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action start
goto menu

:option3
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action stop
goto menu

:option4
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action restart
goto menu

:option5
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action status
pause
goto menu

:option6
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action repair
pause
goto menu

:option7
powershell -ExecutionPolicy Bypass -File "%~dp0docker_engine_enhanced.ps1" -Action clean
pause
goto menu

:option8
if not exist "logs\docker_engine_enhanced.log" (
    echo No log file found.
) else (
    type "logs\docker_engine_enhanced.log"
)
pause
goto menu

:option9
exit /b 0

:invalid
echo Invalid choice. Please try again.
pause
goto menu
