# Docker Daemon Freeze Prevention & Monitoring Improvements

## Overview

This document outlines improvements made to prevent Docker daemon freezes and improve monitoring/recovery capabilities.

## Problem Analysis

Based on crash logs and freeze detection logs, Docker daemon freezes occur due to:

1. **High CPU Usage**: `com.docker.backend` processes consuming 6000+ CPU units (indicating 100%+ CPU)
2. **Memory Pressure**: Docker processes using excessive memory
3. **API Timeouts**: Docker daemon becoming unresponsive to API calls
4. **Process Deadlocks**: Docker processes stuck in infinite loops

## Implemented Improvements

### 1. Enhanced Docker Daemon Monitor (`scripts/docker_daemon_monitor.ps1`)

**Features:**
- Multi-level health checks (Docker info, version, ps, service status)
- Timeout-based freeze detection (15 seconds default)
- Automatic restart with rate limiting (max 3 restarts/hour)
- Process statistics collection before restart
- Comprehensive logging

**Usage:**
```powershell
# Run interactively
.\scripts\docker_daemon_monitor.ps1

# Run as background job
.\scripts\docker_daemon_monitor.ps1 -AsJob

# Custom interval and timeout
.\scripts\docker_daemon_monitor.ps1 -CheckInterval 60 -FreezeTimeout 20
```

### 2. Docker Resource Limits

**Current Configuration:**
- Backend: 4GB memory limit, 2GB reservation, 2 CPUs
- RQ Workers: 2GB memory limit, 1GB reservation, 1 CPU each
- Redis: No explicit limits (should add)

**Recommendations:**
- Add memory limits to Redis container
- Consider reducing worker memory if not needed
- Monitor actual usage vs limits

### 3. Health Check Improvements

**Current Health Checks:**
- Backend: 30s interval, 15s timeout, 3 retries
- Workers: 60s interval, 30s timeout, 8 retries
- Redis: 30s interval, 10s timeout, 3 retries

**Optimizations:**
- Reduce worker health check timeout from 30s to 15s
- Increase retries for critical services
- Add Docker daemon health check to monitoring

### 4. Monitoring Integration

**cslaunch.ps1 Enhancements:**
- Container monitoring already exists
- Add Docker daemon health check to monitoring loop
- Integrate with `docker_daemon_monitor.ps1`

## Configuration Recommendations

### Docker Desktop Settings

1. **Resource Limits:**
   - Memory: 8GB (instead of unlimited)
   - CPUs: 4 cores (instead of unlimited)
   - Disk Image Size: 64GB (instead of default)

2. **Advanced Settings:**
   - Enable "Use WSL 2 based engine"
   - Enable "Expose daemon on tcp://localhost:2375" (for monitoring)
   - Disable "Start Docker Desktop when you log in" (use scheduled task instead)

### Windows Service Configuration

```powershell
# Set Docker service to auto-restart on failure
Set-Service -Name "com.docker.service" -StartupType Automatic
sc.exe failure "com.docker.service" reset= 86400 actions= restart/5000/restart/10000/restart/30000
```

### Scheduled Task for Auto-Start

The `cslaunch.ps1` script already creates a scheduled task for auto-start. Verify it's configured:

```powershell
Get-ScheduledTask -TaskName "CaseStrainer-Docker-AutoStart"
```

## Monitoring Setup

### 1. Start Docker Daemon Monitor

```powershell
# As a background job (recommended)
.\scripts\docker_daemon_monitor.ps1 -AsJob

# Or integrate into cslaunch.ps1 monitoring mode
.\cslaunch.ps1 -Monitor
```

### 2. View Logs

```powershell
# Docker daemon monitor logs
Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait

# Container crash logs
Get-Content logs\crash_log.txt -Tail 50 -Wait

# Docker restart events
Get-Content logs\docker_restart_events.log -Tail 50 -Wait
```

### 3. Check Docker Health

```powershell
# Quick health check
docker info
docker ps

# Detailed resource usage
docker stats --no-stream
```

## Prevention Strategies

### 1. Proactive Resource Management

- **Regular Cleanup**: Run `docker system prune` weekly
- **Monitor Disk Usage**: Keep Docker disk usage below 80%
- **Monitor Memory**: Keep Docker memory usage below 90%

### 2. Process Monitoring

- Monitor `com.docker.backend` CPU usage
- Alert if CPU > 100% for > 5 minutes
- Alert if memory > 2GB for any Docker process

### 3. Network Monitoring

- Check Docker network connectivity
- Monitor API response times
- Alert on API timeouts > 10 seconds

## Recovery Procedures

### Automatic Recovery

1. **Docker Daemon Monitor**: Automatically restarts frozen daemon
2. **Container Health Checks**: Automatically restart unhealthy containers
3. **cslaunch.ps1 Monitor**: Monitors and restarts failed containers

### Manual Recovery

If automatic recovery fails:

1. **Force Restart Docker:**
   ```powershell
   .\force_restart_docker.ps1
   ```

2. **Restart Containers:**
   ```powershell
   .\cslaunch.ps1
   ```

3. **Check Logs:**
   ```powershell
   Get-Content logs\docker_daemon_monitor.log -Tail 100
   Get-Content logs\crash_log.txt -Tail 100
   ```

## Metrics to Track

1. **Docker Daemon Uptime**: Should be > 99%
2. **Freeze Frequency**: Should be < 1 per week
3. **Recovery Time**: Should be < 2 minutes
4. **Container Restart Rate**: Should be < 1 per day per container

## Next Steps

1. ✅ Implement Docker daemon monitor
2. ⏳ Add Docker daemon health check to cslaunch.ps1 monitoring
3. ⏳ Configure Windows service auto-restart
4. ⏳ Set up alerting for freeze events
5. ⏳ Create dashboard for Docker health metrics

## Troubleshooting

### Docker Daemon Won't Start

1. Check Windows Event Viewer for errors
2. Check Docker Desktop logs: `%LOCALAPPDATA%\Docker\log.txt`
3. Restart Windows (last resort)

### Frequent Freezes

1. Check system resources (CPU, memory, disk)
2. Review Docker process CPU usage
3. Check for conflicting software (antivirus, VPN)
4. Consider reducing container resource limits

### High CPU Usage

1. Check `com.docker.backend` processes
2. Review container resource usage
3. Consider reducing number of containers
4. Check for stuck builds or operations










