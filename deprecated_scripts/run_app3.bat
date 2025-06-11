@echo off
setlocal EnableDelayedExpansion

:: Ensure we're running in our own window
if "%1"=="" (
    start "CaseStrainer" /D"%~dp0" cmd /k "%~f0" _
    exit /b
)

:: ===========================================
:: CaseStrainer Application Launcher (Enhanced)
:: ===========================================
:: Version: 2.1.0
:: Last Updated: 2025-06-03
:: ===========================================

echo [DEBUG] Starting CaseStrainer launcher...

:: Initialize configuration with command line arguments
call :init_config %*
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to initialize configuration
    pause
    exit /b 1
)

:: Ensure we have the required configuration
if not defined ENV set "ENV=dev"
if not defined BACKEND_PORT set "BACKEND_PORT=5001"
if not defined FRONTEND_PORT set "FRONTEND_PORT=3000"

echo [DEBUG] Initialization complete, LOG_FILE: %LOG_FILE%

:: Main entry point - handle auto-start or show menu
if defined AUTO_START (
    if "%ENV%"=="prod" (
        echo [INFO] Starting automatic production setup...
        call :production_auto_start
        if %ERRORLEVEL% equ 0 (
            echo [SUCCESS] Production auto-start completed successfully
            echo [INFO] Press any key to open management menu or Ctrl+C to exit...
            pause >nul
        ) else (
            echo [ERROR] Production auto-start failed
            echo [INFO] Opening management menu for troubleshooting...
            pause
        )
    ) else (
        echo [WARNING] Auto-start requires production mode. Use --prod --auto-start
        echo [INFO] Switching to production mode and starting...
        set "ENV=prod"
        call :setup_runtime_config
        call :production_auto_start
    )
)

goto :show_menu

:: ===========================================
:: MAIN MENU
:: ===========================================
:show_menu
    cls
    echo ============================================
    echo  CASESTRAINER APPLICATION LAUNCHER v2.1.0
    echo ============================================
    echo Environment: %ENV%
    echo Backend: http://localhost:%BACKEND_PORT%
    echo Frontend: http://localhost:%FRONTEND_PORT%
    echo Local Access: http://localhost/casestrainer/
    echo ============================================
    echo  1. Start All Services
    echo  2. Stop All Services
    echo  3. Restart All Services
    echo  4. Start Backend Only
    echo  5. Start Frontend Only
    echo  6. Manage Nginx
    echo  7. Manage Configuration
    echo  8. Debug Frontend Setup
    echo  9. Toggle Production Mode (Current: %ENV%)
    echo 10. Check Service Status
    echo 11. Production Auto-Start (Complete Setup)
    echo 12. Exit
    echo ============================================
    
    set /p "menu_choice=Enter your choice (1-12): "
    
    call :validate_numeric_input "%menu_choice%" 1 12
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Invalid choice. Please enter a number between 1 and 12.
        timeout /t 2 >nul
        goto :show_menu
    )
    
    if "%menu_choice%"=="1" (
        call :start_services
    ) else if "%menu_choice%"=="2" (
        call :stop_services
    ) else if "%menu_choice%"=="3" (
        call :stop_services
        call :start_services
    ) else if "%menu_choice%"=="4" (
        call :start_backend
    ) else if "%menu_choice%"=="5" (
        call :start_frontend
    ) else if "%menu_choice%"=="6" (
        call :manage_nginx
    ) else if "%menu_choice%"=="7" (
        call :manage_configuration
    ) else if "%menu_choice%"=="8" (
        call :debug_frontend_setup
        echo.
        echo Press any key to return to the main menu...
        pause >nul
        goto :show_menu
    ) else if "%menu_choice%"=="9" (
        if "%ENV%"=="prod" (
            set "ENV=dev"
            call :setup_runtime_config
            echo [INFO] Switched to DEVELOPMENT mode
        ) else (
            set "ENV=prod"
            call :setup_runtime_config
            echo [INFO] Switched to PRODUCTION mode
        )
        timeout /t 2 >nul
    ) else if "%menu_choice%"=="10" (
        call :check_service_status
        echo.
        echo Press any key to return to the main menu...
        pause >nul
        goto :show_menu
    ) else if "%menu_choice%"=="11" (
        cls
        call :production_restart_workflow
        echo.
        echo Press any key to return to the main menu...
        pause >nul
        goto :show_menu
    ) else if "%menu_choice%"=="12" (
        echo [INFO] Exiting...
        exit /b 0
    )
    
    goto :show_menu

