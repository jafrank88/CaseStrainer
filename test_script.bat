@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo CaseStrainer Environment Test Script
echo ===================================================
echo Started at: %DATE% %TIME%
echo Current directory: %CD%

echo.
echo [1/4] Checking Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not in PATH or not installed
    pause
    exit /b 1
) else (
    echo [SUCCESS] Python is available
)

echo.
echo [2/4] Checking Python modules...
python -c "import flask"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Flask is not installed. Installing...
    pip install flask
) else (
    echo [SUCCESS] Flask is installed
)

echo.
echo [3/4] Checking Node.js...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not in PATH or not installed
    pause
    exit /b 1
) else (
    echo [SUCCESS] Node.js is available
)

echo.
echo [4/4] Checking npm...
npm --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not in PATH or not installed
    pause
    exit /b 1
) else (
    echo [SUCCESS] npm is available
)

echo.
echo ===================================================
echo Test completed at: %TIME%
echo ===================================================

pause
