# cslaunch.ps1 - Quick restart wrapper for production environment
# This is optimized for fast Python code updates without rebuilding Docker images

param(
    [switch]$Build,
    [switch]$Force,
    [switch]$NoCache
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Quick Restart (./cslaunch)" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if containers are already running
$containers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })

if ($containers.Count -gt 0 -and -not $Build -and -not $Force) {
    Write-Host "[OK] Found $($containers.Count) running containers" -ForegroundColor Green
    
    # Check if frontend needs rebuilding (Vue dist files changed)
    $needsFrontendRebuild = $false
    if (Test-Path "casestrainer-vue-new\dist") {
        $vueDistTime = (Get-Item "static\vue\index.html" -ErrorAction SilentlyContinue).LastWriteTime
        $containerDistTime = docker exec casestrainer-frontend-prod stat -c %Y /usr/share/nginx/html/index.html 2>$null
        
        if ($vueDistTime -and $containerDistTime) {
            $containerTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$containerDistTime).LocalDateTime
            if ($vueDistTime -gt $containerTime) {
                Write-Host "[DETECT] Vue frontend files updated - rebuild needed" -ForegroundColor Yellow
                $needsFrontendRebuild = $true
            }
        }
    }
    
    if ($needsFrontendRebuild) {
        Write-Host "[FRONTEND REBUILD] Rebuilding frontend container with latest Vue files..." -ForegroundColor Yellow
        Write-Host ""
        
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        docker-compose -f docker-compose.prod.yml up -d --build frontend-prod
        $sw.Stop()
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Frontend rebuilt in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            
            # Wait for services to be ready
            Write-Host "`n[WAIT] Ensuring services are ready..." -ForegroundColor Yellow
            try {
                $waitScript = Join-Path $PSScriptRoot 'scripts\wait-for-services.py'
                if (Test-Path $waitScript) {
                    docker cp $waitScript casestrainer-backend-prod:/app/wait-for-services.py 2>$null
                    $output = docker exec casestrainer-backend-prod python /app/wait-for-services.py 2>&1
                    $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                }
            } catch {
                Write-Host "  [WARNING] Service check failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            Write-Host "`n[SUCCESS] Frontend rebuild complete - All services ready!" -ForegroundColor Green
            Write-Host "  Vue changes are now active" -ForegroundColor DarkGray
            Write-Host "  Application: http://localhost" -ForegroundColor Cyan
            exit 0
        } else {
            Write-Host "`n[ERROR] Frontend rebuild failed" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[QUICK RESTART] Restarting containers (10-15 seconds)..." -ForegroundColor Yellow
        Write-Host ""
        
        # CRITICAL: Clear Python bytecode cache before restart to ensure code changes are picked up
        Write-Host "[CACHE CLEAR] Clearing Python bytecode cache..." -ForegroundColor Yellow
        try {
            # Clear __pycache__ on HOST (volume mount)
            Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            
            # Clear .pyc files on HOST
            Get-ChildItem -Path "src" -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
            }
            
            # ALSO clear cache INSIDE container before restart
            Write-Host "  Clearing cache inside containers..." -ForegroundColor Yellow
            docker exec casestrainer-backend-prod find /app/src -type d -name '__pycache__' -exec rm -rf {} + 2>$null
            docker exec casestrainer-backend-prod find /app/src -name '*.pyc' -delete 2>$null
            
            Write-Host "  ✅ Python cache cleared (host + containers)" -ForegroundColor Green
        } catch {
            Write-Host "  [WARNING] Could not clear all cache: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # REBUILD backend AND workers to ensure absolutely fresh code
        Write-Host "[REBUILD] Rebuilding backend + workers for clean deployment..." -ForegroundColor Yellow
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
        $sw.Stop()
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Backend + workers rebuilt and deployed in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            
            # CRITICAL: Restart nginx routing container to pick up new backend IP
            Write-Host "`n[NGINX] Restarting nginx routing container for DNS refresh..." -ForegroundColor Yellow
            docker restart casestrainer-nginx-prod > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Nginx routing container restarted" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Warning: Could not restart nginx (container may not exist)" -ForegroundColor Yellow
            }
            
            # NOW wait for services to be ready (after restart)
            Write-Host "`n[WAIT] Ensuring services are ready..." -ForegroundColor Yellow
            $servicesReady = $false
            try {
                $waitScript = Join-Path $PSScriptRoot 'scripts\wait-for-services.py'
                if (Test-Path $waitScript) {
                    docker cp $waitScript casestrainer-backend-prod:/app/wait-for-services.py 2>$null
                    $output = docker exec casestrainer-backend-prod python /app/wait-for-services.py 2>&1
                    $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                    
                    # Check exit code
                    if ($LASTEXITCODE -eq 0) {
                        $servicesReady = $true
                    }
                }
            } catch {
                Write-Host "  [WARNING] Service check failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Clean up stuck RQ jobs (only if services are ready)
            if ($servicesReady) {
                Write-Host "`n[CLEANUP] Cleaning up any stuck RQ jobs..." -ForegroundColor Yellow
                try {
                    $cleanupScript = Join-Path $PSScriptRoot 'scripts\cleanup-stuck-jobs.py'
                    if (Test-Path $cleanupScript) {
                        docker cp $cleanupScript casestrainer-backend-prod:/app/cleanup-stuck-jobs.py 2>$null
                        $output = docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py 2>&1
                        $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                    }
                } catch {
                    Write-Host "  [WARNING] Cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
                }
                
                # USER REQUESTED: Clear all caches for fresh testing
                Write-Host "`n[CACHE CLEAR] Clearing Redis and file caches..." -ForegroundColor Yellow
                try {
                    # Clear Redis cache (ALL databases - 0: RQ queue, 1: citation cache, 2: URL cache, 3: session data)
                    Write-Host "  🗑️  Clearing Redis caches (databases 0, 1, 2, 3)..." -ForegroundColor Gray
                    
                    # Database 0: RQ queue
                    $redisKeys0 = docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=0); keys=r.keys('*'); print(len(keys))" 2>$null
                    docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=0); r.flushdb()" 2>$null | Out-Null
                    
                    # Database 1: Citation cache
                    $redisKeys1 = docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=1); keys=r.keys('*'); print(len(keys))" 2>$null
                    docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=1); r.flushdb()" 2>$null | Out-Null
                    
                    # Database 2: URL/PDF cache
                    $redisKeys2 = docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=2); keys=r.keys('*'); print(len(keys))" 2>$null
                    docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=2); r.flushdb()" 2>$null | Out-Null
                    
                    # Database 3: Session data
                    $redisKeys3 = docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=3); keys=r.keys('*'); print(len(keys))" 2>$null
                    docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=3); r.flushdb()" 2>$null | Out-Null
                    
                    $totalKeys = [int]$redisKeys0 + [int]$redisKeys1 + [int]$redisKeys2 + [int]$redisKeys3
                    if ($totalKeys -gt 0) {
                        Write-Host "  ✅ Cleared $totalKeys Redis keys (DB0: $redisKeys0, DB1: $redisKeys1, DB2: $redisKeys2, DB3: $redisKeys3)" -ForegroundColor Green
                    } else {
                        Write-Host "  ✅ Redis caches already empty" -ForegroundColor Green
                    }
                    
                    # Clear file-based caches
                    Write-Host "  🗑️  Clearing file caches..." -ForegroundColor Gray
                    $cacheDirs = @('citation_cache', 'correction_cache')
                    $clearedFiles = 0
                    foreach ($dir in $cacheDirs) {
                        if (Test-Path $dir) {
                            $files = Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue
                            $clearedFiles += $files.Count
                            $files | Remove-Item -Force -ErrorAction SilentlyContinue
                        }
                    }
                    if ($clearedFiles -gt 0) {
                        Write-Host "  ✅ Cleared $clearedFiles cache files" -ForegroundColor Green
                    } else {
                        Write-Host "  ✅ File caches already empty" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "  ⚠️  Warning: Could not clear all caches: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
            
            # Report actual status
            if ($servicesReady) {
                Write-Host "`n[SUCCESS] RESTART COMPLETE - All services ready!" -ForegroundColor Green
                Write-Host "  Python cache cleared - all code changes active" -ForegroundColor DarkGray
                Write-Host "  Application: http://localhost" -ForegroundColor Cyan
            } else {
                Write-Host "`n[PARTIAL SUCCESS] Containers restarted but some services need more time" -ForegroundColor Yellow
                Write-Host "  Python cache cleared - all code changes active" -ForegroundColor DarkGray
                Write-Host "  Application: http://localhost" -ForegroundColor Cyan
                Write-Host "  ⚠️  Some services may take a few more minutes to be fully ready" -ForegroundColor Yellow
            }
            
            # Automatic Redis maintenance to prevent bloat
            try {
                $aofSizeOutput = docker exec casestrainer-redis-prod du -sh /data/appendonlydir 2>$null
                if ($aofSizeOutput) {
                    $aofSize = ($aofSizeOutput -split '\s+')[0]
                    $needsMaintenance = $false
                    
                    # Check if maintenance is needed (>200MB)
                    if ($aofSize -match '(\d+)M' -and [int]$matches[1] -gt 200) {
                        $needsMaintenance = $true
                    } elseif ($aofSize -match '(\d+\.?\d*)G') {
                        $needsMaintenance = $true
                    }
                    
                    if ($needsMaintenance) {
                        Write-Host "`n[MAINTENANCE] Redis AOF is large (${aofSize}) - running automatic cleanup..." -ForegroundColor Yellow
                        
                        # Run cleanup script
                        $cleanupScript = Join-Path $PSScriptRoot 'scripts\clean_redis_old_jobs.py'
                        if (Test-Path $cleanupScript) {
                            docker cp $cleanupScript casestrainer-backend-prod:/app/ 2>$null
                            docker exec casestrainer-backend-prod python /app/clean_redis_old_jobs.py 2>&1 | Out-Null
                            Write-Host "  ✅ Cleaned old RQ jobs" -ForegroundColor Green
                        }
                        
                        # Compact AOF
                        $compactResult = docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** BGREWRITEAOF 2>&1 | Select-Object -Last 1
                        if ($compactResult -like "*Background*") {
                            Write-Host "  ✅ Started AOF compaction (will complete in background)" -ForegroundColor Green
                        }
                        
                        # Show result
                        Start-Sleep -Seconds 2
                        $newSize = docker exec casestrainer-redis-prod du -sh /data/appendonlydir 2>$null | ForEach-Object { ($_ -split '\s+')[0] }
                        Write-Host "  Redis maintenance complete (AOF: ${aofSize} -> ${newSize})" -ForegroundColor Cyan
                    }
                }
            } catch {
                # Silently ignore errors - don't block startup
            }
            
            exit 0
        } else {
            Write-Host "`n[ERROR] Restart failed, falling back to full deployment..." -ForegroundColor Red
        }
    }
}

# Fall back to full deployment
Write-Host "[FULL DEPLOY] Running full deployment (containers not found or rebuild requested)..." -ForegroundColor Yellow
$fullScriptPath = Join-Path $PSScriptRoot 'scripts\cslaunch.ps1'

if (-not (Test-Path $fullScriptPath)) {
    Write-Host '[ERROR] Could not find scripts\cslaunch.ps1' -ForegroundColor Red
    exit 1
}

# Forward parameters
$params = @{ Command = 'prod' }
if ($Build) { $params.Build = $true }
if ($Force) { $params.Force = $true }
if ($NoCache) { $params.NoCache = $true }

& $fullScriptPath @params
exit $LASTEXITCODE