:: ===========================================
:: CONFIGURATION INITIALIZATION
:: ===========================================
:init_config
    echo [DEBUG] Starting init_config...
    
    :: Set default configuration with regular expansion
    set "SCRIPT_DIR=%~dp0"
    set "CONFIG_FILE=%SCRIPT_DIR%config.ini"
    set "LOG_DIR=%SCRIPT_DIR%logs"
    set "BACKEND_DIR=%SCRIPT_DIR%src"
    set "FRONTEND_DIR=%SCRIPT_DIR%casestrainer-vue-new"
    set "TEMP_DIR=%TEMP%\casestrainer"
    
    echo [DEBUG] SCRIPT_DIR: %SCRIPT_DIR%
    echo [DEBUG] LOG_DIR: %LOG_DIR%
    
    :: Create required directories first
    if not exist "%LOG_DIR%" (
        echo [DEBUG] Creating LOG_DIR: %LOG_DIR%
        mkdir "%LOG_DIR%" 2>nul
    )
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%" 2>nul
    
    :: Set up basic timestamp for log file (improved format)
    call :parse_arguments %*
    
    :: Set default environment if not specified
    if not defined ENV set "ENV=dev"
    
    :: Load configuration based on environment
    call :load_config
    if %ERRORLEVEL% neq 0 exit /b 1
    
    :: Set up runtime configuration
    call :setup_runtime_config
    if %ERRORLEVEL% neq 0 exit /b 1
    
    exit /b 0

