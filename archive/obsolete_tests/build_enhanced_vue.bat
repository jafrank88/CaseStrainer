@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Build Script
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Set the Node.js path explicitly
set NODE_PATH=D:\node
set PATH=%NODE_PATH%;%PATH%

echo Using Node.js from: %NODE_PATH%
echo.

REM Navigate to the Vue.js project directory
cd /d "%~dp0\casestrainer-vue"

REM Install dependencies first
echo Installing Vue.js dependencies...
call %NODE_PATH%\npm.cmd install
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

REM Install Vue CLI service specifically
echo Installing Vue CLI service...
call %NODE_PATH%\npm.cmd install @vue/cli-service
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Vue CLI service.
    exit /b 1
)

REM Build the Vue.js frontend
echo Building Vue.js frontend for production...
call %NODE_PATH%\npm.cmd run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed.
    exit /b 1
)

REM Copy the built files to the static directory
echo.
echo Copying built files to static/vue directory...
cd /d "%~dp0"
if not exist "static\vue" mkdir "static\vue"
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"

echo.
echo Build and deployment complete!
echo Enhanced Validator is now available in the Vue.js frontend.
echo.
