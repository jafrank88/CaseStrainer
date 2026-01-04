# Docker Recovery Integration with cslaunch.ps1

This document describes how the Docker recovery system has been integrated into `cslaunch.ps1`.

## Overview

The Docker recovery functionality has been integrated into the main `cslaunch.ps1` script, providing a unified interface for managing Docker and CaseStrainer. The integration combines the existing monitoring capabilities with new emergency recovery and service recovery features.

## New Parameters Added

### Emergency Recovery

```powershell
.\cslaunch.ps1 -EmergencyRecovery
```

- Performs deep cleanup of Docker Desktop
- Clears corrupted data and resets configurations
- Resets WSL and network adapters
- Useful when Docker is completely unresponsive

### Service Recovery Configuration

```powershell
.\cslaunch.ps1 -ConfigureServiceRecovery
```

- Configures Windows service recovery actions
- Sets automatic restart on service failure
- Requires administrator privileges

```powershell
.\cslaunch.ps1 -RemoveServiceRecovery
```

- Removes all service recovery configurations
- Resets service to default behavior

## Administrator Privilege Requirements

### Operations requiring Administrator privileges

1. **ConfigureAutostart** - Creates startup tasks and shortcuts
2. **ConfigureServiceRecovery** - Sets Windows service recovery actions
3. **RemoveServiceRecovery** - Removes service recovery actions
4. **EmergencyRecovery** - Full system cleanup (recommended but not required)

### Operations that work without Administrator privileges

1. **Monitor** - Standard monitoring mode
2. **Build** - Build and restart containers
3. **Force** - Force restart containers
4. **NoCache** - Build without cache
5. **NoMonitor** - Start without monitoring

## Enhanced Features

### 1. Integrated Service Recovery

When using `-ConfigureAutostart`, the system now automatically:

- Creates startup tasks
- Configures Docker service recovery actions
- Sets service to automatic start
- Provides fallback recovery mechanisms

### 2. Emergency Recovery Integration

The emergency recovery can be triggered:

- Manually via `-EmergencyRecovery` parameter
- Automatically by Windows service recovery (if configured)
- As part of the monitoring system's "nuclear option"

### 3. Unified Logging

All recovery operations log to:

- `logs/docker_daemon_monitor.log` - Service monitoring
- `logs/docker_emergency_recovery.log` - Emergency recovery
- `logs/autostart.log` - Autostart operations

## Usage Examples

### Basic Monitoring (No Admin Required)

```powershell
.\cslaunch.ps1
# Starts monitoring with auto-restart
```

### Full Recovery Setup (Admin Required)

```powershell
# Run as Administrator
.\cslaunch.ps1 -ConfigureAutostart -ConfigureServiceRecovery
```

### Emergency Recovery Procedure

```powershell
# When Docker is completely stuck
.\cslaunch.ps1 -EmergencyRecovery
```

### Standard Operations

```powershell
# Build and start
.\cslaunch.ps1 -Build

# Force restart
.\cslaunch.ps1 -Force

# Start without monitoring
.\cslaunch.ps1 -NoMonitor
```

## Recovery Layers

The integrated system provides multiple layers of recovery:

### Layer 1: Container-Level Recovery

- Automatic container restart (Docker restart policy)
- Handled by Docker daemon
- Always active

### Layer 2: Application-Level Recovery

- `cslaunch.ps1` monitoring loop
- Checks every 60 seconds
- Restarts failed containers
- Restarts Docker daemon if frozen

### Layer 3: Service-Level Recovery

- Windows service recovery actions
- Configured via `-ConfigureServiceRecovery`
- Runs emergency recovery script on failure
- Requires admin privileges

### Layer 4: Emergency Recovery

- Deep cleanup and reset
- Manual trigger via `-EmergencyRecovery`
- Clears corrupted data
- Resets network and WSL

## Migration from Standalone Scripts

The standalone scripts in `scripts/` are still available but are now called by `cslaunch.ps1`:

| Standalone Script | cslaunch.ps1 Equivalent |
| ------------------ | ------------------------ |
| `docker_service_monitor.ps1` | Built into monitoring loop |
| `configure_docker_autostart.ps1` | `-ConfigureAutostart` |
| `docker_emergency_recovery.ps1` | `-EmergencyRecovery` |
| `setup_docker_recovery_tasks.ps1` | `-ConfigureServiceRecovery` |

## Best Practices

1. **Initial Setup** (Run once as Administrator):

   ```powershell
   .\cslaunch.ps1
   ```

   *Note: When run as Administrator, cslaunch now automatically configures both autostart and service recovery by default.*

2. **Daily Use** (No admin required):

   ```powershell
   .\cslaunch.ps1
   ```

3. **When Problems Occur**:

   - First try: `.\cslaunch.ps1 -Force`
   - If stuck: `.\cslaunch.ps1 -EmergencyRecovery`

4. **Monitoring**:
   - Check logs in `logs/` directory
   - Monitoring runs automatically
   - No manual intervention needed

## Troubleshooting

### Service Recovery Not Working

- Ensure running as Administrator
- Check if `com.docker.service` exists
- Verify `scripts/docker_emergency_recovery.ps1` exists

### Emergency Recovery Fails

- Check system resources (memory, disk space)
- Close all Docker-related applications
- Run as Administrator for best results

### Autostart Not Working

- Verify scheduled task was created
- Check Windows Event Viewer for errors
- Ensure password was entered correctly

## Integration Benefits

1. **Single Point of Management** - All Docker operations through `cslaunch.ps1`
2. **Consistent Logging** - Unified logging across all operations
3. **Progressive Recovery** - Multiple layers from gentle to aggressive
4. **Backward Compatibility** - Existing workflows continue to work
5. **Flexible Administration** - Mix of admin and non-admin operations
6. **Automatic Configuration** - Service recovery is enabled by default when running as Administrator
