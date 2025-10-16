# HealthCheck.psm1 - Health check functions

function Test-DockerHealth {
    [CmdletBinding()]
    param()
    
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            return $false
        }
        
        docker info >$null 2>&1
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        
        return $true
    } catch {
        return $false
    }
}

function Test-FrontendHealth {
    [CmdletBinding()]
    param()
    
    try {
        $distDir = Join-Path $PSScriptRoot "..\..\casestrainer-vue-new\dist\assets"
        
        if (-not (Test-Path $distDir)) {
            return $false
        }
        
        $distFiles = Get-ChildItem $distDir -File -ErrorAction SilentlyContinue
        if ($distFiles.Count -eq 0) {
            return $false
        }
        
        return $true
    } catch {
        return $false
    }
}

function Test-BackendHealth {
    [CmdletBinding()]
    param()
    
    try {
        if (Test-DockerHealth) {
            $backendRunning = docker ps --format '{{.Names}}' | Where-Object { $_ -eq 'casestrainer-backend-prod' }
            if (-not $backendRunning) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

function Test-ApplicationHealth {
    [CmdletBinding()]
    param()
    
    try {
        $healthUrl = "http://localhost:5000/api/health"
        $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Test-ComprehensiveHealth {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Comprehensive Health Check ===" -ForegroundColor Cyan
    
    $results = @{
        Docker = Test-DockerHealth
        Frontend = Test-FrontendHealth
        Backend = Test-BackendHealth
        Application = Test-ApplicationHealth
    }
    
    foreach ($component in $results.Keys) {
        $status = if ($results[$component]) { "OK" } else { "WARN" }
        $color = if ($results[$component]) { "Green" } else { "Yellow" }
        Write-Host "  $component`: $status" -ForegroundColor $color
    }
    
    $allHealthy = ($results.Values | Where-Object { $_ -eq $false }).Count -eq 0
    
    if ($allHealthy) {
        Write-Host "`nAll components healthy!" -ForegroundColor Green
    } else {
        Write-Host "`nSome components need attention" -ForegroundColor Yellow
    }
    
    return $results
}

Export-ModuleMember -Function @(
    'Test-DockerHealth',
    'Test-FrontendHealth',
    'Test-BackendHealth',
    'Test-ApplicationHealth',
    'Test-ComprehensiveHealth'
)
