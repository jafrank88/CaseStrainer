# Docker Monitoring and Restart Logging Guide

## Overview

Your Docker health monitoring system now includes comprehensive logging for restart events and freeze detection. This allows you to track patterns, identify root causes, and monitor the effectiveness of auto-recovery.

## Log Files Created

### 1. Health Monitoring (`logs/docker_health_monitor.log`)
- **Purpose**: Records all health check activities
- **Content**: Start/end of health checks, test results, overall health status
- **Example entries**:
```
[2025-08-19 15:53:00] [INFO] === HEALTH CHECK STARTED ===
[2025-08-19 15:53:01] [INFO] Docker CLI test passed in < 10 seconds
[2025-08-19 15:53:02] [SUCCESS] === HEALTH CHECK PASSED ===
```

### 2. Restart Events (`logs/docker_restart_events.log`)
- **Purpose**: Tracks all Docker restart attempts and outcomes
- **Content**: Restart triggers, unique IDs, success/failure status, duration
- **Example entries**:
```
[2025-08-19 15:51:37] [RESTART] === DOCKER RESTART INITIATED ===
[2025-08-19 15:51:37] [RESTART] Restart ID: f944bb44
[2025-08-19 15:51:37] [RESTART] Reason: Health check failed: Docker CLI unresponsive
[2025-08-19 15:52:15] [SUCCESS] === DOCKER RESTART SUCCESSFUL ===
[2025-08-19 15:52:15] [SUCCESS] Recovery completed in 65 seconds
```

### 3. Freeze Detection (`logs/docker_freeze_detection.log`)
- **Purpose**: Records when Docker becomes unresponsive (timeouts)
- **Content**: Test name, timeout duration, process info during freeze
- **Example entries**:
```
[2025-08-19 02:15:30] [FREEZE] === DOCKER FREEZE DETECTED ===
[2025-08-19 02:15:30] [FREEZE] Test: Docker CLI Version Check
[2025-08-19 02:15:30] [FREEZE] Timeout: 10 seconds
[2025-08-19 02:15:30] [FREEZE] Docker appears to be frozen/unresponsive
```

## Freeze Detection Features

### What Triggers Freeze Detection
1. **Docker CLI timeouts** - If `docker --version` takes >10 seconds
2. **Docker daemon timeouts** - If `docker system info` takes >15 seconds
3. **API communication failures** - If Docker API becomes unresponsive

### Process Information During Freezes
When a freeze is detected, the system automatically captures:
- All running Docker processes (PID, CPU, Memory)
- System resource usage
- Timestamp and exact test that failed

## Restart Tracking Features

### Unique Restart IDs
- Each restart gets a unique 8-character ID (e.g., `f944bb44`)
- Allows tracking specific restart events from initiation to completion
- Correlate issues across multiple log files

### Detailed Restart Reasons
- **Health check failures**: Specific tests that failed
- **Manual triggers**: User-initiated restarts
- **Scheduled maintenance**: Planned restart events

### Success/Failure Tracking
- **Duration tracking**: How long each restart took
- **Retry attempts**: Number of attempts before success/failure
- **Docker version verification**: Confirms Docker is responding after restart

## Log Analysis Tools

### Basic Analysis
```powershell
# View recent health check results
.\analyze_docker_logs.ps1

# Show detailed restart and freeze events
.\analyze_docker_logs.ps1 -ShowRestarts -ShowFreezes

# Analyze last 30 days
.\analyze_docker_logs.ps1 -Days 30
```

### Analysis Output
- **Health Check Summary**: Pass/fail rates and percentages
- **Restart Summary**: Number of attempts, success rate
- **Freeze Detection**: Frequency and patterns
- **Pattern Analysis**: Time-based failure patterns
- **Recent Trends**: Success rate of last 10 checks

## Troubleshooting Common Issues

### High Restart Frequency
If you see frequent restarts:
1. Check the restart events log for patterns
2. Look for specific failure reasons
3. Check if freezes occur at specific times
4. Consider resource constraints

### Freeze Detection False Positives
If timeouts occur during heavy load:
1. Review freeze detection thresholds
2. Check system resources during freeze times
3. Consider increasing timeout values for your environment

### Restart Failures
If restarts consistently fail:
1. Check restart events log for failure reasons
2. Look for "DOCKER RESTART FAILED" entries
3. May indicate deeper system issues requiring manual intervention

## Scheduled Task Integration

The enhanced logging works with your scheduled task:
- **Runs every 5 minutes** via `DockerHealthCheck` task
- **Auto-restart enabled by default** for 24/7 recovery
- **Comprehensive logging** for all automated activities

## 2am Auto-Recovery

Your question about 2am auto-recovery is now fully answered:

✅ **YES** - Docker will automatically restart at 2am (or any time) if it becomes unresponsive

✅ **Comprehensive logging** tracks all restart events with timestamps

✅ **Freeze detection** identifies when Docker becomes unresponsive

✅ **Pattern analysis** helps identify recurring issues

## Log File Locations

All logs are stored in the `logs/` directory:
- `docker_health_monitor.log` - Overall health monitoring
- `docker_restart_events.log` - Restart tracking  
- `docker_freeze_detection.log` - Freeze/timeout detection

## Monitoring Commands

```powershell
# Quick health status
.\docker_health_check.ps1

# View recent activity
.\analyze_docker_logs.ps1

# Monitor logs in real-time
Get-Content logs\docker_health_monitor.log -Wait

# Check recent restarts
Get-Content logs\docker_restart_events.log -Tail 20
```

Your Docker monitoring system now provides complete visibility into Docker health, automatic recovery, and detailed forensics for troubleshooting any issues that occur, including at 2am or any other time!

