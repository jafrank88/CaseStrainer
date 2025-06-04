@echo off
setlocal enabledelayedexpansion

:: ===========================================
:: CaseStrainer Application Launcher
:: Manages both backend and frontend processes
:: ===========================================

:: Set console title
title CaseStrainer Launcher

:: Default configuration
set ENV=dev
set BACKEND_PORT=5000
set FRONTEND_PORT=5173
set BACKEND_CONFIG=config_dev.py
set FRONTEND_CMD=dev
set NODE_ENV=development
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONUNBUFFERED=1

:: Log file setup
set LOG_DIR=logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\casestrainer_%date:/=%.log
echo [%TIME%] Starting CaseStrainer >> "%LOG_FILE%"

:: Check for required commands
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not in PATH. Please install Python 3.8 or higher and ensure it's in your PATH.
    pause
    exit /b 1
)

where pip >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip is not found. Please ensure Python is installed correctly.
    pause
    exit /b 1
)

:: Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.8 or higher is required. Current version:
    python --version
    pause
    exit /b 1
)

:: Check for required Python packages
for %%p in (flask waitress) do (
    python -c "import %%p" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [INFO] Installing missing Python package: %%p
        pip install %%p
        if %ERRORLEVEL% NEQ 0 (
            echo [ERROR] Failed to install required package: %%p
            pause
            exit /b 1
        )
    )
)

:: Window titles for process management
set BACKEND_TITLE=CaseStrainer_Backend
set FRONTEND_TITLE=CaseStrainer_Frontend

:check_env
if "%1"=="" goto show_menu
if "%1"=="--prod" (
    set ENV=prod
    set BACKEND_PORT=5001
    set FRONTEND_PORT=4173
    set BACKEND_CONFIG=config_prod.py
    set FRONTEND_CMD=preview
    set NODE_ENV=production
    set FLASK_ENV=production
    set FLASK_DEBUG=0
    shift
    goto :check_env
)
if "%1"=="--dev" (
    set ENV=dev
    shift
    goto :check_env
)

:show_menu
echo ============================================
echo  CaseStrainer Application Manager
echo  Environment: !ENV! Mode (Ports: !BACKEND_PORT!/!FRONTEND_PORT!)
echo ============================================
echo 1. Start Backend (Flask)
echo 2. Start Frontend (Vue.js)
echo 3. Start Both (Backend + Frontend)
echo 4. Run Tests
echo 5. Stop All Services
echo 6. Check Status
echo 7. Switch Environment (Current: !ENV!)
echo 8. Install Dependencies
echo 9. Exit
echo ============================================

:menu
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_both
if "%choice%"=="4" (
    :test_menu
    echo.
    echo === Test Menu ===
    echo 1. Run All Tests
    echo 2. Run API Tests
    echo 3. Run Frontend Tests
    echo 4. Back to Main Menu
    echo ============================================
    set /p test_choice="Select test option (1-4): "
    if "%test_choice%"=="1" call :run_all_tests
    if "%test_choice%"=="2" call :run_api_tests
    if "%test_choice%"=="3" call :run_frontend_tests
    if "%test_choice%"=="4" goto show_menu
    goto test_menu
)
if "%choice%"=="5" (
    call :stop_all
    goto show_menu
)
if "%choice%"=="6" (
    call :check_status
    pause
    goto show_menu
)
if "%choice%"=="7" (
    call :switch_env
    goto show_menu
)
if "%choice%"=="8" (
    call :install_deps
    goto show_menu
)
if "%choice%"=="9" goto end

echo.
echo [ERROR] Invalid choice: %choice%
echo Please enter a number between 1 and 9.
timeout /t 2 >nul
goto show_menu

:start_backend
echo.
echo ============================================
echo  STARTING BACKEND SERVER
echo ============================================
echo Current directory: %CD%
echo Python version:
python --version
echo.

echo Stopping any existing backend processes...
taskkill /f /im python.exe 2>nul

if not exist "%~dp0src\app_final_vue.py" (
    echo [ERROR] Could not find app_final_vue.py in src directory!
    echo Expected path: %~dp0src\app_final_vue.py
    dir "%~dp0src\"
    echo.
    pause
    goto :show_menu
)

echo.
echo Starting backend server...
echo Running: python "%~dp0src\app_final_vue.py"

:: Set environment variables for backend
set FLASK_APP=app_final_vue.py
set FLASK_ENV=!FLASK_ENV!
set FLASK_DEBUG=!FLASK_DEBUG!

