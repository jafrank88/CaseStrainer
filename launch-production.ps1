# PowerShell script for launching CaseStrainer in production with improved error handling
param(
    [Parameter()]
    [string]$Environment = "Production",
    
    [Parameter()]
    [string]$BackendPort = "5000",
    
    [Parameter()]
    [string]$FrontendPort = "443",
    
    [Parameter()]
    [string]$SSL_CERT = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\WolfCertBundle.crt",
    
    [Parameter()]
    [string]$SSL_KEY = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\wolf.law.uw.edu.key",
    
    [Parameter()]
    [string]$CORS_ORIGINS = "https://wolf.law.uw.edu",
    
    [Parameter()]
    [switch]$NoFrontend,
    
    [Parameter()]
    [switch]$NoSSL,

    [Parameter()]
    [string]$LogLevel = "INFO",

    [Parameter()]
    [int]$WaitressThreads = 4,

    [Parameter()]
    [string]$DatabasePath = "data/citations.db",

    [Parameter()]
    [switch]$SkipHealthCheck,

    [Parameter()]
    [int]$HealthCheckRetries = 20,

    [Parameter()]
    [int]$HealthCheckInterval = 5,

    [Parameter()]
    [switch]$EnableMetrics,

    [Parameter()]
    [string]$MetricsPort = "9090",

    [Parameter()]
    [switch]$VerboseLogging
)

# Global variables
$script:BackendProcess = $null
$script:NginxProcess = $null
$script:MetricsProcess = $null
$script:LogDirectory = "logs"

# Path to nginx executable
$nginxExe = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\nginx-1.27.5\nginx.exe"

# Cleanup function for graceful shutdown
function Stop-Services {
    Write-Host "Shutting down services gracefully..." -ForegroundColor Yellow
    
    if ($script:BackendProcess -and !$script:BackendProcess.HasExited) {
        Write-Host "Stopping Flask backend..." -ForegroundColor Yellow
        Stop-Process -Id $script:BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
        Write-Host "Stopping Nginx..." -ForegroundColor Yellow
        Stop-Process -Id $script:NginxProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($script:MetricsProcess -and !$script:MetricsProcess.HasExited) {
        Write-Host "Stopping metrics server..." -ForegroundColor Yellow
        Stop-Process -Id $script:MetricsProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "All services stopped." -ForegroundColor Green
}

# Register cleanup on script exit
Register-EngineEvent PowerShell.Exiting -Action { Stop-Services }

function Initialize-LogDirectory {
    if (!(Test-Path $script:LogDirectory)) {
        New-Item -ItemType Directory -Path $script:LogDirectory -Force | Out-Null
        Write-Host "Created log directory: $script:LogDirectory" -ForegroundColor Green
    }
}

function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Cyan
    
    # Check Python and Flask
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "  Python: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check if waitress is installed
    try {
        $waitressTest = python -c "import waitress; print('Waitress is installed')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Waitress: OK" -ForegroundColor Green
        } else {
            throw "Waitress import failed: $waitressTest"
        }
    }
    catch {
        Write-Error "Waitress is not installed. Run: pip install waitress"
        exit 1
    }
    
    # Check if Flask app exists
    if (!(Test-Path "src/app_final_vue.py")) {
        Write-Error "Flask src/app_final_vue.py not found in current directory"
        exit 1
    }
    
    # Test Flask app import
    try {
        $testImport = python -c "from src.app_final_vue import create_app; print('Flask app import successful')" 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Flask app import failed: $testImport"
        }
        Write-Host "  Flask app import: OK" -ForegroundColor Green
    }
    catch {
        Write-Error "Flask app cannot be imported: $_"
        exit 1
    }
    
    # Check Node.js and npm (if frontend is enabled)
    if (!$NoFrontend) {
        try {
            $nodeVersion = node --version 2>&1
            Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
        }
        catch {
            Write-Error "Node.js is not installed or not in PATH"
            exit 1
        }
        
        if (!(Test-Path "casestrainer-vue-new")) {
            Write-Error "Frontend directory 'casestrainer-vue-new' not found"
            exit 1
        }
    }
    
    # Check Nginx
    if (!(Test-Path $nginxExe)) {
        Write-Error "Nginx executable not found at: $nginxExe"
        exit 1
    }
    
    try {
        $nginxVersion = & $nginxExe -v 2>&1
        Write-Host "  Nginx: $nginxVersion" -ForegroundColor Green
    }
    catch {
        Write-Error "Nginx test failed: $_"
        exit 1
    }
    
    # Check SSL certificates if SSL is enabled
    if (!$NoSSL) {
        if ([string]::IsNullOrEmpty($SSL_CERT) -or [string]::IsNullOrEmpty($SSL_KEY)) {
            Write-Error "SSL certificates must be specified when SSL is enabled"
            exit 1
        }
        
        if (!(Test-Path $SSL_CERT)) {
            Write-Error "SSL certificate file not found: $SSL_CERT"
            exit 1
        }
        
        if (!(Test-Path $SSL_KEY)) {
            Write-Error "SSL key file not found: $SSL_KEY"
            exit 1
        }
        
        Write-Host "  SSL certificates validated" -ForegroundColor Green
    }
    
    Write-Host "Prerequisites check completed successfully" -ForegroundColor Green
}

