@echo off
setlocal enabledelayedexpansion

:: ===========================================
:: CaseStrainer Application Launcher (Improved)
:: ===========================================
:: Version: 2.0.1
:: Last Updated: 2025-06-03
:: ===========================================

:: Initialize configuration with command line arguments
call :init_config %*
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to initialize configuration
    pause
    exit /b 1
)

:: Stop all services function
:stop_services
    echo [INFO] Stopping all services...
    call :stop_backend
    call :stop_frontend
    call :stop_nginx
    echo [INFO] All services stopped

:: Main menu
:show_menu
    cls
    echo ============================================
    echo  CaseStrainer Application Manager (v2.0.1)
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
    echo 9. Manage Nginx
    echo 10. Production Restart Workflow
    echo 11. Exit
    echo ============================================
    set /p "choice=Enter your choice (1-11): "

    :: Process menu choice
    if "!choice!"=="1" (
        echo [INFO] Stopping any running backend...
        call :stop_backend
        call :start_backend
        if !ERRORLEVEL! EQU 0 (
            echo [SUCCESS] Backend started successfully
        ) else (
            echo [ERROR] Failed to start backend
        )
        pause
        goto :show_menu
    ) else if "!choice!"=="2" (
        echo [INFO] Stopping any running frontend...
        call :stop_frontend
        call :start_frontend
        if !ERRORLEVEL! EQU 0 (
            echo [SUCCESS] Frontend started successfully
        ) else (
            echo [ERROR] Failed to start frontend
        )
        pause
        goto :show_menu
    ) else if "!choice!"=="3" (
        echo [INFO] Stopping any running services...
        call :stop_services
        call :start_backend
        if !ERRORLEVEL! EQU 0 (
            call :start_frontend
            if !ERRORLEVEL! EQU 0 (
                echo [SUCCESS] Both services started successfully
            ) else (
                echo [WARNING] Backend started but frontend failed
            )
        ) else (
            echo [ERROR] Backend failed to start
        )
        pause
        goto :show_menu
    ) else if "!choice!"=="4" (
        call :run_tests
        pause
        goto :show_menu
    ) else if "!choice!"=="5" (
        call :stop_services
        pause
        goto :show_menu
    ) else if "!choice!"=="6" (
        call :check_status
        pause
        goto :show_menu
    ) else if "!choice!"=="7" (
        if "!ENV!"=="dev" (
            set "NEW_ENV=prod"
        ) else (
            set "NEW_ENV=dev"
        )
        echo [INFO] Switching to !NEW_ENV! environment...
        call :stop_services
        
        :: Use init_config to set environment properly
        if "!NEW_ENV!"=="prod" (
            call :init_config --prod
        ) else (
            call :init_config --dev
        )
        
        echo [SUCCESS] Switched to !ENV! environment (Backend: !BACKEND_PORT!, Frontend: !FRONTEND_PORT!)
        pause
        goto :show_menu
    ) else if "!choice!"=="8" (
        call :install_dependencies
        pause
        goto :show_menu
    ) else if "!choice!"=="9" (
        call :manage_nginx
        pause
        goto :show_menu
    ) else if "!choice!"=="10" (
        echo [INFO] Starting Production Restart Workflow...
        echo [1/4] Stopping all services...
        call :stop_services
        
        echo [2/4] Switching to production environment...
        if "!ENV!"=="prod" (
            echo [INFO] Already in production environment
        ) else (
            echo [INFO] Switching from !ENV! to production environment...
            :: Set production environment variables directly
            set "ENV=prod"
            set "BACKEND_PORT=5001"
            set "FRONTEND_PORT=4173"
            set "BACKEND_CONFIG=config_prod.py"
            set "NODE_ENV=production"
            set "FLASK_ENV=production"
            set "FLASK_DEBUG=0"
            echo [SUCCESS] Switched to production environment (Backend: !BACKEND_PORT!, Frontend: !FRONTEND_PORT!)
        )
        
        echo [3/4] Starting backend and frontend...
        call :start_backend
        if !ERRORLEVEL! EQU 0 (
            echo [INFO] Backend started successfully, starting frontend...
            call :start_frontend
            if !ERRORLEVEL! EQU 0 (
                echo [SUCCESS] Both services started successfully
            ) else (
                echo [WARNING] Backend started but frontend failed
                echo [INFO] Check the frontend window for errors
            )
        ) else (
            echo [ERROR] Backend failed to start
            echo [INFO] Check the backend window for errors
        )
        
        echo [4/4] Verifying services...
        call :check_status
        echo.
        echo ============================================
        echo [PRODUCTION RESTART COMPLETE]
        echo ============================================
        echo - Backend: http://localhost:!BACKEND_PORT!
        echo - Frontend: http://localhost:!FRONTEND_PORT!
        if "!ENV!"=="prod" (
            echo - Production URL: https://wolf.law.uw.edu/casestrainer/
            echo - Nginx status will be checked automatically
        )
        echo.
        echo Press any key to return to main menu...
        pause >nul
        goto :show_menu
    ) else if "!choice!"=="11" (
        echo [INFO] Exiting...
        exit /b 0
    ) else (
        echo [ERROR] Invalid choice: !choice!
        timeout /t 1 >nul
        goto :show_menu
    )

