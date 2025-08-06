@echo off
echo === Testing Docker Recovery ===

echo Testing Docker responsiveness...
docker info
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker is responsive
) else (
    echo ✗ Docker is unresponsive
)

echo.
echo Container Status:
docker ps -a

echo.
echo ✓ Recovery test completed
pause 