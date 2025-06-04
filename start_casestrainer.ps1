# Start CaseStrainer in PowerShell

# Set environment variables
$env:FLASK_APP = "src/app_final_vue.py"
$env:HOST = "0.0.0.0"
$env:PORT = 5000
$env:THREADS = 10
$env:USE_CHEROOT = "True"

# Create required directories
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" }
if (!(Test-Path "uploads")) { New-Item -ItemType Directory -Path "uploads" }
if (!(Test-Path "casestrainer_sessions")) { New-Item -ItemType Directory -Path "casestrainer_sessions" }

# Check if port 5000 is available
Write-Host "Checking if port 5000 is available..."
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port 5000 is already in use."
    Write-Host "Stopping any processes using port 5000..."
    
    $portInUse | ForEach-Object {
        $processId = $_.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Killing process with PID: $($process.Id) - $($process.ProcessName)"
            Stop-Process -Id $process.Id -Force
        }
    }
    
    Start-Sleep -Seconds 2
}

# Install/update dependencies
Write-Host "Installing dependencies..."
py -3.13 -m pip install -r requirements.txt

# Start Nginx if not already running
$nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
if (-not $nginxProcess) {
    Write-Host "Starting Nginx..."
    Start-Process -FilePath "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe" -ArgumentList "-p `"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5`" -c `"conf\nginx.conf`"" -NoNewWindow
} else {
    Write-Host "Nginx is already running."
}

# Start the Flask application
Write-Host "Starting Flask application..."
Start-Process -FilePath "py" -ArgumentList "-3.13", "src/app_final_vue.py", "--host=$($env:HOST)", "--port=$($env:PORT)" -NoNewWindow

Write-Host "CaseStrainer is now running!"
Write-Host "Access the application at: http://localhost:5000"