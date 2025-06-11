@echo off
setlocal enabledelayedexpansion

:: ============================================
:: CaseStrainer Menu
:: 
:: This script provides a menu interface for running various CaseStrainer
:: batch files with descriptions of what each one does.
:: ============================================

:menu
cls
echo ============================================
echo        CASESTRAINER MANAGEMENT MENU
echo ============================================
echo.
echo [1] Start CaseStrainer (Production)
echo     Starts both backend and Nginx with production settings
echo.
echo [2] Debug Flask Application
echo     Starts Flask in debug mode for development
echo.
echo [3] Build Frontend
echo     Builds the Vue.js frontend and deploys to static directory
echo.
echo [4] Run Tests
echo     Runs the test suite for the application
echo.
echo [5] Update Nginx Configuration
echo     Updates Nginx configuration and restarts Nginx
echo.
echo [6] Commit, Push, and Deploy
echo     Commits changes, pushes to repo, and deploys updates
echo.
echo [7] Cleanup Old Scripts
echo     Moves obsolete batch files to archive directory
echo.
echo [0] Exit
echo.
echo ============================================
set /p "choice=Enter your choice (0-7): "

if not defined choice goto invalid
if "%choice%"=="" goto invalid

if "%choice%"=="1" goto option_1
if "%choice%"=="2" goto option_2
if "%choice%"=="3" goto option_3
if "%choice%"=="4" goto option_4
if "%choice%"=="5" goto option_5
if "%choice%"=="6" goto option_6
if "%choice%"=="7" goto option_7
if "%choice%"=="0" goto option_0

goto invalid

:option_1
    echo.
    echo Starting CaseStrainer in production mode...
    call start_casestrainer.bat
    pause
    goto menu

:option_2
    echo.
    echo Starting Flask in debug mode...
    call debug_flask.bat
    pause
    goto menu

:option_3
    echo.
    echo Building frontend...
    call build_frontend.bat
    pause
    goto menu

:option_4
    echo.
    echo Running tests...
    call run_tests.bat
    pause
    goto menu

:option_5
    echo.
    echo Updating Nginx configuration...
    call update_nginx_config.bat
    pause
    goto menu

:option_6
    echo.
    echo Starting deployment process...
    call commit_push_and_deploy.bat
    pause
    goto menu

:option_7
    echo.
    echo ============================================
    echo  CLEANING UP OLD SCRIPTS
    echo ============================================
    echo.
    
    :: Ensure we're in the correct directory
    pushd "%~dp0"
    
    :: Create necessary directories if they don't exist
    if not exist "archive\scripts" (
        echo Creating archive directory...
        mkdir "archive\scripts"
    )
    
    if not exist "logs" (
        echo Creating logs directory...
        mkdir "logs"
    )
    
    echo.
    echo Starting cleanup process...
    call cleanup_old_scripts.bat
    
    :: Return to original directory
    popd
    
    echo.
    pause
    goto menu

:option_0
    echo.
    echo Exiting CaseStrainer Menu.
    exit /b 0

:invalid
    echo.
    echo Invalid choice. Please enter a number between 0 and 7.
    pause
    goto menu
