# Check Server Status Script for CaseStrainer
# This script checks the status of all CaseStrainer services

# Function to check if a process is running
function Test-ProcessRunning {
    param([string]$processName)
    return [bool](Get-Process -Name $processName -ErrorAction SilentlyContinue)
}

# Function to check if a port is in use
function Test-PortInUse {
    param([int]$port)
    return [bool](Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue)
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param([string]$url, [string]$method = 'GET', [object]$body = $null)
    
    try {
        $params = @{
            Uri = $url
            Method = $method
            ErrorAction = 'Stop'
        }
        
        if ($body) {
            $params.Body = $body | ConvertTo-Json
            $params.ContentType = 'application/json'
        }
        
        $response = Invoke-WebRequest @params
        return @{
            StatusCode = $response.StatusCode
            StatusDescription = $response.StatusDescription
            Content = $response.Content
            Success = $true
        }
    }
    catch [System.Net.WebException] {
        return @{
            StatusCode = $_.Exception.Response.StatusCode.value__
            StatusDescription = $_.Exception.Response.StatusDescription
            Content = $_.ErrorDetails.Message
            Success = $false
        }
    }
    catch {
        return @{
            StatusCode = $null
            StatusDescription = $_.Exception.Message
            Content = $null
            Success = $false
        }
    }
}

# Clear the screen and display header
Clear-Host
Write-Host "=== CaseStrainer Server Status Check ===" -ForegroundColor Cyan
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Check Python processes
Write-Host "[PYTHON PROCESSES]" -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Python processes running:" -ForegroundColor Green
    $pythonProcesses | Select-Object Id, ProcessName, Path | Format-Table -AutoSize
} else {
    Write-Host "No Python processes found" -ForegroundColor Red
}

# Check Node.js processes
Write-Host "`n[NODE.JS PROCESSES]" -ForegroundColor Yellow
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "Node.js processes running:" -ForegroundColor Green
    $nodeProcesses | Select-Object Id, ProcessName, Path | Format-Table -AutoSize
} else {
    Write-Host "No Node.js processes found" -ForegroundColor Red
}

# Check Nginx
Write-Host "`n[NGINX]" -ForegroundColor Yellow
$nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "Nginx is running:" -ForegroundColor Green
    $nginxProcesses | Select-Object Id, ProcessName, Path | Format-Table -AutoSize
    
    # Check Nginx ports
    $nginxPorts = @(80, 443, 3000, 5000, 5001, 8000, 8080, 8443)
    Write-Host "`nChecking Nginx ports:"
    foreach ($port in $nginxPorts) {
        $portInUse = Test-PortInUse -port $port
        Write-Host "  Port $port : $(if ($portInUse) { 'IN USE' } else { 'available' })" -ForegroundColor $(if ($portInUse) { 'Green' } else { 'Gray' })
    }
} else {
    Write-Host "Nginx is not running" -ForegroundColor Red
}

# Check Flask backend
Write-Host "`n[FLASK BACKEND]" -ForegroundColor Yellow
$flaskPorts = @(5000, 5001)
$flaskRunning = $false

foreach ($port in $flaskPorts) {
    $portInUse = Test-PortInUse -port $port
    if ($portInUse) {
        $flaskRunning = $true
        Write-Host "Flask backend may be running on port $port" -ForegroundColor Green
        
        # Test Flask health endpoint
        $healthUrl = "http://localhost:$port/health"
        $healthCheck = Test-HttpEndpoint -url $healthUrl
        
        Write-Host "  Health check ($healthUrl): $($healthCheck.StatusCode) $($healthCheck.StatusDescription)" -ForegroundColor $(if ($healthCheck.Success) { 'Green' } else { 'Red' })
        
        # Test API version endpoint
        $versionUrl = "http://localhost:$port/api/version"
        $versionCheck = Test-HttpEndpoint -url $versionUrl
        
        Write-Host "  API version ($versionUrl): $($versionCheck.StatusCode) $($versionCheck.StatusDescription)" -ForegroundColor $(if ($versionCheck.Success) { 'Green' } else { 'Red' })
        
        if ($versionCheck.Success) {
            try {
                $versionInfo = $versionCheck.Content | ConvertFrom-Json
                Write-Host "  Version: $($versionInfo.version)" -ForegroundColor Cyan
                Write-Host "  Environment: $($versionInfo.environment)" -ForegroundColor Cyan
            } catch {
                Write-Host "  Could not parse version info" -ForegroundColor Yellow
            }
        }
    }
}

