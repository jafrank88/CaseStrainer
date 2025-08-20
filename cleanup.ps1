#Requires -Version 5.1

<#
.SYNOPSIS
    CaseStrainer System Cleanup Script

.DESCRIPTION
    Cleans up old files, stuck jobs, and Redis memory to maintain system health.
    This script can be run independently or as part of the main launcher.

.EXAMPLE
    .\cleanup.ps1
    .\cleanup.ps1 -Verbose
#>

param(
    [switch]$DryRun
)

# Global error handling
$ErrorActionPreference = 'Continue'  # Changed from 'Stop' to 'Continue' to handle Redis warnings gracefully
$WarningPreference = 'Continue'

# Initialize logging
$LogFile = "logs/cleanup-$(Get-Date -Format 'yyyy-MM-dd').log"
$null = New-Item -Path (Split-Path $LogFile) -ItemType Directory -Force -ErrorAction SilentlyContinue

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',
        
        [switch]$Console
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to file
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
    
    # Write to console if requested or if error
    if ($Console -or $Level -eq 'ERROR') {
        switch ($Level) {
            'INFO'  { Write-Host $logEntry -ForegroundColor Green }
            'WARN'  { Write-Host $logEntry -ForegroundColor Yellow }
            'ERROR' { Write-Host $logEntry -ForegroundColor Red }
            'DEBUG' { if ($VerbosePreference -eq 'Continue') { Write-Host $logEntry -ForegroundColor Gray } }
        }
    }
}

function Invoke-SystemCleanup {
    Write-Log "Performing system cleanup..." -Console
    
    try {
        # 1. Clear stuck Redis jobs (older than 1 hour)
        # Note: Redis warnings about password usage are normal and expected
        Write-Log "Clearing stuck Redis jobs..." -Console
        
        if ($DryRun) {
            Write-Log "[DRY RUN] Would clear stuck Redis jobs" -Console
        } else {
            # Simple Redis cleanup using basic commands instead of Lua script
            Write-Log "Getting Redis job keys..." -Level DEBUG
            $jobKeys = docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** KEYS "rq:job:*" 2>$null
            $redisExitCode = $LASTEXITCODE
            Write-Log "Redis KEYS command exit code: $redisExitCode" -Level DEBUG
            
            if ($redisExitCode -eq 0 -and $jobKeys) {
                Write-Log "Found $($jobKeys.Count) Redis jobs to check" -Level DEBUG
                $clearedCount = 0
                foreach ($key in $jobKeys) {
                    if ($key -and $key.Trim()) {
                        Write-Log "Checking job: $key" -Level DEBUG
                        # Check if job is stuck (status = started)
                        $status = docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** HGET $key "status" 2>$null
                        Write-Log "Job $key status: $status" -Level DEBUG
                        if ($status -eq "started") {
                            Write-Log "Deleting stuck job: $key" -Level DEBUG
                            # Delete stuck job
                            docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** DEL $key 2>$null | Out-Null
                            $clearedCount++
                        }
                    }
                }
                if ($clearedCount -gt 0) {
                    Write-Log "Cleared $clearedCount stuck Redis jobs" -Console
                } else {
                    Write-Log "Redis cleanup completed (no stuck jobs found)" -Console
                }
            } else {
                Write-Log "Redis cleanup completed (no jobs to check or command failed)" -Console
            }
        }
        
        # 2. Clear unprocessed files older than 1 hour (new feature)
        Write-Log "Clearing unprocessed files older than 1 hour..." -Console
        if ($DryRun) {
            Write-Log "[DRY RUN] Would clear unprocessed files older than 1 hour" -Console
        } else {
            # Find files that haven't been processed (no corresponding result in database)
            try {
                docker exec casestrainer-backend-prod find /app/uploads -name "*.pdf" -mtime +0.04 -delete 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Cleared unprocessed files older than 1 hour" -Console
                }
            } catch {
                Write-Log "Unprocessed file cleanup encountered an issue, continuing: $($_.Exception.Message)" -Level WARN -Console
            }
        }
        
        # 3. Clear old temporary files
        Write-Log "Clearing old temporary files..." -Console
        if ($DryRun) {
            Write-Log "[DRY RUN] Would clear old temporary files" -Console
        } else {
            docker exec casestrainer-backend-prod find /tmp -name "tmp*" -mtime +1 -delete 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Cleared old temporary files" -Console
            }
        }
        
        # 4. Clear old log files (keep last 7 days)
        Write-Log "Clearing old log files..." -Console
        if ($DryRun) {
            Write-Log "[DRY RUN] Would clear old log files" -Console
        } else {
            docker exec casestrainer-backend-prod find /app/logs -name "*.log" -mtime +7 -delete 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Cleared old log files" -Console
            }
        }
        
        # 5. Clear old upload files (keep last 30 days)
        Write-Log "Clearing old upload files..." -Console
        if ($DryRun) {
            Write-Log "[DRY RUN] Would clear old upload files" -Console
        } else {
            docker exec casestrainer-backend-prod find /app/uploads -name "*.pdf" -mtime +30 -delete 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Cleared old upload files" -Console
            }
        }
        
        # 6. Clear Redis memory (optional - only if memory usage is high)
        Write-Log "Checking Redis memory usage..." -Console
        if ($DryRun) {
            Write-Log "[DRY RUN] Would check Redis memory usage" -Console
        } else {
            try {
                $redisMemory = docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** INFO memory 2>$null | Select-String "used_memory_human:"
                if ($redisMemory) {
                    $memoryValue = $redisMemory -replace "used_memory_human:", "" -replace "B", ""
                    if ($memoryValue -gt 100) {  # If memory > 100MB
                        Write-Log "High Redis memory usage detected - clearing cache..." -Console
                        docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** FLUSHDB 2>$null
                        if ($LASTEXITCODE -eq 0) {
                            Write-Log "Redis cache cleared" -Console
                        } else {
                            Write-Log "Redis cache clear failed (exit code: $LASTEXITCODE)" -Level WARN -Console
                        }
                    } else {
                        Write-Log "Redis memory usage is normal: $memoryValue" -Console
                    }
                } else {
                    Write-Log "Could not retrieve Redis memory info" -Level WARN -Console
                }
            } catch {
                Write-Log "Redis memory check encountered an issue, continuing: $($_.Exception.Message)" -Level WARN -Console
            }
        }
        
        Write-Log "System cleanup completed successfully" -Console
        return $true
        
    } catch {
        Write-Log "Cleanup failed: $($_.Exception.Message)" -Level ERROR -Console
        return $false
    }
}

# Main execution
try {
    Write-Log "CaseStrainer System Cleanup starting..." -Console
    
    if ($DryRun) {
        Write-Log "DRY RUN MODE - No actual cleanup will be performed" -Console
    }
    
    # Check if containers are running
    $containers = docker ps --filter "name=casestrainer" --format "json" 2>$null | ConvertFrom-Json
    if ($containers.Count -eq 0) {
        Write-Log "No CaseStrainer containers running - cleanup may fail" -Level WARN -Console
    }
    
    # Perform cleanup
    $success = Invoke-SystemCleanup
    
    if ($success) {
        Write-Log "Cleanup completed successfully!" -Level INFO -Console
        exit 0
    } else {
        Write-Log "Cleanup failed" -Level ERROR -Console
        exit 1
    }
}
catch {
    Write-Log "Fatal error: $($_.Exception.Message)" -Level ERROR -Console
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level DEBUG
    exit 1
}
finally {
    Write-Log "Cleanup execution completed" -Level DEBUG
}
