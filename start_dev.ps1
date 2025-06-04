# Set the Python path to include the project root
$env:PYTHONPATH = "$PSScriptRoot"

# Start the backend server
Write-Host "Starting backend server..."
$pythonCode = @'
import os
import sys
import logging

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from src.app_final_vue import app
app.run(host='0.0.0.0', port=5000, debug=True)
'@

# Save the Python code to a temporary file
$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$pythonCode | Out-File -FilePath $tempFile -Encoding ascii

# Start the Python process
$backend = Start-Process -FilePath "python" -ArgumentList $tempFile -PassThru -NoNewWindow -WorkingDirectory $PSScriptRoot

# Wait a moment for the backend to start
Start-Sleep -Seconds 5

# Start the frontend development server
Write-Host "Starting frontend development server..."
Set-Location -Path "$PSScriptRoot\casestrainer-vue-new"
$frontend = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -NoNewWindow

# Keep the script running until the user presses a key
Write-Host ""
Write-Host "Development environment is running!"
Write-Host "- Backend: http://localhost:5000"
Write-Host "- Frontend: http://localhost:5173"
Write-Host ""
Write-Host "Press any key to stop all services..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Clean up
Write-Host "Stopping services..."
Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue

Write-Host "All services stopped."
