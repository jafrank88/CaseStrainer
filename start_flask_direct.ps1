# Start the Flask application directly
$env:FLASK_APP = "app_final_vue.py"
$env:FLASK_ENV = "development"
python -c "import app_final_vue; app_final_vue.app.run(host='0.0.0.0', port=5000, debug=True)"
