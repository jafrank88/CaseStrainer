@echo off
echo ===================================================
echo Washington Court Briefs Download and Processing Script
echo ===================================================
echo.

REM Set up variables
set BRIEFS_DIR=wa_briefs
set MAX_CASES=15
set MAX_BRIEFS_PER_CASE=2

echo Step 1: Checking for required Python packages...
echo.
call .venv\Scripts\activate.bat

REM Install required packages if not already installed
pip install requests beautifulsoup4 tqdm PyPDF2

echo.
echo Step 2: Downloading Washington Court briefs...
echo This will download briefs slowly to avoid rate limiting.
echo.

REM Download briefs from Washington State Courts
python download_wa_briefs_from_links.py

echo.
echo Step 3: Processing briefs to extract and verify citations...
echo.

REM Process the downloaded briefs
python process_downloaded_wa_briefs.py

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