:init_config
    :: Set default configuration
    set "SCRIPT_DIR=%~dp0"
    set "LOG_DIR=!SCRIPT_DIR!logs"
    set "BACKEND_DIR=!SCRIPT_DIR!src"
    set "FRONTEND_DIR=!SCRIPT_DIR!casestrainer-vue-new"
    
    :: Create logs directory if it doesn't exist
    if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
    
    :: Process command line arguments
    :parse_args
    if "%1"=="" goto :args_done
    if "%1"=="--prod" (
        set "ENV=prod"
        set "BACKEND_PORT=5001"
        set "FRONTEND_PORT=4173"
        set "BACKEND_CONFIG=config_prod.py"
        set "NODE_ENV=production"
        set "FLASK_ENV=production"
        set "FLASK_DEBUG=0"
        shift
        goto :parse_args
    ) else if "%1"=="--dev" (
        set "ENV=dev"
        set "BACKEND_PORT=5000"
        set "FRONTEND_PORT=5173"
        set "BACKEND_CONFIG=config_dev.py"
        set "NODE_ENV=development"
        set "FLASK_ENV=development"
        set "FLASK_DEBUG=1"
        shift
        goto :parse_args
    ) else (
        echo [WARNING] Unknown argument: %1
        shift
        goto :parse_args
    )
    
    :args_done
    :: Set default if no environment was specified
    if not defined ENV (
        set "ENV=dev"
        set "BACKEND_PORT=5000"
        set "FRONTEND_PORT=5173"
        set "BACKEND_CONFIG=config_dev.py"
        set "NODE_ENV=development"
        set "FLASK_ENV=development"
        set "FLASK_DEBUG=1"
    )
    
    :: Set process titles for management (fixed, not random)
    set "BACKEND_TITLE=CaseStrainer_Backend"
    set "FRONTEND_TITLE=CaseStrainer_Frontend"
    
    :: Set log files with timestamp
    for /f "tokens=2 delims==." %%a in ('wmic os get localdatetime /value') do set "TIMESTAMP=%%a"
    set "LOG_FILE=!LOG_DIR!\casestrainer_!TIMESTAMP:~0,8!_!TIMESTAMP:~8,6!.log"
    
    :: Verify required directories exist
    if not exist "!BACKEND_DIR!" (
        echo [ERROR] Backend directory not found: !BACKEND_DIR!
        exit /b 1
    )
    if not exist "!FRONTEND_DIR!" (
        echo [WARNING] Frontend directory not found: !FRONTEND_DIR!
    )
    exit /b 0

