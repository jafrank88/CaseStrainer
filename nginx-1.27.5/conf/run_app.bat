@echo off
setlocal

:: Set Python path to use the system Python
set PYTHON=python

:: Add src directory to PYTHONPATH
set PYTHONPATH=%CD%;%CD%\src

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set FLASK_DEBUG=1
set HOST=0.0.0.0
set PORT=5000

:: Start the Flask application
echo Starting Flask application...
%PYTHON% -c "import sys; print('Python path:', sys.path); from src.app_final_vue import create_app; print('Creating app...'); app = create_app(); print('Starting server...'); app.run(host='%HOST%', port=%PORT%, debug=True, use_reloader=False)"

endlocal