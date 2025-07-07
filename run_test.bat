@echo off
echo Running PDF test...
echo.

REM Try to find Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python in PATH
    python test_api_simple.py
    goto :end
)

REM Try virtual environment
if exist ".venv\Scripts\python.exe" (
    echo Found Python in virtual environment
    .venv\Scripts\python.exe test_api_simple.py
    goto :end
)

REM Try system Python
if exist "D:\Python\python.exe" (
    echo Found system Python
    D:\Python\python.exe test_api_simple.py
    goto :end
)

echo Python not found. Please run manually:
echo python test_api_simple.py

:end
pause 