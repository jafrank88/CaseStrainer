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

REM Step 4: Troubleshooting Flask startup
netstat -ano | findstr :5000 | findstr LISTENING
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Flask did not start or port 5000 is not listening.
    echo To diagnose, run the following commands in your terminal:
    echo -----------------------------------------------
    echo set FLASK_APP=src/app_final_vue.py
    echo set FLASK_ENV=production
    echo python -m flask run --host=0.0.0.0 --port=5000
    echo -----------------------------------------------
    echo This will show any error messages directly.
    echo If you see missing dependency errors, run:
    echo     pip install -r requirements.txt
    echo If port 5000 is in use, check for processes and kill them as needed.
    echo.
    pause
) else (
    echo Flask is running on port 5000. Deployment appears successful.
    pause
)