:start_backend
    echo [INFO] Starting backend service...
    
    :: Verify backend directory exists
    if not exist "!BACKEND_DIR!" (
        echo [ERROR] Backend directory not found: !BACKEND_DIR!
        exit /b 1
    )
    
    :: Verify app_final_vue.py exists
    if not exist "!BACKEND_DIR!\app_final_vue.py" (
        echo [ERROR] Backend file not found: !BACKEND_DIR!\app_final_vue.py
        dir /b "!BACKEND_DIR!"
        exit /b 1
    )
    
    :: Verify Python is available
    python --version >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Python is not in PATH or not installed
        exit /b 1
    )
    
    echo [INFO] Starting backend with:
    echo [INFO]   Directory: !BACKEND_DIR!
    echo [INFO]   Port: !BACKEND_PORT!
    echo [INFO]   Environment: !FLASK_ENV!
    
    :: Start backend in a new window with better error handling
    echo [INFO] Starting backend process...
    
    :: Create a temporary batch file to run the backend
    echo @echo off > "%TEMP%\start_backend.bat"
    echo echo [BACKEND] Starting CaseStrainer Backend... >> "%TEMP%\start_backend.bat"
    echo echo [BACKEND] Directory: !BACKEND_DIR! >> "%TEMP%\start_backend.bat"
    echo echo [BACKEND] Port: !BACKEND_PORT! >> "%TEMP%\start_backend.bat"
    echo echo [BACKEND] Environment: !FLASK_ENV! >> "%TEMP%\start_backend.bat"
    echo cd /d "!BACKEND_DIR!" ^&^& python app_final_vue.py --port=!BACKEND_PORT! --host=0.0.0.0 --use-waitress >> "%TEMP%\start_backend.bat"
    echo echo [BACKEND] Process exited with error level ^^!ERRORLEVEL^^! >> "%TEMP%\start_backend.bat"
    echo pause >> "%TEMP%\start_backend.bat"
    
    start "!BACKEND_TITLE!" cmd /c ""%TEMP%\start_backend.bat""
    
    :: Wait for backend to start with a timeout
    echo [INFO] Waiting for backend to start (timeout: 15 seconds)...
    set /a "TIMEOUT=15"
    set "STARTED=0"
    
    :wait_backend_loop
    timeout /t 1 >nul
    set /a "TIMEOUT-=1"
    
    :: Check if port is listening
    netstat -ano 2>nul | findstr ":!BACKEND_PORT! " | findstr "LISTENING" >nul
    if !ERRORLEVEL! EQU 0 (
        set "STARTED=1"
        goto backend_started
    )
    
    if !TIMEOUT! GTR 0 (
        set /p "=." <nul
        goto :wait_backend_loop
    )
    
    :backend_started
    if "!STARTED!"=="1" (
        echo.
        echo [SUCCESS] Backend is running at http://localhost:!BACKEND_PORT!
        exit /b 0
    ) else (
        echo.
        echo [ERROR] Backend failed to start within the timeout period
        echo [INFO] Check the backend window for error messages
        exit /b 1
    )

:start_frontend
    echo [INFO] Starting frontend service...
    
    :: Stop any existing frontend first
    call :stop_frontend
    
    :: Try to find an available port starting from FRONTEND_PORT
    set "ORIGINAL_PORT=!FRONTEND_PORT!"
    set "PORT_FOUND=0"
    
    :find_port_loop
    call :check_port_available !FRONTEND_PORT!
    if !ERRORLEVEL! EQU 0 (
        set "PORT_FOUND=1"
        goto :start_frontend_process
    )
    
    echo [INFO] Port !FRONTEND_PORT! is in use, trying next port...
    set /a "FRONTEND_PORT+=1"
    
    :: Prevent infinite loop, max 10 port checks
    if !FRONTEND_PORT! LSS !ORIGINAL_PORT! + 10 (
        goto :find_port_loop
    )
    
    echo [ERROR] Could not find an available port between !ORIGINAL_PORT! and !FRONTEND_PORT!
    exit /b 1
    
    :start_frontend_process
    if exist "!FRONTEND_DIR!\package.json" (
        echo [INFO] Starting frontend on port !FRONTEND_PORT!
        cd /d "!FRONTEND_DIR!"
        start "!FRONTEND_TITLE!" /D"!FRONTEND_DIR!" cmd /c "set PORT=!FRONTEND_PORT! && set NODE_ENV=!NODE_ENV! && npm run dev && pause"
        cd /d "!SCRIPT_DIR!"
        
        echo [INFO] Waiting for frontend to start...
        set /a "TIMEOUT=15"
        :wait_frontend_loop
        timeout /t 1 >nul
        set /a "TIMEOUT-=1"
        
        :: Check if port is listening
        netstat -ano | findstr ":!FRONTEND_PORT! " | findstr "LISTENING" >nul
        if !ERRORLEVEL! EQU 0 (
            echo [SUCCESS] Frontend is running at http://localhost:!FRONTEND_PORT!
            echo [INFO] Note: The actual port might be different if the default was in use
            
            :: Start Nginx in production mode
            if "!ENV!"=="prod" (
                call :start_nginx
            )
            exit /b 0
        )
        
        if !TIMEOUT! GTR 0 (
            goto :wait_frontend_loop
        )
        
        echo [WARNING] Frontend is taking longer than expected to start
        echo [INFO] Check the frontend window for any errors
        exit /b 0
    ) else (
        echo [ERROR] Frontend directory not found: !FRONTEND_DIR!
        exit /b 1
    )

:check_port_available
    netstat -ano | findstr ":%1 " | findstr "LISTENING" >nul
    if !ERRORLEVEL! EQU 0 exit /b 1
    exit /b 0

:stop_backend
        echo [INFO] Stopping backend service...
        taskkill /FI "WINDOWTITLE eq !BACKEND_TITLE!*" /T /F >nul 2>&1
        exit /b 0

