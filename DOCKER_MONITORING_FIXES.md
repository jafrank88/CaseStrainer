# Docker Monitoring and Restart Fixes for cslaunch.ps1

## Issues Identified

1. **Docker Events Not Being Logged**
   - The script monitors Docker health but doesn't capture Docker events
   - No `docker events` command being used to capture real-time events
   - Missing persistent event logging

2. **Background Monitoring Loop Issues**
   - Over 535 failed restart attempts since Dec 11, 2025
   - The "nuclear option" continuously triggered
   - Docker never becomes ready within the 120-second timeout
   - No exponential backoff for retry attempts

3. **Ineffective Restart Logic**
   - The restart attempts are failing repeatedly
   - No diagnostic information captured about why Docker won't start
   - Fixed timeout of 120 seconds is too short for some systems
   - Missing system resource checks (disk space, memory)

4. **Missing Health Diagnostics**
   - Basic health checks don't capture detailed error information
   - No checking of Docker service status
   - No verification of Docker Desktop process
   - Missing Windows Event Log analysis

## Fixes Implemented

### 1. Docker Event Monitoring (`Start-DockerEventMonitoring`)
- Added function to capture Docker events in background
- Events logged to `logs\docker_events.log`
- Uses `docker events --format` for structured logging
- Runs as separate PowerShell job for non-blocking operation

### 2. Enhanced Health Checks (`Test-DockerDaemonHealthDetailed`)
- Captures detailed error messages from Docker commands
- Checks Docker service status
- Verifies Docker Desktop process is running
- Includes diagnostic information in health reports

### 3. Improved Restart Logic (`Restart-DockerEnhancedFixed`)
- Pre-restart diagnostics (process list, disk space, memory)
- Progressive timeout checks (3 minutes total, not 2)
- Graceful shutdown before force kill
- WSL cleanup for thorough restart
- Post-restart verification and logging
- Windows Event Log analysis on failures

### 4. Frozen Detection (`Test-DockerFrozen`)
- Differentiates between slow and frozen Docker
- Measures actual response time
- Provides specific diagnostic messages

### 5. Exponential Backoff (`Get-BackoffDelay`)
- Implements exponential backoff for retry attempts
- Base delay of 30s, doubling each attempt
- Maximum delay capped at 5 minutes
- Prevents system overload during failures

### 6. Enhanced Monitoring Loop
- Added Docker event monitoring to background jobs
- Included event monitoring in watchdog recovery
- Better error handling and logging
- Exponential backoff instead of fixed delays

## Files Created/Modified

1. **cslaunch_docker_fixes.ps1** - Contains all enhanced functions
2. **cslaunch_patch.ps1** - Script to apply patches to main cslaunch.ps1
3. **DOCKER_MONITORING_FIXES.md** - This documentation file

## How to Apply Fixes

1. **Apply the patch:**
   ```powershell
   .\cslaunch_patch.ps1 -Backup
   ```

2. **Or manually integrate the fixes:**
   - Copy functions from `cslaunch_docker_fixes.ps1`
   - Update the monitoring loop in `cslaunch.ps1`
   - Add event monitoring to background jobs

## New Log Files

- **logs\docker_events.log** - Real-time Docker events
- **logs\docker_daemon_monitor.log** - Enhanced with diagnostics

## Testing the Fixes

1. **Test event monitoring:**
   ```powershell
   .\cslaunch.ps1 -Monitor
   # Check logs\docker_events.log for events
   ```

2. **Test enhanced restart:**
   ```powershell
   # Stop Docker Desktop manually
   # Wait for monitoring to detect and restart
   # Check logs for detailed diagnostics
   ```

3. **Verify exponential backoff:**
   ```powershell
   # Check log for "Using exponential backoff" messages
   ```

## Key Improvements

1. **Visibility:** Docker events now captured and logged
2. **Diagnostics:** Detailed system state captured before/after restarts
3. **Reliability:** Exponential backoff prevents system overload
4. **Recovery:** Progressive timeout checks improve restart success
5. **Monitoring:** Event monitoring included in watchdog recovery

## Troubleshooting

If Docker still fails to restart after these fixes:

1. Check `logs\docker_daemon_monitor.log` for:
   - Disk space warnings (< 5GB free)
   - Memory usage information
   - Windows Event Log entries
   - Process cleanup status

2. Check `logs\docker_events.log` for:
   - Container start/stop events
   - Docker daemon events
   - Error events

3. Manual intervention may be needed if:
   - Disk space is critically low
   - Memory is insufficient
   - Docker Desktop installation is corrupted
   - Windows services are failing

## Next Steps

1. Apply the patch using `cslaunch_patch.ps1`
2. Test the enhanced monitoring
3. Monitor logs for improved diagnostics
4. Consider adjusting timeouts based on system performance
