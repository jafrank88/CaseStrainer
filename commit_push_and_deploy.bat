@echo off
REM ================================================
REM All deployments use app_final_vue.py as the backend entrypoint (via start_casestrainer_complete.bat).
REM For normal startup/restarts, use start_casestrainer.bat instead of this script.
REM ================================================
REM Step 1: Commit all changes

echo Adding all changes to git...
git add -A

set /p commitmsg="Enter commit message: "

echo Committing changes...
git commit -m "%commitmsg%"

REM Step 2: Push to remote repository
echo Pushing to remote repository...
git push origin main

REM Step 3: Deploy (run start_casestrainer_complete.bat)
echo Deploying with start_casestrainer_complete.bat...
call start_casestrainer_complete.bat

echo All steps complete!
pause
