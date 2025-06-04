@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Deployment
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if Windows Nginx is running and stop it
echo Checking if Windows Nginx is running...
tasklist /fi "imagename eq nginx.exe" | find /i "nginx.exe" > nul
if %ERRORLEVEL% EQU 0 (
    echo Stopping Windows Nginx...
    taskkill /f /im nginx.exe >nul 2>&1
    echo Windows Nginx stopped.
) else (
    echo Windows Nginx is not running.
)

REM Stop any running Python processes
echo Stopping any running Python processes...
taskkill /f /im python.exe >nul 2>&1
echo Python processes stopped.

REM Create a backup of the original app_final_vue.py
echo Creating backup of app_final_vue.py...
copy "app_final_vue.py" "app_final_vue.py.bak" >nul 2>&1
echo Backup created.

REM Make sure the Vue.js components are up to date
echo Checking Vue.js components...
cd casestrainer-vue
if exist "node_modules" (
    echo Vue.js dependencies already installed.
) else (
    echo Installing Vue.js dependencies...
    call npm install
)

REM Build the Vue.js frontend
echo Building Vue.js frontend...
call npm run build
echo Vue.js build complete.

REM Return to the main directory
cd ..

REM Copy the built files to the static directory
echo Copying Vue.js build to static directory...
if not exist "static\vue" mkdir "static\vue"
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\" >nul 2>&1
echo Vue.js files copied.

REM Update the Home.vue component to include a link to the Enhanced Validator
echo Updating Home.vue to include Enhanced Validator link...
cd casestrainer-vue\src\views
powershell -Command "(Get-Content Home.vue) -replace '<div class=\"col-md-6 mb-4\">', '<div class=\"col-md-6 mb-4\">\n          <!-- Enhanced Validator Card -->\n          <div class=\"card mb-4\">\n            <div class=\"card-body\">\n              <h5 class=\"card-title\">Enhanced Citation Validator</h5>\n              <p class=\"card-text\">Validate legal citations with our enhanced tool that provides context and suggestions.</p>\n              <router-link to=\"/enhanced-validator\" class=\"btn btn-primary\">Try Enhanced Validator</router-link>\n            </div>\n          </div>' | Set-Content Home.vue"
echo Home.vue updated.
cd ..\..\..

REM Ensure the templates directory exists
if not exist "templates" mkdir "templates"

REM Check if the Enhanced Validator template exists
if not exist "templates\enhanced_validator.html" (
    echo Creating Enhanced Validator template...
    echo ^<!DOCTYPE html^> > "templates\enhanced_validator.html"
    echo ^<html lang="en"^> >> "templates\enhanced_validator.html"
    echo ^<head^> >> "templates\enhanced_validator.html"
    echo     ^<meta charset="UTF-8"^> >> "templates\enhanced_validator.html"
    echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^> >> "templates\enhanced_validator.html"
    echo     ^<title^>Enhanced Citation Validator^</title^> >> "templates\enhanced_validator.html"
    echo     ^<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"^> >> "templates\enhanced_validator.html"
    echo ^</head^> >> "templates\enhanced_validator.html"
    echo ^<body^> >> "templates\enhanced_validator.html"
    echo     ^<div class="container mt-5"^> >> "templates\enhanced_validator.html"
    echo         ^<h1^>Enhanced Citation Validator^</h1^> >> "templates\enhanced_validator.html"
    echo         ^<p^>This page has been replaced by the Vue.js version. Please use the Vue.js interface.^</p^> >> "templates\enhanced_validator.html"
    echo         ^<a href="/casestrainer/" class="btn btn-primary"^>Go to Vue.js Interface^</a^> >> "templates\enhanced_validator.html"
    echo     ^</div^> >> "templates\enhanced_validator.html"
    echo ^</body^> >> "templates\enhanced_validator.html"
    echo ^</html^> >> "templates\enhanced_validator.html"
    echo Enhanced Validator template created.
) else (
    echo Enhanced Validator template already exists.
)

REM Check if the server is already running on port 5000
echo Checking if port 5000 is in use...
netstat -ano | findstr :5000 | findstr LISTENING > nul
if %ERRORLEVEL% EQU 0 (
    echo Port 5000 is already in use. Killing the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    echo Process killed.
) else (
    echo Port 5000 is available.
)

echo.
echo Enhanced Validator has been integrated with CaseStrainer.
echo.
echo Starting the server with the Enhanced Validator...
echo.
echo The Enhanced Validator will be accessible at:
echo   - Local URL: http://127.0.0.1:5000/enhanced-validator
echo   - Production URL: https://wolf.law.uw.edu/casestrainer/enhanced-validator
echo.

REM Start the server with the correct host and port for production
start cmd /k "python app_final_vue.py --host 0.0.0.0 --port 5000 --debug"

echo.
echo Server started successfully. The Enhanced Validator should now be accessible.
echo.
echo Press any key to exit this script...
pause >nul
