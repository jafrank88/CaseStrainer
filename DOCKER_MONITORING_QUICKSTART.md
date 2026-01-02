# Docker Daemon Monitoring - Quick Start Guide

## Problem Solved

Docker daemon was freezing frequently, requiring manual login and restart. This monitoring system automatically detects freezes and restarts the Docker daemon.

## Quick Setup (5 minutes)

### 1. Install Monitoring (Run as Administrator)

```powershell
.\scripts\setup_docker_monitoring.ps1 -Install
```

This will:
- ✅ Configure Docker service to auto-restart on failure
- ✅ Create scheduled task to start monitor on boot
- ✅ Set up failure recovery actions

### 2. Start Monitor Now

```powershell
# As background job (recommended)
.\scripts\docker_daemon_monitor.ps1 -AsJob

# Or interactively (for testing)
.\scripts\docker_daemon_monitor.ps1
```

### 3. Verify It's Working

```powershell
# Check status
.\scripts\setup_docker_monitoring.ps1 -Status

# View monitor logs
Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait
```

## What It Does

### Automatic Monitoring
- Checks Docker daemon health every 30 seconds
- Detects freezes within 15 seconds
- Automatically restarts frozen Docker daemon
- Limits restarts to 3 per hour (prevents restart loops)

### Integration with Existing Monitoring
- `cslaunch.ps1 -Monitor` now includes Docker daemon health checks
- Container monitoring continues to work as before
- All logs go to `logs\docker_daemon_monitor.log`

## Monitoring Features

### Health Checks
1. **Docker Info**: Basic daemon connectivity
2. **Docker Version**: Quick API response test
3. **Docker Ps**: Container listing capability
4. **Service Status**: Windows service health

### Freeze Detection
- Timeout-based detection (15 seconds default)
- Process statistics collection before restart
- Comprehensive logging of freeze events

### Auto-Recovery
- Graceful shutdown of Docker Desktop
- Service restart
- Process cleanup
- Automatic restart with health verification

## Logs

### Monitor Logs
```powershell
# Real-time monitoring
Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait

# Recent events
Get-Content logs\docker_daemon_monitor.log -Tail 100
```

### Crash Logs (existing)
```powershell
Get-Content logs\crash_log.txt -Tail 50
```

## Troubleshooting

### Monitor Not Starting

1. **Check if script exists:**
   ```powershell
   Test-Path scripts\docker_daemon_monitor.ps1
   ```

2. **Check PowerShell execution policy:**
   ```powershell
   Get-ExecutionPolicy
   # If Restricted, run:
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Run manually to see errors:**
   ```powershell
   .\scripts\docker_daemon_monitor.ps1
   ```

### Monitor Running But Not Detecting Freezes

1. **Check log file:**
   ```powershell
   Get-Content logs\docker_daemon_monitor.log -Tail 50
   ```

2. **Verify health checks are running:**
   - Look for "Docker daemon health check: OK" messages
   - Should appear every 5 minutes

3. **Adjust timeout if needed:**
   ```powershell
   .\scripts\docker_daemon_monitor.ps1 -FreezeTimeout 20
   ```

### Too Many Restarts

1. **Check restart history:**
   ```powershell
   Select-String -Path logs\docker_daemon_monitor.log -Pattern "RESTART"
   ```

2. **Review system resources:**
   ```powershell
   docker stats --no-stream
   Get-Process | Where-Object {$_.ProcessName -like "*docker*"} | Select-Object ProcessName, CPU, WorkingSet
   ```

3. **Consider increasing rate limit:**
   - Edit `scripts\docker_daemon_monitor.ps1`
   - Change `$MaxRestartsPerHour` parameter

## Advanced Configuration

### Custom Intervals

```powershell
# Check every 60 seconds, timeout after 20 seconds
.\scripts\docker_daemon_monitor.ps1 -CheckInterval 60 -FreezeTimeout 20
```

### Run as Scheduled Task

Already configured by `setup_docker_monitoring.ps1 -Install`. To modify:

```powershell
# View task
Get-ScheduledTask -TaskName "DockerDaemonMonitor"

# Modify trigger
$task = Get-ScheduledTask -TaskName "DockerDaemonMonitor"
$trigger = $task.Triggers[0]
$trigger.Delay = "PT10M"  # 10 minutes delay
Set-ScheduledTask -TaskName "DockerDaemonMonitor" -Trigger $trigger
```

## Integration with cslaunch.ps1

The existing `cslaunch.ps1 -Monitor` command now includes Docker daemon health checks:

```powershell
# Start container monitoring (includes Docker daemon checks)
.\cslaunch.ps1 -Monitor

# Custom interval
.\cslaunch.ps1 -Monitor -MonitorInterval 60
```

## Uninstall

```powershell
# Run as Administrator
.\scripts\setup_docker_monitoring.ps1 -Uninstall
```

## Support

For issues or questions:
1. Check logs: `logs\docker_daemon_monitor.log`
2. Review documentation: `docs\DOCKER_DAEMON_IMPROVEMENTS.md`
3. Check status: `.\scripts\setup_docker_monitoring.ps1 -Status`