if (-not $flaskRunning) {
    Write-Host "Flask backend does not appear to be running on standard ports (5000, 5001)" -ForegroundColor Red
}

# Check Vue.js frontend (development server)
Write-Host "`n[VUE.JS FRONTEND]" -ForegroundColor Yellow
$vueDevServerPorts = @(3000, 8080, 5173)  # Common Vite/Webpack dev server ports
$vueRunning = $false

foreach ($port in $vueDevServerPorts) {
    $portInUse = Test-PortInUse -port $port
    if ($portInUse) {
        $vueRunning = $true
        Write-Host "Vue.js development server may be running on port $port" -ForegroundColor Green
        
        # Try to access the dev server
        $devServerUrl = "http://localhost:$port"
        $devServerCheck = Test-HttpEndpoint -url $devServerUrl
        
        Write-Host "  Dev server ($devServerUrl): $($devServerCheck.StatusCode) $($devServerCheck.StatusDescription)" -ForegroundColor $(if ($devServerCheck.Success) { 'Green' } else { 'Red' })
    }
}

if (-not $vueRunning) {
    Write-Host "Vue.js development server does not appear to be running on standard ports (3000, 8080, 5173)" -ForegroundColor Yellow
}

# Check Docker
Write-Host "`n[DOCKER]" -ForegroundColor Yellow
$dockerRunning = $false

try {
    $null = docker info 2>&1
    $dockerRunning = $true
    Write-Host "Docker is running" -ForegroundColor Green
    
    # Check for running containers
    $containers = docker ps --format "{{.Names}}" 2>$null
    if ($containers) {
        Write-Host "Running containers:" -ForegroundColor Green
        $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
    } else {
        Write-Host "No containers are running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Docker is not running or not installed" -ForegroundColor Red
}

# Check database
Write-Host "`n[DATABASE]" -ForegroundColor Yellow
$dbPath = Join-Path $PWD "citations.db"
if (Test-Path $dbPath) {
    $dbInfo = Get-Item $dbPath
    Write-Host "SQLite database found:" -ForegroundColor Green
    Write-Host "  Path: $($dbInfo.FullName)" -ForegroundColor Cyan
    Write-Host "  Size: $([math]::Round($dbInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "  Last modified: $($dbInfo.LastWriteTime)" -ForegroundColor Cyan
} else {
    Write-Host "SQLite database not found at expected location" -ForegroundColor Red
}

# Summary
Write-Host "`n[SUMMARY]" -ForegroundColor Yellow
$services = @(
    @{ Name = "Python"; Running = [bool]$pythonProcesses },
    @{ Name = "Node.js"; Running = [bool]$nodeProcesses },
    @{ Name = "Nginx"; Running = [bool]$nginxProcesses },
    @{ Name = "Flask Backend"; Running = $flaskRunning },
    @{ Name = "Vue.js Frontend"; Running = $vueRunning },
    @{ Name = "Docker"; Running = $dockerRunning }
)

$services | ForEach-Object {
    $status = if ($_.Running) { "RUNNING" } else { "STOPPED" }
    $color = if ($_.Running) { "Green" } else { "Red" }
    Write-Host "$($_.Name.PadRight(15)): $status" -ForegroundColor $color
}

Write-Host "`nStatus check completed at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
