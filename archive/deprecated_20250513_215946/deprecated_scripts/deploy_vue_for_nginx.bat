@echo off
echo CaseStrainer Vue.js Deployment for Nginx
echo ======================================

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python and try again.
    exit /b 1
)

REM Set the current directory to the script directory
cd /d "%~dp0"

REM Check if port 5000 is already in use
netstat -ano | findstr :5000 >nul
if %ERRORLEVEL% equ 0 (
    echo Port 5000 is already in use. Attempting to kill the process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        taskkill /F /PID %%a
        if %ERRORLEVEL% equ 0 (
            echo Successfully killed process using port 5000.
        ) else (
            echo Failed to kill process. Please close the application using port 5000 manually.
            exit /b 1
        )
    )
)

REM Create static/vue directory if it doesn't exist
if not exist "static\vue" (
    mkdir "static\vue"
    echo Created static/vue directory.
)

REM Check if Vue.js frontend is built
if not exist "casestrainer-vue\dist\index.html" (
    echo Vue.js frontend is not built. Building now...
    
    REM Check if Node.js is installed
    where node >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Node.js is not installed or not in PATH. Please install Node.js and try again.
        exit /b 1
    )
    
    REM Build the Vue.js frontend
    cd casestrainer-vue
    call npm install
    call npm run build
    cd ..
    
    if not exist "casestrainer-vue\dist\index.html" (
        echo Failed to build Vue.js frontend. Please check the error messages above.
        exit /b 1
    )
    
    echo Vue.js frontend built successfully.
)

REM Copy Vue.js frontend to static/vue directory
echo Copying Vue.js frontend to static/vue directory...
xcopy /E /Y "casestrainer-vue\dist\*" "static\vue\"
echo Vue.js frontend copied successfully.

REM Create a simple test file to verify static file serving
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>CaseStrainer Test^</title^>^</head^>^<body^>^<h1^>CaseStrainer Test Page^</h1^>^<p^>If you can see this, static file serving is working correctly.^</p^>^</body^>^</html^> > "static\vue\test.html"

REM Update Nginx configuration to ensure it points to the correct port
echo Updating Nginx configuration...
echo # CaseStrainer configuration> "nginx_casestrainer.conf"
echo server {>> "nginx_casestrainer.conf"
echo     listen 443 ssl;>> "nginx_casestrainer.conf"
echo     server_name wolf.law.uw.edu;>> "nginx_casestrainer.conf"
echo.>> "nginx_casestrainer.conf"
echo     # SSL configuration>> "nginx_casestrainer.conf"
echo     ssl_certificate /etc/ssl/WolfCertBundle.crt;>> "nginx_casestrainer.conf"
echo     ssl_certificate_key /etc/ssl/wolf.law.uw.edu.key;>> "nginx_casestrainer.conf"
echo     ssl_protocols TLSv1.2 TLSv1.3;>> "nginx_casestrainer.conf"
echo.>> "nginx_casestrainer.conf"
echo     # CaseStrainer application>> "nginx_casestrainer.conf"
echo     location /casestrainer/ {>> "nginx_casestrainer.conf"
echo         proxy_pass http://10.158.120.151:5000/;>> "nginx_casestrainer.conf"
echo         proxy_set_header Host $host;>> "nginx_casestrainer.conf"
echo         proxy_set_header X-Real-IP $remote_addr;>> "nginx_casestrainer.conf"
echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;>> "nginx_casestrainer.conf"
echo         proxy_set_header X-Forwarded-Proto $scheme;>> "nginx_casestrainer.conf"
echo.>> "nginx_casestrainer.conf"
echo         # WebSocket support for SSE>> "nginx_casestrainer.conf"
echo         proxy_set_header Connection '';>> "nginx_casestrainer.conf"
echo         proxy_http_version 1.1;>> "nginx_casestrainer.conf"
echo         proxy_buffering off;>> "nginx_casestrainer.conf"
echo         proxy_cache off;>> "nginx_casestrainer.conf"
echo     }>> "nginx_casestrainer.conf"
echo }>> "nginx_casestrainer.conf"
echo Nginx configuration updated.

