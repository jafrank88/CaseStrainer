@echo off
echo Deploying Vue.js frontend for CaseStrainer...

REM Navigate to the Vue.js project directory
cd /d "%~dp0\casestrainer-vue"

REM Check if npm is installed
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: npm is not installed or not in the PATH.
    echo Please install Node.js and npm to build the Vue.js frontend.
    exit /b 1
)

REM Install dependencies if needed
echo Installing Vue.js dependencies...
call npm install

REM Build the Vue.js frontend for production
echo Building Vue.js frontend for production...
call npm run build

REM Create a directory for the built files in the Flask static folder if it doesn't exist
echo Creating directory for Vue.js files in Flask static folder...
cd /d "%~dp0"
if not exist "static\vue" mkdir "static\vue"

REM Copy the built files to the Flask static/vue directory
echo Copying Vue.js build files to Flask static folder...
xcopy /E /Y "%~dp0\casestrainer-vue\dist\*" "%~dp0\static\vue\"

echo Vue.js frontend deployed successfully!
echo.
echo To access the Vue.js frontend, go to:
echo https://wolf.law.uw.edu/casestrainer/vue/
echo.
echo Make sure the Flask application is running with the start_simple.bat script.
echo.
pause
