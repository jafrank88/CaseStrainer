# Monitor and restart Flask application if it crashes
$ErrorActionPreference = "Stop"
$port = 5000
$flaskScript = "test_flask.py"  # Change this to "run_debug.py" for the actual app
$logFile = "monitor_flask_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Function to write log messages
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console with colors
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN"  { Write-Host $logMessage -ForegroundColor Yellow }
        "INFO"  { Write-Host $logMessage -ForegroundColor White }
        "DEBUG" { Write-Host $logMessage -ForegroundColor Gray }
        default { Write-Host $logMessage }
    }
    
    # Append to log file
    Add-Content -Path $logFile -Value $logMessage
}

# Function to check if Flask is running
function Test-FlaskRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -ErrorAction Stop -TimeoutSec 5
        $responseContent = $response.Content | ConvertFrom-Json
        Write-Log "Health check successful: $($response.StatusCode) - $($responseContent | ConvertTo-Json -Compress)" -Level "DEBUG"
        return $true
    } catch [System.Net.WebException] {
        if ($_.Exception.Response) {
            $responseStatusCode = $_.Exception.Response.StatusCode.value__
            Write-Log "Health check failed with status ${responseStatusCode}: $($_.Exception.Message)" -Level "WARN"
        } else {
            Write-Log "Health check failed: $($_.Exception.Message)" -Level "ERROR"
        }
        return $false
    } catch {
        Write-Log "Unexpected error during health check: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

# Function to start Flask app
function Start-FlaskApp {
    param(
        [string]$scriptName = "test_flask.py"
    )
    
    Write-Log "Starting Flask application: $scriptName" -Level "INFO"
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $scriptName -NoNewWindow -PassThru -RedirectStandardOutput "flask_stdout.log" -RedirectStandardError "flask_stderr.log"
        Write-Log "Started Flask process with PID: $($process.Id)" -Level "DEBUG"
        
        # Wait for the server to start
        $maxAttempts = 10
        $attempt = 0
        $isReady = $false
        
        while ($attempt -lt $maxAttempts -and -not $isReady) {
            $attempt++
            Start-Sleep -Seconds 1
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    $isReady = $true
                    Write-Log "Flask application is now ready" -Level "INFO"
                }
            } catch {
                Write-Log "Waiting for Flask to start (attempt $attempt/$maxAttempts)..." -Level "DEBUG"
            }
        }
        
        if (-not $isReady) {
            Write-Log "Warning: Flask application did not become ready after $maxAttempts attempts" -Level "WARN"
        }
        
        return $process
    } catch {
        Write-Log "Failed to start Flask application: $($_.Exception.Message)" -Level "ERROR"
        throw
    }
}

# Main execution
Write-Log "=== Starting Flask Monitor ===" -Level "INFO"
Write-Log "Monitoring script: $($MyInvocation.MyCommand.Path)" -Level "INFO"
Write-Log "Flask script: $flaskScript" -Level "INFO"
Write-Log "Port: $port" -Level "INFO"
Write-Log "Log file: $logFile" -Level "INFO"

# Kill any existing Python processes
try {
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Log "Found $($pythonProcesses.Count) Python process(es) running. Stopping them..." -Level "WARN"
        $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Log "Error stopping Python processes: $($_.Exception.Message)" -Level "ERROR"
}

# Start Flask initially
try {
    $flaskProcess = Start-FlaskApp -scriptName $flaskScript
    
    # Main monitoring loop
    $checkCount = 0
    $consecutiveFailures = 0
    $maxConsecutiveFailures = 3
    
    while ($true) {
        $checkCount++
        Write-Log "Check #$checkCount" -Level "DEBUG"
        
        # Check if the process is still running
        if ($flaskProcess.HasExited) {
            $exitCode = $flaskProcess.ExitCode
            Write-Log "Flask process has exited with code $exitCode" -Level "ERROR"
            
            if ($consecutiveFailures -ge $maxConsecutiveFailures) {
                Write-Log "Too many consecutive failures ($consecutiveFailures). Exiting..." -Level "ERROR"
                exit 1
            }
            
            $consecutiveFailures++
            Write-Log "Restarting Flask (failure #$consecutiveFailures of $maxConsecutiveFailures)" -Level "WARN"
            $flaskProcess = Start-FlaskApp -scriptName $flaskScript
            continue
        }
        
        # Check health endpoint
        $isHealthy = Test-FlaskRunning
        
        if (-not $isHealthy) {
            $consecutiveFailures++
            Write-Log "Flask is not responding (failure #$consecutiveFailures of $maxConsecutiveFailures)" -Level "WARN"
            
            if ($consecutiveFailures -ge $maxConsecutiveFailures) {
                Write-Log "Too many consecutive failures. Restarting Flask process..." -Level "ERROR"
                
                # Kill any existing Python processes
                try {
                    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 1
                } catch {
                    Write-Log "Error stopping Python processes: $($_.Exception.Message)" -Level "ERROR"
                }
                
                # Reset failure counter
                $consecutiveFailures = 0
                
                # Start Flask again
                $flaskProcess = Start-FlaskApp -scriptName $flaskScript
            }
        } else {
            if ($consecutiveFailures -gt 0) {
                Write-Log "Flask is now responding normally" -Level "INFO"
                $consecutiveFailures = 0
            }
        }
        
        # Check more frequently when there are issues
        $sleepTime = if ($consecutiveFailures -gt 0) { 5 } else { 10 }
        Write-Log "Next check in $sleepTime seconds..." -Level "DEBUG"
        Start-Sleep -Seconds $sleepTime
    }
} catch {
    Write-Log "Fatal error in monitor: $($_.Exception.Message)" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    exit 1
} finally {
    Write-Log "=== Stopping Flask Monitor ===" -Level "INFO"
}
