# Add cleanup function to cslaunch.ps1

$scriptPath = ".\cslaunch.ps1"
$content = Get-Content $scriptPath -Raw

$cleanupFunction = @'

function Remove-StaleContainers {
    <#
    .SYNOPSIS
        Removes stale CaseStrainer containers that are in Created/Exited/Dead state.
    #>
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    
    Write-Host "`n=== Cleaning up stale containers ===" -ForegroundColor Cyan
    
    # Get all CaseStrainer containers
    $containers = docker ps -a --filter name=casestrainer --format "{{.ID}}`t{{.Names}}`t{{.Status}}" 2>$null
    
    if (-not $containers) {
        Write-Host "No CaseStrainer containers found." -ForegroundColor Green
        return
    }
    
    # Find stale containers
    $staleContainers = @()
    foreach ($line in $containers) {
        $parts = $line -split "`t"
        if ($parts.Count -ge 3) {
            $id = $parts[0].Trim()
            $name = $parts[1].Trim()
            $status = $parts[2].Trim()
            
            if ($status -eq "Created" -or $status -like "Exited*" -or $status -like "Dead*") {
                $staleContainers += @{
                    ID = $id
                    Name = $name
                    Status = $status
                }
            }
        }
    }
    
    if ($staleContainers.Count -eq 0) {
        Write-Host "✓ No stale containers found." -ForegroundColor Green
        return
    }
    
    Write-Host "Found $($staleContainers.Count) stale containers:" -ForegroundColor Yellow
    foreach ($container in $staleContainers) {
        Write-Host "  - $($container.Name) ($($container.Status))" -ForegroundColor Gray
    }
    
    # Remove with confirmation or force
    if ($PSCmdlet.ShouldProcess($staleContainers.Count.ToString() + " stale containers", "Remove")) {
        foreach ($container in $staleContainers) {
            try {
                Write-Host "Removing $($container.Name)..." -ForegroundColor Gray
                docker rm $container.ID | Out-Null
                Write-Host "✓ Removed" -ForegroundColor Green
            } catch {
                Write-Host "✗ Failed to remove: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}
'@

# Insert the function before the parameter block
$insertPoint = $content.IndexOf("[CmdletBinding()]")
if ($insertPoint -gt 0) {
    $content = $content.Substring(0, $insertPoint) + $cleanupFunction + "`n" + $content.Substring($insertPoint)
    Set-Content -Path $scriptPath -Value $content -Encoding UTF8
    Write-Host "[OK] Added Remove-StaleContainers function to cslaunch.ps1" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Could not find insertion point" -ForegroundColor Red
}

# Also add it to the parameter list as a switch
$pattern = '\[switch\]\$NoMonitor'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$0`n    [switch]`$Cleanup"
    Set-Content -Path $scriptPath -Value $content -Encoding UTF8
    Write-Host "[OK] Added -Cleanup parameter" -ForegroundColor Green
}

Write-Host "`nUsage: .\cslaunch.ps1 -Cleanup" -ForegroundColor Gray
