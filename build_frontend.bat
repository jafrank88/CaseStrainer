@echo off
setlocal enabledelayedexpansion

REM Set the project root directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

REM Set up log directory
set "LOG_DIR=%PROJECT_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\build_frontend_%DATE:/=-%_%TIME::=-%.log"

REM Function to log messages
:log
    echo [%DATE% %TIME%] %* | findstr /v "^[0-9]"
    echo [%DATE% %TIME%] %* >> "%LOG_FILE%" 2>&1
goto :eof

call :log "Building frontend for production..."

REM Install dependencies if needed
if not exist "%PROJECT_ROOT%casestrainer-vue-new\node_modules" (
    call :log "Installing frontend dependencies..."
    cd "%PROJECT_ROOT%casestrainer-vue-new"
    npm install
    if errorlevel 1 (
        call :log "Error: Failed to install frontend dependencies"
        exit /b 1
    )
)

REM Build the frontend
call :log "Building Vue.js application..."
cd "%PROJECT_ROOT%casestrainer-vue-new"
npm run build
if errorlevel 1 (
    call :log "Error: Failed to build frontend"
    exit /b 1
)

REM Copy built files to the static directory
call :log "Copying built files to static directory..."
if exist "%PROJECT_ROOT%static\vue" rmdir /s /q "%PROJECT_ROOT%static\vue"
if not exist "%PROJECT_ROOT%static" mkdir "%PROJECT_ROOT%static"
xcopy /E /I /Y "%PROJECT_ROOT%casestrainer-vue-new\dist\*" "%PROJECT_ROOT%static\vue\"

call :log "Frontend built successfully!"
call :log "Output directory: %PROJECT_ROOT%static\vue\"
