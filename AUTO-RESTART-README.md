# CaseStrainer Auto-Restart & Monitoring System

This document describes the auto-restart and monitoring capabilities built into CaseStrainer to ensure high availability and automatic recovery from crashes.

## Overview

CaseStrainer now includes comprehensive auto-restart and monitoring capabilities to ensure the application remains available even if individual services crash or become unresponsive.

## Features

### 1. Built-in Auto-Restart (launcher.ps1)
- **Crash Logging**: All crashes and errors are logged to timestamped files
- **Process Monitoring**: Monitors backend, frontend, Nginx, and Redis processes
- **Automatic Recovery**: Automatically restarts crashed services
- **Configurable Limits**: Set maximum restart attempts and delays
- **Health Checks**: Regular health checks via API endpoints

### 2. Standalone Monitoring Script (monitor-casestrainer.ps1)
- **Independent Monitoring**: Can run separately from the main launcher
- **Comprehensive Health Checks**: Tests all services including Redis connectivity
- **Detailed Logging**: Verbose logging with different levels
- **Configurable Parameters**: Adjustable check intervals and restart limits
- **Statistics Tracking**: Monitors uptime, restart counts, and performance

### 3. Windows Service Support (install-windows-service.ps1)
- **Windows Service**: Install CaseStrainer as a Windows service
- **Automatic Startup**: Starts automatically when Windows boots
- **Service Management**: Use standard Windows service management tools
- **System Integration**: Integrates with Windows Event Log

## Usage

### Basic Auto-Restart (Built-in)

The main launcher (`launcher.ps1`) now includes basic auto-restart capabilities:

```powershell
# Start with auto-restart enabled (default)
.\launcher.ps1 -Environment Production

# View monitoring status
# Select option 13 from the menu: "Service Monitoring Status"
```

### Advanced Monitoring

For more comprehensive monitoring, use the standalone monitor script:

```powershell
# Monitor production environment
.\monitor-casestrainer.ps1 -Environment Production

# Monitor development environment with verbose logging
.\monitor-casestrainer.ps1 -Environment Development -Verbose

# Custom check interval (60 seconds)
.\monitor-casestrainer.ps1 -CheckInterval 60

# Custom restart limits
.\monitor-casestrainer.ps1 -MaxRestartAttempts 10 -RestartDelay 15

# Get help
.\monitor-casestrainer.ps1 -Help
```

### Windows Service Installation

For production deployments, install as a Windows service:

```powershell
# Run as Administrator
.\install-windows-service.ps1

# Start the service
Start-Service CaseStrainer

# Check service status
Get-Service CaseStrainer

# Stop the service
Stop-Service CaseStrainer

# Remove the service
.\install-windows-service.ps1 -Uninstall
```

## Configuration

### Auto-Restart Settings

The following settings can be configured in `launcher.ps1`:

```powershell
$script:AutoRestartEnabled = $true          # Enable/disable auto-restart
$script:MaxRestartAttempts = 5              # Maximum restart attempts
$script:RestartDelaySeconds = 10            # Delay before restart
$script:HealthCheckInterval = 30            # Health check interval (seconds)
```

### Monitoring Script Settings

The monitoring script supports these parameters:

- `-Environment`: Production or Development
- `-CheckInterval`: Health check interval in seconds (default: 30)
- `-MaxRestartAttempts`: Maximum restart attempts (default: 5)
- `-RestartDelay`: Delay before restart in seconds (default: 10)
- `-Verbose`: Enable verbose logging
- `-Help`: Show help information

## Log Files

### Crash Logs
- **Location**: `logs/crash_log_YYYYMMDD_HHMMSS.log`
- **Content**: Timestamped crash events, errors, and restart attempts
- **Rotation**: New log file created for each launcher session

### Monitoring Logs
- **Location**: `logs/monitor_YYYYMMDD_HHMMSS.log`
- **Content**: Health check results, service status, restart events
- **Rotation**: New log file created for each monitoring session

### Service Logs
- **Backend**: `logs/backend.log` and `logs/backend_error.log`
- **Nginx**: `nginx-1.27.5/logs/access.log` and `nginx-1.27.5/logs/error.log`

## Health Checks

