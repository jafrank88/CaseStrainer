@echo off
setlocal enabledelayedexpansion

echo Starting CaseStrainer...

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_RUN_PORT=5000
set FLASK_RUN_HOST=0.0.0.0

:: Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Running without it...
)

:: Install requirements if needed
if not exist venv\Scripts\activate.bat (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

:: Start the Flask application
echo Starting Flask application...
python -m flask run --port=5000 --host=0.0.0.0

pause
