# Docker Process Analyzer for CaseStrainer
# Identifies and distinguishes between legitimate Docker processes and potential zombie test processes

param(
    [switch]$Analyze,
    [switch]$KillZombies,
    [switch]$DryRun,
    [switch]$Verbose
)

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $(switch($Level) { 
        "ERROR" { "Red" } 
        "WARN" { "Yellow" } 
        "INFO" { "Green" } 
        "TEST" { "Cyan" } 
        default { "White" } 
    })
}

function Get-DockerProcessAnalysis {
    Write-Log "Analyzing Docker processes..." -Level "INFO"
    
    $allProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" -or $_.ProcessName -like "*com.docker*" }
    $legitimateProcesses = @()
    $suspiciousProcesses = @()
    
    foreach ($proc in $allProcesses) {
        $processInfo = [PSCustomObject]@{
            ProcessName = $proc.ProcessName
            Id = $proc.Id
            CPU = $proc.CPU
            WorkingSet = $proc.WorkingSet
            StartTime = $proc.StartTime
            CommandLine = ""
            IsLegitimate = $false
            Reason = ""
        }
        
        # Get command line
        try {
            $wmiProcess = Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)"
            $processInfo.CommandLine = $wmiProcess.CommandLine
        } catch {
            $processInfo.CommandLine = "Unable to retrieve"
        }
        
        # Analyze legitimacy
        $isLegitimate = $false
        $reason = ""
        
        switch ($proc.ProcessName) {
            "com.docker.backend" { 
                $isLegitimate = $true 
                $reason = "Docker Desktop backend service"
            }
            "Docker Desktop" { 
                $isLegitimate = $true 
                $reason = "Docker Desktop GUI"
            }
            "docker" {
                # Check if it's a legitimate Docker CLI vs test script
                if ($processInfo.CommandLine -like "*--version*" -or 
                    $processInfo.CommandLine -like "*info*" -or 
                    $processInfo.CommandLine -like "*ps*") {
                    $isLegitimate = $true
                    $reason = "Docker CLI command"
                } elseif ($processInfo.CPU -gt 0.1) {
                    $isLegitimate = $true
                    $reason = "Active Docker process"
                } else {
                    $reason = "Potentially zombie process (low CPU, no clear purpose)"
                }
            }
            default {
                $reason = "Unknown Docker-related process"
            }
        }
        
        $processInfo.IsLegitimate = $isLegitimate
        $processInfo.Reason = $reason
        
        if ($isLegitimate) {
            $legitimateProcesses += $processInfo
        } else {
            $suspiciousProcesses += $processInfo
        }
    }
    
    return @{
        Legitimate = $legitimateProcesses
        Suspicious = $suspiciousProcesses
    }
}

function Show-ProcessAnalysis {
    $analysis = Get-DockerProcessAnalysis
    
    Write-Log "=== DOCKER PROCESS ANALYSIS ===" -Level "INFO"
    
    Write-Log "LEGITIMATE PROCESSES:" -Level "INFO"
    foreach ($proc in $analysis.Legitimate) {
        Write-Log "  ✅ $($proc.ProcessName) (PID: $($proc.Id)) - $($proc.Reason)" -Level "INFO"
        if ($Verbose) {
            Write-Log "     CPU: $($proc.CPU), Memory: $($([math]::Round($proc.WorkingSet/1MB, 2)))MB, Start: $($proc.StartTime)" -Level "INFO"
            Write-Log "     Command: $($proc.CommandLine)" -Level "INFO"
        }
    }
    
    Write-Log "SUSPICIOUS/ZOMBIE PROCESSES:" -Level "WARN"
    foreach ($proc in $analysis.Suspicious) {
        Write-Log "  ⚠️  $($proc.ProcessName) (PID: $($proc.Id)) - $($proc.Reason)" -Level "WARN"
        Write-Log "     CPU: $($proc.CPU), Memory: $($([math]::Round($proc.WorkingSet/1MB, 2)))MB, Start: $($proc.StartTime)" -Level "WARN"
        Write-Log "     Command: $($proc.CommandLine)" -Level "WARN"
    }
    
    Write-Log "SUMMARY:" -Level "INFO"
    Write-Log "  Legitimate processes: $($analysis.Legitimate.Count)" -Level "INFO"
    Write-Log "  Suspicious processes: $($analysis.Suspicious.Count)" -Level "INFO"
    
    return $analysis
}

function Remove-SuspiciousProcesses {
    param($AnalysisResult)
    
    $killedCount = 0
    
    foreach ($proc in $AnalysisResult.Suspicious) {
        Write-Log "Killing suspicious process: $($proc.ProcessName) (PID: $($proc.Id))" -Level "TEST"
        
        if ($DryRun) {
            Write-Log "DRY RUN: Would kill process $($proc.Id)" -Level "TEST"
            $killedCount++
        } else {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Log "Successfully killed process $($proc.Id)" -Level "TEST"
                $killedCount++
            } catch {
                Write-Log "Failed to kill process $($proc.Id): $($_.Exception.Message)" -Level "ERROR"
            }
        }
    }
    
    Write-Log "Killed $killedCount suspicious processes" -Level "INFO"
    return $killedCount
}

# Main execution
Write-Log "Docker Process Analyzer started" -Level "INFO"

if ($Analyze) {
    $analysis = Show-ProcessAnalysis
    
    if ($KillZombies -and $analysis.Suspicious.Count -gt 0) {
        Write-Log "Killing suspicious processes..." -Level "WARN"
        Remove-SuspiciousProcesses -AnalysisResult $analysis
    }
} else {
    Write-Log "Use: -Analyze to see process analysis, -KillZombies to remove suspicious processes, -DryRun to preview actions" -Level "INFO"
}
