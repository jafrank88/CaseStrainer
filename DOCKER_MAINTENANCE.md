# Docker Maintenance Integration

## Overview

Docker maintenance features have been integrated into `cslaunch.ps1` to automatically manage disk space and prevent crashes caused by resource exhaustion.

## New Features

### 1. Manual Docker Cleanup
```powershell
# Clean up all unused Docker resources
.\cslaunch.ps1 -CleanupDocker
```

This will:
- Remove stopped containers
- Remove unused images
- Clean build cache
- Run full system prune
- Display space reclaimed
- Log the cleanup to `logs\docker_cleanup.log`

### 2. Automatic Cleanup When Low on Space
```powershell
# Enable automatic cleanup (runs when < 30GB free)
.\cslaunch.ps1 -AutoCleanup
```

When enabled:
- Monitors disk space every 5 minutes during monitoring
- Automatically runs cleanup if free space < 30GB
- Forces cleanup if free space < 20GB (critical)
- Logs all automatic cleanup actions

### 3. Weekly Scheduled Cleanup
```powershell
# Schedule weekly cleanup (every Sunday at 2 AM)
.\cslaunch.ps1 -ScheduleCleanup

# Remove the scheduled cleanup
.\cslaunch.ps1 -RemoveCleanupSchedule
```

The scheduled task:
- Runs every Sunday at 2:00 AM
- Executes as SYSTEM user (no login required)
- Cleans up Docker resources automatically
- Logs to `logs\docker_cleanup.log`

## Disk Space Thresholds

| Situation | Action | Threshold |
|-----------|--------|-----------|
| Normal operation | No action | > 30GB free |
| Automatic cleanup triggered | Cleanup runs | < 30GB free |
| Critical cleanup forced | Immediate cleanup | < 20GB free |
| Weekly maintenance | Scheduled cleanup | Every Sunday 2AM |

## Integration with Monitoring

When `-AutoCleanup` is enabled:
- Disk space is checked every 5 minutes during monitoring
- Cleanup runs automatically when needed
- No user intervention required
- Prevents Docker crashes due to disk space

## Usage Examples

### Initial Setup (Recommended)
```powershell
# Run once as Administrator to enable all features
.\cslaunch.ps1 -AutoCleanup -ScheduleCleanup
```

### Daily Use
```powershell
# Normal operation with automatic cleanup enabled
.\cslaunch.ps1

# Manual cleanup if needed
.\cslaunch.ps1 -CleanupDocker
```

### Check Cleanup Logs
```powershell
# View cleanup history
Get-Content logs\docker_cleanup.log -Tail 20

# View scheduler logs
Get-Content logs\cleanup_scheduler.log -Tail 20
```

## Benefits

1. **Prevents Crashes** - Automatically maintains disk space
2. **Zero Maintenance** - Runs without user intervention
3. **Configurable** - Enable/disable features as needed
4. **Logged** - Full audit trail of cleanup actions
5. **Scheduled** - Weekly maintenance without manual effort

## Troubleshooting

### Cleanup Not Running
- Check if `-AutoCleanup` is enabled
- Verify scheduled task is active:
  ```powershell
  Get-ScheduledTask -TaskName "CaseStrainer-Docker-WeeklyCleanup"
  ```

### Disk Space Still Low
- Run manual cleanup: `.\cslaunch.ps1 -CleanupDocker`
- Check for large files outside Docker
- Consider increasing disk space

### Logs Not Created
- Ensure `logs\` directory exists
- Check write permissions
- Run as Administrator if needed

## Best Practices

1. Enable `-AutoCleanup` for automatic maintenance
2. Schedule weekly cleanup for regular maintenance
3. Monitor logs periodically to verify operation
4. Run manual cleanup before large builds
5. Keep at least 20GB free for Docker operations
