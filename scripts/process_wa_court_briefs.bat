@echo off
echo ===================================================
echo Washington State Court Briefs Processing Script
echo ===================================================
echo.

REM Set up variables
set BRIEFS_DIR=wa_briefs
set MAX_RESULTS=5
set COURT=supreme

echo Step 1: Checking for required Python packages...
echo.
call .venv\Scripts\activate.bat

REM Install required packages if not already installed
pip install requests beautifulsoup4 tqdm PyPDF2

echo.
echo Step 2: Downloading Washington State Court briefs...
echo.

REM Download briefs from Washington State Courts
python download_wa_briefs.py --court %COURT% --max_results %MAX_RESULTS% --download_dir %BRIEFS_DIR%

echo.
echo Step 3: Processing briefs to extract and verify citations...
echo.

REM Process the downloaded briefs
python process_wa_briefs.py --briefs_dir %BRIEFS_DIR% --metadata_file %BRIEFS_DIR%\briefs_metadata.json

echo.
echo Step 4: Restarting the CaseStrainer application...
echo.

REM Stop any running Python instances
taskkill /F /IM python.exe 2>NUL

REM Start the application with the correct settings
call start_for_nginx.bat

echo.
echo Process complete! The CaseStrainer application has been updated with new citation data.
echo You can now access the application at https://wolf.law.uw.edu/casestrainer/
echo.

pause
