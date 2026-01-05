# Docker Monitor Service Script
$serviceLog = "D:\dev\casestrainer\logs\docker-service.log"
$restartCount = 0
$maxRestarts = 10
$lastRestart = Get-Date

function Write-ServiceLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $serviceLog -Value $logEntry
}

function Restart-DockerIfNeeded {
    # Check if Docker is responding
    $null = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ServiceLog "Docker not responding - attempting restart"
        
        # Check restart rate limiting
        $now = Get-Date
        $hoursSinceLastRestart = ($now - $lastRestart).TotalHours
        
        if ($hoursSinceLastRestart -lt 1) {
            $restartCount++
            if ($restartCount -gt $maxRestarts) {
                Write-ServiceLog "Max restarts reached - waiting"
                return
            }
        } else {
            $restartCount = 1
        }
        
        # Stop Docker Desktop
        Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        
        # Start Docker Desktop
        Start-Process "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
        
        $lastRestart = $now
        Write-ServiceLog "Docker restart initiated"
        
        # Wait for Docker to be ready
        $waitTime = 0
        while ($waitTime -lt 300) {
            $null = docker info 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ServiceLog "Docker is ready"
                
                # Start containers
                Push-Location "D:\dev\casestrainer"
                docker-compose -f docker-compose.prod.yml up -d
                Pop-Location
                
                break
            }
            Start-Sleep -Seconds 10
            $waitTime += 10
        }
    }
}

# Main monitoring loop
Write-ServiceLog "Docker monitor service started"
while ($true) {
    Restart-DockerIfNeeded
    Start-Sleep -Seconds 60
}
