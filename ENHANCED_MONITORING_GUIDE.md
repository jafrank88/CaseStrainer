# Enhanced Docker Monitoring System - Usage Guide

## Overview

The Enhanced Docker Monitoring System addresses the recurring 24-48 hour Docker crashes by providing comprehensive monitoring, self-healing, and escalation capabilities. This system consists of multiple components working together to ensure maximum uptime and rapid recovery.

## Components

### 1. Enhanced Docker Monitor (`enhanced_docker_monitor.ps1`)
- **Purpose**: Comprehensive Docker health monitoring with resource tracking
- **Features**:
  - Multi-point health checks (docker info, docker ps, container status)
  - Resource usage monitoring (memory, CPU, disk)
  - Automatic recovery with enhanced restart procedures
  - Response time tracking and performance metrics

### 2. Self-Health Monitor (`monitor_self_health.ps1`)
- **Purpose**: Monitors the monitoring system itself
- **Features**:
  - Detects when monitoring scripts crash or stop responding
  - Automatically restarts failed monitoring components
  - Prevents the 41-hour monitoring gap that occurred previously
  - Rate limiting to prevent restart loops

### 3. System Recovery Logger (`system_recovery_logger.ps1`)
- **Purpose**: Tracks system reboots and recovery patterns
- **Features**:
  - Detects system reboots and downtime
  - Logs Docker crash and recovery events
  - Analyzes historical patterns to identify recurring issues
  - JSON structured logging for analysis

### 4. Escalation Manager (`escalation_manager.ps1`)
- **Purpose**: External monitoring and notification system
- **Features**:
  - Tests external endpoint availability
  - Sends notifications when internal systems fail
  - Provides backup monitoring when primary systems fail
  - Configurable notification channels (email, Slack, Teams)

### 5. Enhanced Docker Restart (`enhanced_docker_restart.ps1`)
- **Purpose**: Advanced Docker restart procedures
- **Features**:
  - Multi-phase shutdown (graceful → force → cleanup)
  - Deep cleaning of Docker state and caches
  - Memory optimization before restart
  - Extended readiness verification

## Usage

### Basic Usage (Recommended for Production)

```powershell
# Start with all enhanced monitoring features
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableSelfHealthMonitoring -EnableSystemRecoveryLogging -EnableEscalationManager -EnableAutoRecovery -EnableResourceMonitoring
```

### Individual Component Usage

```powershell
# Enable only specific components
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableAutoRecovery
.\cslaunch.ps1 -EnableSelfHealthMonitoring -EnableSystemRecoveryLogging
```

### Advanced Configuration

```powershell
# Custom thresholds and intervals
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableResourceMonitoring -MemoryThreshold 80 -CpuThreshold 85 -EnhancedCheckInterval 30

# Deep clean and memory optimization for problematic systems
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableAutoRecovery -DeepCleanRestart -MemoryOptimizeRestart
```

## Monitoring Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-EnableEnhancedMonitoring` | false | Enable comprehensive Docker monitoring |
| `-EnableSelfHealthMonitoring` | false | Enable monitoring self-health checks |
| `-EnableSystemRecoveryLogging` | false | Enable system reboot detection |
| `-EnableEscalationManager` | false | Enable external monitoring backup |
| `-EnableResourceMonitoring` | false | Enable Docker resource monitoring |
| `-EnableAutoRecovery` | false | Enable automatic recovery actions |
| `-MemoryThreshold` | 85 | Memory usage warning threshold (%) |
| `-CpuThreshold` | 90 | CPU usage warning threshold (%) |
| `-EnhancedCheckInterval` | 60 | Enhanced monitoring check interval (seconds) |
| `-DeepCleanRestart` | false | Perform deep cleanup during restarts |
| `-MemoryOptimizeRestart` | false | Optimize memory before restarts |

## Status Monitoring

### Check Enhanced Monitoring Status

```powershell
# Show status of all enhanced monitoring components
Show-EnhancedMonitoringStatus
```

### Check Individual Components

```powershell
# Check running monitoring jobs
Get-Job | Where-Object { $_.Name -match "Enhanced|Self-Health|System-Recovery|Escalation" }

# Check log file status
Get-ChildItem logs\enhanced_*.log | ForEach-Object { 
    $file = $_
    $timeSince = (Get-Date) - $file.LastWriteTime
    Write-Host "$($file.Name): $($timeSince.TotalMinutes.ToString('F0')) minutes ago" 
}
```

### View Real-time Logs

```powershell
# Enhanced Docker Monitor logs
Get-Content logs\enhanced_monitor.log -Tail 20 -Wait

# Self-Health Monitor logs
Get-Content logs\self_health_monitor.log -Tail 20 -Wait

# System Recovery logs
Get-Content logs\system_recovery.log -Tail 20 -Wait

# Escalation logs
Get-Content logs\escalation.log -Tail 20 -Wait
```

## Manual Recovery

### Enhanced Docker Restart

