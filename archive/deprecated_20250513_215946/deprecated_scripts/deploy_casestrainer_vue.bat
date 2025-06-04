@echo off
echo Deploying CaseStrainer with Vue.js frontend for production...

REM Check if Windows Nginx is running and stop it
echo Checking for Windows Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Windows Nginx...
    taskkill /F /IM nginx.exe
    echo Windows Nginx stopped.
) else (
    echo Windows Nginx is not running.
)

REM Check if port 5000 is already in use
echo Checking if port 5000 is in use...
netstat -ano | findstr :5000 | findstr LISTENING
if "%ERRORLEVEL%"=="0" (
    echo Port 5000 is in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        echo Killing process with PID %%a
        taskkill /F /PID %%a
    )
    echo Process killed.
) else (
    echo Port 5000 is available.
)

REM Build Vue.js frontend for production
echo Building Vue.js frontend for production...
cd "%~dp0\casestrainer-vue"
call npm run build
echo Vue.js frontend built successfully.

REM Create a directory for the built files in the Flask static folder if it doesn't exist
echo Creating directory for Vue.js files in Flask static folder...
cd "%~dp0"
if not exist "static\vue" mkdir "static\vue"

REM Copy the built files to the Flask static/vue directory
echo Copying Vue.js build files to Flask static folder...
xcopy /E /Y "%~dp0\casestrainer-vue\dist\*" "%~dp0\static\vue\"

REM Update Flask app to serve Vue.js files
echo Updating Flask app to serve Vue.js files...

REM Start Flask backend with Vue.js integration on port 5000 with host 0.0.0.0
echo Starting Flask backend with Vue.js integration on port 5000 with host 0.0.0.0...
cd "%~dp0"
start cmd /k "python app_final_vue.py --host=0.0.0.0 --port=5000"

echo.
echo CaseStrainer with Vue.js frontend deployed successfully!
echo.
echo The application should now be accessible at:
echo - Local: http://localhost:5000
echo - External: https://wolf.law.uw.edu/casestrainer/
echo.
echo Press any key to stop the server when done...
pause > nul

REM Kill all services when done
taskkill /F /FI "WINDOWTITLE eq *python*"
echo All services stopped.
