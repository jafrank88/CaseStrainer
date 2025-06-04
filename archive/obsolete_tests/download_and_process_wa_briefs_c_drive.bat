@echo off
echo ===================================================
echo Washington Court Briefs Downloader and Processor
echo ===================================================
echo.

echo Step 1: Downloading Washington Court briefs...
python "%~dp0download_wa_briefs_to_c_drive.py"
if %ERRORLEVEL% NEQ 0 (
    echo Error downloading briefs. Check the log file at c:\wa_briefs_download.log
    pause
    exit /b 1
)

echo.
echo Step 2: Processing downloaded briefs...
python "%~dp0process_c_drive_wa_briefs.py"
if %ERRORLEVEL% NEQ 0 (
    echo Error processing briefs. Check the log file at c:\wa_briefs_processing.log
    pause
    exit /b 1
)

echo.
echo ===================================================
echo All done! 
echo.
echo Briefs have been downloaded to: %USERPROFILE%\Documents\WA_Court_Briefs
echo Extracted text is in: %USERPROFILE%\Documents\WA_Court_Briefs\extracted_text
echo Unverified citations are saved to: %USERPROFILE%\Documents\WA_Court_Briefs\unverified_wa_citations.json
echo.
echo The citations have been added to the CaseStrainer database.
echo You can view them in the Multitool and Unconfirmed citations tabs.
echo ===================================================

pause
