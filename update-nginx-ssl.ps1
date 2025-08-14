# Update Nginx SSL Configuration Script

# Stop and remove existing Nginx container if it's running
Write-Host "Stopping and removing existing Nginx container..." -ForegroundColor Cyan
docker stop casestrainer-nginx-prod 2> $null
docker rm casestrainer-nginx-prod 2> $null

# Create necessary directories if they don't exist
$sslDir = "D:\dev\casestrainer\nginx\ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir -Force | Out-Null
    Write-Host "Created SSL directory: $sslDir" -ForegroundColor Green
}

# Check if SSL certificate and key exist
$certPath = "$sslDir\WolfCertBundle.crt"
$keyPath = "$sslDir\wolf.law.uw.edu.key"

if (-not (Test-Path $certPath) -or -not (Test-Path $keyPath)) {
    Write-Host "Error: SSL certificate or key file is missing" -ForegroundColor Red
    Write-Host "Please ensure these files exist:"
    Write-Host "- $certPath"
    Write-Host "- $keyPath"
    exit 1
}

# Copy the new Nginx configuration and SSL certificates to the container
Write-Host "Copying Nginx configuration and SSL certificates..." -ForegroundColor Cyan

# Build the docker run command as an array to avoid line continuation issues
$dockerArgs = @(
    "run", "-d",
    "--name", "casestrainer-nginx-prod",
    "-p", "80:80",
    "-p", "443:443",
    "-v", "D:\dev\casestrainer\nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro",
    "-v", "D:\dev\casestrainer\nginx\ssl:/etc/nginx/ssl:ro",
    "-v", "D:\dev\casestrainer\casestrainer-vue-new\dist:/usr/share/nginx/html/casestrainer:ro",
    "--network", "casestrainer_app-network",
    "--restart", "unless-stopped",
    "nginx:alpine"
)

# Start a new Nginx container with the updated configuration
Write-Host "Starting Nginx container with SSL configuration..." -ForegroundColor Cyan
docker $dockerArgs

# Check if the container started successfully
$containerId = docker ps -q -f name=casestrainer-nginx-prod
if ($containerId) {
    Write-Host "Nginx container started successfully with ID: $containerId" -ForegroundColor Green
    
    # Wait a moment for Nginx to start
    Write-Host "Waiting for Nginx to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    # Test the Nginx configuration inside the container
    Write-Host "`nTesting Nginx configuration..." -ForegroundColor Cyan
    $configTest = docker exec casestrainer-nginx-prod nginx -t 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Nginx configuration test successful!" -ForegroundColor Green
        
        # Reload Nginx to apply the new configuration
        Write-Host "Reloading Nginx to apply the new configuration..." -ForegroundColor Cyan
        docker exec casestrainer-nginx-prod nginx -s reload 2>&1 | Out-Null
        Write-Host "Nginx has been reloaded with the new SSL configuration" -ForegroundColor Green
        
        # Display SSL certificate information
        Write-Host "`nSSL Certificate Information:" -ForegroundColor Cyan
        docker exec casestrainer-nginx-prod openssl x509 -in /etc/nginx/ssl/WolfCertBundle.crt -noout -text | 
            Select-String -Pattern "Not Before|Not After|Subject:|Issuer:|DNS:" -Context 0,1
        
        # Test HTTPS connection
        Write-Host "`nTesting HTTPS connection..." -ForegroundColor Cyan
        try {
            # Disable SSL certificate validation for testing self-signed certs
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
            
            # Test both HTTP (should redirect to HTTPS) and HTTPS
            $httpResponse = Invoke-WebRequest -Uri "http://localhost/casestrainer/" -UseBasicParsing -Method Head -ErrorAction Stop -MaximumRedirection 0 -ErrorVariable httpErr -ErrorAction SilentlyContinue
            $httpsResponse = Invoke-WebRequest -Uri "https://localhost/casestrainer/" -UseBasicParsing -Method Head -ErrorAction Stop -SkipCertificateCheck
            
            if ($httpResponse.Headers.Location -match "^https://") {
                Write-Host "HTTP to HTTPS redirect is working correctly" -ForegroundColor Green
            } else {
                Write-Host "Warning: HTTP to HTTPS redirect may not be working as expected" -ForegroundColor Yellow
            }
            
            Write-Host "HTTPS connection successful! Status: $($httpsResponse.StatusCode) $($httpsResponse.StatusDescription)" -ForegroundColor Green
            Write-Host "You can now access the site at: https://localhost/casestrainer/" -ForegroundColor Green
        } catch {
            Write-Host "HTTPS connection failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Checking Nginx error logs..." -ForegroundColor Yellow
            docker logs casestrainer-nginx-prod 2>&1 | Select-Object -Last 20
        }
    } else {
        Write-Host "Nginx configuration test failed:" -ForegroundColor Red
        $configTest
        
        # Show container logs for more details
        Write-Host "`nContainer logs:" -ForegroundColor Yellow
        docker logs casestrainer-nginx-prod 2>&1 | Select-Object -Last 20
    }
} else {
    Write-Host "Failed to start Nginx container" -ForegroundColor Red
    
    # Try to get more detailed error information
    $errorDetails = docker logs casestrainer-nginx-prod 2>&1 | Select-Object -Last 20
    if ($errorDetails) {
        Write-Host "Container logs:" -ForegroundColor Yellow
        $errorDetails
    }
    
    Write-Host "`nTroubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Check if port 80 or 443 is already in use:"
    Write-Host "   netstat -ano | findstr \":80|:443\""
    Write-Host "2. Verify Docker is running and has access to the host filesystem"
    Write-Host "3. Check Docker logs for more details:"
    Write-Host "   docker logs casestrainer-nginx-prod"
    Write-Host "4. If using Docker Desktop, ensure file sharing is enabled for D:\"
    Write-Host "5. Try running with elevated privileges if needed"
}

# Display final status
Write-Host "`nNginx SSL configuration update complete!" -ForegroundColor Cyan
