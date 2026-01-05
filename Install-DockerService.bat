@echo off
echo ========================================
echo Installing CaseStrainer Docker Service
echo ========================================
echo.
echo This requires Administrator privileges...
echo.

powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File D:\dev\casestrainer\Create-DockerService.ps1' -Verb RunAs"

echo.
echo If the UAC prompt appeared, please approve to continue...
echo.
pause
