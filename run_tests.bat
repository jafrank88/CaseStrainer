@echo off
echo ========================================
echo CaseStrainer Comprehensive Test Suite
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Python found. Starting test suite...
echo.

REM Run the test suite with detailed output and save results
python test_suite.py --detailed --save-results

echo.
echo ========================================
echo Test suite completed!
echo Check test_results.json for detailed results.
echo ========================================
pause
