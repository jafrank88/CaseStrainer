@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Commit, Push, and Deploy Script v2.0
REM ===================================================
REM USAGE: Run from the CaseStrainer root directory
REM REQUIREMENTS: Node.js, npm, Python 3.8+, git, PowerShell 5.1+
REM LOG: Output logged to casestrainer_deploy.log
REM ===================================================

set "LOGFILE=casestrainer_deploy.log"
set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=C:\Users\jafrank\venv_casestrainer"
set "NGINX_DIR=%PROJECT_ROOT%nginx-1.27.5"
set "NGINX_CONFIG=%NGINX_DIR%\conf\casestrainer.conf"
set "HOST=0.0.0.0"
set "PORT=5000"
set "THREADS=4"

REM === Initialize Logging ===
(
echo ===================================================
echo [%DATE% %TIME%] Starting CaseStrainer Deployment
) > "%LOGFILE%" 2>&1

call :log "Starting deployment process..."

REM === Check Required Tools ===
call :check_tool "Node.js" "node"
call :check_tool "npm" "npm"
call :check_tool "Python" "python"
call :check_tool "Git" "git"
call :check_tool "PowerShell" "powershell"

REM === Check Python Version ===
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" || (
    call :log_error "Python 3.8 or higher is required"
    exit /b 1
)
REM === Git Operations ===
call :log "Updating git repository..."
if not exist ".git" (
    call :log_error "Not a git repository. Please run from the root of the repository."
    exit /b 1
)

git fetch --all
if errorlevel 1 (
    call :log_error "Failed to fetch from remote repository"
    exit /b 1
)

git status -uno

REM === Pre-commit Hooks ===
call :log "Setting up pre-commit hooks..."
if exist "%VENV_PATH%\Scripts\pre-commit.exe" (
    "%VENV_PATH%\Scripts\pre-commit.exe" autoupdate
    "%VENV_PATH%\Scripts\pre-commit.exe" clean
    "%VENV_PATH%\Scripts\pre-commit.exe" install
) else (
    call :log "pre-commit not found in virtual environment, installing..."
    pip install pre-commit
    if errorlevel 1 (
        call :log_error "Failed to install pre-commit"
        exit /b 1
    )
    pre-commit install
)

REM === Git Add and Commit ===
call :log "Staging changes..."
git add -A

set /p commit_msg=Enter commit message: 
if "%commit_msg%"=="" (
    call :log_error "Commit message cannot be empty"
    exit /b 1
)

call :log "Running pre-commit checks..."
pre-commit run --all-files
if errorlevel 1 (
    call :log_error "Pre-commit checks failed. Please fix the issues before committing."
    exit /b 1
)

call :log "Creating commit..."
git commit -m "%commit_msg%"
if errorlevel 1 (
    call :log_error "Failed to create commit"
    exit /b 1
)

REM === Push Changes ===
call :log "Pushing changes to remote repository..."
git pull --rebase origin main
if errorlevel 1 (
    call :log_error "Failed to pull latest changes. Resolve conflicts and try again."
    exit /b 1
)

git push origin main
if errorlevel 1 (
    call :log_error "Failed to push changes to remote repository"
    exit /b 1
)

REM === Stop Existing Services ===
call :log "Stopping existing services..."
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul && (
    call :log "Stopping Nginx..."
    taskkill /F /IM nginx.exe >nul 2>&1
    timeout /t 2 >nul
)

REM === Clean Up Port ===
call :log "Checking port %PORT%..."
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    call :log "Port %PORT% is in use by PID %%a. Terminating process..."
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 >nul
)

REM === Create Required Directories ===
call :log "Creating required directories..."
for %%d in (logs uploads casestrainer_sessions static) do (
    if not exist "%%~d" (
        mkdir "%%~d"
        if errorlevel 1 (
            call :log_warning "Failed to create directory: %%~d"
        ) else (
            call :log "Created directory: %%~d"
        )
    )
)

REM === Activate Virtual Environment ===
call :log "Activating Python virtual environment..."
if not exist "%VENV_PATH%" (
    call :log_error "Virtual environment not found at: %VENV_PATH%"
    exit /b 1
)
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    call :log_error "Failed to activate virtual environment"
    exit /b 1
)

REM === Install Dependencies ===
call :log "Installing Python dependencies..."
pip install -r requirements.txt
if errorlevel 1 (
    call :log_error "Failed to install Python dependencies"
    exit /b 1
)

REM === Start Backend ===
call :log "Starting CaseStrainer backend..."
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=production

start "CaseStrainer Backend" cmd /k "python src\app_final_vue.py --use-waitress --host=%HOST% --port=%PORT% --threads=%THREADS% & echo. & echo Backend process ended. Press any key to close. & pause"

REM === Start Nginx ===
call :log "Starting Nginx..."
if not exist "%NGINX_DIR%\nginx.exe" (
    call :log_error "Nginx not found at: %NGINX_DIR%"
    exit /b 1
)

cd /d "%NGINX_DIR%"
start "Nginx" nginx.exe -c "%NGINX_CONFIG%"
cd /d "%PROJECT_ROOT%"

timeout /t 2 >nul

REM === Verify Services ===
call :log "Verifying services..."
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul && (
    call :log "Nginx is running"
) || (
    call :log_error "Failed to start Nginx"
    exit /b 1
)

tasklist /FI "WINDOWTITLE eq CaseStrainer Backend*" 2>nul | find /I "python.exe" >nul && (
    call :log "Backend is running"
) || (
    call :log_error "Failed to start backend"
    exit /b 1
)

REM === Final Status ===
call :log "Deployment completed successfully!"
call :log "Backend URL: http://%HOST%:%PORT%"
call :log "Frontend URL: http://localhost:80"
call :log "Log file: %LOGFILE%"

timeout /t 5 >nul
exit /b 0

REM === Functions ===
:log
    echo [%TIME%] %~1
    echo [%TIME%] %~1 >> "%LOGFILE%" 2>&1
goto :eof

:log_warning
    echo [%TIME%] [WARNING] %~1
    echo [%TIME%] [WARNING] %~1 >> "%LOGFILE%" 2>&1
goto :eof

:log_error
    echo [%TIME%] [ERROR] %~1
    echo [%TIME%] [ERROR] %~1 >> "%LOGFILE%" 2>&1
goto :eof

:check_tool
    where %~2 >nul 2>&1
    if errorlevel 1 (
        call :log_error "%1 (%2) is not installed or not in PATH"
        exit /b 1
    )
    call :log "Found %1: %~2"
goto :eof

REM Step 9: Verify Flask is running
timeout /t 5 >nul
netstat -ano | findstr :5000 | findstr LISTENING
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Flask did not start or port 5000 is not listening.
    echo To diagnose, run the following commands in your terminal:
    echo -----------------------------------------------
    echo set FLASK_APP=src/app_final_vue.py
    echo set FLASK_ENV=production
    echo python -m flask run --host=0.0.0.0 --port=5000
    echo -----------------------------------------------
    echo This will show any error messages directly.
    echo If you see missing dependency errors, run:
    echo     pip install -r requirements.txt
    echo If port 5000 is in use, check for processes and kill them as needed.
    echo.
    pause
) else (
    echo Flask is running on port 5000. Deployment appears successful.
    pause
)