### Backend Health Check
- **URL**: `http://127.0.0.1:5000/casestrainer/api/health`
- **Expected Response**: `{"status": "ok"}` or `{"status": "healthy"}`
- **Timeout**: 10 seconds

### Process Health Checks
- **Backend**: Python processes running Waitress or Flask
- **Frontend**: Node.js processes running Vite (development mode)
- **Nginx**: Nginx processes (production mode)
- **Redis**: Redis connectivity test

## Recovery Scenarios

### Backend Crash
1. Monitor detects backend process exit or health check failure
2. Logs the crash event with timestamp and exit code
3. Waits for configured delay period
4. Attempts to restart backend via launcher
5. Increments restart counter
6. Continues monitoring

### Nginx Crash (Production)
1. Monitor detects Nginx process exit
2. Logs the crash event
3. Stops existing Nginx processes
4. Restarts Nginx with production configuration
5. Verifies Nginx is running

### Redis Unavailability
1. Monitor detects Redis connection failure
2. Logs the issue (non-critical)
3. Continues monitoring other services
4. Services can run with limited functionality

### Maximum Restarts Reached
1. Monitor reaches maximum restart attempts
2. Logs critical error
3. Stops monitoring
4. Requires manual intervention

## Monitoring Dashboard

Access the monitoring status through the launcher menu:

1. Run `.\launcher.ps1`
2. Select option 13: "Service Monitoring Status"
3. View current status and configure settings

### Status Information
- Auto-restart enabled/disabled
- Monitoring active/inactive
- Restart count and limits
- Last restart timestamp
- Crash log file information

### Configuration Options
- Enable/disable auto-restart
- View crash logs
- Clear crash logs
- Restart monitoring

## Best Practices

### Production Deployment
1. **Use Windows Service**: Install as Windows service for automatic startup
2. **Enable Monitoring**: Run monitoring script for comprehensive oversight
3. **Configure Logging**: Ensure log directories exist and are writable
4. **Set Appropriate Limits**: Configure restart limits based on your environment
5. **Monitor Logs**: Regularly check crash and monitoring logs

### Development Environment
1. **Use Built-in Monitoring**: The launcher includes basic monitoring
2. **Enable Verbose Logging**: Use `-Verbose` flag for detailed output
3. **Frequent Health Checks**: Use shorter check intervals for faster detection

### Troubleshooting
1. **Check Crash Logs**: Review crash logs for error details
2. **Verify Dependencies**: Ensure Redis, Python, and Node.js are available
3. **Check Permissions**: Ensure scripts have necessary permissions
4. **Review Service Status**: Use Windows service management tools

## Integration with Existing Scripts

The auto-restart system integrates with existing CaseStrainer scripts:

- **launcher.ps1**: Enhanced with crash logging and basic monitoring
- **monitor-casestrainer.ps1**: Standalone monitoring script
- **install-windows-service.ps1**: Windows service installation
- **Existing batch scripts**: Compatible with existing deployment scripts

## Security Considerations

- **Log File Access**: Ensure log files are not publicly accessible
- **Service Permissions**: Windows service runs with appropriate permissions
- **Network Access**: Health checks use localhost only
- **Error Information**: Crash logs may contain sensitive information

## Performance Impact

- **Monitoring Overhead**: Minimal CPU and memory usage
- **Health Check Frequency**: Configurable to balance responsiveness and overhead
- **Log File Size**: Monitor log file sizes and implement rotation if needed
- **Restart Delays**: Configure appropriate delays to prevent rapid restart loops

## Support and Maintenance

### Regular Maintenance
- **Log Rotation**: Archive old log files periodically
- **Service Updates**: Update Windows service after application updates
- **Configuration Review**: Review and adjust monitoring parameters as needed

### Troubleshooting Commands
```powershell
# Check service status
Get-Service CaseStrainer

# View recent crash logs
Get-Content logs/crash_log_*.log | Select-Object -Last 50

# Check monitoring status
Get-Process python, nginx, node -ErrorAction SilentlyContinue

# Test health endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:5000/casestrainer/api/health"
```

This auto-restart and monitoring system ensures CaseStrainer remains highly available and automatically recovers from crashes, making it suitable for production deployments. 