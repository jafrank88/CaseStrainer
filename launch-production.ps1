# PowerShell script for launching CaseStrainer in production
param(
    [Parameter()]
    [string]$Environment = "Production",
    
    [Parameter()]
    [string]$BackendPort = "5000",
    
    [Parameter()]
    [string]$FrontendPort = "80",
    
    [Parameter()]
    [string]$SSL_CERT = "",
    
    [Parameter()]
    [string]$SSL_KEY = "",
    
    [Parameter()]
    [string]$CORS_ORIGINS = "https://wolf.law.uw.edu",
    
    [Parameter()]
    [switch]$NoFrontend,
    
    [Parameter()]
    [switch]$NoSSL
)

# Error handling
$ErrorActionPreference = 'Stop'
$script:ProcessesToCleanup = @()

# Configuration
$config = @{
    Environment = $Environment
    BackendPath = "src/app_final_vue.py"
    FrontendPath = "casestrainer-vue-new"
    BackendPort = [int]$BackendPort
    FrontendPort = [int]$FrontendPort
    BackendUrl = "http://localhost:${BackendPort}"
    FrontendUrl = "http://localhost:${FrontendPort}"
    HealthCheckEndpoint = "/api/health"
    LogLevel = "INFO"
    WaitressThreads = 4
}

# Functions
function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host "          CASESTRAINER PRODUCTION LAUNCHER" -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Environment: $($config.Environment)" -ForegroundColor Yellow
    Write-Host "  Backend:    $($config.BackendUrl)" -ForegroundColor Cyan
    Write-Host "  Frontend:   $($config.FrontendUrl)" -ForegroundColor Cyan
    Write-Host "  SSL:        $(if ($NoSSL) { 'Disabled' } else { 'Enabled' })" -ForegroundColor Cyan
    Write-Host "  Frontend:   $(if ($NoFrontend) { 'Disabled' } else { 'Enabled' })" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Starting services..." -ForegroundColor Gray
    Write-Host ""
}

function Test-Dependencies {
    Write-Host "Checking dependencies..." -ForegroundColor Cyan
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Host "  Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check required Python packages
    $requiredPackages = @("flask", "waitress", "flask-cors")
    foreach ($package in $requiredPackages) {
        try {
            python -c "import $($package.Replace('-', '_'))" 2>$null
            Write-Host "  Python package '$package': OK" -ForegroundColor Green
        } catch {
            Write-Error "Required Python package '$package' is not installed"
            exit 1
        }
    }
    
    # Check Node.js if frontend is enabled
    if (-not $NoFrontend) {
        try {
            $nodeVersion = node --version
            Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
        } catch {
            Write-Error "Node.js is not installed or not in PATH"
            exit 1
        }
    }
}

function Start-Backend {
    Write-Host "Starting backend server..." -ForegroundColor Green
    
    # Set environment variables
    $env:FLASK_ENV = "production"
    $env:FLASK_APP = 'src.app_final_vue:create_app()'
    $env:FLASK_DEBUG = "0"
    $env:PYTHONUNBUFFERED = "1"
    $env:HOST = "0.0.0.0"
    $env:PORT = $config.BackendPort
    $env:WAITRESS_THREADS = $config.WaitressThreads
    $env:CORS_ORIGINS = $CORS_ORIGINS
    
    # Set SSL configuration if enabled
    if (-not $NoSSL) {
        if ([string]::IsNullOrEmpty($SSL_CERT) -or [string]::IsNullOrEmpty($SSL_KEY)) {
            Write-Error "SSL is enabled but certificate paths are not provided"
            exit 1
        }
        if (-not (Test-Path $SSL_CERT) -or -not (Test-Path $SSL_KEY)) {
            Write-Error "SSL certificate or key file not found"
            exit 1
        }
        $env:SSL_CERT = $SSL_CERT
        $env:SSL_KEY = $SSL_KEY
    }
    
    # Start the production server
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "src.run_production" -PassThru -NoNewWindow
        $script:ProcessesToCleanup += $process
        Write-Host "  Backend started with PID: $($process.Id)" -ForegroundColor Green
        return $process
    } catch {
        Write-Error "Failed to start backend server: $_"
        exit 1
    }
}

