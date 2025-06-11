@echo off
setlocal enabledelayedexpansion

:: ============================================
:: cleanup_old_scripts.bat - Move old batch files to archive
:: 
:: This script moves obsolete batch files to the archive/scripts directory
:: to keep the root directory clean.
:: ============================================

echo.
echo ============================================
echo  Starting cleanup of old batch files...
echo ============================================
echo.

:: Set paths - using full paths to avoid any issues
set "PROJECT_ROOT=%~dp0"
set "ARCHIVE_DIR=%PROJECT_ROOT%archive\scripts"
set "LOG_DIR=%PROJECT_ROOT%logs"

:: Create necessary directories if they don't exist
if not exist "%ARCHIVE_DIR%" (
    echo Creating archive directory: %ARCHIVE_DIR%
    mkdir "%ARCHIVE_DIR%"
)

if not exist "%LOG_DIR%" (
    echo Creating logs directory: %LOG_DIR%
    mkdir "%LOG_DIR%"
)

:: List of batch files to keep
set "KEEP_FILES=casestrainer_menu.bat start_casestrainer.bat debug_flask.bat build_frontend.bat run_tests.bat cleanup_old_scripts.bat commit_push_and_deploy.bat update_nginx_config.bat"

:: Counters for summary
set "moved=0"
set "kept=0"

echo The following batch files will be kept:
for %%k in (%KEEP_FILES%) do (
    if exist "%PROJECT_ROOT%%%k" (
        echo   - %%~k
        set /a "kept+=1"
    )
)

echo.
echo Looking for batch files to archive...

:: Process each .bat file in the project root
for %%f in ("%PROJECT_ROOT%*.bat") do (
    set "filename=%%~nxf"
    set "keep=0"
    
    :: Check if this is a file we should keep
    for %%k in (%KEEP_FILES%) do (
        if /i "!filename!"=="%%~k" set "keep=1"
    )
    
    if "!keep!"=="0" (
        echo Archiving: !filename!
        move /Y "%%f" "%ARCHIVE_DIR%\" >nul
        if !ERRORLEVEL! EQU 0 (
            set /a "moved+=1"
        )
    )
)

echo.
echo ============================================
echo  Cleanup Summary
echo ============================================
echo  Batch files kept:    !kept!
echo  Batch files moved:   !moved!
echo  Archive location:   %ARCHIVE_DIR%
echo ============================================
echo.

if "!moved!"=="0" (
    echo No files needed to be archived.
) else (
    echo !moved! batch files were moved to the archive.
)

echo.
pause
pause
