@echo off
setlocal enabledelayedexpansion

:: ============================================
:: build_frontend.bat - Build the frontend for production
::
:: This script builds the Vue.js frontend and copies the output to the static directory.
:: It handles dependency installation and provides detailed logging.
::
:: Usage: build_frontend.bat [--clean] [--no-install]
::   --clean     : Clean node_modules and reinstall all dependencies
::   --no-install: Skip npm install step
:: ============================================

:: Configuration
set "PROJECT_ROOT=%~dp0"
set "VUE_DIR=%PROJECT_ROOT%casestrainer-vue-new"
set "STATIC_DIR=%PROJECT_ROOT%static"
set "LOG_DIR=%PROJECT_ROOT%logs"
set "LOG_FILE=%LOG_DIR%\build_frontend_%DATE:/=-%_%TIME::=-%.log"
set "NODE_ENV=production"

:: Parse command line arguments
set "CLEAN_INSTALL="
set "SKIP_INSTALL="

:parse_args
if "%~1"=="" goto args_done
if "%~1"=="--clean" set CLEAN_INSTALL=1
if "%~1"=="--no-install" set SKIP_INSTALL=1
shift
goto parse_args
:args_done

:: Initialize
cd /d "%PROJECT_ROOT%"

:: Create log directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================ > "%LOG_FILE%"
echo [%DATE% %TIME%] Starting frontend build >> "%LOG_FILE%"

:: Log function
:log
    echo [%TIME%] %* | findstr /v "^[0-9]"
    echo [%TIME%] %* >> "%LOG_FILE%" 2>&1
goto :eof

:: Error handler
:error
    call :log "ERROR: %~1"
    echo.
    echo Build failed! Check the log file for details:
    echo %LOG_FILE%
    pause
    exit /b 1

:: Check for required tools
where node >nul 2>&1 || (call :error "Node.js is not installed or not in PATH")
where npm >nul 2>&1 || (call :error "npm is not installed or not in PATH")

call :log "Building frontend for production..."
call :log "Project root: %PROJECT_ROOT%"
call :log "Vue directory: %VUE_DIR%"
call :log "Static directory: %STATIC_DIR%\vue"

:: Check Vue directory exists
if not exist "%VUE_DIR%" (
    call :error "Vue.js directory not found at: %VUE_DIR%"
)

:: Clean node_modules if requested
if defined CLEAN_INSTALL (
    call :log "Cleaning node_modules..."
    if exist "%VUE_DIR%\node_modules" (
        rmdir /s /q "%VUE_DIR%\node_modules"
    )
    if exist "%VUE_DIR%\package-lock.json" (
        del "%VUE_DIR%\package-lock.json"
    )
)

:: Install dependencies if needed
if not defined SKIP_INSTALL (
    call :log "Checking/installing frontend dependencies..."
    cd /d "%VUE_DIR%"
    
    if not exist "node_modules" (
        call :log "Running npm install..."
        npm install
        if errorlevel 1 (
            call :error "Failed to install frontend dependencies"
        )
    ) else (
        call :log "Running npm ci..."
        npm ci
        if errorlevel 1 (
            call :log "npm ci failed, falling back to npm install..."
            npm install
            if errorlevel 1 (
                call :error "Failed to install frontend dependencies"
            )
        )
    )
) else (
    call :log "Skipping npm install as requested..."
)

:: Build the frontend
call :log "Building Vue.js application..."
cd /d "%VUE_DIR%"
call npm run build
if errorlevel 1 (
    call :error "Failed to build frontend"
)

:: Copy built files to the static directory
call :log "Copying built files to static directory..."
if exist "%STATIC_DIR%\vue" (
    rmdir /s /q "%STATIC_DIR%\vue"
)

if not exist "%STATIC_DIR%" (
    mkdir "%STATIC_DIR%"
)

xcopy /E /I /Q /Y "%VUE_DIR%\dist\*" "%STATIC_DIR%\vue\" >nul
if errorlevel 1 (
    call :error "Failed to copy files to static directory"
)

:: Verify the build
if not exist "%STATIC_DIR%\vue\index.html" (
    call :error "Build failed - index.html not found in output"
)

call :log "Frontend built successfully!"
call :log "Output directory: %STATIC_DIR%\vue\"
call :log "Build completed in %SECONDS% seconds"

echo.
echo ============================================
echo  Frontend build completed successfully!
echo  Output directory: %STATIC_DIR%\vue\
echo  Log file: %LOG_FILE%
echo ============================================

exit /b 0
