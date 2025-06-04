# Change to the script directory
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path $scriptPath
Set-Location $scriptDir

# Set environment variables
$env:FLASK_APP = "app_final_vue.py"
$env:FLASK_ENV = "development"

# Run the Flask application
Write-Host "Starting Flask application..."
python -m flask run --host=0.0.0.0 --port=5000