:stop_frontend
        echo [INFO] Stopping frontend service...
        taskkill /FI "WINDOWTITLE eq !FRONTEND_TITLE!*" /T /F >nul 2>&1
        :: Kill any remaining Node.js processes
        taskkill /F /IM node.exe >nul 2>&1
        exit /b 0


:check_status
echo.
echo ============================================
echo  SERVICE STATUS
echo ============================================

echo [Backend]
:: Check if the port is in use
netstat -ano 2>nul | findstr ":!BACKEND_PORT! " | findstr "LISTENING" >nul
set "PORT_LISTENING=!ERRORLEVEL!"

:: Find the process using the port
set "PROCESS_INFO="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":!BACKEND_PORT! " ^| findstr "LISTENING"') do (
    for /f "tokens=1,2" %%b in ('tasklist /FI "PID eq %%~a" /FO LIST ^| findstr /i "Image Name:"') do (
        set "PROCESS_INFO=%%c (PID: %%~a)"
    )
)

if !PORT_LISTENING! EQU 0 (
    if defined PROCESS_INFO (
        echo Status: RUNNING
        echo URL: http://localhost:!BACKEND_PORT!
        echo Process: !PROCESS_INFO!
    ) else (
        echo Status: PORT IN USE (but process not found)
        echo Port !BACKEND_PORT! is in use by an unknown process
    )
) else (
    echo Status: STOPPED
    echo [INFO] Port !BACKEND_PORT! is not in use
    echo [INFO] Use option 1 to start the backend
)

echo.
echo [Port Check]
netstat -ano 2>nul | findstr ":!BACKEND_PORT! " | findstr "LISTENING" 2>nul

echo.
echo [Frontend]
:: Check for any running Vue development server (ports 5173-5183)
set "FRONTEND_RUNNING=0"
set "FRONTEND_ACTUAL_PORT=0"

for /L %%P in (5173,1,5183) do (
    netstat -ano 2>nul | findstr ":%%P " | findstr "LISTENING" >nul
    if !ERRORLEVEL! EQU 0 (
        set "FRONTEND_RUNNING=1"
        set "FRONTEND_ACTUAL_PORT=%%P"
        goto :frontend_check_done
    )
)

:frontend_check_done
if !FRONTEND_RUNNING! EQU 1 (
    echo Status: RUNNING [Port !FRONTEND_ACTUAL_PORT!]
    echo URL: http://localhost:!FRONTEND_ACTUAL_PORT!
    :: Update FRONTEND_PORT to the actual port being used
    set "FRONTEND_PORT=!FRONTEND_ACTUAL_PORT!"
) else (
    echo Status: STOPPED
    echo [INFO] Checked ports 5173-5183 for Vue dev server
)

echo.
echo [Ports in Use]
echo Backend (Port !BACKEND_PORT!):
netstat -ano 2>nul | findstr ":!BACKEND_PORT! " | findstr "LISTENING"
echo.
echo Frontend (Port !FRONTEND_PORT!):
netstat -ano 2>nul | findstr ":!FRONTEND_PORT! " | findstr "LISTENING"

echo.
exit /b 0

:install_dependencies
    echo [INFO] Installing dependencies...
    
    :: Install Python dependencies
    if exist "!BACKEND_DIR!\requirements.txt" (
        echo [1/2] Installing Python dependencies...
        pip install -r "!BACKEND_DIR!\requirements.txt"
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Failed to install Python dependencies
            exit /b 1
        )
    )
    
    :: Install Node.js dependencies
    if exist "!FRONTEND_DIR!\package.json" (
        echo [2/2] Installing Node.js dependencies...
        cd /d "!FRONTEND_DIR!"
        npm install
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Failed to install Node.js dependencies
            cd /d "!SCRIPT_DIR!"
            exit /b 1
        )
        cd /d "!SCRIPT_DIR!"
    )
    
    echo [SUCCESS] All dependencies installed successfully
    exit /b 0

