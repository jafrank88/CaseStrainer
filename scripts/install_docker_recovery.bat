@echo off
echo Installing Docker Recovery System...
echo This requires administrator privileges.
echo.

powershell -Command "Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0setup_docker_recovery_tasks.ps1\" -Install' -Verb RunAs"

echo.
echo Installation initiated. Please approve the UAC prompt.
pause
