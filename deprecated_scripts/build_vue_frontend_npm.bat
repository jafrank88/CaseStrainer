@echo off
echo ===================================================
echo CaseStrainer Vue.js Build Script
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if the Vue.js project directory exists
if not exist "casestrainer-vue" (
    echo Error: casestrainer-vue directory not found.
    echo Please make sure you're running this script from the CaseStrainer root directory.
    exit /b 1
)

REM Navigate to the Vue.js project directory
echo Navigating to the Vue.js project directory...
cd casestrainer-vue

REM Check if npm is available
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: npm not found in PATH.
    echo Please make sure Node.js is properly installed and in your PATH.
    
    REM Try to find npm in common installation directories
    for %%i in (
        "C:\Program Files\nodejs\npm.cmd"
        "C:\Program Files (x86)\nodejs\npm.cmd"
        "%APPDATA%\npm\npm.cmd"
        "%USERPROFILE%\AppData\Roaming\npm\npm.cmd"
    ) do (
        if exist %%i (
            echo Found npm at: %%i
            set "NPM_PATH=%%i"
            goto :found_npm
        )
    )
    
    echo Could not find npm. Please install Node.js and try again.
    exit /b 1
)

:found_npm
echo npm found in PATH.
set "NPM_PATH=npm"

REM Install dependencies
echo Installing dependencies...
if defined NPM_PATH (
    if "%NPM_PATH%"=="npm" (
        call npm install
    ) else (
        call "%NPM_PATH%" install
    )
) else (
    call npm install
)

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies.
    echo Please check the error messages above.
    exit /b 1
)

REM Build the Vue.js frontend
echo Building the Vue.js frontend...
if defined NPM_PATH (
    if "%NPM_PATH%"=="npm" (
        call npm run build
    ) else (
        call "%NPM_PATH%" run build
    )
) else (
    call npm run build
)

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to build the Vue.js frontend.
    echo Please check the error messages above.
    exit /b 1
)

REM Check if the build was successful
if not exist "dist" (
    echo Error: Build directory not found.
    echo Please check the error messages above.
    exit /b 1
)

REM Create static/vue directory if it doesn't exist
cd ..
if not exist "static\vue" (
    echo Creating static/vue directory...
    mkdir "static\vue"
)

REM Copy the built files to the static/vue directory
echo Copying the built files to the static/vue directory...
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"

echo.
echo Vue.js frontend has been successfully built and copied to the static/vue directory.
echo Now you can run the application using your existing start_for_nginx.bat script.
echo.
echo Press any key to exit...
pause > nul
