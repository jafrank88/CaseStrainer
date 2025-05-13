@echo off
echo ===================================================
echo CaseStrainer Dependencies Installation Script
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if Python is installed
IF EXIST "C:\Python313\python.exe" (
    echo Found Python at C:\Python313\python.exe
    set "PYTHON_PATH=C:\Python313\python.exe"
) ELSE (
    echo Python not found at C:\Python313\python.exe
    echo Checking for Python in virtual environment...
    
    IF EXIST ".venv\Scripts\python.exe" (
        echo Found Python in virtual environment
        set "PYTHON_PATH=.venv\Scripts\python.exe"
    ) ELSE (
        echo Python not found in virtual environment
        echo Please install Python and try again
        exit /b 1
    )
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    echo Please make sure you're running this script from the CaseStrainer root directory
    exit /b 1
)

REM Install dependencies
echo Installing dependencies using %PYTHON_PATH%...
"%PYTHON_PATH%" -m pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies
    echo Please check the error messages above
    exit /b 1
)

echo.
echo Dependencies installed successfully
echo You can now run the application using start_for_nginx.bat
echo.
echo Press any key to exit...
pause > nul