:run_tests
    echo [INFO] Running tests...
    
    :: Check if backend is running, start if needed
    netstat -ano 2>nul | findstr ":!BACKEND_PORT! " | findstr "LISTENING" >nul
    if !ERRORLEVEL! NEQ 0 (
        echo [INFO] Backend not running, starting it first...
        call :start_backend
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Failed to start backend for testing
            exit /b 1
        )
        :: Wait for backend to be ready
        timeout /t 3 >nul
    else
        echo [INFO] Backend already running on port !BACKEND_PORT!
    )
    
    :: Check if frontend is needed for tests
    set "FRONTEND_NEEDED=0"
    if exist "!FRONTEND_DIR!\cypress.config.js" set "FRONTEND_NEEDED=1"
    if exist "!FRONTEND_DIR!\cypress.json" set "FRONTEND_NEEDED=1"
    
    if !FRONTEND_NEEDED! EQU 1 (
        :: Check if frontend is running, start if needed  
        set "FRONTEND_RUNNING=0"
        for /L %%P in (5173,1,5183) do (
            netstat -ano 2>nul | findstr ":%%P " | findstr "LISTENING" >nul
            if !ERRORLEVEL! EQU 0 set "FRONTEND_RUNNING=1"
        )
        
        if !FRONTEND_RUNNING! EQU 0 (
            echo [INFO] Frontend not running, starting it first...
            call :start_frontend
            if !ERRORLEVEL! NEQ 0 (
                echo [ERROR] Failed to start frontend for testing
                exit /b 1
            )
            :: Wait for frontend to be ready
            timeout /t 5 >nul
        ) else (
            echo [INFO] Frontend already running
        )
    )
    
    :: Run backend tests
    if exist "!BACKEND_DIR!\test_api.py" (
        echo [1/2] Running backend tests...
        cd /d "!BACKEND_DIR!"
        python test_api.py
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Backend tests failed
            cd /d "!SCRIPT_DIR!"
            exit /b 1
        )
        cd /d "!SCRIPT_DIR!"
    )
    
    :: Run frontend tests if needed
    if !FRONTEND_NEEDED! EQU 1 (
        echo [2/2] Running frontend tests...
        cd /d "!FRONTEND_DIR!"
        if exist "package.json" (
            if exist "node_modules\.bin\cypress" (
                npx cypress run --headless
            ) else (
                npm test
            )
            if !ERRORLEVEL! NEQ 0 (
                echo [ERROR] Frontend tests failed
                cd /d "!SCRIPT_DIR!"
                exit /b 1
            )
        )
        cd /d "!SCRIPT_DIR!"
    )
    
    echo [SUCCESS] All tests completed successfully
    exit /b 0

:: ===========================================
:: Nginx Management
:: ===========================================
:start_nginx
    echo [INFO] Starting Nginx...
    
    :: Check if Nginx is already running
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if !ERRORLEVEL! EQU 0 (
        echo [INFO] Nginx is already running
        exit /b 0
    )
    
    :: Set Nginx directory
    set "NGINX_DIR=%~dp0nginx-1.27.5"
    set "NGINX_CONFIG=!NGINX_DIR!\conf\casestrainer.conf"
    
    if not exist "!NGINX_DIR!\nginx.exe" (
        echo [ERROR] Nginx not found at: !NGINX_DIR!
        exit /b 1
    )
    
    cd /d "!NGINX_DIR!"
    start "Nginx" nginx.exe -c "!NGINX_CONFIG!"
    
    :: Wait for Nginx to start
    timeout /t 2 >nul
    
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if !ERRORLEVEL! EQU 0 (
        echo [SUCCESS] Nginx started successfully
        exit /b 0
    else
        echo [ERROR] Failed to start Nginx
        exit /b 1
    )

:stop_nginx
    echo [INFO] Stopping Nginx...
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if !ERRORLEVEL! EQU 0 (
        taskkill /F /IM nginx.exe >nul 2>&1
        echo [SUCCESS] Nginx stopped
    else
        echo [INFO] Nginx is not running
    )
    exit /b 0

:check_nginx_status
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if !ERRORLEVEL! EQU 0 (
        echo [INFO] Nginx status: RUNNING
        exit /b 0
    else
        echo [INFO] Nginx status: STOPPED
        exit /b 1
    )

:manage_nginx
    :nginx_menu
    cls
    echo ============================================
    echo  Nginx Management
    echo ============================================
    call :check_nginx_status
    echo.
    echo 1. Start Nginx
    echo 2. Stop Nginx
    echo 3. Restart Nginx
    echo 4. View Nginx Logs
    echo 5. Back to Main Menu
    echo ============================================
    set /p "nginx_choice=Enter your choice (1-5): "
    
    if "!nginx_choice!"=="1" (
        call :start_nginx
    ) else if "!nginx_choice!"=="2" (
        call :stop_nginx
    ) else if "!nginx_choice!"=="3" (
        call :stop_nginx
        timeout /t 1 >nul
        call :start_nginx
    ) else if "!nginx_choice!"=="4" (
        if exist "%~dp0nginx-1.27.5\logs\error.log" (
            notepad "%~dp0nginx-1.27.5\logs\error.log"
        ) else (
            echo [ERROR] Nginx log file not found
        )
    ) else if "!nginx_choice!"=="5" (
        exit /b 0
    ) else (
        echo [ERROR] Invalid choice
        pause
    )
    
    pause
    goto :nginx_menu
