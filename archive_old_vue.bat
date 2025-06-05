@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: Archive Old Vue Project
:: Moves old project to an organized archive location
:: ===================================================

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "OLD_VUE_DIR=%SCRIPT_DIR%casestrainer-vue"
set "ARCHIVE_ROOT=%SCRIPT_DIR%archived"
set "TIMESTAMP=%DATE:~-4,4%%DATE:~0,2%%DATE:~3,2%_%TIME:~0,2%%TIME:~3,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "ARCHIVE_NAME=casestrainer-vue_%TIMESTAMP%"
set "ARCHIVE_DIR=%ARCHIVE_ROOT%\%ARCHIVE_NAME%"
set "ZIP_FILE=%ARCHIVE_DIR%.zip"

:: Create archive root if it doesn't exist
if not exist "%ARCHIVE_ROOT%" (
    mkdir "%ARCHIVE_ROOT%"
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create archive root directory: %ARCHIVE_ROOT%
        pause
        exit /b 1
    )
)

:: Check if old vue directory exists
if not exist "%OLD_VUE_DIR%" (
    echo [ERROR] Directory not found: %OLD_VUE_DIR%
    echo Nothing to archive.
    pause
    exit /b 1
)

echo ===================================================
echo  Archiving Old Vue Project
echo ===================================================
echo Source: %OLD_VUE_DIR%
echo Archive: %ARCHIVE_DIR%
echo ===================================================
echo.

:: Create archive directory
mkdir "%ARCHIVE_DIR%"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to create archive directory: %ARCHIVE_DIR%
    pause
    exit /b 1
)

:: Create README file with archive info
echo Archiving old Vue project at %DATE% %TIME% > "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo. >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo Original Path: %OLD_VUE_DIR% >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo Archived At: %DATE% %TIME% >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo Reason: Superseded by casestrainer-vue-new >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo. >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"
echo This is an automated archive. The original directory has been moved here. >> "%ARCHIVE_DIR%\ARCHIVE_README.txt"

:: Use robocopy for more reliable file copying with long path support
echo Copying %OLD_VUE_DIR% to archive...
robocopy "%OLD_VUE_DIR%" "%ARCHIVE_DIR%" /E /COPYALL /R:3 /W:10 /NP /LOG:"%ARCHIVE_DIR%\copy_log.txt"

:: robocopy returns success codes 0-7 for successful operations
if !ERRORLEVEL! GTR 7 (
    echo [ERROR] Failed to copy files to archive directory. Check %ARCHIVE_DIR%\copy_log.txt for details.
    rmdir /S /Q "%ARCHIVE_DIR%"
    pause
    exit /b 1
)

:: Create a zip backup using PowerShell with long path support
echo Creating zip backup...
powershell -NoProfile -ExecutionPolicy Bypass -Command "
    $ErrorActionPreference = 'Stop';
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem;
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            '%ARCHIVE_DIR%', 
            '%ZIP_FILE%',
            [System.IO.Compression.CompressionLevel]::Optimal,
            $false  # Don't include base directory
        );
        Write-Output 'Zip backup created successfully.';
        exit 0;
    } catch {
        Write-Output '[WARNING] Failed to create zip backup: $_';
        exit 1;
    }"

if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Failed to create zip backup, continuing with directory copy only...
) else (
    echo Zip backup created: %ZIP_FILE%
)

:: Verify the copy was successful
if exist "%ARCHIVE_DIR%\package.json" (
    echo [SUCCESS] Archive created successfully at:
    echo %ARCHIVE_DIR%
    if exist "%ZIP_FILE%" echo %ZIP_FILE%
    
    echo.
    echo Removing original directory...
    rmdir /s /q "%OLD_VUE_DIR%" 2>nul
    
    if exist "%OLD_VUE_DIR%" (
        echo [WARNING] Could not remove original directory. It may be in use.
    ) else (
        echo [SUCCESS] Original directory removed.
    )
) else (
    echo [ERROR] Archive verification failed. Original directory not removed.
    rmdir /s /q "%ARCHIVE_DIR%" 2>nul
    if exist "%ZIP_FILE%" del "%ZIP_FILE%"
    pause
    exit /b 1
)

echo.
echo ===================================================
echo  Archive Complete
echo ===================================================
echo Old Vue project has been archived to:
echo %ARCHIVE_DIR%
if exist "%ZIP_FILE%" echo %ZIP_FILE%
echo.
echo The original directory has been removed.
echo ===================================================
pause
