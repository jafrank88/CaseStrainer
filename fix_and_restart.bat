@echo off
echo ========================================
echo CaseStrainer: Fix Syntax Error and Restart
echo ========================================
echo.

echo Step 1: Stopping backend (PID 19760)...
taskkill /F /PID 19760 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Fixing syntax error in unified_citation_processor_v2.py...
python fix_syntax_error_v2.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to fix syntax error
    pause
    exit /b 1
)

echo Step 3: Verifying syntax...
python -m py_compile src\unified_citation_processor_v2.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Syntax error still present
    pause
    exit /b 1
)

echo Step 4: Restarting backend...
start "CaseStrainer Backend" python app_final.py

echo.
echo ========================================
echo Done! Backend restarting...
echo ========================================
timeout /t 3 /nobreak >nul
