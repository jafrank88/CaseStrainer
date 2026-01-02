# Docker Daemon Monitoring Integration into cslaunch.ps1

## Overview

Docker daemon monitoring has been fully integrated into `cslaunch.ps1`, eliminating the need for separate monitoring scripts. All Docker daemon health checks and auto-recovery are now managed through the main launcher script.

## New Parameters

### Command-Line Parameters

```powershell
.\cslaunch.ps1 -Monitor [options]
```

**New Options:**
- `-EnableDockerDaemonMonitor` (default: `$true`) - Enable/disable Docker daemon monitoring
- `-DockerDaemonTimeout` (default: `15`) - Freeze detection timeout in seconds
- `-MaxDockerRestartsPerHour` (default: `3`) - Maximum Docker daemon restarts per hour

**Existing Options:**
- `-Monitor` - Enable monitoring mode
- `-MonitorInterval` (default: `30`) - Container health check interval in seconds

### Examples

```powershell
# Standard monitoring with Docker daemon monitoring enabled (default)
.\cslaunch.ps1 -Monitor

# Monitoring with custom intervals
.\cslaunch.ps1 -Monitor -MonitorInterval 60 -DockerDaemonTimeout 20

# Disable Docker daemon monitoring (only monitor containers)
.\cslaunch.ps1 -Monitor -EnableDockerDaemonMonitor:$false

# Increase restart rate limit
.\cslaunch.ps1 -Monitor -MaxDockerRestartsPerHour 5
```

## Integrated Features

### 1. Docker Daemon Health Checks

**Multi-Level Health Checks:**
- Docker Info: Basic daemon connectivity
- Docker Version: Quick API response test
- Docker Ps: Container listing capability
- Service Status: Windows service health

**Check Frequency:**
- Every 2 monitoring cycles (to avoid overhead)
- Immediately if previous failures detected
- Configurable timeout (default: 15 seconds)

### 2. Freeze Detection

**Detection Logic:**
- Timeout-based detection (configurable, default 15s)
- Requires 2 consecutive failures before restart attempt
- Process statistics collection for diagnostics
- Comprehensive logging to `logs\docker_daemon_monitor.log`

### 3. Auto-Recovery

**Recovery Process:**
1. Graceful shutdown of Docker Desktop
2. Stop Docker service
3. Clean up remaining Docker processes
4. Start Docker service
5. Start Docker Desktop
6. Wait for Docker to become ready (max 2 minutes)
7. Verify health before continuing

**Rate Limiting:**
- Maximum 3 restarts per hour (configurable)
- Prevents restart loops
- Tracks restart history for 24 hours

### 4. Logging

**Log Files:**
- `logs\docker_daemon_monitor.log` - Docker daemon specific logs
- `logs\crash_log.txt` - Container crashes and Docker daemon restarts

**Log Levels:**
- INFO: Normal operations, health checks
- WARN: Freeze detection, restart attempts
- ERROR: Failed health checks, restart failures
- SUCCESS: Successful recovery

## Monitoring Flow

```
┌─────────────────────────────────────┐
│  cslaunch.ps1 -Monitor              │
└──────────────┬──────────────────────┘
               │
               ├─► Container Monitoring (every MonitorInterval)
               │   ├─ Check container status
               │   ├─ Check container health
               │   └─ Auto-restart failed containers
               │
               └─► Docker Daemon Monitoring (every 2 cycles)
                   ├─ Multi-level health checks
                   ├─ Freeze detection
                   ├─ Process statistics
                   └─ Auto-restart if frozen (with rate limiting)
```

## Usage Examples

### Basic Monitoring

```powershell
# Start monitoring (Docker daemon monitoring enabled by default)
.\cslaunch.ps1 -Monitor
```

**Output:**
```
========================================
MONITORING MODE - Press Ctrl+C to stop
========================================

Container Check Interval: 30 seconds
Crash log: logs\crash_log.txt
Docker Daemon Monitor: ENABLED
  - Freeze timeout: 15s
  - Max restarts/hour: 3
  - Daemon log: logs\docker_daemon_monitor.log

[INFO] Docker daemon monitoring enabled
[10:30:00] All services healthy
[10:30:30] All services healthy
```

### Custom Configuration

