@echo off
setlocal enabledelayedexpansion

set LOG_FILE=flask_debug.log
echo Starting Flask server with monitoring...
echo Logging to %LOG_FILE%
echo.

echo [%date% %time%] Starting Flask server... > "%LOG_FILE%"

:: Start Flask server in a new window and capture output
start "Flask Server" /B cmd /c "python run_debug.py 1>>"%LOG_FILE%" 2>&1"

echo Waiting for Flask to start...

:: Wait for the server to start (up to 30 seconds)
set started=0
for /l %%i in (1,1,30) do (
    timeout /t 1 >nul
    netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
    if !errorlevel! equ 0 (
        set started=1
        echo Flask server is running on port 5000
        goto server_running
    )
    echo Waiting for Flask to start (%%i/30)...
)

echo Error: Flask failed to start within 30 seconds
call :show_log
pause
goto :eof

:server_running
echo.
echo Flask server is running. Monitoring for shutdown...
echo Press Ctrl+C to stop monitoring.
echo.

:monitor_loop
:: Check if the Python process is still running
tasklist | find "python" >nul
if !errorlevel! equ 1 (
    echo.
    echo Flask server has stopped.
    call :show_log
    pause
    goto :eof
)

timeout /t 1 >nul
goto monitor_loop

:show_log
echo.
echo ===== LAST 20 LINES OF LOG =====
tail -n 20 "%LOG_FILE%"
echo ================================
echo.
return
