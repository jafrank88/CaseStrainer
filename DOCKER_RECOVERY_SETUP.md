# Docker Recovery System Setup

This document describes the automated Docker recovery system implemented to ensure Docker Desktop and CaseStrainer containers stay running.

## Overview

The recovery system consists of multiple layers of monitoring and automatic recovery:

1. **Service Monitor** - Continuous monitoring of Docker Desktop service

2. **Autostart Configuration** - Ensures Docker starts with Windows

3. **Emergency Recovery** - Deep recovery when standard methods fail

4. **Task Scheduler Integration** - Windows-native task automation

## Components

### 1. Docker Service Monitor (`docker_service_monitor.ps1`)

- Monitors Docker Desktop health every 60 seconds
- Detects service failures and process crashes
- Attempts automatic restart with configurable retry limits
- Logs all activities to `logs/docker_service_monitor.log`
- Can run as a Windows service or scheduled task

### 2. Autostart Configuration (`configure_docker_autostart.ps1`)

- Sets Docker Desktop to start with Windows
- Configures service recovery actions
- Manages startup shortcuts and registry settings
- Provides status checking capabilities

### 3. Emergency Recovery (`docker_emergency_recovery.ps1`)

- Performs deep cleanup and recovery
- Clears corrupted Docker data
- Resets WSL and network configurations
- Can run diagnostics to identify issues

### 4. Task Scheduler Setup (`setup_docker_recovery_tasks.ps1`)

- Installs all necessary Windows Task Scheduler tasks
- Configures service failure triggers
- Sets up monitoring intervals and recovery actions

## Installation

### Prerequisites

- Windows 10/11 Pro/Enterprise
- Docker Desktop installed
- Administrator privileges

### Step 1: Enable Docker Autostart

```powershell
.\scripts\configure_docker_autostart.ps1 -Enable
```

### Step 2: Install Recovery Tasks

```powershell
# Run as Administrator
.\scripts\setup_docker_recovery_tasks.ps1 -Install
```

### Step 3: Verify Installation

```powershell
.\scripts\setup_docker_recovery_tasks.ps1 -Test
```

## Installed Tasks

The installation creates the following Windows Task Scheduler tasks:

1. **Docker-Service-Monitor**
   - Runs at system startup
   - Monitors Docker continuously
   - Restarts on failure

2. **Docker-Health-Check**
   - Runs every 5 minutes
   - Quick health verification
   - Triggers recovery if needed

3. **Docker-Emergency-Recovery**
   - Runs on user logon
   - Available for manual execution
   - Performs deep recovery

4. **Docker-Autostart**
   - Runs 30 seconds after system boot
   - Ensures Docker starts correctly
   - Configures startup settings


## Configuration

### Monitoring Settings

Edit `docker_service_monitor.ps1` to adjust:
- Check interval (default: 60 seconds)
- Max restart attempts (default: 3)
- Restart delay (default: 30 seconds)

### Service Recovery

The Docker service is configured with:

- First failure: Restart after 5 seconds
- Second failure: Run recovery script after 15 seconds
- Subsequent failures: Restart after 30 seconds
- Reset period: 24 hours

## Usage

### Manual Recovery

```powershell
# Quick restart
.\scripts\docker_service_monitor.ps1 -RunOnce

# Emergency recovery
.\scripts\docker_emergency_recovery.ps1 -Force

# Full cleanup and recovery
.\scripts\docker_emergency_recovery.ps1 -Cleanup

# Run diagnostics
.\scripts\docker_emergency_recovery.ps1 -Diagnostics
```

### Check Status

```powershell
# Autostart status
.\scripts\configure_docker_autostart.ps1 -Status

# Task status
.\scripts\setup_docker_recovery_tasks.ps1 -Test
```

### Uninstall

```powershell
# Run as Administrator
.\scripts\setup_docker_recovery_tasks.ps1 -Uninstall

# Disable autostart
.\scripts\configure_docker_autostart.ps1 -Disable
```

## Logging

All recovery activities are logged to:
- `logs/docker_service_monitor.log` - Service monitoring
- `logs/docker_emergency_recovery.log` - Emergency recovery actions
- `logs/docker_diagnostics_*.txt` - Diagnostic reports

## Troubleshooting

### Common Issues

1. **Tasks Not Running**
   - Ensure running as Administrator
   - Check Task Scheduler service is running
   - Verify script execution policy: `Set-ExecutionPolicy RemoteSigned`

2. **Docker Won't Start**
   - Run emergency recovery: `.\scripts\docker_emergency_recovery.ps1 -Force`
   - Check system resources (memory, disk space)
   - Review Docker logs in Docker Desktop

3. **Recovery Loop**
   - Check logs for error patterns
   - Run diagnostics to identify root cause
   - Consider full cleanup: `.\scripts\docker_emergency_recovery.ps1 -Cleanup`

### Advanced Diagnostics

For detailed troubleshooting:
1. Run diagnostics script
2. Check Windows Event Viewer for service errors
3. Review Docker Desktop logs
4. Monitor system resources

## Integration with CaseStrainer

The recovery system automatically:
- Starts CaseStrainer containers after Docker recovery
- Monitors container health
- Logs container status changes
- Integrates with existing `cslaunch.ps1` monitoring

## Security Considerations

- All tasks run as SYSTEM account

- Scripts use PowerShell execution policy bypass
- No external dependencies required
- Logs contain sensitive information - secure appropriately

## Maintenance

- Review logs weekly for issues
- Update scripts if Docker paths change
- Test recovery procedures monthly
- Keep backup of configuration

## Support

For issues or questions:
1. Check logs in the `logs` directory
2. Run diagnostic scripts
3. Review this documentation
4. Contact system administrator
