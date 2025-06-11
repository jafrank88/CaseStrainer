@echo off
echo Starting Flask backend server...
set FLASK_APP=deployment\app_final.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set USE_CHEROOT=False

cd /d %~dp0
python -m flask run --host=0.0.0.0 --port=5000

if %ERRORLEVEL% neq 0 (
    echo Failed to start Flask server. Make sure you're in the correct directory and have all dependencies installed.
    echo You may need to run: pip install -r requirements.txt
)

pause
