Write-Host "=== Docker Health Check ===" -ForegroundColor Cyan

# Check if Docker is running
docker info

Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
docker ps -a

Write-Host "`n=== Resource Usage ===" -ForegroundColor Cyan
docker stats --no-stream

Write-Host "`n=== System Resources ===" -ForegroundColor Cyan

# CPU Usage
$cpu = Get-Counter "\Processor(_Total)\% Processor Time" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
Write-Host "CPU Usage: $([math]::Round($cpu, 2))%" -ForegroundColor Green

# Memory Usage
$memory = Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
$totalMemory = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB
$memoryPercent = (($totalMemory - $memory) / $totalMemory) * 100
Write-Host "Memory Usage: $([math]::Round($memoryPercent, 2))%" -ForegroundColor Green

# Disk Usage
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object Size, FreeSpace
$diskPercent = (($disk.Size - $disk.FreeSpace) / $disk.Size) * 100
Write-Host "Disk Usage: $([math]::Round($diskPercent, 2))%" -ForegroundColor Green 