:: First try running directly to see any Python errors
echo Starting backend with port: !BACKEND_PORT!
python "%~dp0src\app_final_vue.py" --port=!BACKEND_PORT! --host=0.0.0.0 --use-waitress
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Backend server failed to start with error level %ERRORLEVEL%
    echo.
    echo Possible issues:
    echo 1. Missing Python dependencies - try: pip install -r requirements.txt
    echo 2. Port !BACKEND_PORT! might be in use - try: netstat -ano | findstr :!BACKEND_PORT!
    echo 3. Check for syntax errors in app_final_vue.py
    echo.
    pause
    goto :show_menu
)

:: Start the backend in a new window
echo [INFO] Starting backend at http://localhost:!BACKEND_PORT!

:: Start the backend in a new window with logging
echo [INFO] Starting backend process in a new window...
start "%BACKEND_TITLE%" /D "%~dp0src" cmd /k "@echo [%DATE% %TIME%] Starting CaseStrainer Backend && echo Backend URL: http://localhost:!BACKEND_PORT! && python app_final_vue.py --port=!BACKEND_PORT! --host=0.0.0.0 --use-waitress"

echo.
echo ============================================
echo  BACKEND STARTED SUCCESSFULLY
echo ============================================
echo  URL: http://localhost:!BACKEND_PORT!
echo  Press Ctrl+C in the backend window to stop the server
echo ============================================
echo.

timeout /t 2 >nul
goto :show_menu

:start_frontend
setlocal enabledelayedexpansion
echo.
echo ============================================
echo  STARTING FRONTEND DEVELOPMENT SERVER
echo ============================================
echo Current directory: %CD%
echo Node version:
node --version
echo.

if not exist "%~dp0casestrainer-vue-new\package.json" (
    echo [ERROR] Could not find Vue.js frontend directory!
    echo Expected path: %~dp0casestrainer-vue-new\package.json
    dir "%~dp0"
    pause
    goto :show_menu
)

echo Starting frontend development server...
echo Frontend command: npm run %FRONTEND_CMD%
echo Frontend port: %FRONTEND_PORT%
echo.

:: Set environment variables for the frontend
set VITE_API_BASE_URL=http://localhost:%BACKEND_PORT%
set NODE_ENV=%NODE_ENV%

start "CaseStrainer Frontend" /D "%~dp0casestrainer-vue-new" cmd /k "@echo [%DATE% %TIME%] Starting CaseStrainer Frontend && echo Frontend URL: http://localhost:%FRONTEND_PORT% && echo API URL: %VITE_API_BASE_URL% && npm run %FRONTEND_CMD%"

echo.
echo ============================================
echo  FRONTEND STARTED SUCCESSFULLY
echo ============================================
echo  Frontend URL: http://localhost:%FRONTEND_PORT%
echo  API URL: %VITE_API_BASE_URL%
echo  Environment: %NODE_ENV%
echo  Press Ctrl+C in the frontend window to stop the server
echo ============================================
echo.

timeout /t 2 >nul
endlocal
goto :show_menu

:start_both
echo.
echo ============================================
echo  STARTING BOTH BACKEND AND FRONTEND
echo ============================================

:: First stop any running services
echo.
echo [1/3] Stopping any existing processes...
echo.

:: Check if the port is already in use
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!BACKEND_PORT! " ^| findstr "LISTENING"') do (
    set PID=%%a
    if defined PID (
        echo [WARNING] Port !BACKEND_PORT! is in use by process ID !PID!
        tasklist /FI "PID eq !PID!" | findstr /i "python" >nul
        if !ERRORLEVEL! EQU 0 (
            echo [INFO] Killing existing Python process using port !BACKEND_PORT!
            taskkill /F /PID !PID! >nul 2>&1
        ) else (
            echo [ERROR] Port !BACKEND_PORT! is in use by a non-Python process. Please free the port and try again.
            pause
            exit /b 1
        )
    )
)

:: Kill any Node.js processes (Vite dev server)
echo [INFO] Stopping any running Node.js processes...
taskkill /F /IM node.exe /T >nul 2>&1

:: Kill any Python processes (Flask backend)
echo [INFO] Stopping any running Python processes...
taskkill /F /IM python.exe /T >nul 2>&1

:: Kill any CMD windows with our titles
echo [INFO] Cleaning up any existing application windows...
taskkill /F /FI "WINDOWTITLE eq %BACKEND_TITLE%*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq %FRONTEND_TITLE%*" /T >nul 2>&1

:: Wait for processes to terminate
timeout /t 2 /nobreak >nul

:: Start Backend
echo.
echo [2/3] Starting Backend...