:load_config
    if not exist "%CONFIG_FILE%" (
        echo [INFO] Creating default configuration file: %CONFIG_FILE%
        echo # CaseStrainer Configuration File > "%CONFIG_FILE%"
        echo # SSL Certificate Paths - Update these to your certificate locations >> "%CONFIG_FILE%"
        echo SSL_CERT_PATH=D:/CaseStrainer/ssl/WolfCertBundle.crt >> "%CONFIG_FILE%"
        echo SSL_KEY_PATH=D:/CaseStrainer/ssl/wolf.law.uw.edu.key >> "%CONFIG_FILE%"
        echo # Nginx Directory >> "%CONFIG_FILE%"
        echo NGINX_DIR=%SCRIPT_DIR%nginx-1.27.5 >> "%CONFIG_FILE%"
        echo # Default Ports >> "%CONFIG_FILE%"
        echo DEV_BACKEND_PORT=5000 >> "%CONFIG_FILE%"
        echo DEV_FRONTEND_PORT=5173 >> "%CONFIG_FILE%"
        echo PROD_BACKEND_PORT=5001 >> "%CONFIG_FILE%"
        echo PROD_FRONTEND_PORT=4173 >> "%CONFIG_FILE%"
        echo # Server Configuration >> "%CONFIG_FILE%"
        echo SERVER_NAME=wolf.law.uw.edu >> "%CONFIG_FILE%"
        echo SERVER_IP=128.208.154.3 >> "%CONFIG_FILE%"
    )
    
    echo [INFO] Loading configuration from %CONFIG_FILE%
    for /f "usebackq tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        if not "%%a"=="" (
            if not "%%a"=="#" (
                if not "%%a"=="# CaseStrainer Configuration File" (
                    if not "%%a"=="# SSL Certificate Paths - Update these to your certificate locations" (
                        if not "%%a"=="# Nginx Directory" (
                            if not "%%a"=="# Default Ports" (
                                if not "%%a"=="# Server Configuration" (
                                    set "%%a=%%b"
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    exit /b 0

:parse_arguments
    :parse_args_loop
    if "%~1"=="" goto :args_done
    
    set "arg=%~1"
    if "%arg%"=="--prod" (
        set "ENV=prod"
    ) else if "%arg%"=="--dev" (
        set "ENV=dev"
    ) else if "%arg%"=="--auto-start" (
        set "AUTO_START=true"
    ) else if "%arg%"=="--help" (
        call :show_help
        exit /b 1
    ) else if "%arg%"=="_" (
        rem Internal argument used for script restart - ignore
    ) else (
        echo [WARNING] Unknown argument: %arg%
        echo [INFO] Use --help for usage information
    )
    shift
    goto :parse_args_loop
    
    :args_done
    exit /b 0

:show_help
    echo Usage: %~nx0 [OPTIONS]
    echo.
    echo Options:
    echo   --dev         Start in development mode (default)
    echo   --prod        Start in production mode
    echo   --auto-start  Automatically start all services in production mode
    echo   --help        Show this help message
    echo.
    echo Examples:
    echo   %~nx0                     # Interactive menu (development mode)
    echo   %~nx0 --prod              # Interactive menu (production mode)
    echo   %~nx0 --prod --auto-start # Automatic production setup
    echo.
    exit /b 0

:setup_runtime_config
    if "%ENV%"=="prod" (
        if defined PROD_BACKEND_PORT set "BACKEND_PORT=%PROD_BACKEND_PORT%"
        if defined PROD_FRONTEND_PORT set "FRONTEND_PORT=%PROD_FRONTEND_PORT%"
        set "BACKEND_CONFIG=config_prod.py"
        set "FLASK_DEBUG=0"
    ) else (
        set "BACKEND_PORT=%DEV_BACKEND_PORT%"
        set "FRONTEND_PORT=%DEV_FRONTEND_PORT%"
        set "BACKEND_CONFIG=config_dev.py"
        set "NODE_ENV=development"
        set "FLASK_ENV=development"
        set "FLASK_DEBUG=1"
    )
    
    :: Set process titles for management
    set "BACKEND_TITLE=CaseStrainer_Backend_%ENV%"
    set "FRONTEND_TITLE=CaseStrainer_Frontend_%ENV%"
    
    :: Set default ports if not loaded from config
    if not defined DEV_BACKEND_PORT set "DEV_BACKEND_PORT=5000"
    if not defined DEV_FRONTEND_PORT set "DEV_FRONTEND_PORT=5173"
    if not defined PROD_BACKEND_PORT set "PROD_BACKEND_PORT=5001"
    if not defined PROD_FRONTEND_PORT set "PROD_FRONTEND_PORT=4173"
    if not defined SSL_CERT_PATH set "SSL_CERT_PATH=D:/CaseStrainer/ssl/WolfCertBundle.crt"
    if not defined SSL_KEY_PATH set "SSL_KEY_PATH=D:/CaseStrainer/ssl/wolf.law.uw.edu.key"
    if not defined NGINX_DIR set "NGINX_DIR=%SCRIPT_DIR%nginx-1.27.5"
    if not defined SERVER_NAME set "SERVER_NAME=wolf.law.uw.edu"
    if not defined SERVER_IP set "SERVER_IP=128.208.154.3"
    
    :: Update environment variables in .env files if they exist
    if exist "%FRONTEND_DIR%\.env" (
        echo # Auto-generated by CaseStrainer launcher > "%FRONTEND_DIR%\.env"
        echo VITE_APP_ENV=%ENV% >> "%FRONTEND_DIR%\.env"
        echo NODE_ENV=%NODE_ENV% >> "%FRONTEND_DIR%\.env"
        echo VITE_API_BASE_URL=/casestrainer/api >> "%FRONTEND_DIR%\.env"
        echo VITE_APP_NAME=CaseStrainer >> "%FRONTEND_DIR%\.env"
        echo VITE_SERVER_NAME=%SERVER_NAME% >> "%FRONTEND_DIR%\.env"
        echo VITE_SERVER_IP=%SERVER_IP% >> "%FRONTEND_DIR%\.env"
        echo DEV_FRONTEND_PORT=%DEV_FRONTEND_PORT% >> "%FRONTEND_DIR%\.env"
        echo DEV_BACKEND_PORT=%DEV_BACKEND_PORT% >> "%FRONTEND_DIR%\.env"
        echo PROD_FRONTEND_PORT=%PROD_FRONTEND_PORT% >> "%FRONTEND_DIR%\.env"
        echo PROD_BACKEND_PORT=%PROD_BACKEND_PORT% >> "%FRONTEND_DIR%\.env"
    )
    exit /b 0

:: ===========================================
:: VALIDATION FUNCTION
:: ===========================================
:validate_numeric_input
    set "input=%~1"
    set "min=%~2"
    set "max=%~3"
    
    :: Check if input is empty
    if "%input%"=="" exit /b 1
    
    :: Remove any spaces
    set "input=%input: =%"
    
    :: Check if it's numeric and within range using a more robust method
    echo %input%| findstr /r "^[0-9][0-9]*$" >nul
    if %ERRORLEVEL% neq 0 exit /b 1
    
    :: Check range
    if %input% geq %min% if %input% leq %max% exit /b 0

:: ===========================================
:: PRODUCTION AUTO-START SEQUENCE
:: ===========================================
:production_restart_workflow
    echo [INFO] Starting Production Auto-Start Sequence
    echo ============================================
    echo  PRODUCTION AUTO-START SEQUENCE
    echo ============================================
    echo This will automatically:
    echo 1. Stop all current services
    echo 2. Switch to production environment  
    echo 3. Update configurations
    echo 4. Start backend service
    echo 5. Start frontend service
    echo 6. Configure and start Nginx
    echo 7. Run diagnostics
    echo 8. Display access URLs
    echo ============================================
    echo.
    
    set /p confirm=Start production auto-setup? (y/N): 
    if /i not "%confirm%"=="y" (
        echo [INFO] Production auto-start cancelled
        exit /b 0
    )
    
    echo.
    echo [STEP 1/8] Stopping all current services...
    call :stop_services
    
    echo.
    echo [STEP 2/8] Switching to production environment...
    set "ENV=prod"
    call :setup_runtime_config
    echo [SUCCESS] Switched to production environment
    
    echo.
    echo [STEP 3/8] Updating configurations...
    :: Create/update .env file with production settings
    if exist "%FRONTEND_DIR%" (
        echo [INFO] Updating frontend .env file...
        (
            echo # Production Environment Configuration
            echo VITE_APP_ENV=production
            echo NODE_ENV=production
            echo VITE_API_BASE_URL=/casestrainer/api
            echo VITE_APP_NAME=CaseStrainer
            echo VITE_SERVER_NAME=%SERVER_NAME%
            echo VITE_SERVER_IP=%SERVER_IP%
            echo DEV_FRONTEND_PORT=%DEV_FRONTEND_PORT%
            echo DEV_BACKEND_PORT=%DEV_BACKEND_PORT%
            echo PROD_FRONTEND_PORT=%PROD_FRONTEND_PORT%
            echo PROD_BACKEND_PORT=%PROD_BACKEND_PORT%
        ) > "%FRONTEND_DIR%\.env"
    )
    
    echo.
    echo [STEP 4/8] Starting backend service (Port: %BACKEND_PORT%)...
    call :start_backend
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Backend failed to start - aborting auto-start
        exit /b 1
    )
    echo [SUCCESS] Backend is running on port %BACKEND_PORT%
    
    echo.
    echo [STEP 5/8] Starting frontend service (Port: %FRONTEND_PORT%)...
    call :start_frontend
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Frontend failed to start - continuing with backend only
    ) else (
        echo [SUCCESS] Frontend is running on port %FRONTEND_PORT%
    )
    
    echo.
    echo [STEP 6/8] Configuring and starting Nginx...
    if not exist "%NGINX_DIR%\conf\casestrainer.conf" (
        echo [INFO] Creating Nginx configuration...
        call :create_nginx_config
    )
    
    call :start_nginx
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Nginx failed to start - application accessible via direct ports only
    ) else (
        echo [SUCCESS] Nginx is running
    )
    
    echo.
    echo [STEP 7/8] Running diagnostics...
    call :check_service_status
    
    echo.
    echo [STEP 8/8] Production setup complete
    echo ============================================
    echo  PRODUCTION AUTO-START SUMMARY
    echo ============================================
    echo Environment: %ENV%
    echo.
    
    echo [SERVICE STATUS]
    call :check_service_status
    
    echo.
    echo [ACCESS INFORMATION]
    echo "Internal Testing:"
    echo "  - Backend API: http://localhost:%BACKEND_PORT%"
    echo "  - Frontend: http://localhost:%FRONTEND_PORT%"
    echo.
    echo "External Access:"
    echo "  - Frontend: https://%SERVER_NAME%/casestrainer/"
    echo "  - Backend API: https://%SERVER_NAME%/casestrainer/api/"
    echo.
    echo ============================================
    echo [SUCCESS] Production setup completed successfully
    echo.
    
    call :log_message "Production auto-start sequence completed" "SUCCESS"
    exit /b 0

:show_production_summary
    echo ============================================
    echo  PRODUCTION AUTO-START SUMMARY
    echo ============================================
    echo Environment: %ENV%
    echo.
    
    :: Service Status
    echo [SERVICE STATUS]
    
    :: Backend
    call :check_port_available %BACKEND_PORT%
    if %ERRORLEVEL% neq 0 (
        echo Backend: RUNNING (Port %BACKEND_PORT%)
        echo    URL: http://localhost:%BACKEND_PORT%
    ) else (
        echo Backend: FAILED
    )
    
    :: Frontend
    if "%frontend_failed%"=="false" (
        echo Frontend: RUNNING (Port %FRONTEND_PORT%)
        echo    URL: http://localhost:%FRONTEND_PORT%
    ) else (
        echo Frontend: FAILED
    )
    
    :: Nginx
    if "%nginx_failed%"=="false" (
        echo Nginx: RUNNING
        echo    HTTP: http://localhost/casestrainer/
        echo    HTTPS: https://%SERVER_NAME%/casestrainer/
    ) else (
        echo Nginx: FAILED
    )
    
    echo.
    echo [ACCESS INFORMATION]
    echo Internal Testing:
    echo   - Backend API: http://localhost:%BACKEND_PORT%
    if "%frontend_failed%"=="false" (
        echo   - Frontend: http://localhost:%FRONTEND_PORT%
    )
    if "%nginx_failed%"=="false" (
        echo   - Via Nginx: http://localhost/casestrainer/
        echo.
        echo External Access (if firewall configured):
        echo   - Production URL: https://%SERVER_NAME%/casestrainer/
        echo   - Direct Backend: http://%SERVER_NAME%:%BACKEND_PORT% (if port open)
    )
    
    echo.
    echo [NEXT STEPS]
    if "%nginx_failed%"=="true" (
        echo 1. Check SSL certificates at: %SSL_CERT_PATH%
        echo 2. Verify Nginx configuration
        echo 3. Check port 443 availability
    )
    if "%frontend_failed%"=="true" (
        echo 1. Check Node.js installation and npm dependencies
        echo 2. Verify frontend directory: %FRONTEND_DIR%
        echo 3. Check port %FRONTEND_PORT% availability
    )
    echo 1. Test external connectivity from outside the network
    echo 2. Verify university firewall settings for ports 443 and %BACKEND_PORT%
    echo 3. Monitor logs for any errors
    
    echo.
    echo ============================================
    exit /b 0

:: ===========================================
:: UTILITY FUNCTIONS
:: ===========================================
:log_message
    set "message=%~1"
    set "level=%~2"
    if not defined level set "level=INFO"
    
    echo [%level%] %message%
    echo %date% %time% [%level%] %message% >> "%LOG_FILE%" 2>nul
    exit /b 0

:verify_directories
    set "missing_dirs="
    
    if not exist "%BACKEND_DIR%" (
        echo [ERROR] Backend directory not found: %BACKEND_DIR%
        set "missing_dirs=%missing_dirs% backend"
    )
    
    if not exist "%FRONTEND_DIR%" (
        echo [WARNING] Frontend directory not found: %FRONTEND_DIR%
        set "missing_dirs=%missing_dirs% frontend"
    )
    
    if not exist "%NGINX_DIR%" (
        echo [WARNING] Nginx directory not found: %NGINX_DIR%
        set "missing_dirs=%missing_dirs% nginx"
    )
    
    if defined missing_dirs (
        if not "%missing_dirs%"==" frontend nginx" (
            echo [ERROR] Critical directories missing:%missing_dirs%
            exit /b 1
        )
    )
    exit /b 0

:: ===========================================
:: SERVICE STATUS CHECKING
:: ===========================================
:check_service_status
    echo.
    echo ===== SERVICE STATUS =====
    echo.
    
    :: Check backend status
    set "backend_running=0"
    set "backend_pid="
    echo [BACKEND]
    for /f "tokens=2" %%p in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr /i "PID:"') do (
        set "backend_pid=%%p"
    )
    if defined backend_pid (
        echo Status: RUNNING (PID: !backend_pid!) on port %BACKEND_PORT%
        echo URL: http://localhost:%BACKEND_PORT%
        set "backend_running=1"
    ) else (
        echo Status: STOPPED
    )
    
    :: Check frontend status
    set "frontend_running=0"
    set "frontend_pid="
    echo.
    echo [FRONTEND]
    for /f "tokens=2" %%p in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST 2^>nul ^| findstr /i "vite"') do (
        set "frontend_pid=%%p"
    )
    if defined frontend_pid (
        echo Status: RUNNING (PID: !frontend_pid!) on port %FRONTEND_PORT%
        echo URL: http://localhost:%FRONTEND_PORT%
        set "frontend_running=1"
    ) else (
        echo Status: STOPPED
    )
    
    :: Check Nginx status
    set "nginx_running=0"
    set "nginx_pid="
    echo.
    echo [NGINX]
    for /f "tokens=2" %%p in ('tasklist /FI "IMAGENAME eq nginx.exe" /FO LIST 2^>nul ^| findstr /i "PID:"') do (
        set "nginx_pid=%%p"
    )
    if defined nginx_pid (
        echo Status: RUNNING (PID: !nginx_pid!)
        echo HTTP: http://localhost/casestrainer/
        echo HTTPS: https://%SERVER_NAME%/casestrainer/
        set "nginx_running=1"
    ) else (
        echo Status: STOPPED
    )
    
    echo.
    echo ==========================
    
    :: Set return code based on service status
    if "!backend_running!"=="1" if "!frontend_running!"=="1" if "!nginx_running!"=="1" (
        exit /b 0
    ) else (
        exit /b 1
    )

:check_nginx_status
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if %ERRORLEVEL% equ 0 (
        echo [NGINX]
        echo Status: RUNNING
        echo HTTP: http://localhost/casestrainer/
        echo HTTPS: https://%SERVER_NAME%/casestrainer/
    ) else (
        echo [NGINX]
        echo Status: STOPPED
    )
    exit /b %ERRORLEVEL%

:: ===========================================
:: PORT MANAGEMENT
:: ===========================================
:check_port_available
    set "check_port=%~1"
    if "%check_port%"=="" exit /b 1
    
    netstat -ano 2>nul | findstr ":%check_port% " | findstr "LISTENING" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        exit /b 1
    )
    exit /b 0

