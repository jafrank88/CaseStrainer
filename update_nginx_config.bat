@echo off
setlocal enabledelayedexpansion

:: Configuration
set "TEMPLATE_FILE=nginx.conf.template"
set "OUTPUT_FILE=nginx-1.27.5\conf\nginx.conf"
set "CONFIG_FILE=config.ini"

:: Check if template file exists
if not exist "%TEMPLATE_FILE%" (
    echo Error: Template file %TEMPLATE_FILE% not found
    exit /b 1
)

:: Read config.ini
for /f "usebackq tokens=1* delims==" %%a in ("%CONFIG_FILE%") do (
    set "var=%%a"
    set "val=%%b"
    
    :: Remove quotes and trailing whitespace
    set "var=!var: =!"
    set "val=!val:"=!"
    set "val=!val: =!"
    
    :: Skip comments and empty lines
    if not "!var:~0,1!"=="#" if not "!var!"=="" (
        set "CONFIG_!var!=!val!"
    )
)

:: Create a copy of the template
copy /y "%TEMPLATE_FILE%" "%OUTPUT_FILE%" >nul

:: Replace placeholders with values from config
for /f "tokens=2 delims={}" %%a in ('findstr /r "\${\w*}" "%TEMPLATE_FILE%"') do (
    set "placeholder=%%a"
    set "value=!CONFIG_%%a!"
    
    if "!value!"=="" (
        echo Warning: No value found for placeholder: %%a
    )
    
    powershell -Command "(Get-Content '%OUTPUT_FILE%') -replace '\$\{%a\}', '!value!' | Set-Content '%OUTPUT_FILE%'"
)

echo Nginx configuration has been updated: %OUTPUT_FILE%

:: Restart Nginx if it's running
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
if %ERRORLEVEL% equ 0 (
    echo Restarting Nginx...
    nginx -s reload
)

echo Done.
