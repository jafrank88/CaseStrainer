@echo off
setlocal enabledelayedexpansion

echo Checking for Visual Studio Build Tools...
where cl.exe >nul 2>nul
if errorlevel 1 (
    echo Visual Studio Build Tools not found.
    echo Please install Visual Studio Build Tools with C++ workload from:
    echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo After installation, please run this script again.
    pause
    exit /b 1
)

echo Checking for CMake...
where cmake.exe >nul 2>nul
if errorlevel 1 (
    echo CMake not found.
    echo Please install CMake from:
    echo https://cmake.org/download/
    echo.
    echo After installation, please run this script again.
    pause
    exit /b 1
)

echo Installing Python packages...
pip install --upgrade pip
pip install wheel setuptools
pip install hyperscan

echo.
echo Setup complete! You can now use Hyperscan in your Python scripts.
echo.
pause 