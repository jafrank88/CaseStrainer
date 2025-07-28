@echo off
echo.
echo ============================================================
echo   DEPRECATED STARTUP SCRIPT
echo ============================================================
echo.
echo This startup script has been deprecated in favor of the
echo modern, comprehensive cslaunch.ps1 PowerShell script.
echo.
echo Please use instead:
echo   .\cslaunch.ps1
echo.
echo Benefits of cslaunch.ps1:
echo   - Docker-based deployment
echo   - Menu-driven interface
echo   - Health checks and validation
echo   - Vue.js build management
echo   - Error handling and logging
echo   - Multiple deployment modes
echo.
echo ============================================================
echo.
pause
echo.
echo Launching cslaunch.ps1 for you...
powershell -ExecutionPolicy Bypass -File ".\cslaunch.ps1"