:: Check if backend is already running on this port
set PORT_IN_USE=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!BACKEND_PORT! " ^| findstr "LISTENING"') do (
    set PORT_IN_USE=1
    set PID=%%a
    for /f "tokens=1,2" %%b in ('tasklist /FI "PID eq !PID!" /NH') do (
        echo [WARNING] Port !BACKEND_PORT! is in use by !b! (PID: !PID!)
        if /i "!b!"=="python.exe" (
            echo [INFO] Killing existing Python process using port !BACKEND_PORT!
            taskkill /F /PID !PID! >nul 2>&1
            if !ERRORLEVEL! EQU 0 (
                echo [INFO] Successfully terminated process
                set PORT_IN_USE=0
                timeout /t 2 /nobreak >nul
            )
        )
    )
)

if !PORT_IN_USE! EQU 1 (
    echo [ERROR] Could not free port !BACKEND_PORT!. Please close the application using this port and try again.
    pause
    exit /b 1
)

if not exist "%~dp0src\app_final_vue.py" (
    echo [ERROR] Could not find app_final_vue.py in src directory!
    echo Expected path: %~dp0src\app_final_vue.py
    pause
    exit /b 1
)

:: Create logs directory if it doesn't exist
if not exist "%~dp0logs" mkdir "%~dp0logs"

:: Set the log file path for the backend
set BACKEND_LOG=%~dp0logs\backend_%date:/=%.log

echo [INFO] Starting backend at http://localhost:!BACKEND_PORT!
echo [INFO] Backend logs will be written to: !BACKEND_LOG!

:: Start the backend in a new window with logging
echo [INFO] Starting backend process in a new window...
start "%BACKEND_TITLE%" /D "%~dp0src" cmd /k "@echo [%DATE% %TIME%] Starting CaseStrainer Backend && echo Backend URL: http://localhost:!BACKEND_PORT! && echo Logs: !BACKEND_LOG! && python -u app_final_vue.py --port=!BACKEND_PORT! --host=0.0.0.0 --use-waitress"

echo [INFO] Backend started in a new window. Waiting a moment for it to initialize...
timeout /t 3 /nobreak >nul

:: Check if the port is now in use
netstat -ano | findstr ":!BACKEND_PORT! " | findstr "LISTENING" >nul
if ERRORLEVEL 1 (
    echo [WARNING] Backend might be slow to start. The backend window will remain open for debugging.
    echo [INFO] You can check the backend window for any error messages.
) else (
    echo [SUCCESS] Backend is running on port !BACKEND_PORT!
)

echo [INFO] Proceeding to start frontend...

goto start_frontend

:start_frontend
echo.
echo [3/3] Starting Frontend...
if not exist "%~dp0casestrainer-vue-new\package.json" (
    echo [WARNING] Could not find Vue.js frontend directory!
    echo Expected path: %~dp0casestrainer-vue-new\package.json
    echo Skipping frontend startup...
    pause
    exit /b 0
)

cd /d "%~dp0casestrainer-vue-new"

:: Set environment variables for the frontend
set VITE_API_BASE_URL=http://localhost:!BACKEND_PORT!/casestrainer/api
echo [INFO] API Base URL set to: !VITE_API_BASE_URL!

echo [INFO] Frontend starting at http://localhost:!FRONTEND_PORT!

:: Set the log file path for the frontend
set FRONTEND_LOG=%~dp0logs\frontend_%date:/=%.log

echo [INFO] Frontend logs will be written to: !FRONTEND_LOG!

:: Start frontend in a new window
echo [INFO] Starting frontend in a new window...
start "%FRONTEND_TITLE%" /D "%~dp0casestrainer-vue-new" cmd /k "@echo [%DATE% %TIME%] Starting Frontend && echo Frontend URL: http://localhost:!FRONTEND_PORT! && set PORT=!FRONTEND_PORT! && set NODE_ENV=!NODE_ENV! && set VITE_API_BASE_URL=!VITE_API_BASE_URL! && echo Using API: !VITE_API_BASE_URL! && npm run !FRONTEND_CMD! -- --port=!FRONTEND_PORT! --host"

echo.
echo ============================================
echo  CaseStrainer is now running!
echo  - Backend:   http://localhost:!BACKEND_PORT!
echo  - Frontend:  http://localhost:!FRONTEND_PORT!
echo  - API Base:  http://localhost:!BACKEND_PORT!/casestrainer/api
echo ============================================
echo.
echo  Note: Frontend may take a moment to start.
echo  Check the frontend window for completion.
echo.
echo  To stop the application:
echo  - Backend:  taskkill /F /FI "WINDOWTITLE eq %BACKEND_TITLE%*" /T
echo  - Frontend: taskkill /F /FI "WINDOWTITLE eq %FRONTEND_TITLE%*" /T
echo ============================================
echo.
echo Press any key to return to the main menu...
pause >nul
goto show_menu