```powershell
# Standard enhanced restart
.\scripts\enhanced_docker_restart.ps1

# Deep clean restart for problematic systems
.\scripts\enhanced_docker_restart.ps1 -DeepClean -MemoryOptimize

# Force restart even if Docker appears healthy
.\scripts\enhanced_docker_restart.ps1 -Force
```

### Restart Individual Monitoring Components

```powershell
# Restart enhanced Docker monitor
Stop-Job -Name "Enhanced-Docker-Monitor" -ErrorAction SilentlyContinue
Start-Job -Name "Enhanced-Docker-Monitor" -ScriptBlock { & ".\scripts\enhanced_docker_monitor.ps1" -EnableAutoRecovery -EnableResourceMonitoring }

# Restart self-health monitor
Stop-Job -Name "Self-Health-Monitor" -ErrorAction SilentlyContinue
Start-Job -Name "Self-Health-Monitor" -ScriptBlock { & ".\scripts\monitor_self_health.ps1" }
```

## Troubleshooting

### Common Issues

1. **Monitoring Jobs Not Starting**
   ```powershell
   # Check if scripts exist
   Test-Path .\scripts\enhanced_docker_monitor.ps1
   Test-Path .\scripts\monitor_self_health.ps1
   
   # Check PowerShell execution policy
   Get-ExecutionPolicy
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **High Resource Usage**
   ```powershell
   # Check resource thresholds
   .\cslaunch.ps1 -EnableEnhancedMonitoring -MemoryThreshold 75 -CpuThreshold 80
   
   # Monitor resource usage
   Get-Process "*Docker*" | Format-Table ProcessName, WorkingSet, CPU
   ```

3. **Frequent Restarts**
   ```powershell
   # Check logs for patterns
   Get-Content logs\enhanced_monitor.log | Select-String "RESTART|CRASH|ERROR"
   
   # Analyze recovery patterns
   Get-Content logs\system_recovery.log | ConvertFrom-Json | Where-Object { $_.message -match "reboot|crash" }
   ```

### Log Analysis

```powershell
# Find recent crashes
Get-Content logs\enhanced_monitor.log | Select-String "CRITICAL|ERROR" | Select-Object -Last 10

# Analyze Docker restart patterns
Get-Content logs\enhanced_monitor.log | Select-String "RESTART|RECOVERY" | Group-Object { $_ -split " " | Select-Object -First 1 } | Format-Table Count, Name

# Check system reboot history
Get-Content logs\system_recovery.log | ConvertFrom-Json | Where-Object { $_.message -match "SYSTEM REBOOT" } | Format-Table timestamp, message
```

## Configuration Files

### Environment Variables (Optional)

```powershell
# Notification settings (if using escalation manager)
$env:CASESTRAINER_ADMIN_EMAIL = "admin@example.com"
$env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/..."
$env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/..."
```

### Custom Thresholds

Create `config\enhanced_monitoring.json`:
```json
{
    "memoryThreshold": 80,
    "cpuThreshold": 85,
    "diskThreshold": 90,
    "checkInterval": 60,
    "maxWaitTime": 300,
    "enableAutoRecovery": true,
    "enableResourceMonitoring": true
}
```

## Integration with Existing Systems

### Backward Compatibility

The enhanced monitoring system is fully backward compatible with existing cslaunch.ps1 functionality:

```powershell
# Existing commands still work
.\cslaunch.ps1                    # Standard deployment
.\cslaunch.ps1 -Monitor           # Standard monitoring
.\cslaunch.ps1 -Build             # Build with containers
```

### Gradual Migration

```powershell
# Phase 1: Add enhanced monitoring alongside existing
.\cslaunch.ps1 -EnableEnhancedMonitoring

# Phase 2: Add self-health monitoring
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableSelfHealthMonitoring

# Phase 3: Full deployment
.\cslaunch.ps1 -EnableEnhancedMonitoring -EnableSelfHealthMonitoring -EnableSystemRecoveryLogging -EnableEscalationManager -EnableAutoRecovery
```

## Performance Impact

### Resource Usage

- **Enhanced Docker Monitor**: ~50MB memory, minimal CPU
- **Self-Health Monitor**: ~30MB memory, minimal CPU
- **System Recovery Logger**: ~20MB memory, minimal CPU
- **Escalation Manager**: ~25MB memory, minimal CPU

### Network Usage

- Health checks: ~1KB per check
- External monitoring: ~2KB per check
- Logs: ~10KB per day (typical usage)

## Best Practices

1. **Production Deployment**: Use all enhanced monitoring components
2. **Development**: Use enhanced monitoring + resource monitoring
3. **Testing**: Start with enhanced monitoring, add components gradually
4. **Resource-Constrained**: Use enhanced monitoring + self-health monitoring
5. **Critical Systems**: Use all components + custom thresholds

## Support

For issues with the enhanced monitoring system:

1. Check the relevant log files in `logs\enhanced_*.log`
2. Run `Show-EnhancedMonitoringStatus` for component status
3. Review this guide for common troubleshooting steps
4. Check system event logs for underlying issues

## Version History

- **v1.0**: Initial release with comprehensive monitoring suite
- Addresses recurring 24-48 hour Docker crashes
- Implements lessons learned from December 2025 outage analysis
