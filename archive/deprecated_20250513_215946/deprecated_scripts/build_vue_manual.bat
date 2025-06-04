@echo off
echo CaseStrainer Vue.js Manual Build Script
echo =====================================

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if the Vue.js project directory exists
if not exist "casestrainer-vue" (
    echo Error: casestrainer-vue directory not found.
    echo Please make sure you're running this script from the CaseStrainer root directory.
    exit /b 1
)

echo This script will help you manually build the Vue.js frontend.
echo.
echo Follow these steps:
echo 1. Open a new command prompt
echo 2. Navigate to the casestrainer-vue directory:
echo    cd "%~dp0casestrainer-vue"
echo 3. Run the following commands:
echo    npm install
echo    npm run build
echo 4. Once the build is complete, come back to this script and press any key.
echo.
echo After the build is complete, this script will copy the built files to the static/vue directory.
echo.
pause

REM Check if the build was successful
if not exist "casestrainer-vue\dist" (
    echo Error: Build directory not found.
    echo Please make sure you've successfully built the Vue.js frontend.
    exit /b 1
)

REM Create static/vue directory if it doesn't exist
if not exist "static\vue" (
    mkdir "static\vue"
    echo Created static/vue directory.
)

REM Copy Vue.js frontend to static/vue directory
echo Copying Vue.js frontend to static/vue directory...
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"
echo Vue.js frontend copied successfully.

REM Create a simple test file to verify static file serving
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>CaseStrainer Test^</title^>^</head^>^<body^>^<h1^>CaseStrainer Test Page^</h1^>^<p^>If you can see this, static file serving is working correctly.^</p^>^</body^>^</html^> > "static\vue\test.html"

echo.
echo Vue.js frontend has been successfully built and deployed to the static/vue directory.
echo.
echo To start the application:
echo 1. Run start_vue_nginx.bat
echo 2. Access the application at https://wolf.law.uw.edu/casestrainer/
echo.
echo To test if the application is working correctly:
echo 1. Check if http://127.0.0.1:5000 is accessible locally
echo 2. Check if https://wolf.law.uw.edu/casestrainer/test.html is accessible externally
echo.

pause
