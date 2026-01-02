# Default Monitoring Enabled

## Overview

Monitoring is now **enabled by default** in `cslaunch.ps1`. Docker daemon monitoring starts automatically after containers are successfully started or restarted, without requiring any flags.

## What's Changed

### Before
```powershell
# Monitoring required explicit flag
.\cslaunch.ps1 -Monitor
```

### After
```powershell
# Monitoring starts automatically
.\cslaunch.ps1

# Can be disabled if needed
.\cslaunch.ps1 -NoMonitor
```

## Monitoring Modes

### 1. **Background Monitoring (Default)**
- **When**: Starts automatically after containers are started/restarted
- **What**: Lightweight Docker daemon health checks only
- **How**: Runs as a background PowerShell job
- **Features**:
  - Checks Docker daemon health every 60 seconds (2x MonitorInterval)
  - Detects freezes and logs alerts
  - Does NOT auto-restart (requires admin privileges)
  - Alerts recommend using `-Monitor` flag for full monitoring

**Usage:**
```powershell
# Just start containers - monitoring starts automatically
.\cslaunch.ps1

# Monitoring runs in background
# View logs: Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait
```

### 2. **Foreground Monitoring (Explicit)**
- **When**: Use `-Monitor` flag
- **What**: Full monitoring with container checks + Docker daemon monitoring
- **How**: Runs in foreground (blocks until Ctrl+C)
- **Features**:
  - Container health checks
  - Container auto-restart
  - Docker daemon health checks
  - Docker daemon auto-restart (with admin privileges)
  - Comprehensive logging

**Usage:**
```powershell
# Full monitoring mode
.\cslaunch.ps1 -Monitor

# Custom intervals
.\cslaunch.ps1 -Monitor -MonitorInterval 60 -DockerDaemonTimeout 20
```

### 3. **No Monitoring**
- **When**: Use `-NoMonitor` flag
- **What**: Disables all automatic monitoring
- **Use Case**: When you want to manage monitoring separately

**Usage:**
```powershell
# Start containers without monitoring
.\cslaunch.ps1 -NoMonitor
```

## Background Monitoring Details

### What It Monitors
- Docker daemon health (Docker info, Docker ps)
- Detects freezes (timeout-based)
- Logs alerts when issues detected

### What It Doesn't Do
- Container health checks (use `-Monitor` for that)
- Auto-restart Docker daemon (requires admin, use `-Monitor` for that)
- Auto-restart containers (use `-Monitor` for that)

### Logs
- `logs\docker_daemon_monitor.log` - Docker daemon health checks
- Alerts when Docker daemon appears frozen

### Managing Background Monitoring

**Check if running:**
```powershell
Get-Job -Name "CaseStrainer-Monitor"
```

**View logs:**
```powershell
Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait
```

**Stop monitoring:**
```powershell
Stop-Job -Name CaseStrainer-Monitor
Remove-Job -Name CaseStrainer-Monitor
```

**Restart monitoring:**
```powershell
# Just restart containers - monitoring will start automatically
.\cslaunch.ps1
```

## Examples

### Normal Usage (Monitoring Enabled by Default)
```powershell
# Start containers - monitoring starts automatically in background
.\cslaunch.ps1

# Output:
# [OK] Found 8 running containers
# [QUICK RESTART] Restarting containers...
# [OK] Containers restarted successfully
# [INFO] Starting background Docker daemon monitoring...
# [OK] Background monitoring started (job ID: 123)
```

### Full Monitoring Mode
```powershell
# Start containers and run full monitoring in foreground
.\cslaunch.ps1 -Monitor

# Output:
# ========================================
# MONITORING MODE - Press Ctrl+C to stop
# ========================================
# Container Check Interval: 30 seconds
# Docker Daemon Monitor: ENABLED
# ...
```

### Disable Monitoring
```powershell
# Start containers without any monitoring
.\cslaunch.ps1 -NoMonitor

# Output:
# [OK] Found 8 running containers
# [QUICK RESTART] Restarting containers...
# [OK] Containers restarted successfully
# [INFO] Background monitoring disabled (NoMonitor flag)
```

## Configuration

### Default Settings
- **Monitor Interval**: 30 seconds
- **Docker Daemon Timeout**: 15 seconds
- **Max Restarts/Hour**: 3
- **Docker Daemon Monitor**: Enabled

### Customize Defaults
```powershell
# Custom intervals (applies to background monitoring too)
.\cslaunch.ps1 -MonitorInterval 60 -DockerDaemonTimeout 20
```

## Migration Guide

### If You Were Using `-Monitor` Flag

**Before:**
```powershell
.\cslaunch.ps1 -Monitor
```

**After:**
- **Option 1**: Just use `.\cslaunch.ps1` - background monitoring starts automatically
- **Option 2**: Keep using `.\cslaunch.ps1 -Monitor` for full foreground monitoring

### If You Want to Disable Monitoring

**Before:**
```powershell
.\cslaunch.ps1  # No monitoring
```

**After:**
```powershell
.\cslaunch.ps1 -NoMonitor  # Explicitly disable
```

## Benefits

1. **Always Protected**: Docker daemon monitoring runs automatically
2. **No Extra Steps**: No need to remember to start monitoring
3. **Lightweight**: Background monitoring has minimal overhead
4. **Flexible**: Can still use `-Monitor` for full monitoring or `-NoMonitor` to disable

## Troubleshooting

### Monitoring Not Starting

1. **Check if disabled:**
   ```powershell
   # Make sure you didn't use -NoMonitor
   ```

2. **Check if job exists:**
   ```powershell
   Get-Job -Name "CaseStrainer-Monitor"
   ```

3. **Check logs:**
   ```powershell
   Get-Content logs\docker_daemon_monitor.log -Tail 50
   ```

### Too Many Background Jobs

If you see multiple monitoring jobs:
```powershell
# Remove all monitoring jobs
Get-Job -Name "CaseStrainer-Monitor" | Remove-Job -Force

# Restart containers - new monitoring will start
.\cslaunch.ps1
```

### Want Full Monitoring Instead

If background monitoring detects issues and you want full monitoring with auto-restart:
```powershell
# Stop background monitoring
Stop-Job -Name CaseStrainer-Monitor; Remove-Job -Name CaseStrainer-Monitor

# Start full monitoring
.\cslaunch.ps1 -Monitor
```










