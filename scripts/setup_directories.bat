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

REM Copy SSL certificates if they exist in the new location
if exist "C:\Users\jafrank\wolf-cert-bundle.crt" (
    if not exist "D:\CaseStrainer\ssl\WolfCertBundle.crt" (
        copy "C:\Users\jafrank\wolf-cert-bundle.crt" "D:\CaseStrainer\ssl\WolfCertBundle.crt"
        if %ERRORLEVEL% EQU 0 (
            echo [%TIME%] Copied wolf-cert-bundle.crt to D:\CaseStrainer\ssl\WolfCertBundle.crt
        ) else (
            echo [%TIME%] WARNING: Failed to copy wolf-cert-bundle.crt
        )
    )
)

if exist "C:\Users\jafrank\wolf.law.uw.edu.key" (
    if not exist "D:\CaseStrainer\ssl\wolf.law.uw.edu.key" (
        copy "C:\Users\jafrank\wolf.law.uw.edu.key" "D:\CaseStrainer\ssl\"
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
