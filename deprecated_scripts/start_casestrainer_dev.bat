@echo off
REM === Simple Dev Startup for CaseStrainer (Flask only, no Nginx/Waitress) ===

REM Activate virtual environment (if not already active)
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
)

REM Create required directories if missing
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist casestrainer_sessions mkdir casestrainer_sessions

REM Install/update dependencies (optional, comment out if not needed every run)
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start Flask app (runs on http://127.0.0.1:5000 by default)
echo Starting CaseStrainer Flask backend for development...
python src/app_final_vue.py

echo =============================================
echo   CaseStrainer development server started!
echo   Access at: http://localhost:5000/casestrainer/
echo =============================================
pause
