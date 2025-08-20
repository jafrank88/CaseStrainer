# Intelligent Docker Desktop GUI Auto-Restart Script
# Monitors GUI stability and restarts intelligently

$crashCount = 0
$maxCrashesPerHour = 5
$crashHistory = @()
$startTime = Get-Date

Write-Host "Starting intelligent Docker Desktop GUI monitor..." -ForegroundColor Green
Write-Host "Max crashes per hour: $maxCrashesPerHour" -ForegroundColor Yellow

while ($true) {
    $currentTime = Get-Date
    
    # Clean old crash history (older than 1 hour)
    $crashHistory = $crashHistory | Where-Object { $currentTime - $_ -lt [TimeSpan]::FromHours(1) }
    
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    
    if ($dockerProcesses.Count -eq 0) {
        $crashCount++
        $crashHistory += $currentTime
        
        Write-Host "[$($currentTime.ToString('HH:mm:ss'))] GUI CRASHED! (Crash #$crashCount in last hour)" -ForegroundColor Red
        
        if ($crashHistory.Count -le $maxCrashesPerHour) {
            Write-Host "  Attempting intelligent restart..." -ForegroundColor Yellow
            
            # Wait a bit before restarting to avoid rapid restart loops
            Start-Sleep -Seconds ([Math]::Min(30, $crashCount * 10))
            
            # Start Docker Desktop with minimal settings
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
            
            # Wait longer for restart
            Start-Sleep -Seconds ([Math]::Min(60, $crashCount * 15))
        } else {
            Write-Host "  Too many crashes in last hour. Waiting 5 minutes before restart..." -ForegroundColor Red
            Start-Sleep -Seconds 300
            $crashHistory.Clear()
            $crashCount = 0
        }
    } else {
        $processAge = $currentTime - $dockerProcesses[0].StartTime
        if ($processAge.TotalMinutes -gt 5) {
            Write-Host "[$($currentTime.ToString('HH:mm:ss'))] GUI: Stable (PID: $($dockerProcesses[0].Id), Age: $($processAge.ToString('mm\:ss')))" -ForegroundColor Green
        }
    }
    
    Start-Sleep -Seconds 10
}
