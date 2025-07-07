# CaseStrainer Reliable Uptime Guide

This guide provides comprehensive strategies and configurations to achieve 99.9%+ uptime for CaseStrainer in production environments.

## Overview

CaseStrainer now includes multiple layers of reliability improvements:

1. **Enhanced Auto-Restart System** - More resilient with exponential backoff
2. **Improved Docker Configuration** - Better resource limits and health checks
3. **External Monitoring** - Independent health monitoring with alerts
4. **Windows Service Integration** - Automatic startup on system boot
5. **Comprehensive Health Checks** - Multi-layer health validation

## Quick Start for Production

### 1. Install as Windows Service (Recommended)

```powershell
# Run as Administrator
.\scripts\install-windows-service.ps1 -Environment Production
```

This will:
- Install CaseStrainer as a Windows service
- Configure automatic startup on boot
- Set up service recovery (restart on failure)
- Enable automatic restart after 30 seconds

### 2. Start External Monitoring

```powershell
# Start external monitoring with email alerts
.\scripts\monitor_external.ps1 -Environment Production -AlertEmail "admin@yourdomain.com" -CheckInterval 300
```

### 3. Verify Installation

```powershell
# Check service status
Get-Service -Name "CaseStrainer"

# Test health endpoint
Invoke-WebRequest -Uri "http://localhost:5001/casestrainer/api/health"
```

## Configuration Improvements

### Auto-Restart Configuration

The auto-restart system has been enhanced with:

```powershell
# Increased restart attempts and better timing
$script:MaxRestartAttempts = 10          # Was 5
$script:RestartDelaySeconds = 30         # Was 10
$script:HealthCheckInterval = 60         # Was 30
$script:ExponentialBackoff = $true       # New
$script:BackoffMultiplier = 2            # New
```

**Exponential Backoff Schedule:**
- Attempt 1: 30 seconds delay
- Attempt 2: 60 seconds delay
- Attempt 3: 120 seconds delay
- Attempt 4: 240 seconds delay
- Attempt 5+: 300 seconds delay (capped)

### Docker Production Configuration

Enhanced Docker configuration with better resource management:

```yaml
# Backend container
mem_limit: 4g                    # Was 2g
mem_reservation: 2g              # Was 1g
healthcheck:
  interval: 30s                  # Was 60s
  timeout: 15s                   # Was 30s
  retries: 5                     # Was 8
  start_period: 120s             # Was 180s

# Redis container
healthcheck:
  interval: 30s                  # Was 60s
  timeout: 10s                   # Was 30s
  retries: 5                     # Was 8
  start_period: 60s              # Was 180s
```

## Monitoring Layers

### 1. Built-in Auto-Restart (Primary)

- **Frequency**: Every 60 seconds
- **Scope**: Backend, Frontend, Nginx, Redis
- **Action**: Automatic restart with exponential backoff
- **Max Attempts**: 10 (was 5)

### 2. External Monitoring (Secondary)

- **Frequency**: Every 5 minutes (configurable)
- **Scope**: Health endpoints, Docker services, Redis
- **Action**: Email/Slack alerts, detailed logging
- **Independent**: Runs separately from main application

### 3. Windows Service Recovery (Tertiary)

- **Trigger**: Service crash or failure
- **Action**: Automatic restart after 30 seconds
- **Scope**: System-level service management

### 4. Docker Health Checks (Infrastructure)

- **Frequency**: Every 30 seconds per container
- **Action**: Container restart if unhealthy
- **Scope**: Individual container health

## Health Check Endpoints

### Primary Health Check
```
GET http://localhost:5001/casestrainer/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-03T20:42:05.775Z",
  "services": {
    "backend": "ok",
    "redis": "ok",
    "database": "ok"
  }
}
```

### Backup Health Check
```
GET http://localhost:5000/casestrainer/api/health
```

### Comprehensive Health Check
```powershell
# Run the robust health check script
python src/healthcheck_robust.py
```

## Alert Configuration

### Email Alerts

Configure email alerts in the external monitoring script:

```powershell
.\scripts\monitor_external.ps1 -AlertEmail "admin@yourdomain.com" -CheckInterval 300
```

### Slack Alerts

Configure Slack webhook for instant notifications:

```powershell
.\scripts\monitor_external.ps1 -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" -CheckInterval 300
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start

**Symptoms:**
- Windows service fails to start
- Docker containers exit immediately
- Health checks fail

**Solutions:**
```powershell
# Check service logs
Get-EventLog -LogName Application -Source "CaseStrainer"

# Check Docker logs
docker logs casestrainer-backend-prod
docker logs casestrainer-redis-prod

# Test health manually
.\scripts\monitor_external.ps1 -TestMode
```

#### 2. Redis Connection Issues

**Symptoms:**
- "Error 10061 connecting to localhost:6379"
- RQ worker failures
- Task processing errors

**Solutions:**
```powershell
# Restart Redis container
docker restart casestrainer-redis-prod

# Check Redis logs
docker logs casestrainer-redis-prod

