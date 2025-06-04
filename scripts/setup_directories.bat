@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Directory Setup Script
REM ===================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo [%TIME%] ===================================
echo [%TIME%] Setting up required directories
echo [%TIME%] ===================================

REM Create required directories
echo [%TIME%] Creating directories...
if not exist "D:\CaseStrainer" mkdir "D:\CaseStrainer"
if not exist "D:\CaseStrainer\ssl" mkdir "D:\CaseStrainer\ssl"
if not exist "D:\CaseStrainer\static" mkdir "D:\CaseStrainer\static"
if not exist "D:\CaseStrainer\static\vue" mkdir "D:\CaseStrainer\static\vue"
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"

REM Set permissions (Windows specific)
icacls "D:\CaseStrainer" /grant "Users:(OI)(CI)F" /T /C >nul 2>&1

REM Copy SSL certificates if they exist in the project
if exist "ssl\WolfCertBundle.crt" (
    if not exist "D:\CaseStrainer\ssl\WolfCertBundle.crt" (
        copy "ssl\WolfCertBundle.crt" "D:\CaseStrainer\ssl\"
        if %ERRORLEVEL% EQU 0 (
            echo [%TIME%] Copied WolfCertBundle.crt to D:\CaseStrainer\ssl\
        ) else (
            echo [%TIME%] WARNING: Failed to copy WolfCertBundle.crt
        )
    )
)

if exist "ssl\wolf.law.uw.edu.key" (
    if not exist "D:\CaseStrainer\ssl\wolf.law.uw.edu.key" (
        copy "ssl\wolf.law.uw.edu.key" "D:\CaseStrainer\ssl\"
        if %ERRORLEVEL% EQU 0 (
            echo [%TIME%] Copied wolf.law.uw.edu.key to D:\CaseStrainer\ssl\
        ) else (
            echo [%TIME%] WARNING: Failed to copy wolf.law.uw.edu.key
        )
    )
)

echo [%TIME%] ===================================
echo [%TIME%] Directory setup complete.
echo [%TIME%] ===================================

REM Verify SSL certificates
echo [%TIME%] Verifying SSL certificates...
if not exist "D:\CaseStrainer\ssl\WolfCertBundle.crt" (
    echo [%TIME%] WARNING: SSL certificate not found at D:\CaseStrainer\ssl\WolfCertBundle.crt
    echo [%TIME%] Please ensure you have the correct SSL certificate in place.
)

if not exist "D:\CaseStrainer\ssl\wolf.law.uw.edu.key" (
    echo [%TIME%] WARNING: SSL private key not found at D:\CaseStrainer\ssl\wolf.law.uw.edu.key
    echo [%TIME%] Please ensure you have the correct SSL private key in place.
)

echo [%TIME%] ===================================
echo [%TIME%] Setup complete. Press any key to continue...
pause >nul

exit /b 0
