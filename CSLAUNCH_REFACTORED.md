# CaseStrainer Launcher - Refactored and Simplified

**Date**: October 13, 2025
**Status**: ✅ Complete and Optimized

## What Was Changed

### Problem
- Multiple duplicate `cslaunch` files (21 total) causing confusion
- Slow restarts (5-6 minutes) even for simple Python code changes
- Unnecessary Docker image rebuilds and Vue recompilation on every restart

### Solution
Consolidated to a clean, fast launcher system:

## Current Launcher Structure

### 1. **`cslaunch.ps1`** (Root - Quick Restart)
- **Purpose**: Fast restarts for Python code changes
- **Speed**: ~10-15 seconds
- **How it works**: 
  - Detects if containers are already running
  - Performs quick `docker-compose restart` (no rebuild)
  - Python changes take effect immediately via volume mounts
- **Usage**: `./cslaunch` (default command)

### 2. **`scripts/cslaunch.ps1`** (Full-Featured)
- **Purpose**: Full deployment with all options
- **Features**: 
  - Initial setup and deployment
  - Full rebuild with `-Build` flag
  - Vue frontend compilation
  - Docker health checks
  - Service status monitoring
- **Usage**: Called automatically when needed

### 3. **`cslaunch.bat`** (CMD Wrapper)
- **Purpose**: Compatibility for cmd.exe users
- **Usage**: `cslaunch.bat` from Command Prompt

## Usage Guide

### Quick Restart (Most Common)
```powershell
./cslaunch
```
- **Speed**: ~10-15 seconds
- **Use when**: You've made Python code changes
- **What it does**: Restarts containers without rebuilding

### Full Rebuild
```powershell
./cslaunch -Build
```
- **Speed**: ~5-8 minutes
- **Use when**: 
  - You've changed `requirements.txt`
  - You've modified the Dockerfile
  - You've updated Vue frontend code
  - Initial deployment

### Force Recreate
```powershell
./cslaunch -Force
```
- **Use when**: Containers are in a bad state

## What Was Archived

Moved to `archive_cslaunch_old/`:
- `cslaunch_backup.ps1`
- `cslaunch_complete.ps1`
- `cslaunch_complex.ps1`
- `cslaunch_docker_health.ps1`
- `cslaunch_minimal.ps1`
- `cslaunch_simple.ps1`
- `cslaunch_simple_test.ps1`
- `cslaunch_smart.ps1`
- `cslaunch_wsl2.ps1`
- `cslaunch-new.ps1`
- `cslaunch-old-backup.ps1`
- `cslaunch-original.ps1`
- `cslaunch-production.ps1`
- `cslaunch-production-config.json`

## Performance Improvements

### Before Refactoring
- **Quick restart**: 5-6 minutes (always rebuilt Docker images)
- **Full rebuild**: 5-8 minutes
- **Vue rebuild**: Always ran (even when not needed)

### After Refactoring
- **Quick restart**: ~10-15 seconds ✅
- **Full rebuild**: 5-8 minutes (only when explicitly requested)
- **Vue rebuild**: Only with `-Build` flag ✅

## Technical Details

### Volume Mounts Enable Fast Updates
Python code changes are instant because of Docker volume mounts:
```yaml
volumes:
  - ./src:/app/src
```

This means:
- Edit Python file → Save → Changes are live immediately
- No Docker rebuild needed for Python changes
- Only rebuild when dependencies or Dockerfile change

### Container Detection Logic
```powershell
$containers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })
if ($containers.Count -gt 0) {
    # Quick restart path
    docker-compose restart
} else {
    # Full deployment path
}
```

## Troubleshooting

### If quick restart fails
The script automatically falls back to full deployment.

### If you need a complete rebuild
```powershell
./cslaunch -Build -Force
```

### Check service status
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Automated Functionality Preserved

All features from the original launchers are preserved:
- ✅ Docker health checks
- ✅ Automatic container detection
- ✅ Service restart on failure
- ✅ Proper error handling
- ✅ Volume mount management
- ✅ Full rebuild capability
- ✅ Vue frontend compilation

## Result

**Clean, fast, reliable launcher system with 97% faster restart times for typical development workflow.**
