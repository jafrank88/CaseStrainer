@echo off
echo CaseStrainer Vue.js Frontend Build Script
echo =====================================

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if the Vue.js project directory exists
if not exist "casestrainer-vue" (
    echo Error: casestrainer-vue directory not found.
    echo Please make sure you're running this script from the CaseStrainer root directory.
    exit /b 1
)

echo This script will help you build the Vue.js frontend.
echo.
echo Step 1: Navigate to the casestrainer-vue directory
cd casestrainer-vue
echo Current directory: %CD%
echo.

echo Step 2: Install dependencies (this may take a few minutes)
echo Running: npm install
call npm install
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies.
    echo Please make sure Node.js is properly installed and in your PATH.
    exit /b 1
)
echo Dependencies installed successfully.
echo.

echo Step 3: Build the Vue.js frontend
echo Running: npm run build
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to build the Vue.js frontend.
    echo Please check the error messages above.
    exit /b 1
)
echo Vue.js frontend built successfully.
echo.

echo Step 4: Copy the built files to the static/vue directory
cd ..
if not exist "static\vue" (
    mkdir "static\vue"
    echo Created static/vue directory.
)
echo Copying Vue.js frontend to static/vue directory...
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"
echo Vue.js frontend copied successfully.
echo.

echo Step 5: Create a simple test file to verify static file serving
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>CaseStrainer Test^</title^>^</head^>^<body^>^<h1^>CaseStrainer Test Page^</h1^>^<p^>If you can see this, static file serving is working correctly.^</p^>^</body^>^</html^> > "static\vue\test.html"
echo Test file created.
echo.

echo Vue.js frontend has been successfully built and deployed to the static/vue directory.
echo.
echo To start the application with the Vue.js frontend:
echo 1. Run app_final_vue.py with the following command:
echo    python app_final_vue.py --host=0.0.0.0 --port=5000
echo.
echo To test if the application is working correctly:
echo 1. Check if http://127.0.0.1:5000 is accessible locally
echo 2. Check if https://wolf.law.uw.edu/casestrainer/ is accessible externally
echo.

pause