REM Create a simplified app.py file for serving the Vue.js frontend
echo Creating simplified app.py file...
echo """>> "app_vue_nginx.py"
echo CaseStrainer Flask application with Vue.js frontend for Nginx.>> "app_vue_nginx.py"
echo """>> "app_vue_nginx.py"
echo.>> "app_vue_nginx.py"
echo from flask import Flask, send_from_directory, request, jsonify, redirect>> "app_vue_nginx.py"
echo import os>> "app_vue_nginx.py"
echo.>> "app_vue_nginx.py"
echo # Create the Flask application>> "app_vue_nginx.py"
echo app = Flask(__name__)>> "app_vue_nginx.py"
echo.>> "app_vue_nginx.py"
echo # Serve the Vue.js static files>> "app_vue_nginx.py"
echo @app.route('/', defaults={'path': ''})>> "app_vue_nginx.py"
echo @app.route('/<path:path>')>> "app_vue_nginx.py"
echo def serve_vue(path):>> "app_vue_nginx.py"
echo     if path == "":>> "app_vue_nginx.py"
echo         return send_from_directory('static/vue', 'index.html')>> "app_vue_nginx.py"
echo     # Check if the file exists in static/vue>> "app_vue_nginx.py"
echo     if os.path.exists(os.path.join('static/vue', path)):>> "app_vue_nginx.py"
echo         return send_from_directory('static/vue', path)>> "app_vue_nginx.py"
echo     # For all other paths, serve the index.html file (for Vue router)>> "app_vue_nginx.py"
echo     return send_from_directory('static/vue', 'index.html')>> "app_vue_nginx.py"
echo.>> "app_vue_nginx.py"
echo # Add a test endpoint>> "app_vue_nginx.py"
echo @app.route('/api/test')>> "app_vue_nginx.py"
echo def test_api():>> "app_vue_nginx.py"
echo     return jsonify({'status': 'success', 'message': 'API is working'})>> "app_vue_nginx.py"
echo.>> "app_vue_nginx.py"
echo if __name__ == '__main__':>> "app_vue_nginx.py"
echo     # Run the application>> "app_vue_nginx.py"
echo     app.run(host='0.0.0.0', port=5000)>> "app_vue_nginx.py"
echo Simplified app.py file created.

REM Create a startup script for the simplified app
echo Creating startup script...
echo @echo off> "start_vue_nginx.bat"
echo echo Starting CaseStrainer with Vue.js frontend for Nginx...>> "start_vue_nginx.bat"
echo.>> "start_vue_nginx.bat"
echo REM Check if Python is installed>> "start_vue_nginx.bat"
echo where python ^>nul 2^>nul>> "start_vue_nginx.bat"
echo if %%ERRORLEVEL%% neq 0 (>> "start_vue_nginx.bat"
echo     echo Python is not installed or not in PATH. Please install Python and try again.>> "start_vue_nginx.bat"
echo     exit /b 1>> "start_vue_nginx.bat"
echo )>> "start_vue_nginx.bat"
echo.>> "start_vue_nginx.bat"
echo REM Check if port 5000 is already in use>> "start_vue_nginx.bat"
echo netstat -ano ^| findstr :5000 ^>nul>> "start_vue_nginx.bat"
echo if %%ERRORLEVEL%% equ 0 (>> "start_vue_nginx.bat"
echo     echo Port 5000 is already in use. Attempting to kill the process...>> "start_vue_nginx.bat"
echo     for /f "tokens=5" %%%%a in ('netstat -ano ^^^| findstr :5000') do (>> "start_vue_nginx.bat"
echo         taskkill /F /PID %%%%a>> "start_vue_nginx.bat"
echo         if %%ERRORLEVEL%% equ 0 (>> "start_vue_nginx.bat"
echo             echo Successfully killed process using port 5000.>> "start_vue_nginx.bat"
echo         ) else (>> "start_vue_nginx.bat"
echo             echo Failed to kill process. Please close the application using port 5000 manually.>> "start_vue_nginx.bat"
echo             exit /b 1>> "start_vue_nginx.bat"
echo         )>> "start_vue_nginx.bat"
echo     )>> "start_vue_nginx.bat"
echo )>> "start_vue_nginx.bat"
echo.>> "start_vue_nginx.bat"
echo REM Set the Flask app environment variables>> "start_vue_nginx.bat"
echo set FLASK_APP=app_vue_nginx.py>> "start_vue_nginx.bat"
echo set FLASK_ENV=production>> "start_vue_nginx.bat"
echo.>> "start_vue_nginx.bat"
echo REM Start the Flask application>> "start_vue_nginx.bat"
echo echo Starting CaseStrainer on http://127.0.0.1:5000>> "start_vue_nginx.bat"
echo echo For external access, use https://wolf.law.uw.edu/casestrainer/>> "start_vue_nginx.bat"
echo python app_vue_nginx.py>> "start_vue_nginx.bat"
echo.>> "start_vue_nginx.bat"
echo pause>> "start_vue_nginx.bat"
echo Startup script created.

echo.
echo Deployment preparation complete.
echo.
echo To start the application:
echo 1. Run start_vue_nginx.bat
echo 2. Access the application at https://wolf.law.uw.edu/casestrainer/
echo.
echo To test if the application is working correctly:
echo 1. Check if http://127.0.0.1:5000 is accessible locally
echo 2. Check if https://wolf.law.uw.edu/casestrainer/test.html is accessible externally
echo 3. Check if https://wolf.law.uw.edu/casestrainer/api/test returns {"status":"success","message":"API is working"}
echo.

pause
