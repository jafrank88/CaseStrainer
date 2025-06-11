@echo off
setlocal enabledelayedexpansion

REM ===================================================
REM CaseStrainer Production Server with Auto-Restart
REM ===================================================
REM This script will:
REM 1. Kill any running Python/Node/Nginx processes
REM 2. Rebuild the Vue.js frontend if needed
REM 3. Start Nginx with proper configuration
REM 4. Start the Flask backend with auto-restart
REM ===================================================
REM This script will:
REM 1. Kill any running Python/Node processes
REM 2. Rebuild the Vue.js frontend if needed
REM 3. Start the backend with auto-restart
REM 4. Watch for file changes and restart automatically
REM 
REM Usage:
REM   restart_full.bat [watch]
REM   - Without arguments: One-time restart
REM   - With 'watch': Monitor for file changes and auto-restart
REM ===================================================

SET WATCH_MODE=0
IF NOT "%1"=="" IF /I "%1"=="watch" SET WATCH_MODE=1

echo ===================================================
echo [%date% %time%] Starting CaseStrainer %WATCH_MODE%{watch mode: !WATCH_MODE!}
echo ===================================================
echo.

REM --- Step 1: Kill any running Python processes ---
echo [%date% %time%] Stopping any running Python processes...

REM Force kill all Python processes without checking if they exist first
echo Terminating any Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

REM Also kill any Node.js processes that might be running from previous sessions
echo Terminating any Node.js processes...
taskkill /F /IM node.exe >nul 2>&1

REM Ensure processes are fully terminated
timeout /t 2 /nobreak >nul

REM --- Step 2: Rebuild Vue.js frontend ---
echo.
echo [%date% %time%] Rebuilding Vue.js frontend...
call scripts\build_and_deploy_vue.bat
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERROR: Failed to build Vue.js frontend!
    pause
    exit /b 1
)

REM --- Step 3: Start backend with auto-restart ---
:start_server
echo.
if %WATCH_MODE% EQU 1 (
    echo [%date% %time%] Starting in WATCH MODE - will auto-restart on file changes
    echo [%date% %time%] Watching for file changes in: src\, casestrainer-vue\src\
) else (
    REM Start Nginx
    echo [%TIME%] Starting Nginx...
    if exist "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" (
        "%SCRIPT_DIR%nginx-1.27.5\nginx.exe" -c "%SCRIPT_DIR%nginx.conf"
    ) else (
        start "" /B nginx.exe -c "%SCRIPT_DIR%nginx.conf"
    )
    echo [%date% %time%] Press Ctrl+C to stop the application
)
echo.

set RESTART_COUNT=0
:start_process
  set /a RESTART_COUNT+=1
  
  if !RESTART_COUNT! gtr 10 (
    echo [%date% %time%] ERROR: Maximum restart attempts (10) reached. Please check the application logs.
    pause
    exit /b 1
  )
  
  if !RESTART_COUNT! gtr 1 (
    echo [%date% %time%] Restarting application (Attempt !RESTART_COUNT! of 10)...
    timeout /t 2 /nobreak >nul
  )
  
  echo [%date% %time%] Starting CaseStrainer backend...
  
  REM Set environment variables
  set FLASK_APP=src/app_final_vue.py
  set FLASK_ENV=production
  set HOST=0.0.0.0
  set PORT=5000
  set THREADS=4
  set PREFIX=/casestrainer

  REM Add the project root to PYTHONPATH
  set PYTHONPATH=%CD%;%PYTHONPATH%

  REM Start the Python process in the background
  start "CaseStrainer Backend" /B python -m src.app_final_vue
  
  if %WATCH_MODE% EQU 1 (
    REM In watch mode, start the file watcher
    echo [%date% %time%] Starting file watcher...
    
    :watch_loop
    REM Check for changes in Python and Vue source files
    powershell -Command "
      $watcher = New-Object System.IO.FileSystemWatcher;
      $watcher.Path = '%~dp0';
      $watcher.IncludeSubdirectories = $true;
      $watcher.EnableRaisingEvents = $true;
      $watcher.Filter = '*.py';
      $watcher2 = New-Object System.IO.FileSystemWatcher;
      $watcher2.Path = '%~dp0casestrainer-vue\src';
      $watcher2.IncludeSubdirectories = $true;
      $watcher2.EnableRaisingEvents = $true;
      $watcher2.Filter = '*.vue';
      $change = $watcher.WaitForChanged('Changed', 1000);
      $change2 = $watcher2.WaitForChanged('Changed', 1000);
      if ($change.TimedOut -eq $false -or $change2.TimedOut -eq $false) {
        Write-Output 'CHANGE_DETECTED'
      }
    " | findstr /C:"CHANGE_DETECTED" >nul
    
    if %ERRORLEVEL% EQU 0 (
      echo [%date% %time%] Detected file changes. Restarting...
      
      REM Kill the Python process
      taskkill /F /IM python.exe >nul 2>&1
      
      REM Rebuild Vue.js if Vue files changed
      powershell -Command "
        $vueChanged = (Get-ChildItem -Path '%~dp0casestrainer-vue\src' -Filter '*.vue' -Recurse | 
                      Where-Object { $_.LastWriteTime -gt (Get-Date).AddSeconds(-5) } | 
                      Measure-Object).Count -gt 0;
        if ($vueChanged) { 
          Write-Output 'VUE_CHANGED' 
        }
      " | findstr /C:"VUE_CHANGED" >nul
      
      if %ERRORLEVEL% EQU 0 (
        echo [%date% %time%] Vue.js files modified. Rebuilding frontend...
        call scripts\build_and_deploy_vue.bat
        if %ERRORLEVEL% neq 0 (
          echo [%date% %time%] WARNING: Vue.js rebuild failed, continuing with previous build
        )
      )
      
      REM Reset restart counter and restart the server
      set RESTART_COUNT=0
      goto start_process
    )
    
    REM If we get here, no changes were detected within the timeout
    REM Check if the Python process is still running
    tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
    if %ERRORLEVEL% NEQ 0 (
      echo [%date% %time%] Backend process died. Restarting...
      set /a RESTART_COUNT=!RESTART_COUNT! + 1
      goto start_process
    )
    
    goto watch_loop
  ) else (
    REM In non-watch mode, just run the process and wait for it to exit
    python -m src.app_final_vue
    set EXIT_CODE=!ERRORLEVEL!
    echo [%date% %time%] Process exited with code !EXIT_CODE!
    
    if !EXIT_CODE! EQU 0 (
      echo [%date% %time%] Application exited normally. Not restarting.
      exit /b 0
    )
  )

goto start_process