# Test Redis connection
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')"
```

#### 3. Memory Issues

**Symptoms:**
- Out of memory errors
- Slow performance
- Container restarts

**Solutions:**
```powershell
# Check memory usage
docker stats

# Increase memory limits in docker-compose.prod.yml
mem_limit: 6g
mem_reservation: 3g

# Restart with new limits
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Port Conflicts

**Symptoms:**
- "Address already in use" errors
- Services can't bind to ports

**Solutions:**
```powershell
# Check port usage
netstat -ano | findstr :5001
netstat -ano | findstr :6379

# Kill conflicting processes
taskkill /PID <PID> /F

# Use different ports in docker-compose.prod.yml
ports:
  - "5002:5000"  # Change from 5001:5000
```

## Performance Optimization

### Resource Allocation

**Recommended Settings:**
```yaml
# Backend container
mem_limit: 4g
mem_reservation: 2g
cpus: '2.0'

# Redis container
mem_limit: 512M
mem_reservation: 256M

# RQ Worker containers
mem_limit: 1g
mem_reservation: 512M
```

### Health Check Optimization

**Optimal Settings:**
```yaml
healthcheck:
  interval: 30s      # Balance between responsiveness and overhead
  timeout: 15s       # Enough time for slow responses
  retries: 5         # Reasonable failure tolerance
  start_period: 120s # Allow for startup time
```

## Maintenance Procedures

### Regular Maintenance

#### Weekly
1. **Check Logs**: Review crash logs and health check logs
2. **Update Dependencies**: Check for security updates
3. **Backup Data**: Ensure database backups are working
4. **Performance Review**: Monitor resource usage trends

#### Monthly
1. **Service Restart**: Restart services to clear memory leaks
2. **Log Rotation**: Clean up old log files
3. **Security Review**: Check for unauthorized access
4. **Capacity Planning**: Review resource usage and plan for growth

### Emergency Procedures

#### Service Down
1. **Check External Monitor**: Verify if external monitoring detected the issue
2. **Check Windows Service**: `Get-Service -Name "CaseStrainer"`
3. **Check Docker**: `docker ps -a`
4. **Check Logs**: Review recent crash logs
5. **Manual Restart**: `Restart-Service -Name "CaseStrainer"`

#### Data Loss
1. **Stop Services**: Prevent further data corruption
2. **Check Backups**: Verify backup integrity
3. **Restore from Backup**: Use latest known good backup
4. **Verify Data**: Test application functionality
5. **Investigate Cause**: Determine root cause of data loss

## Monitoring Dashboard

### Key Metrics to Monitor

1. **Uptime**: Target 99.9%+
2. **Response Time**: < 2 seconds for health checks
3. **Memory Usage**: < 80% of allocated memory
4. **CPU Usage**: < 70% average
5. **Disk Usage**: < 85% of available space
6. **Error Rate**: < 1% of requests

### Log Analysis

```powershell
# Check recent errors
Select-String -Path "logs\*.log" -Pattern "ERROR" | Select-Object -Last 20

# Check health check success rate
Select-String -Path "logs\health_check.log" -Pattern "healthy" | Measure-Object | Select-Object Count

# Check restart frequency
Select-String -Path "logs\crash_log_*.log" -Pattern "auto-restart" | Measure-Object | Select-Object Count
```

## Best Practices

### 1. Use Production Mode
Always use Docker Production mode for production deployments:
```powershell
.\launcher.ps1 -Environment DockerProduction
```

### 2. Enable External Monitoring
Run external monitoring alongside the main application:
```powershell
.\scripts\monitor_external.ps1 -Environment Production -AlertEmail "admin@yourdomain.com"
```

### 3. Regular Testing
Test the monitoring and recovery systems regularly:
```powershell
# Test health check
.\scripts\monitor_external.ps1 -TestMode

# Test service restart
Restart-Service -Name "CaseStrainer"
```

### 4. Log Management
Implement log rotation to prevent disk space issues:
```powershell
# Clean old logs (older than 30 days)
Get-ChildItem "logs\*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
```

### 5. Backup Strategy
Ensure regular backups of critical data:
- Database files
- Configuration files
- Log files (for debugging)

## Expected Uptime

With these improvements, CaseStrainer should achieve:

- **Target Uptime**: 99.9%+ (less than 8.76 hours downtime per year)
- **Mean Time to Recovery (MTTR)**: < 5 minutes
- **Mean Time Between Failures (MTBF)**: > 30 days

## Support and Maintenance

For issues or questions about the reliability improvements:

1. **Check Documentation**: Review this guide and related documentation
2. **Review Logs**: Examine crash logs and health check logs
3. **Test Components**: Use the test modes in monitoring scripts
4. **Contact Support**: If issues persist, contact the development team

## Conclusion

These reliability improvements provide multiple layers of protection against downtime:

1. **Prevention**: Better resource management and health checks
2. **Detection**: Comprehensive monitoring at multiple levels
3. **Recovery**: Automatic restart with intelligent backoff
4. **Alerting**: Immediate notification of issues
5. **Persistence**: Windows service integration for automatic startup

By implementing these improvements, CaseStrainer should achieve enterprise-grade reliability and uptime. 