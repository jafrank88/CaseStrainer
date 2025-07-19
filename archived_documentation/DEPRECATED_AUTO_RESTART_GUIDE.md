# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# CaseStrainer Auto-Restart System Guide

## Overview

CaseStrainer includes a robust auto-restart system that automatically monitors and recovers from service failures. The system can automatically start Docker Desktop, manage Redis containers, and restart all application services when needed.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Auto-Restart Features](#auto-restart-features)
- [Service Management](#service-management)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [Log Files](#log-files)
- [Emergency Procedures](#emergency-procedures)

## Prerequisites

Before using CaseStrainer with auto-restart, ensure you have:

- **Windows 10/11** with PowerShell
- **Node.js** and **npm** installed
- **Python 3.8+** installed
- **Docker Desktop** installed (recommended for Redis)
- **CaseStrainer** project downloaded and extracted

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB free space
- **Network**: Internet connection for API calls
- **Ports**: 5000, 5173, 6379 (Redis), 443 (production)

## Quick Start

### 1. Navigate to CaseStrainer Directory

```powershell
cd "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
```

### 2. Start CaseStrainer

```powershell
.\launcher.ps1
```

### 3. Choose Environment

When the menu appears, select:

- **Option 1**: Development Mode (recommended for testing)
- **Option 2**: Production Mode (for production use)

### 4. Handle Redis Setup (if needed)

If Docker Desktop isn't running, you'll see:

```
=== Redis Alternative Setup ===
Docker Desktop is not running. Please choose an alternative:

1. Install and start Redis manually
2. Use Redis Cloud (free tier available)
3. Skip Redis (some features will be limited)
4. Start Docker Desktop and retry
```

**Select Option 4** - The launcher will automatically:
- Start Docker Desktop
- Wait for it to become available (30-60 seconds)
- Start Redis container
- Continue with the application startup

## Auto-Restart Features

### What Auto-Restart Monitors

The system automatically monitors and restarts:

| Service | Description | Auto-Restart |
|---------|-------------|--------------|
| **Docker Desktop** | Container management | ✅ Yes |
| **Redis Container** | Background task queue | ✅ Yes |
| **Backend (Flask/Waitress)** | API server | ✅ Yes |
| **Frontend (Vue.js)** | Web interface | ✅ Yes |
| **RQ Worker** | Background task processor | ✅ Yes |
| **Nginx** | Reverse proxy (production) | ✅ Yes |

### Auto-Restart Configuration

- **Enabled by default** when you start the launcher
- **Maximum restart attempts**: 5 (configurable)
- **Health check interval**: Every 30 seconds
- **Restart delay**: 10 seconds between attempts
- **Crash logging**: All events logged with timestamps

### How Auto-Restart Works

1. **Health Monitoring**: Every 30 seconds, the system checks all services
2. **Failure Detection**: If any service is unhealthy, auto-restart is triggered
3. **Recovery Process**: Services are restarted in the correct order:
   - Docker Desktop (if needed)
   - Redis container
   - RQ Worker
   - Backend services
   - Frontend services
4. **Logging**: All events are logged to crash logs
5. **Retry Logic**: Up to 5 restart attempts before giving up

## Service Management

### View Auto-Restart Status

From the main menu, select **Option 13** (Service Monitoring Status)

You'll see:
```
=== Service Monitoring Status ===

Auto-Restart: ENABLED
Monitoring: ACTIVE
Restart Count: 0 / 5
Last Restart: Never
Crash Log: logs\crash_log_20250622_192247.log (2.5 KB)
```

### Auto-Restart Management Options

| Option | Description |
|--------|-------------|
| **1. Enable Auto-Restart** | Turn on automatic recovery |
| **2. Disable Auto-Restart** | Turn off automatic recovery |
| **3. View Crash Log** | See detailed error logs |
| **4. Clear Crash Log** | Clear old log entries |
| **5. Test Service Health** | Check if all services are healthy |
| **6. Force Auto-Restart Recovery** | Manually trigger recovery |

### Test Service Health

Select **Option 5** to see:
```
=== Service Health Check ===

Environment: Development
Backend: HEALTHY
Frontend: HEALTHY
Redis: HEALTHY
RQ Worker: HEALTHY

Overall Status: HEALTHY
```

### Manual Service Management

#### Stop All Services
From main menu, select **Option 4** (Stop All Services)

#### Restart Specific Services
From main menu, select **Option 7** (Redis/RQ Management)

Options:
- Start/Stop Redis
- Start/Stop RQ Worker
- Restart Redis
- Restart RQ Worker

#### View Logs
From main menu, select **Option 5** (View Logs)
- Shows all log files with timestamps
- Select a log file to view its contents
- Press Ctrl+C to stop viewing logs

## Monitoring and Health Checks

### Health Check Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **Backend Health** | http://localhost:5000/casestrainer/api/health | API server status |
| **Frontend (Dev)** | http://localhost:5173/ | Vue.js development server |
| **Production** | https://localhost:443/casestrainer/ | Production build |

### Health Check Criteria

- **Backend**: Responds to health API calls
- **Frontend**: Serves web pages correctly
- **Redis**: Accepts connections and responds to ping
- **RQ Worker**: Process is running and connected to Redis
- **Nginx**: Serves static files and proxies API calls

### Monitoring Dashboard

The system provides real-time monitoring through:

1. **Console Output**: Real-time status updates
2. **Crash Logs**: Detailed error tracking
3. **Health Checks**: Automated service validation
4. **Progress Tracking**: Task processing status

## Troubleshooting

### Common Issues and Solutions

#### Docker Desktop Issues

**Problem**: Docker Desktop won't start automatically
**Solution**: 
1. Start Docker Desktop manually
2. Wait for it to fully load
3. Restart CaseStrainer

**Problem**: Docker containers not starting
**Solution**:
1. Check Docker Desktop is running
2. Ensure ports 6379 is available
3. Use "Force Auto-Restart Recovery" option

#### Port Conflicts

**Problem**: "Port already in use" errors
**Solution**:
1. Check what's using the ports: `netstat -ano | findstr :5000`
2. Stop conflicting applications
3. Restart CaseStrainer

#### Node.js Issues

**Problem**: Vue.js frontend won't start
**Solution**:
1. Ensure Node.js and npm are installed
2. Check npm is in PATH: `npm --version`
3. Clear node_modules and reinstall: `npm ci`

#### Python Issues

**Problem**: Backend won't start
**Solution**:
1. Ensure Python virtual environment exists
2. Check Python path: `python --version`
3. Reinstall dependencies: `pip install -r requirements.txt`

### If Auto-Restart Fails

1. **Check crash logs**: View the crash log file for detailed error information
2. **Manual recovery**: Use "Force Auto-Restart Recovery" option
3. **Check Docker**: Ensure Docker Desktop is running
4. **Check ports**: Ensure ports 5000, 5173, and 6379 are available
5. **Restart manually**: Stop all services and restart the launcher

### Emergency Procedures

#### System Unresponsive
1. Press **Ctrl+C** to stop the launcher
2. Run: `.\launcher.ps1 -Environment Development -NoMenu`
3. This bypasses the menu and starts directly in development mode

#### Complete Reset
1. Stop all services: `.\launcher.ps1` → Option 4
2. Clear logs: Delete `logs\` directory
3. Restart Docker Desktop manually
4. Start fresh: `.\launcher.ps1`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `NODE_ENV` | Node.js environment | `development` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |

### Auto-Restart Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `AutoRestartEnabled` | Enable/disable auto-restart | `true` |
| `MaxRestartAttempts` | Maximum restart attempts | `5` |
| `RestartDelaySeconds` | Delay between restarts | `10` |
| `HealthCheckInterval` | Health check frequency | `30` |

### Customizing Auto-Restart

To modify auto-restart settings, edit the launcher script:

```powershell
# In launcher.ps1, modify these variables:
$script:AutoRestartEnabled = $true
$script:MaxRestartAttempts = 5
$script:RestartDelaySeconds = 10
$script:HealthCheckInterval = 30
```

## Log Files

### Log File Locations

| Log Type | Location | Description |
|----------|----------|-------------|
| **Crash Logs** | `logs\crash_log_YYYYMMDD_HHMMSS.log` | Auto-restart events and errors |
| **Backend Logs** | `logs\backend.log` | Flask/Waitress server logs |
| **Frontend Logs** | `logs\npm_build.log` | Vue.js build and dev server logs |
| **Nginx Logs** | `nginx-1.27.5\logs\` | Web server access and error logs |

### Log File Format

Crash logs include:
- Timestamp
- Log level (INFO, WARN, ERROR, DEBUG)
- Event description
- Exception details (if applicable)
- Stack traces (for errors)

Example log entry:
```
[2025-06-22 19:22:47] [INFO] Starting Development mode
[2025-06-22 19:22:54] [WARN] Docker Desktop not running, attempting to start
[2025-06-22 19:23:15] [INFO] Docker Desktop started successfully
```

### Log Management

- **View logs**: Use menu option 5
- **Clear logs**: Use monitoring menu option 4
- **Log rotation**: Logs are automatically timestamped
- **Log size**: Monitor log file sizes to prevent disk space issues

## Emergency Procedures

### Complete System Failure

If the system becomes completely unresponsive:

1. **Force Stop**: Press `Ctrl+C` multiple times
2. **Kill Processes**: Use Task Manager to end Python and Node.js processes
3. **Restart Docker**: Restart Docker Desktop manually
4. **Clear Ports**: Restart computer if ports remain locked
5. **Fresh Start**: Run launcher with `-NoMenu` flag

### Data Recovery

If you need to recover from a crash:

1. **Check crash logs**: Look for the most recent crash log
2. **Identify the issue**: Read the error messages
3. **Manual recovery**: Use the specific recovery steps for the identified issue
4. **Verify data**: Check that your citation cache and database are intact

### Backup and Restore

Before making changes:

1. **Backup data**: Copy `data\` directory
2. **Backup logs**: Copy `logs\` directory
3. **Backup config**: Copy any custom configuration files
4. **Test changes**: Test in development mode first

## Quick Reference Commands

### Starting CaseStrainer

```powershell
# Normal start with menu
.\launcher.ps1

# Direct development mode
.\launcher.ps1 -Environment Development -NoMenu

# Direct production mode
.\launcher.ps1 -Environment Production -NoMenu

# Skip frontend build in production
.\launcher.ps1 -Environment Production -NoMenu -SkipBuild
```

### Service Management

```powershell
# Stop all services
.\launcher.ps1 → Option 4

# View service status
.\launcher.ps1 → Option 3

# View logs
.\launcher.ps1 → Option 5

# Redis management
.\launcher.ps1 → Option 7

# Auto-restart management
.\launcher.ps1 → Option 13
```

### Health Checks

```powershell
# Backend health
Invoke-RestMethod -Uri "http://localhost:5000/casestrainer/api/health"

# Redis connection
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')"

# Docker status
docker info
```

## Support and Maintenance

### Regular Maintenance

- **Weekly**: Check crash logs for recurring issues
- **Monthly**: Clear old log files
- **Quarterly**: Update dependencies
- **As needed**: Monitor disk space usage

### Performance Monitoring

- **Memory usage**: Monitor Python and Node.js processes
- **Disk space**: Check log file sizes
- **Network**: Monitor API response times
- **Docker**: Check container resource usage

### Updates and Upgrades

When updating CaseStrainer:

1. **Backup**: Create backup of data and configuration
2. **Test**: Test in development mode first
3. **Gradual**: Update one component at a time
4. **Monitor**: Watch for issues after updates
5. **Rollback**: Keep previous version available

---

## Summary

The CaseStrainer auto-restart system provides:

- **Automatic recovery** from service failures
- **Comprehensive monitoring** of all components
- **Detailed logging** for troubleshooting
- **Flexible configuration** for different environments
- **Emergency procedures** for critical failures

The system is designed to be self-healing and will automatically recover from most common failures, ensuring maximum uptime for your CaseStrainer application.

For additional support, check the crash logs and use the built-in health check and recovery tools. 