:: ===========================================
:: SERVICE FUNCTIONS
:: ===========================================
:stop_services
    call :log_message "Stopping all services" "INFO"
    call :stop_backend
    call :stop_frontend
    call :stop_nginx
    call :log_message "All services stopped" "INFO"
    exit /b 0

:start_services
    call :log_message "Starting all services" "INFO"
    call :start_backend
    call :start_frontend
    call :log_message "Services started" "INFO"
    echo.
    echo Press any key to return to the main menu...
    pause >nul
    exit /b 0

:start_backend
    echo [INFO] Starting backend service
    echo [INFO] Starting backend service on port %BACKEND_PORT%
    start "CaseStrainer Backend" /MIN cmd /c "title CaseStrainer Backend & python -m uvicorn app_final_vue:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
    timeout /t 3 /nobreak >nul
    echo [INFO] Backend startup completed
    exit /b 0

:stop_backend
    call :log_message "Stopping backend service" "INFO"
    echo [INFO] Stopping backend service
    exit /b 0

:start_frontend
    echo [INFO] Starting frontend service
    echo [INFO] Starting frontend service on port %FRONTEND_PORT%
    cd /d "%FRONTEND_DIR%"
    start "CaseStrainer Frontend" /MIN cmd /c "title CaseStrainer Frontend & npm run dev -- --port %FRONTEND_PORT%"
    cd /d "%SCRIPT_DIR%"
    timeout /t 5 /nobreak >nul
    echo [INFO] Frontend startup completed
    exit /b 0

