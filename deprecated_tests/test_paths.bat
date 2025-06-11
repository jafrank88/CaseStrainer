@echo off
echo Script directory: %~dp0
set "BACKEND_DIR=%~dp0src"
echo BACKEND_DIR: %BACKEND_DIR%

echo Checking if app_final_vue.py exists in src:
if exist "%BACKEND_DIR%\app_final_vue.py" (
    echo [OK] Found: %BACKEND_DIR%\app_final_vue.py
) else (
    echo [ERROR] Not found: %BACKEND_DIR%\app_final_vue.py
    echo Current directory: %CD%
    echo Directory listing of %BACKEND_DIR%:
    dir "%BACKEND_DIR%"
)

pause
