@echo off
setlocal enabledelayedexpansion

echo ===== Environment Check =====
echo Date: %date% %time%
echo Current directory: %CD%
echo.

echo === Python Check ===
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python is not in PATH or not installed.
) else (
    echo Python found in PATH
    where python
)

echo.
echo === Required Files ===
dir /b start_casestrainer.bat
if exist start_casestrainer.bat (
    echo start_casestrainer.bat exists
) else (
    echo ERROR: start_casestrainer.bat not found!
)

echo.
echo === Python Files ===
dir /b app_final_vue.py
if exist app_final_vue.py (
    echo app_final_vue.py exists
) else (
    echo ERROR: app_final_vue.py not found!
)

echo.
echo === Nginx Check ===
if exist "nginx-1.27.5" (
    echo Nginx directory exists
    dir /b nginx-1.27.5\nginx.exe
) else (
    echo WARNING: nginx-1.27.5 directory not found
)

echo.
echo ===== Running start_casestrainer.bat with echo on =====
@echo on
call start_casestrainer.bat
@echo off

echo.
echo ===== start_casestrainer.bat has exited =====
pause
