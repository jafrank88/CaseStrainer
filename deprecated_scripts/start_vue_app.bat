@echo off
set FLASK_APP=docker\src\app_final_vue.py
set FLASK_ENV=development
set SESSION_TYPE=filesystem
set FLASK_DEBUG=0

python -m flask run --host=0.0.0.0 --port=5000 --no-debugger --no-reload
