staro off
setlocal

:: Set Python path to use the system Python
set PYTHON=python

:: Install requirements
echo Installing requirements...
%PYTHON% -m pip install -r requirements.txt

:: Set environment variables
set FLASK_APP=src/app_final_vue.py
set FLASK_DEBUG=1
set HOST=0.0.0.0
set PORT=5000

:: Start the Flask application
echo Starting Flask application...
%PYTHON% -c "from src.app_final_vue import create_app; app = create_app(); print('Application created successfully'); app.run(host='%HOST%', port=%PORT%, debug=True, use_reloader=False)"

endlocal