function Start-Frontend {
    if ($NoFrontend) {
        Write-Host "Skipping frontend build (NoFrontend flag set)" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Building frontend for production..." -ForegroundColor Cyan
    
    Push-Location (Join-Path $PSScriptRoot "casestrainer-vue-new")
    try {
        Write-Host "  Installing dependencies..." -ForegroundColor Cyan
        npm ci 2>&1 | Tee-Object -FilePath "../$script:LogDirectory/npm_install.log"
        if ($LASTEXITCODE -ne 0) {
            throw "npm ci failed. Check $script:LogDirectory/npm_install.log"
        }
        
        Write-Host "  Building production assets..." -ForegroundColor Cyan
        
        # Clear NODE_ENV to avoid Vite issues - Vite will set it to production automatically for build
        $originalNodeEnv = $env:NODE_ENV
        $env:NODE_ENV = $null
        
        try {
            npm run build 2>&1 | Tee-Object -FilePath "../$script:LogDirectory/npm_build.log"
            if ($LASTEXITCODE -ne 0) {
                throw "npm run build failed. Check $script:LogDirectory/npm_build.log"
            }
        }
        finally {
            # Restore original NODE_ENV
            $env:NODE_ENV = $originalNodeEnv
        }
        
        Write-Host "Frontend build completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "Frontend build failed: $_"
        exit 1
    }
    finally {
        Pop-Location
    }
}

function Start-Backend {
    Write-Host "Starting Flask backend..." -ForegroundColor Cyan
    
    # Set environment variables
    $env:FLASK_ENV = $Environment.ToLower()
    $env:FLASK_APP = "src/app_final_vue.py"
    $env:CORS_ORIGINS = $CORS_ORIGINS
    $env:DATABASE_PATH = $DatabasePath
    $env:LOG_LEVEL = $LogLevel
    $env:PYTHONPATH = $PSScriptRoot  # Fix Python path issues
    
    # Create data directory if it doesn't exist
    $dataDir = Split-Path $DatabasePath -Parent
    if (![string]::IsNullOrEmpty($dataDir) -and !(Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force
        Write-Host "  Created data directory: $dataDir" -ForegroundColor Green
    }
    
    # Prepare log files
    $backendLogPath = Join-Path $script:LogDirectory "backend.log"
    $backendErrorPath = Join-Path $script:LogDirectory "backend_error.log"
    
    # Start Flask with Waitress (production WSGI server)
    # Use --call to invoke the factory function
    $waitressArgs = @(
        "--host=127.0.0.1"
        "--port=$BackendPort"
        "--threads=$WaitressThreads"
        "--call"
        "src.app_final_vue:create_app"
    )
    
    try {
        Write-Host "  Starting Waitress server on port $BackendPort with $WaitressThreads threads..." -ForegroundColor Cyan
        Write-Host "  Command: waitress-serve $($waitressArgs -join ' ')" -ForegroundColor Gray
        
        # Use simpler process startup without event handlers that might cause issues
        $script:BackendProcess = Start-Process -FilePath "waitress-serve" -ArgumentList $waitressArgs -NoNewWindow -PassThru -RedirectStandardOutput $backendLogPath -RedirectStandardError $backendErrorPath
        
        Write-Host "Flask backend started (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
        Write-Host "  Logs: $backendLogPath" -ForegroundColor Gray
        Write-Host "  Errors: $backendErrorPath" -ForegroundColor Gray
        
        # Give it a moment to settle
        Start-Sleep -Seconds 3
        
        # Check if process is still running
        if ($script:BackendProcess.HasExited) {
            $exitCode = $script:BackendProcess.ExitCode
            Write-Host "Backend error log:" -ForegroundColor Red
            if (Test-Path $backendErrorPath) {
                Get-Content $backendErrorPath | Write-Host -ForegroundColor Red
            }
            throw "Backend process exited immediately with code: $exitCode"
        }
        
        Write-Host "  Backend process is running successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to start Flask backend: $_"
        Write-Host "Check error log at: $backendErrorPath" -ForegroundColor Yellow
        if (Test-Path $backendErrorPath) {
            Write-Host "Error log contents:" -ForegroundColor Red
            Get-Content $backendErrorPath | Write-Host -ForegroundColor Red
        }
        exit 1
    }
}

function Test-BackendHealth {
    if ($SkipHealthCheck) {
        Write-Host "Skipping backend health check" -ForegroundColor Yellow
        return $true
    }
    
    Write-Host "Performing backend health check..." -ForegroundColor Cyan
    
    $healthUrls = @(
        "http://127.0.0.1:$BackendPort/casestrainer/api/health",
        "http://127.0.0.1:$BackendPort/health",
        "http://127.0.0.1:$BackendPort/"
    )
    
    $retries = 0
    
    while ($retries -lt $HealthCheckRetries) {
        foreach ($healthUrl in $healthUrls) {
            try {
                Write-Host "  Testing: $healthUrl" -ForegroundColor Gray
                $response = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
                Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
                
                if ($response.status -eq "healthy" -or $response.status -eq "ok" -or $response) {
                    Write-Host "Backend health check passed" -ForegroundColor Green
                    return $true
                }
            }
            catch {
                Write-Host "  Health check failed for $healthUrl : $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        $retries++
        if ($retries -lt $HealthCheckRetries) {
            Write-Host "  Health check attempt $retries failed, retrying in $HealthCheckInterval seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $HealthCheckInterval
        }
    }
    
    # Final test - just check if the port is responding
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ConnectAsync("127.0.0.1", $BackendPort).Wait(3000)
        if ($tcpClient.Connected) {
            Write-Host "Backend port $BackendPort is accepting connections" -ForegroundColor Green
            $tcpClient.Close()
            return $true
        }
    }
    catch {
        Write-Host "Port test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Error "Backend health check failed after $HealthCheckRetries attempts"
    Write-Host "Check backend logs at: $script:LogDirectory/backend_error.log" -ForegroundColor Yellow
    return $false
}

function Test-BackendDirectly {
    Write-Host "Testing backend directly..." -ForegroundColor Cyan
    
    $baseUrl = "http://127.0.0.1:$BackendPort"
    $testUrls = @(
        "$baseUrl/",
        "$baseUrl/api/",
        "$baseUrl/health",
        "$baseUrl/casestrainer/",
        "$baseUrl/casestrainer/api/",
        "$baseUrl/casestrainer/api/health"
    )
    
    foreach ($url in $testUrls) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
            Write-Host "  $url : $($response.StatusCode)" -ForegroundColor Green
            if ($url.EndsWith("/") -and $response.Content.Length -lt 200) {
                Write-Host "    Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))" -ForegroundColor DarkGray
            }
        }
        catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($statusCode) {
                Write-Host "  $url : $statusCode" -ForegroundColor Yellow
            } else {
                Write-Host "  $url : Connection failed - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

function New-NginxConfig {
    Write-Host "Generating Nginx configuration..." -ForegroundColor Cyan
    
    # Convert Windows paths to forward slashes and properly escape for nginx
    $frontendPath = (Join-Path $PSScriptRoot "casestrainer-vue-new/dist") -replace '\\', '/'
    $staticPath = (Join-Path $PSScriptRoot "casestrainer-vue-new/dist/static") -replace '\\', '/'
    $sslCertPath = $SSL_CERT -replace '\\', '/'
    $sslKeyPath = $SSL_KEY -replace '\\', '/'
    
    $sslBlock = ""
    if (!$NoSSL) {
        $sslBlock = @"
        # SSL Configuration
        ssl_certificate     "$sslCertPath";
        ssl_certificate_key "$sslKeyPath";
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;
"@
    }
    $listenLine = "listen       $FrontendPort" + $(if (!$NoSSL) { " ssl" } else { "" }) + ";"
    $http2Line = if (!$NoSSL) { "http2 on;" } else { "" }
    
    # Create logs directory for nginx
    $nginxLogsDir = "logs"
    if (!(Test-Path $nginxLogsDir)) {
        New-Item -ItemType Directory -Path $nginxLogsDir -Force | Out-Null
    }
    
    $nginxConfig = @"
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    # Logging settings
    access_log  logs/access.log;
    error_log   logs/error.log warn;

    server {
        $listenLine
        $http2Line
        server_name  wolf.law.uw.edu localhost;
$sslBlock        
        # Increase timeouts for large file uploads
        client_max_body_size 100M;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        fastcgi_read_timeout 300s;

        # Enhanced proxy settings
        proxy_intercept_errors on;
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        # Vue.js built assets
        location /casestrainer/assets/ {
            alias   "$frontendPath/assets/";
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files `$uri =404;
        }
        
        # Other static files
        location /casestrainer/vite.svg {
            alias   "$frontendPath/vite.svg";
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }

        # API routes - Flask handles the full /casestrainer/api/ path
        location /casestrainer/api/ {
            proxy_pass http://127.0.0.1:$BackendPort;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade `$http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Frontend routes - serve Vue.js app with SPA support
        location /casestrainer/ {
            alias   "$frontendPath/";
            index   index.html;
            try_files `$uri `$uri/ /casestrainer/index.html;
        }

        # Redirect root to casestrainer
        location = / {
            return 301 /casestrainer/;
        }

        # Error pages
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}
"@

    $configPath = "nginx.conf"
    # Remove any existing config file first
    if (Test-Path $configPath) {
        Remove-Item $configPath -Force
    }
    
    # Write file as ASCII to completely avoid BOM issues
    $nginxConfig | Out-File -FilePath $configPath -Encoding ASCII
    Write-Host "Nginx configuration saved to: $configPath" -ForegroundColor Green
    
    # Verify the file was created correctly
    if (Test-Path $configPath) {
        $firstLine = Get-Content $configPath -TotalCount 1
        Write-Host "First line of config: '$firstLine'" -ForegroundColor Gray
    }
    
    return $configPath
}

function Start-Nginx {
    $configPath = New-NginxConfig
    
    Write-Host "Starting Nginx..." -ForegroundColor Cyan
    
    try {
        # Test nginx configuration
        Write-Host "  Testing Nginx configuration..." -ForegroundColor Cyan
        $configTest = & $nginxExe -t -c (Resolve-Path $configPath).Path 2>&1
        Write-Host "  Config test result: $configTest" -ForegroundColor Gray
        
        if ($LASTEXITCODE -ne 0) {
            throw "Nginx configuration test failed: $configTest"
        }
        
        # Start nginx
        $nginxConfPath = (Resolve-Path $configPath).Path
        $nginxConfPathQuoted = '"' + $nginxConfPath + '"'
        
        $processStartInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processStartInfo.FileName = $nginxExe
        $processStartInfo.Arguments = "-c $nginxConfPathQuoted"
        $processStartInfo.UseShellExecute = $false
        $processStartInfo.WorkingDirectory = $PSScriptRoot
        
        $script:NginxProcess = New-Object System.Diagnostics.Process
        $script:NginxProcess.StartInfo = $processStartInfo
        $script:NginxProcess.Start()
        
        # Give nginx a moment to start
        Start-Sleep -Seconds 2
        
        Write-Host "Nginx started (PID: $($script:NginxProcess.Id))" -ForegroundColor Green
        
        if (!$NoSSL) {
            Write-Host "Server available at: https://localhost:$FrontendPort/casestrainer/" -ForegroundColor Green
        } else {
            Write-Host "Server available at: http://localhost:$FrontendPort/casestrainer/" -ForegroundColor Green
        }
    }
    catch {
        Write-Error "Failed to start Nginx: $_"
        Write-Host "Check nginx error log at: logs/error.log" -ForegroundColor Yellow
        exit 1
    }
}

function Start-MetricsServer {
    if (!$EnableMetrics) {
        return
    }
    
    Write-Host "Starting metrics server..." -ForegroundColor Cyan
    
    try {
        # Create a simple metrics server
        $metricsScript = @"
import http.server
import socketserver
import json
import time
from datetime import datetime

class MetricsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'uptime_seconds': int(time.time() - start_time),
                'port': $MetricsPort
            }
            self.wfile.write(json.dumps(metrics, indent=2).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Metrics endpoint: /metrics')

start_time = time.time()
print(f'Starting metrics server on port $MetricsPort')

with socketserver.TCPServer(('127.0.0.1', $MetricsPort), MetricsHandler) as httpd:
    httpd.serve_forever()
"@
        
        $metricsScriptPath = Join-Path $script:LogDirectory "metrics_server.py"
        $metricsScript | Out-File -FilePath $metricsScriptPath -Encoding UTF8
        
        $script:MetricsProcess = Start-Process -FilePath "python" -ArgumentList $metricsScriptPath -NoNewWindow -PassThru
        
        Write-Host "Metrics server started on port $MetricsPort (PID: $($script:MetricsProcess.Id))" -ForegroundColor Green
        Write-Host "  Metrics available at: http://localhost:$MetricsPort/metrics" -ForegroundColor Gray
    }
    catch {
        Write-Warning "Failed to start metrics server: $_"
    }
}

function Show-Status {
    Write-Host "`n=== CaseStrainer Production Server Status ===" -ForegroundColor Cyan
    Write-Host "Environment: $Environment" -ForegroundColor White
    Write-Host "Backend Port: $BackendPort" -ForegroundColor White
    Write-Host "Frontend Port: $FrontendPort" -ForegroundColor White
    Write-Host "SSL Enabled: $(!$NoSSL)" -ForegroundColor White
    Write-Host "Frontend Enabled: $(!$NoFrontend)" -ForegroundColor White
    Write-Host "Metrics Enabled: $EnableMetrics" -ForegroundColor White
    Write-Host "CORS Origins: $CORS_ORIGINS" -ForegroundColor White
    Write-Host "Database Path: $DatabasePath" -ForegroundColor White
    Write-Host "Log Directory: $script:LogDirectory" -ForegroundColor White
    
    if ($script:BackendProcess -and !$script:BackendProcess.HasExited) {
        Write-Host "Backend Status: Running (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "Backend Status: Stopped" -ForegroundColor Red
    }
    
    if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
        Write-Host "Nginx Status: Running (PID: $($script:NginxProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "Nginx Status: Stopped" -ForegroundColor Red
    }
    
    if ($EnableMetrics) {
        if ($script:MetricsProcess -and !$script:MetricsProcess.HasExited) {
            Write-Host "Metrics Status: Running (PID: $($script:MetricsProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "Metrics Status: Stopped" -ForegroundColor Red
        }
    }
    
    Write-Host "`nAccess URLs:" -ForegroundColor Cyan
    $protocol = if (!$NoSSL) { "https" } else { "http" }
    Write-Host "  Main App: $protocol`://localhost:$FrontendPort/casestrainer/" -ForegroundColor Green
    Write-Host "  API Base: $protocol`://localhost:$FrontendPort/casestrainer/api/" -ForegroundColor Green
    Write-Host "  Backend Direct: http://localhost:$BackendPort/" -ForegroundColor Green
    if ($EnableMetrics) {
        Write-Host "  Metrics: http://localhost:$MetricsPort/metrics" -ForegroundColor Green
    }
    
    Write-Host "`nLog Files:" -ForegroundColor Cyan
    Write-Host "  Backend: $script:LogDirectory/backend.log" -ForegroundColor Gray
    Write-Host "  Backend Errors: $script:LogDirectory/backend_error.log" -ForegroundColor Gray
    Write-Host "  Nginx Access: logs/access.log" -ForegroundColor Gray
    Write-Host "  Nginx Errors: logs/error.log" -ForegroundColor Gray
    
    Write-Host "=============================================" -ForegroundColor Cyan
}

function Show-TroubleshootingInfo {
    Write-Host "`n=== Troubleshooting Information ===" -ForegroundColor Yellow
    Write-Host "If you're experiencing issues:" -ForegroundColor White
    Write-Host "1. Check backend error log: $script:LogDirectory/backend_error.log" -ForegroundColor White
    Write-Host "2. Check nginx error log: logs/error.log" -ForegroundColor White
    Write-Host "3. Test backend directly: http://localhost:$BackendPort/" -ForegroundColor White
    Write-Host "4. Verify Flask app can start: python -c 'from src.app_final_vue import create_app; create_app()'" -ForegroundColor White
    Write-Host "5. Check if ports are available: netstat -an | findstr :$BackendPort" -ForegroundColor White
    Write-Host "=================================" -ForegroundColor Yellow
}

# Main execution
try {
    Write-Host "Starting CaseStrainer Production Server..." -ForegroundColor Green
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    
    # Initialize logging
    Write-Host "Step 1: Initializing logs..." -ForegroundColor Yellow
    Initialize-LogDirectory
    
    # Check prerequisites
    Write-Host "Step 2: Checking prerequisites..." -ForegroundColor Yellow
    Test-Prerequisites
    
    # Build frontend
    Write-Host "Step 3: Building frontend..." -ForegroundColor Yellow
    Start-Frontend
    
    # Start backend
    Write-Host "Step 4: Starting backend..." -ForegroundColor Yellow
    Start-Backend
    
    # Wait for backend to start
    Write-Host "Step 5: Waiting for backend to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Test backend directly
    Write-Host "Step 6: Testing backend..." -ForegroundColor Yellow
    Test-BackendDirectly
    
    # Health check
    Write-Host "Step 7: Health check..." -ForegroundColor Yellow
    if (!(Test-BackendHealth)) {
        Write-Warning "Backend health check failed, but continuing with startup..."
        Write-Host "You may need to check the backend logs and configuration." -ForegroundColor Yellow
    }
    
    # Start metrics server
    Write-Host "Step 8: Starting metrics server..." -ForegroundColor Yellow
    Start-MetricsServer
    
    # Start Nginx
    Write-Host "Step 9: Starting Nginx..." -ForegroundColor Yellow
    Start-Nginx
    
    # Show status
    Write-Host "Step 10: Showing status..." -ForegroundColor Yellow
    Show-Status
    
    Write-Host "`nProduction server is running. Press Ctrl+C to stop all services." -ForegroundColor Green
    
    if ($VerboseLogging) {
        Write-Host "`nVerbose logging is enabled - showing additional output." -ForegroundColor Yellow
    }
    
    Write-Host "Entering monitoring loop..." -ForegroundColor Yellow
    
    # Keep script running and monitor processes
    $lastStatusTime = Get-Date
    while ($true) {
        Start-Sleep -Seconds 10
        
        # Show periodic status in verbose mode
        if ($VerboseLogging -and ((Get-Date) - $lastStatusTime).TotalMinutes -gt 1) {
            Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Status check..." -ForegroundColor DarkCyan
            $lastStatusTime = Get-Date
        }
        
        # Check if any critical process has died
        if ($script:BackendProcess -and $script:BackendProcess.HasExited) {
            Write-Error "Backend process has exited unexpectedly (Exit Code: $($script:BackendProcess.ExitCode))"
            Show-TroubleshootingInfo
            break
        }
        
        if ($script:NginxProcess -and $script:NginxProcess.HasExited) {
            Write-Error "Nginx process has exited unexpectedly (Exit Code: $($script:NginxProcess.ExitCode))"
            Show-TroubleshootingInfo
            break
        }
        
        if ($EnableMetrics -and $script:MetricsProcess -and $script:MetricsProcess.HasExited) {
            Write-Warning "Metrics process has exited unexpectedly, restarting..."
            Start-MetricsServer
        }
    }
}
catch [System.Management.Automation.PipelineStoppedException] {
    Write-Host "`nReceived stop signal, shutting down..." -ForegroundColor Yellow
}
catch {
    Write-Error "Startup failed: $_"
    Write-Host "`nDetailed error information:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    Show-TroubleshootingInfo
    Stop-Services
    exit 1
}
finally {
    Stop-Services
}