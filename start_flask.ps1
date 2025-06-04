# Start the Flask application
$env:FLASK_APP = "app_final_vue.py"
$env:FLASK_ENV = "development"
python -m flask run --host=0.0.0.0 --port=5000