function Start-Frontend {
    if (-not (Test-Path $config.FrontendPath)) {
        Write-Error "Frontend directory not found at $($config.FrontendPath)"
        exit 1
    }
    
    Write-Host "Building frontend for production..." -ForegroundColor Green
    
    try {
        Push-Location $config.FrontendPath
        
        # Install dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Host "  Installing frontend dependencies..." -ForegroundColor Cyan
            npm install
        }
        
        # Build for production
        Write-Host "  Building production assets..." -ForegroundColor Cyan
        npm run build
        
        # Start production server
        Write-Host "  Starting production server..." -ForegroundColor Cyan
        $process = Start-Process -FilePath "npx" -ArgumentList "http-server", "dist", "-p", $config.FrontendPort, "-c-1" -PassThru -NoNewWindow
        $script:ProcessesToCleanup += $process
        
        Write-Host "  Frontend started with PID: $($process.Id)" -ForegroundColor Green
        return $process
    } catch {
        Write-Error "Failed to start frontend: $_"
        exit 1
    } finally {
        Pop-Location
    }
}

function Test-BackendHealth {
    param (
        [string]$BaseUrl,
        [string]$Endpoint,
        [int]$MaxRetries = 10,
        [int]$RetryDelay = 2
    )
    
    $url = "$BaseUrl$Endpoint"
    $retryCount = 0
    
    Write-Host "Checking backend health at $url" -ForegroundColor Cyan
    
    while ($retryCount -lt $MaxRetries) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $status = $response.Content | ConvertFrom-Json
                Write-Host "  Backend is healthy: $($status.status)" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "  Attempt $($retryCount + 1) of $MaxRetries failed: $($_.Exception.Message)" -ForegroundColor Yellow
            $retryCount++
            if ($retryCount -lt $MaxRetries) {
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }
    
    Write-Error "Failed to connect to backend after $MaxRetries attempts"
    return $false
}

function Stop-ProcessesOnPort {
    param ([int]$Port)
    
    Write-Host "Checking for processes on port $Port..." -ForegroundColor Cyan
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                Where-Object { $_.State -eq 'Listen' } | 
                Select-Object -ExpandProperty OwningProcess -Unique
    
    if ($processes) {
        Write-Host "  Found processes on port $Port, stopping them..." -ForegroundColor Yellow
        foreach ($pid in $processes) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "    Stopped process $pid" -ForegroundColor Green
            } catch {
                Write-Host "    Failed to stop process $pid: $_" -ForegroundColor Red
            }
        }
    }
}

# Cleanup function
function Cleanup {
    Write-Host "`nCleaning up processes..." -ForegroundColor Yellow
    foreach ($process in $script:ProcessesToCleanup) {
        if ($process -and -not $process.HasExited) {
            try {
                Stop-Process -Id $process.Id -Force
                Write-Host "  Stopped process $($process.Id)" -ForegroundColor Green
            } catch {
                Write-Host "  Failed to stop process $($process.Id): $_" -ForegroundColor Red
            }
        }
    }
}

# Register cleanup on script exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

# Main execution
try {
    # Show header
    Show-Header
    
    # Check dependencies
    Test-Dependencies
    
    # Stop any existing processes
    Stop-ProcessesOnPort -Port $config.BackendPort
    Stop-ProcessesOnPort -Port $config.FrontendPort
    
    # Start backend
    Start-Backend
    
    # Wait for backend to start
    Start-Sleep -Seconds 2
    
    # Test backend health
    $backendHealthy = Test-BackendHealth -BaseUrl $config.BackendUrl -Endpoint $config.HealthCheckEndpoint
    
    if (-not $backendHealthy) {
        throw "Backend health check failed"
    }
    
    # Start frontend if enabled
    if (-not $NoFrontend) {
        Start-Frontend
    }
    
    # Show final status
    Write-Host "`n===================================================" -ForegroundColor Green
    Write-Host "          CASESTRAINER $($config.Environment.ToUpper()) STATUS" -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Backend:   Running on $($config.BackendUrl)" -ForegroundColor Green
    if (-not $NoFrontend) {
        Write-Host "  Frontend:  Running on $($config.FrontendUrl)" -ForegroundColor Green
    }
    Write-Host "  SSL:       $(if ($NoSSL) { 'Disabled' } else { 'Enabled' })" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    
    # Keep script running
    Wait-Event
    
} catch {
    Write-Error "Error: $_"
    Cleanup
    exit 1
}
