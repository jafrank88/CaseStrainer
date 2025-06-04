@echo off
echo Running Git update with administrator privileges...
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0update_d_drive_git.ps1\"' -Verb RunAs"
echo Please respond to the UAC prompt to continue.
pause