:run_all_tests
echo.
echo ===== Running All Tests =====
call :run_api_tests
if !ERRORLEVEL! NEQ 0 (
    echo API Tests failed. Aborting frontend tests.
    goto :eof
)
call :run_frontend_tests
goto :eof

:run_api_tests
echo.
echo ===== Running API Tests =====
python test_api_direct.py
set "test_result=!ERRORLEVEL!"
if !test_result! NEQ 0 (
    echo.
    echo ===== API Tests Failed =====
    pause
) else (
    echo.
    echo ===== API Tests Passed =====
)
goto :eof

:run_frontend_tests
echo.
echo ===== Running Frontend Tests =====
cd casestrainer-vue
call npm test
set "test_result=!ERRORLEVEL!"
cd ..
if !test_result! NEQ 0 (
    echo.
    echo ===== Frontend Tests Failed =====
    pause
) else (
    echo.
    echo ===== Frontend Tests Passed =====
)
goto :eof

:stop_all
echo.
echo Stopping backend services...
taskkill /F /FI "WINDOWTITLE eq %BACKEND_TITLE%*" /T >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Successfully stopped backend services.
) else (
    echo No backend services were running or could not be stopped.
)

echo Stopping frontend services...
taskkill /F /FI "WINDOWTITLE eq %FRONTEND_TITLE%*" /T >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Successfully stopped frontend services.
) else (
    echo No frontend services were running or could not be stopped.
)

timeout /t 1 >nul
goto :eof

:check_status
echo.
echo ============================================
echo  SERVICE STATUS
echo ============================================

echo [Backend]
tasklist /FI "WINDOWTITLE eq %BACKEND_TITLE%*" | findstr /i "cmd.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo Status: RUNNING
    echo URL: http://localhost:%BACKEND_PORT%
) else (
    echo Status: STOPPED
)

echo.
echo [Frontend]
set FRONTEND_RUNNING=0
set FRONTEND_ACTUAL_PORT=0
set FRONTEND_STATUS=STOPPED

:: Check if frontend is running on port 5173 or 5174
set FRONTEND_RUNNING=0
netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo Status: RUNNING [Port 5173]
    echo URL: http://localhost:5173
    set FRONTEND_RUNNING=1
    set FRONTEND_ACTUAL_PORT=5173
) else (
    netstat -ano | findstr ":5174 " | findstr "LISTENING" >nul
    if not errorlevel 1 (
        echo Status: RUNNING [Port 5174]
        echo URL: http://localhost:5174
        set FRONTEND_RUNNING=1
        set FRONTEND_ACTUAL_PORT=5174
    ) else (
        tasklist /FI "WINDOWTITLE eq %FRONTEND_TITLE%*" | findstr /i "node.exe" >nul
        if not errorlevel 1 (
            echo Status: RUNNING [Starting...]
            echo URL: http://localhost:5174
            set FRONTEND_RUNNING=1
            set FRONTEND_ACTUAL_PORT=5174
        ) else (
            echo Status: STOPPED
        )
    )
)

echo.
echo [Ports in Use]
echo Backend (Port %BACKEND_PORT%):
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING"
echo.
echo Frontend (Port %FRONTEND_PORT%):
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING"

if "!FRONTEND_RUNNING!"=="0" (
    echo.
    echo [Troubleshooting]
    echo If the frontend should be running but isn't detected:
    echo 1. Check if port %FRONTEND_PORT% is in use: netstat -ano | findstr ":%FRONTEND_PORT%"
    echo 2. Try stopping all services (option 5) and start again
) else (
    echo.
    echo Frontend is running on port !FRONTEND_ACTUAL_PORT!
)

echo.
pause
goto :show_menu

:switch_env
if "!ENV!"=="dev" (
    start "" "%~dp0%~nx0" --prod
) else (
    start "" "%~dp0%~nx0" --dev
)
exit /b 0

:install_deps
echo.
echo ============================================
echo  INSTALLING DEPENDENCIES
echo ============================================
echo [1/2] Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Python dependencies
    pause
    goto :show_menu
)

echo.
echo [2/2] Installing Node.js dependencies...
cd /d "%~dp0casestrainer-vue-new"
npm install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Node.js dependencies
    cd /d "%~dp0"
    pause
    goto :show_menu
)
cd /d "%~dp0"
echo.
echo All dependencies installed successfully!
pause
goto :show_menu

:end
echo Exiting...
exit /b 0
