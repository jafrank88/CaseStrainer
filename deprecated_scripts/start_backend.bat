@echo off 
call .venv\Scripts\activate 
set FLASK_APP=src.app_final_vue:app 
python -m waitress --host=0.0.0.0 --port=5000 --threads=10 src.app_final_vue:app 
