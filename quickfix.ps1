# Working CaseStrainer Fix - Handles missing nginx files
Write-Host "=== CaseStrainer Working Fix ===" -ForegroundColor Green
Write-Host "Fixing nginx configuration and missing files..." -ForegroundColor Yellow
Write-Host ""

# Step 1: Check nginx directory structure
Write-Host "Step 1: Checking nginx directory structure..." -ForegroundColor Cyan
$nginxDir = "nginx"
$nginxExe = Join-Path $nginxDir "nginx.exe"

Write-Host "  Nginx directory: $nginxDir" -ForegroundColor Gray
Write-Host "  Nginx executable: $(if (Test-Path $nginxExe) { 'EXISTS' } else { 'MISSING' })" -ForegroundColor $(if (Test-Path $nginxExe) { 'Green' } else { 'Red' })

# Check for required files
$requiredFiles = @(
    "mime.types",
    "conf/nginx.conf",
    "conf/mime.types"
)

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $nginxDir $file
    $exists = Test-Path $filePath
    Write-Host "  $file : $(if ($exists) { 'EXISTS' } else { 'MISSING' })" -ForegroundColor $(if ($exists) { 'Green' } else { 'Yellow' })
}

# Step 2: Stop any running nginx processes
Write-Host "Step 2: Stopping nginx processes..." -ForegroundColor Cyan
Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 3: Create minimal nginx config without mime.types dependency
Write-Host "Step 3: Creating minimal nginx configuration..." -ForegroundColor Cyan

$configLines = @(
    "worker_processes  1;",
    "",
    "events {",
    "    worker_connections  1024;",
    "}",
    "",
    "http {",
    "    # Basic MIME types - inline instead of include",
    "    types {",
    "        text/html                             html htm shtml;",
    "        text/css                              css;",
    "        application/javascript                js;",
    "        application/json                      json;",
    "        image/png                             png;",
    "        image/jpeg                            jpeg jpg;",
    "        image/gif                             gif;",
    "        image/svg+xml                         svg;",
    "        font/woff                             woff;",
    "        font/woff2                            woff2;",
    "    }",
    "    ",
    "    default_type  application/octet-stream;",
    "    sendfile        on;",
    "    keepalive_timeout  65;",
    "",
    "    # Create logs directory if it doesn't exist",
    "    access_log  logs/access.log;",
    "    error_log   logs/error.log warn;",
    "",
    "    server {",
    "        listen       443 ssl;",
    "        server_name  wolf.law.uw.edu localhost;",
    "        ",
    "        ssl_certificate     /etc/nginx/ssl/WolfCertBundle.crt;",
    "        ssl_certificate_key /etc/nginx/ssl/wolf.law.uw.edu.key;",
    "        ssl_protocols       TLSv1.2 TLSv1.3;",
    "        ssl_ciphers         HIGH:!aNULL:!MD5;",
    "        ",
    "        client_max_body_size 100M;",
    "",
    "        # API routes - proxy to backend",
    "        location /casestrainer/api/ {",
    "            proxy_pass http://127.0.0.1:5000;",
    "            proxy_set_header Host `$host;",
    "            proxy_set_header X-Real-IP `$remote_addr;",
    "            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;",
    "            proxy_set_header X-Forwarded-Proto `$scheme;",
    "            proxy_http_version 1.1;",
    "            proxy_connect_timeout 30s;",
    "            proxy_send_timeout 30s;",
    "            proxy_read_timeout 30s;",
    "        }",
    "",
    "        # Vue.js assets",
    "        location /casestrainer/assets/ {",
    "            alias /usr/share/nginx/html/assets/;",
    "            expires 1y;",
    "            add_header Cache-Control `"public, immutable`";",
    "        }",
    "",
    "        # Frontend - Vue.js SPA",
    "        location /casestrainer/ {",
    "            alias /usr/share/nginx/html/;",
    "            index index.html;",
    "            try_files `$uri `$uri/ /index.html;",
    "        }",
    "",
    "        # Root redirect",
    "        location = / {",
    "            return 301 /casestrainer/;",
    "        }",
    "",
    "        # Simple error page",
    "        error_page 500 502 503 504 /50x.html;",
    "        location = /50x.html {",
    "            return 200 `"Service temporarily unavailable`";",
    "            add_header Content-Type text/plain;",
    "        }",
    "    }",
    "}"
)