:stop_frontend
    call :log_message "Stopping frontend service" "INFO"
    echo [INFO] Stopping frontend service
    exit /b 0

:start_nginx
    call :log_message "Starting Nginx" "INFO"
    echo [INFO] Starting Nginx...
    
    :: Stop any running Nginx instances first
    echo [INFO] Stopping any existing Nginx processes...
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if %ERRORLEVEL% equ 0 (
        echo [INFO] Found running Nginx process, stopping it...
        taskkill /F /IM nginx.exe >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
    
    :: Verify Nginx executable exists
    if not exist "%NGINX_DIR%\nginx.exe" (
        echo [ERROR] Nginx executable not found at: %NGINX_DIR%\nginx.exe
        echo [INFO] Please set the correct NGINX_DIR in the configuration
        exit /b 1
    )
    
    :: Check if port 80 or 443 are in use
    set "port_conflict=0"
    netstat -ano | findstr ":80 " >nul
    if %ERRORLEVEL% equ 0 (
        echo [WARNING] Port 80 is already in use. This may prevent Nginx from starting.
        set "port_conflict=1"
    )
    
    netstat -ano | findstr ":443 " >nul
    if %ERRORLEVEL% equ 0 (
        echo [WARNING] Port 443 is already in use. This may prevent Nginx from starting.
        set "port_conflict=1"
    )
    
    if "%port_conflict%"=="1" (
        echo [INFO] Attempting to start Nginx anyway...
    )
    
    :: Start Nginx with error logging
    echo [INFO] Starting Nginx with config: %NGINX_DIR%\conf\nginx.conf
    
    :: First test the configuration
    "%NGINX_DIR%\nginx.exe" -t -c "%NGINX_DIR%\conf\nginx.conf"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Nginx configuration test failed
        echo [INFO] Check the configuration file for errors: %NGINX_DIR%\conf\nginx.conf
        exit /b 1
    )
    
    :: Start Nginx
    echo [INFO] Starting Nginx service...
    "%NGINX_DIR%\nginx.exe" -c "%NGINX_DIR%\conf\nginx.conf"
    
    :: Verify Nginx started
    echo [INFO] Verifying Nginx started...
    timeout /t 3 /nobreak >nul
    tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Nginx started successfully
        exit /b 0
    ) else (
        echo [ERROR] Nginx process not found after starting
        echo [INFO] Check the error log: %NGINX_DIR%\logs\error.log
        
        :: Try to get more detailed error information
        if exist "%NGINX_DIR%\logs\error.log" (
            echo [INFO] Last 5 lines of error log:
            echo ===========================================
            type "%NGINX_DIR%\logs\error.log" | findstr /n "^" | findstr /r "[0-9]*:.*[Ee]rror\|[0-9]*:.*[Ff]atal" | tail -5
            echo ===========================================
        )
        
        exit /b 1
    )

:stop_nginx
    call :log_message "Stopping Nginx" "INFO"
    echo [INFO] Stopping Nginx...
    taskkill /F /IM nginx.exe >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Nginx stopped successfully
    ) else (
        echo [WARNING] No Nginx processes were running
    )
    exit /b 0

:create_nginx_config
    call :log_message "Creating Nginx configuration" "INFO"
    echo [INFO] Creating Nginx config