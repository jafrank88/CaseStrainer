@echo off

:: Get the current directory
set "CURRENT_DIR=%~dp0"
echo Current directory: %CURRENT_DIR%

:: Check if file exists using relative path
if exist "src\app_final_vue.py" (
    echo [1] File found using relative path: src\app_final_vue.py
) else (
    echo [1] File NOT found using relative path: src\app_final_vue.py
)

:: Check if file exists using full path
if exist "%CURRENT_DIR%src\app_final_vue.py" (
    echo [2] File found using full path: %CURRENT_DIR%src\app_final_vue.py
) else (
    echo [2] File NOT found using full path: %CURRENT_DIR%src\app_final_vue.py
)

:: List contents of src directory
echo.
echo Contents of src directory:
dir /b "%CURRENT_DIR%src" | findstr /i "app_final"

pause
