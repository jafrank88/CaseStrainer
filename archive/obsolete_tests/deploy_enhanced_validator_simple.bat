@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Simple Deployment
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

REM Modify app_final_vue.py to include the Enhanced Validator
echo Integrating Enhanced Validator with app_final_vue.py...
python -c "with open('app_final_vue.py', 'r') as f: content = f.read(); with open('app_final_vue.py', 'w') as f: f.write(content.replace('# Import the API endpoints\nfrom citation_api import citation_api', '# Import the API endpoints\nfrom citation_api import citation_api\n\n# Import the Enhanced Validator\ntry:\n    from enhanced_validator_production import register_enhanced_validator\n    print(\"Enhanced Validator module imported successfully\")\nexcept ImportError:\n    print(\"Warning: Enhanced Validator module not found\")\n    def register_enhanced_validator(app):\n        return app').replace('# Register the citation API blueprint\napp.register_blueprint(citation_api, url_prefix=\'/api\')', '# Register the citation API blueprint\napp.register_blueprint(citation_api, url_prefix=\'/api\')\n\n# Register the Enhanced Validator\ntry:\n    app = register_enhanced_validator(app)\n    print(\"Enhanced Validator registered with Flask app\")\nexcept NameError:\n    print(\"Warning: Enhanced Validator not registered\")'))"

echo.
echo Enhanced Validator has been integrated with app_final_vue.py.
echo.
echo To start the server with the Enhanced Validator, run:
echo   start_for_nginx.bat
echo.
echo The Enhanced Validator will be accessible at:
echo   - Local URL: http://127.0.0.1:5000/enhanced-validator
echo   - Production URL: https://wolf.law.uw.edu/casestrainer/enhanced-validator
echo.
echo Press any key to start the server...
pause >nul

REM Start the server with the correct host and port for production
start_for_nginx.bat

echo.
echo If the server started successfully, the Enhanced Validator should now be accessible.
echo.
