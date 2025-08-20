# Docker Engine Optimization Script for CaseStrainer
# Run this after resetting Docker Desktop to factory defaults
# Optimizes Docker Desktop settings, daemon configuration, and WSL2 integration

param(
    [switch]$Apply,
    [switch]$ShowCurrent,
    [switch]$RestoreDefaults,
    [switch]$Verbose
)

# Configuration paths
$DockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$DockerConfigPath = "$env:ProgramData\Docker\config\daemon.json"
$DockerDesktopSettingsPath = "$env:APPDATA\Docker\settings.json"
$WSLConfigPath = "$env:USERPROFILE\.wslconfig"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

$LogFile = "logs/docker_engine_optimization.log"

function Write-Log {
    param($Message, $Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    try {
        Add-Content -Path $LogFile -Value $logMessage -Force -ErrorAction Stop
    } catch {
        Write-Host "Failed to write to log file: $_" -ForegroundColor Red
    }
    
    if ($Verbose -or $Level -in @("ERROR", "WARN")) {
        $color = switch($Level) { 
            "ERROR" { "Red" } 
            "WARN"  { "Yellow" } 
            "INFO"  { "Green" } 
            "DEBUG" { "Gray" }
            default { "White" }
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Test-DockerDesktopRunning {
    try {
        $processes = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        return $processes.Count -gt 0
    } catch {
        return $false
    }
}

function Test-DockerServiceRunning {
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        return $service -and $service.Status -eq "Running"
    } catch {
        return $false
    }
}

function Show-CurrentConfiguration {
    Write-Host "🔍 Current Docker Configuration:" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    # Check Docker Desktop status
    Write-Host "Docker Desktop Process:" -ForegroundColor White
    if (Test-DockerDesktopRunning) {
        Write-Host "  ✅ Running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Not running" -ForegroundColor Red
    }
    
    # Check Docker service status
    Write-Host "Docker Service:" -ForegroundColor White
    if (Test-DockerServiceRunning) {
        Write-Host "  ✅ Running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Not running" -ForegroundColor Red
    }
    
    # Check Docker CLI
    Write-Host "Docker CLI:" -ForegroundColor White
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "  ✅ Available: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Error checking version" -ForegroundColor Red
    }
    
    # Check daemon configuration
    Write-Host "Daemon Configuration:" -ForegroundColor White
    if (Test-Path $DockerConfigPath) {
        Write-Host "  ✅ Found at: $DockerConfigPath" -ForegroundColor Green
        try {
            $daemonConfig = Get-Content $DockerConfigPath -Raw | ConvertFrom-Json
            Write-Host "  📋 Current settings:" -ForegroundColor Gray
            $daemonConfig | ConvertTo-Json -Depth 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        } catch {
            Write-Host "  ⚠️  Could not parse configuration" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Not found" -ForegroundColor Red
    }
    
    # Check WSL configuration
    Write-Host "WSL Configuration:" -ForegroundColor White
    if (Test-Path $WSLConfigPath) {
        Write-Host "  ✅ Found at: $WSLConfigPath" -ForegroundColor Green
        try {
            $wslConfig = Get-Content $WSLConfigPath -Raw
            Write-Host "  📋 Current settings:" -ForegroundColor Gray
            $wslConfig | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        } catch {
            Write-Host "  ⚠️  Could not read configuration" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Not found" -ForegroundColor Red
    }
    
    # Check Docker Desktop settings
    Write-Host "Docker Desktop Settings:" -ForegroundColor White
    if (Test-Path $DockerDesktopSettingsPath) {
        Write-Host "  ✅ Found at: $DockerDesktopSettingsPath" -ForegroundColor Green
        try {
            $desktopSettings = Get-Content $DockerDesktopSettingsPath -Raw | ConvertFrom-Json
            Write-Host "  📋 Current settings:" -ForegroundColor Gray
            $desktopSettings | ConvertTo-Json -Depth 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        } catch {
            Write-Host "  ⚠️  Could not parse settings" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Not found" -ForegroundColor Red
    }
}

function Optimize-DockerDaemon {
    Write-Log "Optimizing Docker daemon configuration"
    
    # Create optimized daemon configuration
    $optimizedDaemonConfig = @{
        "builder" = @{
            "gc" = @{
                "defaultKeepStorage" = "20GB"
                "enabled" = $true
                "policy" = @(
                    @{"keepStorage" = "10GB"; "filter" = @("unused-for=24h")},
                    @{"keepStorage" = "50GB"; "all" = $true}
                )
            }
        }
        "experimental" = $false
        "features" = @{
            "buildkit" = $true
            "containerd-snapshotter" = $true
        }
        "log-driver" = "json-file"
        "log-opts" = @{
            "max-size" = "10m"
            "max-file" = "3"
            "compress" = $true
        }
        "storage-driver" = "overlay2"
        "default-ulimits" = @{
            "nofile" = @{
                "Name" = "nofile"
                "Hard" = 65535
                "Soft" = 65535
            }
        }
        "max-concurrent-downloads" = 10
        "max-concurrent-uploads" = 5
        "registry-mirrors" = @("https://registry-1.docker.io")
        "insecure-registries" = @()
        "default-address-pools" = @(
            @{
                "base" = "172.17.0.0/16"
                "size" = 24
            }
        )
        "shutdown-timeout" = 30
        "debug" = $false
        "metrics-addr" = "127.0.0.1:9323"
        "dns" = @("8.8.8.8", "8.8.4.4", "1.1.1.1")
        "ipv6" = $false
        "ip-forward" = $true
        "ip-masq" = $true
        "userland-proxy" = $true
        "ip" = "0.0.0.0"
        "icc" = $true
        "live-restore" = $true
        "exec-opts" = @("native.cgroupdriver=systemd")
        "cgroup-parent" = "/docker/containers"
        "max-memory" = "4GB"
        "max-cpu" = "4"
        "storage-opts" = @(
            "overlay2.override_kernel_check=true",
            "overlay2.size=10GB"
        )
    }
    
    # Ensure Docker config directory exists
    $dockerConfigDir = Split-Path $DockerConfigPath -Parent
    if (!(Test-Path $dockerConfigDir)) {
        New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
        Write-Log "Created Docker config directory: $dockerConfigDir"
    }
    
    # Write optimized configuration
    $optimizedDaemonConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $DockerConfigPath -Force -Encoding utf8
    Write-Log "Applied optimized Docker daemon configuration"
    
    return $true
}

function Optimize-WSLConfiguration {
    Write-Log "Optimizing WSL configuration for Docker"
    
    # Create optimized WSL configuration
    $wslConfig = @"
# WSL Configuration for Docker Desktop
[wsl2]
# Memory limit for WSL2
memory=4GB
# CPU limit for WSL2
processors=4
# Enable nested virtualization
nestedVirtualization=true
# Enable WSLg
guiApplications=true
# Network configuration
networkingMode=mirrored
# DNS configuration
dnsTunneling=true
# Enable localhost forwarding
localhostForwarding=true
# Kernel command line
kernelCommandLine=vsyscall=emulate
# Enable experimental features
experimental=true
# Swap configuration
swap=2GB
# Page reporting
pageReporting=true
# Memory reclaim
memoryReclaim=true
# Enable nested virtualization
nestedVirtualization=true
"@
    
    # Write WSL configuration
    $wslConfig | Out-File -FilePath $WSLConfigPath -Force -Encoding utf8
    Write-Log "Applied optimized WSL configuration"
    
    return $true
}

function Optimize-DockerDesktopSettings {
    Write-Log "Optimizing Docker Desktop settings"
    
    # Create optimized Docker Desktop settings
    $desktopSettings = @{
        "dockerEngine" = @{
            "experimental" = $false
            "features" = @{
                "buildkit" = $true
                "containerd-snapshotter" = $true
            }
        }
        "general" = @{
            "autoStart" = $true
            "checkForUpdates" = $false
            "includeBetaVersions" = $false
            "openTunnels" = @()
            "showStartupMessage" = $false
            "startDockerDesktop" = $true
        }
        "resources" = @{
            "cpu" = @{
                "count" = 4
                "limit" = 4
            }
            "memory" = @{
                "limit" = 4096
                "swap" = 2048
            }
            "disk" = @{
                "imageStorage" = @{
                    "path" = "C:\\Users\\$env:USERNAME\\AppData\\Local\\Docker\\wsl\\data\\ext4.vhdx"
                    "size" = 256000
                }
            }
        }
        "advanced" = @{
            "debug" = $false
            "experimental" = $false
            "hosts" = @()
            "registryMirrors" = @("https://registry-1.docker.io")
            "insecureRegistries" = @()
        }
        "kubernetes" = @{
            "enabled" = $false
            "port" = 6443
            "suppressSudo" = $false
            "switchContext" = $false
        }
        "pro" = @{
            "enabled" = $false
        }
        "softwareUpdates" = @{
            "checkForUpdates" = $false
            "includeBetaVersions" = $false
        }
    }
    
    # Ensure Docker Desktop settings directory exists
    $desktopSettingsDir = Split-Path $DockerDesktopSettingsPath -Parent
    if (!(Test-Path $desktopSettingsDir)) {
        New-Item -ItemType Directory -Path $desktopSettingsDir -Force | Out-Null
        Write-Log "Created Docker Desktop settings directory: $desktopSettingsDir"
    }
    
    # Write optimized settings
    $desktopSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath $DockerDesktopSettingsPath -Force -Encoding utf8
    Write-Log "Applied optimized Docker Desktop settings"
    
    return $true
}

function Restart-DockerDesktop {
    Write-Log "Restarting Docker Desktop"
    
    # Stop Docker Desktop if running
    if (Test-DockerDesktopRunning) {
        Write-Host "🛑 Stopping Docker Desktop..." -ForegroundColor Yellow
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }
    
    # Stop Docker service if running
    if (Test-DockerServiceRunning) {
        Write-Host "🛑 Stopping Docker service..." -ForegroundColor Yellow
        Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }
    
    # Start Docker Desktop
    Write-Host "🚀 Starting Docker Desktop..." -ForegroundColor Green
    Start-Process -FilePath $DockerDesktopPath -WindowStyle Minimized
    
    # Wait for Docker to start
    Write-Host "⏳ Waiting for Docker to start..." -ForegroundColor Cyan
    $timeout = 60
    $elapsed = 0
    
    while ($elapsed -lt $timeout) {
        if (Test-DockerServiceRunning) {
            Write-Host "✅ Docker service is running" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  Waiting... ($elapsed/$timeout seconds)" -ForegroundColor Gray
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host "⚠️  Docker service startup timeout" -ForegroundColor Yellow
        return $false
    }
    
    # Wait for Docker CLI to be responsive
    Write-Host "⏳ Waiting for Docker CLI..." -ForegroundColor Cyan
    $timeout = 30
    $elapsed = 0
    
    while ($elapsed -lt $timeout) {
        try {
            $dockerVersion = docker --version 2>$null
            if ($dockerVersion) {
                Write-Host "✅ Docker CLI is responsive: $dockerVersion" -ForegroundColor Green
                break
            }
        } catch {
            # Ignore errors during startup
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  Waiting for CLI... ($elapsed/$timeout seconds)" -ForegroundColor Gray
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host "⚠️  Docker CLI startup timeout" -ForegroundColor Yellow
        return $false
    }
    
    Write-Log "Docker Desktop restarted successfully"
    return $true
}

function Restore-DefaultConfiguration {
    Write-Log "Restoring default Docker configuration"
    
    # Remove custom configurations
    if (Test-Path $DockerConfigPath) {
        Remove-Item $DockerConfigPath -Force
        Write-Log "Removed custom daemon configuration"
    }
    
    if (Test-Path $WSLConfigPath) {
        Remove-Item $WSLConfigPath -Force
        Write-Log "Removed custom WSL configuration"
    }
    
    if (Test-Path $DockerDesktopSettingsPath) {
        Remove-Item $DockerDesktopSettingsPath -Force
        Write-Log "Removed custom Docker Desktop settings"
    }
    
    Write-Log "Default configuration restored"
    return $true
}

# Main execution
Write-Host "🐳 Docker Engine Optimization Script for CaseStrainer" -ForegroundColor Cyan
Write-Host "=" * 60

if ($ShowCurrent) {
    Show-CurrentConfiguration
    exit 0
}

if ($RestoreDefaults) {
    Write-Host "🔄 Restoring default Docker configuration..." -ForegroundColor Yellow
    if (Restore-DefaultConfiguration) {
        Write-Host "✅ Default configuration restored" -ForegroundColor Green
        Write-Host "🔄 Restart Docker Desktop to apply changes" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Failed to restore default configuration" -ForegroundColor Red
        exit 1
    }
    exit 0
}

if ($Apply) {
    Write-Host "🚀 Applying Docker Engine optimizations..." -ForegroundColor Green
    
    # Check if Docker Desktop is running
    if (Test-DockerDesktopRunning) {
        Write-Host "⚠️  Docker Desktop is currently running" -ForegroundColor Yellow
        Write-Host "🔄 It will be restarted to apply optimizations" -ForegroundColor Cyan
        $continue = Read-Host "Continue? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "❌ Operation cancelled" -ForegroundColor Red
            exit 0
        }
    }
    
    # Apply optimizations
    Write-Host "📝 Optimizing Docker daemon configuration..." -ForegroundColor Cyan
    if (!(Optimize-DockerDaemon)) {
        Write-Host "❌ Failed to optimize daemon configuration" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📝 Optimizing WSL configuration..." -ForegroundColor Cyan
    if (!(Optimize-WSLConfiguration)) {
        Write-Host "❌ Failed to optimize WSL configuration" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📝 Optimizing Docker Desktop settings..." -ForegroundColor Cyan
    if (!(Optimize-DockerDesktopSettings)) {
        Write-Host "❌ Failed to optimize Docker Desktop settings" -ForegroundColor Red
        exit 1
    }
    
    # Restart Docker Desktop
    Write-Host "🔄 Restarting Docker Desktop to apply optimizations..." -ForegroundColor Yellow
    if (Restart-DockerDesktop) {
        Write-Host "✅ Docker Engine optimization completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎯 Optimizations applied:" -ForegroundColor Cyan
        Write-Host "  • Enhanced Docker daemon configuration" -ForegroundColor White
        Write-Host "  • Optimized WSL2 settings for Docker" -ForegroundColor White
        Write-Host "  • Improved Docker Desktop resource allocation" -ForegroundColor White
        Write-Host "  • Better stability and performance" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 You can now use '.\cslaunch.ps1' to start CaseStrainer" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to restart Docker Desktop" -ForegroundColor Red
        Write-Host "🔄 Please restart Docker Desktop manually to apply optimizations" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "📋 Usage Options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  .\optimize_docker_engine.ps1 -ShowCurrent    # Show current configuration" -ForegroundColor Cyan
    Write-Host "  .\optimize_docker_engine.ps1 -Apply          # Apply optimizations" -ForegroundColor Green
    Write-Host "  .\optimize_docker_engine.ps1 -RestoreDefaults # Restore factory defaults" -ForegroundColor Yellow
    Write-Host "  .\optimize_docker_engine.ps1 -Verbose        # Show detailed output" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 This script will optimize Docker Desktop for:" -ForegroundColor White
    Write-Host "  • Better stability and performance" -ForegroundColor Gray
    Write-Host "  • Optimized resource allocation" -ForegroundColor Gray
    Write-Host "  • Enhanced WSL2 integration" -ForegroundColor Gray
    Write-Host "  • Production-ready daemon settings" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Recommended: Run with -Apply after factory reset" -ForegroundColor Green
}
