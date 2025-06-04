@echo off
echo ===================================================
echo CaseStrainer Enhanced Validator Deployment Script
echo ===================================================
echo.

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Stop any running Python processes
echo Stopping any running Python processes...
taskkill /f /im python.exe >nul 2>&1

REM Create a backup of the original app_final_vue.py
echo Creating backup of app_final_vue.py...
copy "app_final_vue.py" "app_final_vue.py.bak"

REM Modify app_final_vue.py to include the Enhanced Validator
echo Integrating Enhanced Validator with app_final_vue.py...
python -c "with open('app_final_vue.py', 'r') as f: content = f.read(); with open('app_final_vue.py', 'w') as f: f.write(content.replace('# Import the API endpoints\nfrom citation_api import citation_api', '# Import the API endpoints\nfrom citation_api import citation_api\n\n# Import the Enhanced Validator\ntry:\n    from enhanced_validator_production import register_enhanced_validator\n    print(\"Enhanced Validator module imported successfully\")\nexcept ImportError:\n    print(\"Warning: Enhanced Validator module not found\")\n    def register_enhanced_validator(app):\n        return app').replace('# Register the citation API blueprint\napp.register_blueprint(citation_api, url_prefix=\'/api\')', '# Register the citation API blueprint\napp.register_blueprint(citation_api, url_prefix=\'/api\')\n\n# Register the Enhanced Validator\ntry:\n    app = register_enhanced_validator(app)\n    print(\"Enhanced Validator registered with Flask app\")\nexcept NameError:\n    print(\"Warning: Enhanced Validator not registered\")'))"

REM Build the Vue.js frontend with the Enhanced Validator component
echo Building Vue.js frontend with Enhanced Validator...
call build_enhanced_vue.bat

REM Start the application using the proper production startup script
echo.
echo Starting CaseStrainer with Enhanced Validator...
echo.
echo To access the Enhanced Validator:
echo - Local URL: http://127.0.0.1:5000/enhanced-validator
echo - Production URL: https://wolf.law.uw.edu/casestrainer/enhanced-validator
echo.
echo Press any key to start the server...
pause >nul

REM Start the server with the correct host and port for production
start_for_nginx.bat

echo.
echo If the server started successfully, the Enhanced Validator should now be accessible.
echo.
