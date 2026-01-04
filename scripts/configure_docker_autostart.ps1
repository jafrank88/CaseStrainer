# Configure Docker Desktop to start automatically with Windows
# This script sets up Docker Desktop for automatic startup and recovery

param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
}

function Enable-DockerAutostart {
    Write-Log "Enabling Docker Desktop autostart..."
    
    # Method 1: Set Docker Desktop to start with Windows
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        # Create shortcut in startup folder
        $startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
        $shortcutPath = Join-Path $startupFolder "Docker Desktop.lnk"
        
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $dockerDesktopPath
        $shortcut.Arguments = "--autostart"
        $shortcut.WorkingDirectory = Split-Path $dockerDesktopPath -Parent
        $shortcut.Save()
        
        Write-Log "Created startup shortcut: $shortcutPath"
    }
    
    # Method 2: Configure Docker Desktop settings
    $settingsPath = "$env:APPDATA\Docker\settings.json"
    if (Test-Path $settingsPath) {
        try {
            $settings = Get-Content $settingsPath | ConvertFrom-Json
            $settings.autoStart = $true
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            Write-Log "Updated Docker Desktop settings to enable autostart"
        }
        catch {
            Write-Log "Failed to update Docker Desktop settings: $($_.Exception.Message)" "WARN"
        }
    }
    
    # Method 3: Set Docker service to automatic
    try {
        Set-Service -Name "com.docker.service" -StartupType Automatic
        Write-Log "Set com.docker.service to automatic startup"
    }
    catch {
        Write-Log "Failed to set service startup type: $($_.Exception.Message)" "WARN"
    }
    
    # Method 4: Configure Windows to restart service on failure
    try {
        $serviceName = "com.docker.service"
        sc.exe failure $serviceName reset= 86400 actions= restart/5000/restart/20000/restart/60000
        Write-Log "Configured service recovery actions for com.docker.service"
    }
    catch {
        Write-Log "Failed to configure service recovery: $($_.Exception.Message)" "WARN"
    }
    
    Write-Log "Docker Desktop autostart enabled successfully"
}

function Disable-DockerAutostart {
    Write-Log "Disabling Docker Desktop autostart..."
    
    # Remove startup shortcut
    $shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Docker Desktop.lnk"
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-Log "Removed startup shortcut"
    }
    
    # Update Docker Desktop settings
    $settingsPath = "$env:APPDATA\Docker\settings.json"
    if (Test-Path $settingsPath) {
        try {
            $settings = Get-Content $settingsPath | ConvertFrom-Json
            $settings.autoStart = $false
            $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
            Write-Log "Updated Docker Desktop settings to disable autostart"
        }
        catch {
            Write-Log "Failed to update Docker Desktop settings: $($_.Exception.Message)" "WARN"
        }
    }
    
    # Set Docker service to manual
    try {
        Set-Service -Name "com.docker.service" -StartupType Manual
        Write-Log "Set com.docker.service to manual startup"
    }
    catch {
        Write-Log "Failed to set service startup type: $($_.Exception.Message)" "WARN"
    }
    
    Write-Log "Docker Desktop autostart disabled"
}

function Get-AutostartStatus {
    Write-Log "Checking Docker Desktop autostart status..."
    
    # Check startup shortcut
    $shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Docker Desktop.lnk"
    $hasShortcut = Test-Path $shortcutPath
    Write-Log "Startup shortcut exists: $hasShortcut"
    
    # Check Docker Desktop settings
    $settingsPath = "$env:APPDATA\Docker\settings.json"
    if (Test-Path $settingsPath) {
        try {
            $settings = Get-Content $settingsPath | ConvertFrom-Json
            $autoStartSetting = $settings.autoStart
            Write-Log "Docker Desktop autoStart setting: $autoStartSetting"
        }
        catch {
            Write-Log "Could not read Docker Desktop settings" "WARN"
        }
    }
    
    # Check service startup type
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Log "Service startup type: $($service.StartType)"
            Write-Log "Service status: $($service.Status)"
        }
    }
    catch {
        Write-Log "Could not get service information" "WARN"
    }
    
    # Check service recovery settings
    try {
        $recoveryInfo = sc.exe qfailure "com.docker.service" 2>$null
        if ($recoveryInfo) {
            Write-Log "Service recovery configuration:"
            $recoveryInfo | ForEach-Object { Write-Log "  $_" }
        }
    }
    catch {
        Write-Log "Could not get service recovery information" "WARN"
    }
}

# Main execution
if ($Enable) {
    Enable-DockerAutostart
}
elseif ($Disable) {
    Disable-DockerAutostart
}
elseif ($Status) {
    Get-AutostartStatus
}
else {
    Write-Host "Usage:"
    Write-Host "  .\configure_docker_autostart.ps1 -Enable   # Enable autostart"
    Write-Host "  .\configure_docker_autostart.ps1 -Disable  # Disable autostart"
    Write-Host "  .\configure_docker_autostart.ps1 -Status   # Check current status"
}
