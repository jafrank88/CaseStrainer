@echo off
echo Running CaseStrainer restart script...
cd /d %~dp0
call scripts\restart_casestrainer.bat %*
