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
    
    # Check if Vue source files are newer than dist files
    $needsVueBuild = $false
    if (Test-Path "casestrainer-vue-new\src") {
        $vueSourceFiles = Get-ChildItem -Path "casestrainer-vue-new\src" -Recurse -File -Include "*.vue","*.js" -ErrorAction SilentlyContinue
        $distIndexPath = "casestrainer-vue-new\dist\index.html"
        
        if (Test-Path $distIndexPath) {
            $distTime = (Get-Item $distIndexPath).LastWriteTime
            $newestSource = $vueSourceFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            
            if ($newestSource -and $newestSource.LastWriteTime -gt $distTime) {
                Write-Host "[DETECT] Vue source files changed - rebuild needed" -ForegroundColor Yellow
                $needsVueBuild = $true
            }
        } else {
            # No dist folder exists, need to build
            Write-Host "[DETECT] No dist folder found - initial build needed" -ForegroundColor Yellow
            $needsVueBuild = $true
        }
    }
    
    # Build Vue frontend if needed
    if ($needsVueBuild) {
        Write-Host "[VUE BUILD] Building Vue frontend..." -ForegroundColor Yellow
        Write-Host ""
        
        Push-Location "casestrainer-vue-new"
        $vueBuildStart = [System.Diagnostics.Stopwatch]::StartNew()
        
        try {
            & npm run build
            $vueBuildStart.Stop()
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`n✅ Vue build completed in $([math]::Round($vueBuildStart.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            } else {
                Write-Host "`n[ERROR] Vue build failed" -ForegroundColor Red
                Pop-Location
                exit 1
            }
        } catch {
            Write-Host "`n[ERROR] Vue build failed: $($_.Exception.Message)" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        Pop-Location
        Write-Host ""
    }
    
    # Check if frontend container needs rebuilding (Vue dist files changed)
    $needsFrontendRebuild = $false
    if (Test-Path "casestrainer-vue-new\dist\index.html") {
        # Check the actual dist folder that Docker uses
        $vueDistTime = (Get-Item "casestrainer-vue-new\dist\index.html" -ErrorAction SilentlyContinue).LastWriteTime
        $containerDistTime = docker exec casestrainer-frontend-prod stat -c %Y /usr/share/nginx/html/index.html 2>$null
        
        if ($vueDistTime -and $containerDistTime) {
            $containerTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$containerDistTime).LocalDateTime
            if ($vueDistTime -gt $containerTime) {
                Write-Host "[DETECT] Vue dist files updated - Docker rebuild needed" -ForegroundColor Yellow
                $needsFrontendRebuild = $true
            }
        } elseif ($needsVueBuild) {
            # Just built Vue, so definitely need Docker rebuild
            $needsFrontendRebuild = $true
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
            
            # NEW: Always restart backend + workers after a frontend rebuild so API picks up new Python code
            Write-Host "[BACKEND RESTART] Restarting backend API and workers to load latest code..." -ForegroundColor Yellow
            try {
                # Clear Python caches on host
                Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
                Get-ChildItem -Path "src" -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
                
                # Quick rebuild with cache for backend+workers
                $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
                docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
                $sw2.Stop()
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Backend + workers restarted in $([math]::Round($sw2.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
                    # Clear caches inside container (best-effort)
                    docker exec casestrainer-backend-prod find /app/src -type d -name '__pycache__' -exec rm -rf {} + 2>$null | Out-Null
                    docker exec casestrainer-backend-prod find /app/src -name '*.pyc' -delete 2>$null | Out-Null
                } else {
                    Write-Host "  ⚠️  Warning: Backend restart returned non-zero exit code" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  [WARNING] Backend restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Reload reverse-proxy to ensure API routing is up-to-date
            try {
                docker exec casestrainer-nginx-prod nginx -s reload > $null 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Nginx configuration reloaded successfully" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠️  Warning: Could not reload nginx config (container may not exist)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  [WARNING] Nginx reload step failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
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
        
        # SMART DETECTION: Check if source files are newer than Docker images
        Write-Host "[DETECT] Checking if Python source files changed..." -ForegroundColor Yellow
        $needsNoCacheRebuild = $false
        
        try {
            # Get newest Python file in src/
            $srcFiles = Get-ChildItem -Path "src" -Recurse -Filter "*.py" -File -ErrorAction SilentlyContinue
            if ($srcFiles) {
                $newestSrcFile = ($srcFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
                $newestSrcTime = $newestSrcFile.LastWriteTime
                
                # Get Docker image creation time for backend
                # USER FIX: Check actual Docker Compose image name (casestrainer_backend or casestrainer-backend)
                $imageCreated = $null
                $imageName = $null
                
                # Try common Docker Compose image naming patterns
                $possibleImageNames = @(
                    "casestrainer_backend",
                    "casestrainer-backend", 
                    "casestrainer_backend:latest",
                    "casestrainer-backend:latest"
                )
                
                foreach ($name in $possibleImageNames) {
                    $testCreated = docker inspect $name --format='{{.Created}}' 2>$null
                    if ($testCreated) {
                        $imageCreated = $testCreated
                        $imageName = $name
                        break
                    }
                }
                
                if ($imageCreated) {
                    $imageTime = [DateTime]::Parse($imageCreated)
                    
                    if ($newestSrcTime -gt $imageTime) {
                        $timeDiff = ($newestSrcTime - $imageTime).TotalMinutes
                        Write-Host "  🔍 Source files changed $([math]::Round($timeDiff, 1)) minutes after last build" -ForegroundColor Yellow
                        Write-Host "  📝 Newest: $($newestSrcFile.Name) (modified: $($newestSrcTime.ToString('HH:mm:ss')))" -ForegroundColor Gray
                        Write-Host "  🐳 Image: $imageName built at $($imageTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
                        Write-Host "  ⚠️  FORCING --no-cache rebuild to ensure fresh code" -ForegroundColor Red
                        $needsNoCacheRebuild = $true
                    } else {
                        Write-Host "  ✅ Source files unchanged since last build ($imageName) - using cached layers" -ForegroundColor Green
                    }
                } else {
                    Write-Host "  ⚠️  Could not find backend image - forcing --no-cache rebuild for safety" -ForegroundColor Yellow
                    Write-Host "  💡 Tried: $($possibleImageNames -join ', ')" -ForegroundColor Gray
                    $needsNoCacheRebuild = $true
                }
            }
        } catch {
            Write-Host "  ⚠️  Detection failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  ⚠️  Forcing --no-cache rebuild for safety" -ForegroundColor Yellow
            $needsNoCacheRebuild = $true
        }
        Write-Host ""
        
        # REBUILD backend AND workers with smart caching
        if ($needsNoCacheRebuild) {
            Write-Host "[FULL REBUILD] Building backend + workers with --no-cache (6-7 minutes)..." -ForegroundColor Red
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            docker-compose -f docker-compose.prod.yml build --no-cache backend rqworker1 rqworker2 rqworker3
            docker-compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
            $sw.Stop()
        } else {
            Write-Host "[QUICK REBUILD] Rebuilding backend + workers with cache (10-15 seconds)..." -ForegroundColor Yellow
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
            $sw.Stop()
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Backend + workers rebuilt and deployed in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            
            # CRITICAL: Reload nginx configuration to pick up any changes
            Write-Host "`n[NGINX] Reloading nginx configuration..." -ForegroundColor Yellow
            docker exec casestrainer-nginx-prod nginx -s reload > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Nginx configuration reloaded successfully" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Warning: Could not reload nginx config (container may not exist)" -ForegroundColor Yellow
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
                    Write-Host "  🗑️  Clearing file caches and databases..." -ForegroundColor Gray
                    
                    # Clear cache directories
                    $cacheDirs = @('citation_cache', 'correction_cache')
                    $clearedFiles = 0
                    foreach ($dir in $cacheDirs) {
                        if (Test-Path $dir) {
                            $files = Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue
                            $clearedFiles += $files.Count
                            $files | Remove-Item -Force -ErrorAction SilentlyContinue
                        }
                    }
                    
                    # Clear SQLite cache databases (CRITICAL for fresh extraction)
                    $cacheDb = @(
                        'data\citations.db',
                        'src\data\citations.db',
                        'legal_search_cache.db',
                        'data\legal_search_cache.db',
                        'data\langsearch_cache.db',
                        'src\data\legal_search_cache.db'
                    )
                    $clearedDbs = 0
                    foreach ($db in $cacheDb) {
                        if (Test-Path $db) {
                            Remove-Item -Path $db -Force -ErrorAction SilentlyContinue
                            $clearedDbs++
                        }
                    }
                    
                    if ($clearedFiles -gt 0 -or $clearedDbs -gt 0) {
                        Write-Host "  ✅ Cleared $clearedFiles cache files + $clearedDbs SQLite databases" -ForegroundColor Green
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

# Forward parameters using hashtable for proper splatting
$scriptParams = @{
    Command = 'prod'
}
if ($Build) { $scriptParams['Build'] = $true }
if ($Force) { $scriptParams['Force'] = $true }
if ($NoCache) { $scriptParams['NoCache'] = $true }

& $fullScriptPath @scriptParams
exit $LASTEXITCODE
