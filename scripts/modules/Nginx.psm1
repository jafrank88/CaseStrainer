# Nginx.psm1 - Nginx management for CaseStrainer

# Ensure errors are caught
$ErrorActionPreference = 'Stop'

# Default Nginx configuration paths
$script:nginxConfig = @{
    NginxPath = "C:\nginx\nginx.exe"
    ConfigPath = "C:\nginx\conf\nginx.conf"
    LogsPath = "C:\nginx\logs"
}

# Set Nginx configuration paths
function Set-NginxConfig {
    [CmdletBinding()]
    param(
        [string]$NginxPath,
        [string]$ConfigPath,
        [string]$LogsPath
    )
    
    if ($NginxPath) { $script:nginxConfig.NginxPath = $NginxPath }
    if ($ConfigPath) { $script:nginxConfig.ConfigPath = $ConfigPath }
    if ($LogsPath) { $script:nginxConfig.LogsPath = $LogsPath }
    
    # Create logs directory if it doesn't exist
    if (-not (Test-Path $script:nginxConfig.LogsPath)) {
        New-Item -ItemType Directory -Path $script:nginxConfig.LogsPath -Force | Out-Null
    }
    
    return $script:nginxConfig
}

# Check if Nginx is installed and accessible
function Test-NginxInstalled {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    try {
        if (-not (Test-Path $script:nginxConfig.NginxPath)) {
            Write-Host "[WARNING] Nginx not found at: $($script:nginxConfig.NginxPath)" -ForegroundColor Yellow
            return $false
        }
        
        $version = & $script:nginxConfig.NginxPath -v 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Nginx version check failed"
        }
        
        Write-Host ("[OK] {0}" -f ($version -join "`n")) -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host ("[ERROR] Nginx check failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
}

# Check if Nginx is running
function Test-NginxRunning {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    $process = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host ("[INFO] Nginx is running (PID: {0})" -f ($process.Id -join ", ")) -ForegroundColor Green
        return $true
    }
    
    Write-Host "[INFO] Nginx is not running" -ForegroundColor Yellow
    return $false
}

# Start Nginx
function Start-NginxServer {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    if (Test-NginxRunning) {
        Write-Host "[INFO] Nginx is already running" -ForegroundColor Yellow
        return $true
    }
    
    if (-not (Test-NginxInstalled)) {
        Write-Host "[ERROR] Cannot start Nginx: Nginx is not properly installed" -ForegroundColor Red
        return $false
    }
    
    try {
        if ($PSCmdlet.ShouldProcess("Nginx", "Start Nginx server")) {
            # Start Nginx
            Push-Location (Split-Path $script:nginxConfig.NginxPath)
            & $script:nginxConfig.NginxPath -c $script:nginxConfig.ConfigPath
            
            # Wait a moment for Nginx to start
            Start-Sleep -Seconds 2
            
            if (-not (Test-NginxRunning)) {
                throw "Failed to start Nginx"
            }
            
            Write-Host "[OK] Nginx started successfully" -ForegroundColor Green
            return $true
        }
        return $false
    }
    catch {
        Write-Host ("[ERROR] Failed to start Nginx: {0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
    finally {
        Pop-Location
    }
}

# Stop Nginx
function Stop-NginxServer {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    if (-not (Test-NginxRunning)) {
        Write-Host "[INFO] Nginx is not running" -ForegroundColor Yellow
        return $true
    }
    
    try {
        if ($PSCmdlet.ShouldProcess("Nginx", "Stop Nginx server")) {
            # Graceful shutdown
            & $script:nginxConfig.NginxPath -s stop
            
            # Wait for Nginx to stop
            $timeout = 10 # seconds
            $startTime = Get-Date
            
            while ((Get-Date).Subtract($startTime).TotalSeconds -lt $timeout) {
                if (-not (Test-NginxRunning)) {
                    Write-Host "[OK] Nginx stopped successfully" -ForegroundColor Green
                    return $true
                }
                Start-Sleep -Seconds 1
            }
            
            # Force stop if graceful shutdown failed
            Write-Host "[WARNING] Graceful shutdown timed out, forcing stop..." -ForegroundColor Yellow
            Get-Process -Name "nginx" -ErrorAction SilentlyContinue | Stop-Process -Force
            
            if (Test-NginxRunning) {
                throw "Failed to stop Nginx"
            }
            
            Write-Host "[OK] Nginx stopped (forced)" -ForegroundColor Green
            return $true
        }
        return $false
    }
    catch {
        Write-Host ("[ERROR] Failed to stop Nginx: {0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
}

# Reload Nginx configuration
function Update-NginxConfig {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    if (-not (Test-NginxRunning)) {
        Write-Host "[WARNING] Nginx is not running. Starting Nginx..." -ForegroundColor Yellow
        return Start-NginxServer
    }
    
    try {
        if ($PSCmdlet.ShouldProcess("Nginx", "Reload configuration")) {
            # Test configuration first
            & $script:nginxConfig.NginxPath -t -c $script:nginxConfig.ConfigPath
            if ($LASTEXITCODE -ne 0) {
                throw "Nginx configuration test failed"
            }
            
            # Reload configuration
            & $script:nginxConfig.NginxPath -s reload -c $script:nginxConfig.ConfigPath
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to reload Nginx configuration"
            }
            
            Write-Host "[OK] Nginx configuration reloaded successfully" -ForegroundColor Green
            return $true
        }
        return $false
    }
    catch {
        Write-Host ("[ERROR] Failed to reload Nginx configuration: {0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
}

# Check if a port is available
function Test-PortAvailable {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [int]$Port
    )
    
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    }
    catch {
        Write-Host ("[WARNING] Port {0} is in use: {1}" -f $Port, $_.Exception.Message) -ForegroundColor Yellow
        return $false
    }
}

# Get Nginx status
function Get-NginxStatus {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param()
    
    $status = [PSCustomObject]@{
        IsInstalled = $false
        IsRunning = $false
        Version = $null
        ConfigFile = $script:nginxConfig.ConfigPath
        Error = $null
    }
    
    try {
        $status.IsInstalled = Test-Path $script:nginxConfig.NginxPath
        
        if ($status.IsInstalled) {
            $version = & $script:nginxConfig.NginxPath -v 2>&1
            $status.Version = ($version | Where-Object { $_ -match 'nginx version:' }) -replace 'nginx version: ','' | Select-Object -First 1
            $status.IsRunning = [bool](Get-Process -Name "nginx" -ErrorAction SilentlyContinue)
        }
    }
    catch {
        $status.Error = $_.Exception.Message
    }
    
    return $status
}

# Export public functions
Export-ModuleMember -Function * -Alias *
