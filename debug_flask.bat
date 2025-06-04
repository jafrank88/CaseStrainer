@echo off
setlocal enabledelayedexpansion

echo Starting Flask server in debug mode...
echo Output will be shown below. Server will stay running until you press Ctrl+C.
echo ============================================

:: Kill any existing Python processes
taskkill /f /im python.exe >nul 2>&1

:: Start Flask server and show output
python run_debug.py

echo.
echo ============================================
echo Flask server has stopped.
pause