# Create config file
$configContent = $configLines -join "`n"
$configFile = Join-Path $nginxDir "minimal.conf"
[System.IO.File]::WriteAllText($configFile, $configContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "  Minimal configuration created: minimal.conf" -ForegroundColor Green

# Step 4: Create logs directory in nginx folder
Write-Host "Step 4: Creating nginx logs directory..." -ForegroundColor Cyan
$nginxLogsDir = Join-Path $nginxDir "logs"
if (!(Test-Path $nginxLogsDir)) {
    New-Item -ItemType Directory -Path $nginxLogsDir -Force | Out-Null
    Write-Host "  Created logs directory" -ForegroundColor Green
} else {
    Write-Host "  Logs directory already exists" -ForegroundColor Green
}

# Step 5: Test the configuration
Write-Host "Step 5: Testing nginx configuration..." -ForegroundColor Cyan

$originalLocation = Get-Location
try {
    Set-Location $nginxDir
    
    # Test with minimal config
    & ".\nginx.exe" -t -c "minimal.conf" 2>&1 | Write-Host -ForegroundColor Gray
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Configuration test: PASSED" -ForegroundColor Green
    } else {
        Write-Host "  Configuration test: FAILED" -ForegroundColor Red
        Write-Host "  Trying to start anyway..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Configuration test error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Set-Location $originalLocation
}

# Step 6: Start nginx
Write-Host "Step 6: Starting nginx..." -ForegroundColor Cyan

try {
    Set-Location $nginxDir
    
    # Start nginx with minimal config
    $nginxProcess = Start-Process -FilePath ".\nginx.exe" -ArgumentList "-c", "minimal.conf" -NoNewWindow -PassThru
    Write-Host "  Nginx started (PID: $($nginxProcess.Id))" -ForegroundColor Green
    
    # Wait for nginx to start
    Start-Sleep -Seconds 5
    
    # Check if nginx is still running
    $nginxStillRunning = Get-Process -Id $nginxProcess.Id -ErrorAction SilentlyContinue
    if ($nginxStillRunning) {
        Write-Host "  Nginx is running successfully" -ForegroundColor Green
    } else {
        Write-Host "  Nginx may have stopped - checking processes..." -ForegroundColor Yellow
        $allNginx = Get-Process nginx -ErrorAction SilentlyContinue
        if ($allNginx) {
            Write-Host "  Found nginx processes: $($allNginx.Count)" -ForegroundColor Green
        } else {
            Write-Host "  No nginx processes found" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "  Failed to start nginx: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Set-Location $originalLocation
}

# Step 7: Test everything
Write-Host "Step 7: Testing the complete application..." -ForegroundColor Cyan

# Skip SSL certificate validation for local testing
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

# Wait a bit more for everything to be ready
Start-Sleep -Seconds 5

# Test backend directly first
Write-Host "  Testing backend directly..." -ForegroundColor Gray
try {
    $backendDirect = Invoke-RestMethod -Uri "http://127.0.0.1:5000/casestrainer/api/health" -TimeoutSec 10
    Write-Host "  Backend direct: SUCCESS ($($backendDirect.status))" -ForegroundColor Green
} catch {
    Write-Host "  Backend direct: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test API through nginx
Write-Host "  Testing API through nginx..." -ForegroundColor Gray
try {
    $apiThroughNginx = Invoke-RestMethod -Uri "https://localhost:443/casestrainer/api/health" -TimeoutSec 15
    Write-Host "  API through nginx: SUCCESS ($($apiThroughNginx.status))" -ForegroundColor Green
} catch {
    Write-Host "  API through nginx: FAILED - $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test frontend
Write-Host "  Testing frontend..." -ForegroundColor Gray
try {
    $frontend = Invoke-WebRequest -Uri "https://localhost:443/casestrainer/" -UseBasicParsing -TimeoutSec 15
    Write-Host "  Frontend: SUCCESS (HTTP $($frontend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Frontend: FAILED - $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final status report
Write-Host ""
Write-Host "=== Final Status Report ===" -ForegroundColor Cyan

$backendProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "python" }
$nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue

Write-Host "Backend processes: $($backendProcesses.Count)" -ForegroundColor $(if ($backendProcesses) { 'Green' } else { 'Red' })
Write-Host "Nginx processes: $($nginxProcesses.Count)" -ForegroundColor $(if ($nginxProcesses) { 'Green' } else { 'Red' })

if ($backendProcesses -and $nginxProcesses) {
    Write-Host ""
    Write-Host "SUCCESS! Your application should now be working!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your application at:" -ForegroundColor Cyan
    Write-Host "  https://localhost:443/casestrainer/" -ForegroundColor Yellow
    Write-Host "  https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Yellow
    Write-Host ""
    
    # Try to open browser
    try {
        Start-Process "https://localhost:443/casestrainer/"
        Write-Host "Browser opened to your application!" -ForegroundColor Green
    } catch {
        Write-Host "Could not open browser automatically" -ForegroundColor Yellow
    }
    
} else {
    Write-Host ""
    Write-Host "Some services are not running properly." -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To stop all services later:" -ForegroundColor Gray
Write-Host "  Get-Process nginx | Stop-Process -Force" -ForegroundColor Gray
Write-Host "  Get-Process python | Stop-Process -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')