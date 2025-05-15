@echo off
setlocal enabledelayedexpansion

echo Checking required packages...
python -c "import PyPDF2" 2>nul
if errorlevel 1 (
    echo Installing PyPDF2...
    pip install PyPDF2
)

python -c "import eyecite" 2>nul
if errorlevel 1 (
    echo Installing eyecite...
    pip install eyecite
)

echo.
echo Extracting citations from Washington Appellate Court PDFs...
python extract_wa_citations.py

if not exist wa_test_citations.txt (
    echo Error: Failed to extract citations
    exit /b 1
)

echo.
echo Citations extracted successfully. Running comprehensive test...
python comprehensive_test.py --input-file wa_test_citations.txt

echo.
echo Test completed. Check the results in the results directory. 