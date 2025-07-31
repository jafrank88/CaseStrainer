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
- **Ports**: 5000, 5001, 6379 (Redis), 443 (production)

## Quick Start

### 1. Navigate to CaseStrainer Directory

```powershell
# Navigate to your CaseStrainer directory
cd "d:\dev\casestrainer"
```

### 2. Start CaseStrainer

```powershell
.\launcher.ps1
```

```text

### 3. Choose Environment

When the menu appears, select:

- **Option 1**: Development Mode (recommended for testing)
- **Option 2**: Production Mode (for production use)
- **Option 3**: Docker Development Mode (containerized development)
- **Option 4**: Docker Production Mode (full containerized production with comprehensive network cleanup and advanced diagnostics)

### 4. Docker-Specific Diagnostics (Option 4)

Option 4 now includes comprehensive Docker diagnostics that help identify restart issues:

#### **Docker Daemon & System Checks**

- Docker daemon status and version
- Container resource usage (CPU, memory, network I/O)
- Docker system resource usage
- Port conflict detection

#### **Network Diagnostics**

- Docker network inspection
- Container-to-container connectivity tests
- DNS resolution within containers
- Direct IP connectivity verification
- Network event monitoring

#### **Container Health Monitoring**

- Container health status
- Restart history analysis
- Recent Docker events
- Resource pressure detection
- Error log scanning

#### **Restart-Specific Diagnostics**

- Container restart frequency analysis
- Memory/CPU pressure detection
- Network connectivity issues
- DNS resolution problems
- IP address conflicts

#### **Actionable Recommendations**

- Automatic issue detection and reporting
- Specific troubleshooting commands
- Quick fix suggestions based on detected problems

### 5. Handle Redis Setup (if needed)

If Docker Desktop isn't running, you'll see:

```text

=== Redis Alternative Setup ===
Docker Desktop is not running. Please choose an alternative:

1. Install and start Redis manually
2. Use Redis Cloud (free tier available)
3. Skip Redis (some features will be limited)
4. Start Docker Desktop and retry

```text

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

```text

=== Service Monitoring Status ===

Auto-Restart: ENABLED
Monitoring: ACTIVE
Restart Count: 0 / 5
Last Restart: Never
Crash Log: logs\crash_log_20250622_192247.log (2.5 KB)

```text

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

```text

=== Service Health Check ===

Environment: DockerProduction
Backend: HEALTHY
Frontend: HEALTHY
Redis: HEALTHY
RQ Worker: HEALTHY

Overall Status: HEALTHY

```text

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
| **Backend Health** | http://localhost:5001/casestrainer/api/health | API server status |
| **Frontend (Dev)** | http://localhost:5173/ | Vue.js development server |
| **Production** | https://localhost:443/casestrainer/ | Production build |

### Health Check Criteria

- **Backend**: Responds to health API calls with timeout protection
- **Frontend**: Serves web pages correctly
- **Redis**: Accepts connections and responds to ping
- **RQ Worker**: Process is running and connected to Redis
- **Nginx**: Serves static files and proxies API calls

### Health Check Improvements

Recent improvements to health checks include:

1. **Timeout Protection**: Health checks now have 3-second timeouts to prevent hanging
2. **Robust Connection Testing**: Uses `Test-NetConnection` instead of HTTP requests for basic connectivity
3. **Threading-Based Timeouts**: Windows-compatible timeout implementation for RQ worker checks
4. **Better Error Handling**: Graceful degradation when services are unavailable

### Monitoring Dashboard

The system provides real-time monitoring through:

1. **Console Output**: Real-time status updates
2. **Crash Logs**: Detailed error tracking
3. **Health Checks**: Automated service validation
4. **Docker Logs**: Container-specific logs

## Docker Production Health Checks

### Backend Health Check

The backend health check now includes timeout protection:

```python
def check_redis():
    """Check Redis connection with timeout."""
    try:
        redis_conn.ping()
        return "ok"
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")
        return "down"

def check_db():
    """Check database connection with timeout."""
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=3)
        conn.execute('SELECT 1')
        conn.close()
        return "ok"
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return "down"

def check_rq_worker():
    """Check RQ worker with threading-based timeout."""
    try:
        if RQ_AVAILABLE:
            from rq import Worker
            import threading
            import time
            
            result = {"status": "down", "error": None}
            
            def worker_check():
                try:
                    workers = Worker.all(connection=redis_conn)
                    result["status"] = "ok" if workers else "down"
                except Exception as e:
                    result["status"] = "down"
                    result["error"] = str(e)
            
            thread = threading.Thread(target=worker_check)
            thread.daemon = True
            thread.start()
            thread.join(timeout=3)  # 3-second timeout
            
            if thread.is_alive():
                logger.warning("RQ worker check timed out")
                return "timeout"
            
            return result["status"]
    except Exception as e:
        logger.warning(f"RQ worker check failed: {e}")
        return "down"

```text

### Docker Health Check Configuration

```yaml

# Backend container health check

healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/casestrainer/api/health"]
  interval: 60s
  timeout: 30s
  retries: 8
  start_period: 180s

# Redis container health check

healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 60s
  timeout: 30s
  retries: 8
  start_period: 180s

# RQ Worker health check

healthcheck:
  test: ["CMD", "python", "src/healthcheck_rq.py"]
  interval: 60s
  timeout: 30s
  retries: 8
  start_period: 180s

```text

## Troubleshooting

### Health Check Failures

If health checks are failing:

1. **Check service status**:

   ```powershell
   .\launcher.ps1 -Environment DockerProduction -NoMenu
   ```text

2. **View detailed logs**:

   ```powershell
   # From launcher menu, select Option 5 (View Logs)
   # Or check Docker logs directly
   docker logs casestrainer-backend-prod
   docker logs casestrainer-redis-prod
   ```text

3. **Test connectivity manually**:

   ```powershell
   # Test backend health
   Invoke-WebRequest -Uri "http://localhost:5001/casestrainer/api/health" -TimeoutSec 5
   
   # Test Redis connection
   docker exec casestrainer-redis-prod redis-cli ping
   ```text

### Common Issues

1. **Docker Desktop not running**:
   - The launcher will prompt to start Docker Desktop
   - Wait 30-60 seconds for Docker to become available

2. **Port conflicts**:
   - Ensure ports 5000, 5001, 6379, 443, 80 are available
   - Stop conflicting services

3. **Health check timeouts**:
   - Recent improvements should prevent hanging
   - Check if services are overloaded

4. **Redis connection issues**:
   - Verify Redis container is running
   - Check Redis logs for errors

### Emergency Procedures

1. **Stop all services**:

   ```powershell
   .\launcher.ps1 -Environment DockerProduction -NoMenu
   # Select option 4: Stop All Services
   ```text

2. **Restart Docker Desktop**:
   - Close Docker Desktop
   - Restart Docker Desktop
   - Wait for it to become available

3. **Clean restart**:

   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker system prune -f
   docker-compose -f docker-compose.prod.yml up -d
   ```text

## Configuration

### Environment Variables

Key environment variables for auto-restart:

```ini

# Auto-restart configuration

AUTO_RESTART_ENABLED=true
MAX_RESTART_ATTEMPTS=5
HEALTH_CHECK_INTERVAL=30
RESTART_DELAY=10

# Service ports

BACKEND_PORT=5001
FRONTEND_PORT=5173
REDIS_PORT=6379
NGINX_PORT=443

```text

### Launcher Configuration

The launcher uses these default settings:

```powershell

# Health check configuration

$config.HealthCheckInterval = 30  # seconds
$config.MaxRestartAttempts = 5
$config.RestartDelay = 10  # seconds

# Service ports (2)

$config.BackendPort = 5001
$config.FrontendPort = 5173
$config.RedisPort = 6379

```text

## Log Files

### Crash Logs

Crash logs are stored in the `logs/` directory:

```text

logs/
├── crash_log_20250622_192247.log
├── crash_log_20250623_143022.log
└── backend_health_diag.log

```text

### Log Format

Crash logs include:

```text

2025-06-22T19:22:47.123Z [INFO] Auto-restart enabled
2025-06-22T19:22:47.456Z [WARN] Backend health check failed: Connection timeout
2025-06-22T19:22:47.789Z [INFO] Attempting to restart backend service
2025-06-22T19:22:57.012Z [INFO] Backend service restarted successfully

```text

### Log Analysis

To analyze logs:

```powershell

# View recent crash log

Get-Content "logs\crash_log_$(Get-Date -Format 'yyyyMMdd').log" -Tail 50

# Search for errors

Select-String -Path "logs\*.log" -Pattern "ERROR|WARN"

# Monitor health checks

Select-String -Path "logs\*.log" -Pattern "health|Health"

```text

## Performance Monitoring

### Resource Usage

Monitor resource usage:

```powershell

# Docker container stats

docker stats

# System resource usage

Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}

```text

### Health Check Performance

Health check performance metrics:

- **Average response time**: < 1 second
- **Timeout threshold**: 3 seconds
- **Success rate**: > 95%
- **Recovery time**: < 30 seconds

## Best Practices

### Production Deployment

1. **Use Docker Production mode** for production deployments
2. **Monitor resource usage** regularly
3. **Set up log rotation** to prevent disk space issues
4. **Configure alerts** for critical failures
5. **Test recovery procedures** regularly

### Development

1. **Use Development mode** for local development
2. **Enable debug logging** for troubleshooting
3. **Test health checks** after making changes
4. **Monitor crash logs** during development

### Maintenance

1. **Regular log cleanup** to prevent disk space issues
2. **Update dependencies** regularly
3. **Test auto-restart** after updates
4. **Backup configuration** before major changes

## Support

For issues with the auto-restart system:

1. **Check crash logs** in the `logs/` directory
2. **Test health checks** manually
3. **Review Docker logs** for container-specific issues
4. **Create GitHub issue** with detailed error information

### Getting Help

1. **Documentation**: Review this guide and other docs
2. **Logs**: Check crash logs and Docker logs
3. **Health checks**: Use launcher menu option 5
4. **GitHub issues**: Report bugs and request features
