@echo off
echo Copying CaseStrainer files to D:\CaseStrainer...

REM Create the destination directory if it doesn't exist
if not exist D:\CaseStrainer mkdir D:\CaseStrainer

REM Copy all files and folders
xcopy /E /I /Y "c:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\*" "D:\CaseStrainer"

echo.
echo Copy process complete. Please check D:\CaseStrainer to verify files were copied successfully.
echo.

pause
