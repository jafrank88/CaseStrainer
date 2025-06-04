@echo off
setlocal enabledelayedexpansion

REM Function to check if a process is running
:check_running
wmic process where "name='python.exe'" get processid 2>nul | find "ProcessId" >nul
if %ERRORLEVEL% EQU 0 (
    echo Python process is still running...
    timeout /t 1 >nul
    goto check_running
)
echo No Python processes found.
goto continue

:continue

echo.
echo ===== Starting CaseStrainer Backend =====
start "CaseStrainer Backend" /B python run_debug.py

echo.
echo ===== Waiting for backend to start (max 30 seconds) =====
set "started=0"
for /l %%i in (1,1,30) do (
    timeout /t 1 >nul
    netstat -ano | find ":5000" | find "LISTENING" >nul
    if !errorlevel! equ 0 (
        set started=1
        echo Backend is running on port 5000
        goto run_tests
    )
    echo Waiting for backend to start (%%i/30)...
)

echo Error: Backend failed to start within 30 seconds
pause
exit /b 1

:run_tests
echo.
echo ===== Running API Tests =====
python test_api_direct.py
set "test_result=!errorlevel!"

echo.
echo ===== Stopping Backend =====
taskkill /f /im python.exe >nul 2>&1

if !test_result! NEQ 0 (
    echo.
    echo ===== Tests failed with error code !test_result! =====
    pause
    exit /b !test_result!
)

echo.
echo ===== Tests completed successfully =====
pause
