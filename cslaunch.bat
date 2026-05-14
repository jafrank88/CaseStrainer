@echo off
echo [DEPRECATED] cslaunch.bat is deprecated. Use cslauncher.ps1 instead.
echo Redirecting to cslauncher.ps1...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cslauncher.ps1" %*
exit /b %ERRORLEVEL%