```powershell
# Faster checks, longer timeout, more restarts allowed
.\cslaunch.ps1 -Monitor `
    -MonitorInterval 15 `
    -DockerDaemonTimeout 20 `
    -MaxDockerRestartsPerHour 5
```

### Container-Only Monitoring

```powershell
# Disable Docker daemon monitoring (only monitor containers)
.\cslaunch.ps1 -Monitor -EnableDockerDaemonMonitor:$false
```

## What Happens During a Freeze

1. **Detection** (after 2 consecutive failures):
   ```
   [10:30:00] ⚠️  Docker daemon health check failed (1/2)
   [10:30:30] ⚠️  Docker daemon health check failed (2/2)
   [10:30:30] ⚠️  Docker daemon appears frozen - attempting restart...
   ```

2. **Restart Process**:
   ```
   === DOCKER DAEMON RESTART INITIATED ===
   Stopping Docker Desktop...
   Stopping Docker service...
   Cleaning up remaining Docker processes...
   Starting Docker service...
   Starting Docker Desktop...
   Waiting for Docker to become ready...
   ```

3. **Recovery**:
   ```
   === DOCKER DAEMON RESTART SUCCESSFUL ===
   Recovery completed in 45 seconds
   [10:31:15] ✅ Docker daemon restarted successfully
   ```

4. **Rate Limiting** (if too many restarts):
   ```
   [10:32:00] ⚠️  Docker daemon frozen but restart rate limit reached
     Recent restarts: 3 in last hour
   ```

## Benefits of Integration

1. **Single Command**: One script manages everything
2. **Unified Logging**: All monitoring logs in one place
3. **Coordinated Recovery**: Docker daemon and containers restart together
4. **Simplified Configuration**: All settings in one place
5. **Better Diagnostics**: Combined container and daemon health information

## Migration from Separate Scripts

If you were using `scripts\docker_daemon_monitor.ps1` separately:

**Before:**
```powershell
# Start container monitoring
.\cslaunch.ps1 -Monitor

# Start Docker daemon monitoring separately
.\scripts\docker_daemon_monitor.ps1 -AsJob
```

**After:**
```powershell
# Everything in one command
.\cslaunch.ps1 -Monitor
```

The separate `docker_daemon_monitor.ps1` script is still available for standalone use if needed, but integration into `cslaunch.ps1` is recommended.

## Troubleshooting

### Docker Daemon Monitoring Not Working

1. **Check if enabled:**
   ```powershell
   # Should show "Docker Daemon Monitor: ENABLED"
   .\cslaunch.ps1 -Monitor
   ```

2. **Check logs:**
   ```powershell
   Get-Content logs\docker_daemon_monitor.log -Tail 50
   ```

3. **Verify health checks:**
   ```powershell
   docker info
   docker ps
   ```

### Too Many Restarts

1. **Check restart history in logs:**
   ```powershell
   Select-String -Path logs\docker_daemon_monitor.log -Pattern "RESTART"
   ```

2. **Review system resources:**
   ```powershell
   docker stats --no-stream
   Get-Process | Where-Object {$_.ProcessName -like "*docker*"}
   ```

3. **Adjust rate limit:**
   ```powershell
   .\cslaunch.ps1 -Monitor -MaxDockerRestartsPerHour 5
   ```

## Configuration Recommendations

### Production Environment

```powershell
# Recommended settings for production
.\cslaunch.ps1 -Monitor `
    -MonitorInterval 30 `
    -DockerDaemonTimeout 15 `
    -MaxDockerRestartsPerHour 3
```

### Development Environment

```powershell
# Faster checks for development
.\cslaunch.ps1 -Monitor `
    -MonitorInterval 15 `
    -DockerDaemonTimeout 10 `
    -MaxDockerRestartsPerHour 5
```

### High-Availability Setup

```powershell
# More aggressive monitoring and recovery
.\cslaunch.ps1 -Monitor `
    -MonitorInterval 20 `
    -DockerDaemonTimeout 10 `
    -MaxDockerRestartsPerHour 6
```

## Next Steps

1. ✅ Docker daemon monitoring integrated
2. ✅ Auto-recovery implemented
3. ✅ Rate limiting configured
4. ✅ Comprehensive logging
5. ⏳ Consider adding email/Slack alerts for critical failures
6. ⏳ Add metrics dashboard integration










