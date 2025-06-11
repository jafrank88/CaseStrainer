@echo off
setlocal enabledelayedexpansion

:: ===========================================
:: CaseStrainer Test Runner
:: Runs various test suites for the application
:: ===========================================

:menu
cls
echo ============================================
echo  CaseStrainer Test Runner
echo ============================================
echo 1. Run All Tests (Backend + Frontend)
echo 2. Run API Tests Only
echo 3. Run Frontend Tests Only
echo 4. Run Backend with Debug Mode
echo 5. Exit
echo ============================================
set /p choice="Select an option (1-5): "

if "!choice!"=="1" (
    call :run_all_tests
) else if "!choice!"=="2" (
    call :run_api_tests
) else if "!choice!"=="3" (
    call :run_frontend_tests
) else if "!choice!"=="4" (
    call :run_backend_debug
) else if "!choice!"=="5" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto menu
)

goto menu

:run_all_tests
echo.
echo ===== Running All Tests =====
call :run_api_tests
if !ERRORLEVEL! NEQ 0 (
    echo API Tests failed. Aborting frontend tests.
    pause
    goto :eof
)
call :run_frontend_tests
pause
goto :eof

:run_api_tests
echo.
echo ===== Running API Tests =====
python test_api_direct.py
set "test_result=!ERRORLEVEL!"
if !test_result! NEQ 0 (
    echo.
    echo ===== API Tests Failed =====
) else (
    echo.
    echo ===== API Tests Passed =====
)
pause
goto :eof

:run_frontend_tests
echo.
echo ===== Running Frontend Tests =====
if not exist "casestrainer-vue\package.json" (
    echo Error: Frontend directory not found or package.json missing
    pause
    goto :eof
)

cd casestrainer-vue
call npm test
set "test_result=!ERRORLEVEL!"
cd ..

if !test_result! NEQ 0 (
    echo.
    echo ===== Frontend Tests Failed =====
) else (
    echo.
    echo ===== Frontend Tests Passed =====
)
pause
goto :eof

:run_backend_debug
echo.
echo ===== Starting Backend in Debug Mode =====
python -m debugpy --listen 5678 --wait-for-client run_debug.py
pause
goto :eof
