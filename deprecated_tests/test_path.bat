@echo off
echo Testing file existence...

echo Method 1: Relative path
if exist "src\app_final_vue.py" (
    echo [OK] File exists at src\app_final_vue.py
) else (
    echo [ERROR] File not found at src\app_final_vue.py
)

echo.
echo Method 2: Full path
set "FULL_PATH=%~dp0src\app_final_vue.py"
if exist "%FULL_PATH%" (
    echo [OK] File exists at %FULL_PATH%
) else (
    echo [ERROR] File not found at %FULL_PATH%
)

echo.
echo Method 3: Using dir command
dir /b "src\app_final_vue.py"

echo.
echo Current directory:
cd

echo.
@REM Try to run the Flask app directly
echo Trying to run Flask app directly...
python -c "import os; print(f'Python working directory: {os.getcwd()}'); print(f'File exists: {os.path.exists(\"src/app_final_vue.py\")}')"

pause
