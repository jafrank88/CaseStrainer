@echo off
echo Copying new files to D:\CaseStrainer with administrator privileges...
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0copy_new_files_to_d_drive.ps1\"' -Verb RunAs"
echo Please respond to the UAC prompt to continue.
pause
