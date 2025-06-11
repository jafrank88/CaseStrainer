@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: Debug Simple Deployment - Shows each step
:: ===================================================

:: Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Please run as administrator
    pause
    exit /b 1
)

:: Define paths
set "CASESTRAINER_DIR=C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
set "BACKEND_DIR=%CASESTRAINER_DIR%\src"
set "FRONTEND_DIR=%CASESTRAINER_DIR%\casestrainer-vue-new"
set "NGINX_DIR=%CASESTRAINER_DIR%\nginx-1.27.5"

echo.
echo ===================================================
echo  Debug Simple Deployment
echo ===================================================
echo Time: %DATE% %TIME%
echo.

:: Change to CaseStrainer directory
cd /d "%CASESTRAINER_DIR%"
echo [INFO] Working directory: %CD%
echo.

:: Load configuration
echo [STEP 1] Loading configuration...
for /f "tokens=1,* delims==" %%a in ('type config.ini ^| findstr "PROD_BACKEND_PORT"') do set "PROD_BACKEND_PORT=%%b"
echo [DEBUG] Backend port from config: %PROD_BACKEND_PORT%
echo.

:: Check if Vue build exists
echo [STEP 2] Checking Vue build...
if exist "%FRONTEND_DIR%\dist\index.html" (
    echo [OK] Vue build exists: %FRONTEND_DIR%\dist\index.html
) else (
    echo [ERROR] Vue build not found - need to build first
    pause
    exit /b 1
)
echo.

:: Check backend directory
echo [STEP 3] Checking Flask backend...
if exist "%BACKEND_DIR%\app_final_vue.py" (
    echo [OK] Flask app found: %BACKEND_DIR%\app_final_vue.py
) else (
    echo [ERROR] Flask app not found
    pause
    exit /b 1
)
echo.

:: Check if port is available
echo [STEP 4] Checking port %PROD_BACKEND_PORT%...
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [WARNING] Port %PROD_BACKEND_PORT% already in use
    echo [INFO] Stopping existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PROD_BACKEND_PORT% " ^| findstr "LISTENING"') do (
        echo [INFO] Killing process ID: %%a
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Port %PROD_BACKEND_PORT% is available
)
echo.

:: Start Flask backend with detailed logging
echo [STEP 5] Starting Flask backend...
cd /d "%BACKEND_DIR%"
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Starting Flask on port %PROD_BACKEND_PORT%...

:: Create a detailed Flask startup script
set "FLASK_SCRIPT=%TEMP%\start_flask.bat"
(
    echo @echo off
    echo setlocal enabledelayedexpansion
    echo title CaseStrainer Flask Backend - Port %PROD_BACKEND_PORT%
    echo echo ============================================
    echo echo  CaseStrainer Flask Backend
    echo echo ============================================
    echo echo Port: %PROD_BACKEND_PORT%
    echo echo Directory: %BACKEND_DIR%
    echo echo Time: %%TIME%%
    echo echo ============================================
    echo echo.
    echo cd /d "%BACKEND_DIR%"
    echo echo [FLASK] Current directory: %%CD%%
    echo echo [FLASK] Checking Python...
    echo python --version
    echo echo [FLASK] Checking app file...
    echo dir app_final_vue.py
    echo echo [FLASK] Starting Flask application...
    echo echo [FLASK] Command: python app_final_vue.py --port=%PROD_BACKEND_PORT% --host=0.0.0.0
    echo echo.
    echo python app_final_vue.py --port=%PROD_BACKEND_PORT% --host=0.0.0.0
    echo echo.
    echo echo [FLASK] Flask process ended with exit code: %%ERRORLEVEL%%
    echo echo Press any key to close this window...
    echo pause
) > "%FLASK_SCRIPT%"

echo [INFO] Starting Flask in new window...
start "Flask_Backend" cmd /c "%FLASK_SCRIPT%"

echo [INFO] Waiting 10 seconds for Flask to start...
timeout /t 10 /nobreak

:: Check if Flask started
echo [STEP 6] Verifying Flask startup...
netstat -ano | findstr ":%PROD_BACKEND_PORT% " | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Flask is running on port %PROD_BACKEND_PORT%
    
    :: Try to get the process info
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PROD_BACKEND_PORT% " ^| findstr "LISTENING"') do (
        echo [INFO] Flask process ID: %%a
    )
) else (
    echo [ERROR] Flask is not responding on port %PROD_BACKEND_PORT%
    echo [DEBUG] Checking what's on that port...
    netstat -ano | findstr ":%PROD_BACKEND_PORT%"
    echo.
    echo [DEBUG] Check the Flask window for error messages
    pause
    exit /b 1
)
echo.

:: Continue with Nginx...
echo [STEP 7] Preparing Nginx configuration...
cd /d "%NGINX_DIR%"
echo [DEBUG] Nginx directory: %CD%

if not exist "nginx.exe" (
    echo [ERROR] nginx.exe not found in %CD%
    pause
    exit /b 1
)

echo [OK] Nginx executable found
echo.

echo [INFO] Deployment continuing... Flask is ready!
echo [INFO] Next: Nginx configuration and startup
echo.
echo Press any key to continue with Nginx setup...
pause

echo [INFO] Nginx setup would continue here...
echo [SUCCESS] Debug deployment completed!
echo.
echo Flask Backend: Running on port %PROD_BACKEND_PORT%
echo Access the Flask directly at: http://localhost:%PROD_BACKEND_PORT%
echo.
pause