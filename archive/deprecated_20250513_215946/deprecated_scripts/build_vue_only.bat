@echo off
echo ===================================================
echo CaseStrainer Vue.js Build Script
echo ===================================================
echo.

:: Set the current directory to the script directory
cd /d "%~dp0"

:: Check if the Vue.js project directory exists
if not exist "casestrainer-vue" (
    echo Error: casestrainer-vue directory not found.
    echo Please make sure you're running this script from the CaseStrainer root directory.
    exit /b 1
)

:: Navigate to the Vue.js project directory
echo Navigating to the Vue.js project directory...
cd casestrainer-vue

:: Install dependencies
echo Installing dependencies...
call npm install
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies.
    echo Please check the error messages above.
    exit /b 1
)

:: Build the Vue.js frontend
echo Building the Vue.js frontend...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to build the Vue.js frontend.
    echo Please check the error messages above.
    exit /b 1
)

:: Check if the build was successful
if not exist "dist" (
    echo Error: Build directory not found.
    echo Please check the error messages above.
    exit /b 1
)

:: Create static/vue directory if it doesn't exist
cd ..
if not exist "static\vue" (
    echo Creating static/vue directory...
    mkdir "static\vue"
)

:: Copy the built files to the static/vue directory
echo Copying the built files to the static/vue directory...
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"

echo.
echo Vue.js frontend has been successfully built and copied to the static/vue directory.
echo Now you can run the application using your existing start_for_nginx.bat script.
echo.
echo Press any key to exit...
pause > nul
