# Start the Flask application and keep it running
$env:FLASK_APP = "app_final_vue.py"
$env:FLASK_ENV = "development"

# Run the Flask app in a loop to keep it running
while ($true) {
    try {
        Write-Host "Starting Flask application..."
        python -c "import app_final_vue; app_final_vue.app.run(host='0.0.0.0', port=5000, debug=True)"
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
    }
    Write-Host "Flask application stopped. Restarting in 5 seconds..."
    Start-Sleep -Seconds 5
}
