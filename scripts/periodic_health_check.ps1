# CaseStrainer Periodic Health Check
# This runs every 2 hours as a backup to the main monitoring

$ErrorActionPreference = "Continue"
$logFile = Join-Path $PSScriptRoot "logs\periodic_health_check.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
}

Write-Log "=== PERIODIC HEALTH CHECK STARTED ===" "INFO"

# Check if Docker is responding
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Docker info failed - Docker may be frozen" "ERROR"
        
        # Try to restart Docker Desktop
        Write-Log "Attempting Docker Desktop restart..." "WARN"
        Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 60
        
        # Start containers
        Write-Log "Starting containers..." "INFO"
        Set-Location $PSScriptRoot
        docker-compose -f docker-compose.prod.yml up -d 2>&1
        Write-Log "Containers started" "SUCCESS"
    } else {
        # Check if containers are running
        $containers = docker ps --format "{{.Names}}" 2>&1
        $expectedContainers = @("casestrainer-backend-prod", "casestrainer-nginx-prod", "casestrainer-redis-prod")
        $allRunning = $true
        
        foreach ($expected in $expectedContainers) {
            if ($containers -notcontains $expected) {
                Write-Log "Container $expected not running" "WARN"
                $allRunning = $false
            }
        }
        
        if (-not $allRunning) {
            Write-Log "Some containers not running - starting..." "WARN"
            Set-Location $PSScriptRoot
            docker-compose -f docker-compose.prod.yml up -d 2>&1
            Write-Log "Containers started" "SUCCESS"
        } else {
            Write-Log "All containers healthy" "SUCCESS"
        }
    }
} catch {
    Write-Log "Health check error: $($_.Exception.Message)" "ERROR"
}

Write-Log "=== PERIODIC HEALTH CHECK COMPLETED ===" "INFO"
