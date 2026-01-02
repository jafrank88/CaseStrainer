# cslaunch.ps1 - Flags and Required Parameters

## Summary

**Only 2 functions require flags:**
1. **Configure Autostart** - Requires `-ConfigureAutostart` flag
2. **Foreground Monitoring** - Requires `-Monitor` flag

**Everything else runs by default or is optional.**

## All Available Flags

### Required Flags (Functions that ONLY work with flags)

| Flag | Function | Description |
|------|----------|-------------|
| `-ConfigureAutostart` | Configure Docker autostart on boot | Sets up scheduled task to start containers on system boot |
| `-Monitor` | Foreground monitoring mode | Full monitoring with container checks + Docker daemon monitoring (blocks until Ctrl+C) |

### Optional Flags (Modify default behavior)

| Flag | Function | Default Behavior |
|------|----------|----------------|
| `-Build` | Force rebuild containers | Uses existing images if available |
| `-Force` | Force full deployment | Quick restart if containers exist |
| `-NoCache` | Build without cache | Uses Docker build cache |
| `-NoMonitor` | Disable background monitoring | Background monitoring enabled by default |

### Optional Parameters (Have defaults)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-MonitorInterval` | 30 | Health check interval in seconds |
| `-DockerDaemonTimeout` | 15 | Docker daemon freeze timeout in seconds |
| `-MaxDockerRestartsPerHour` | 3 | Maximum Docker daemon restarts per hour |
| `-EnableDockerDaemonMonitor` | `$true` | Enable Docker daemon monitoring |

## Default Behavior (No Flags)

When you run `.\cslaunch.ps1` with no flags:

1. ✅ **Quick restart** - Restarts existing containers (if they exist)
2. ✅ **Auto-build Vue** - Builds Vue frontend if source files changed
3. ✅ **Auto-rebuild frontend** - Rebuilds frontend container if dist files changed
4. ✅ **Background monitoring** - Starts Docker daemon monitoring automatically
5. ✅ **Full deployment** - Falls back to full deployment if containers don't exist

## Functions That Require Flags

### 1. Configure Autostart (`-ConfigureAutostart`)

**Required:** Yes - This function ONLY works with the flag

```powershell
.\cslaunch.ps1 -ConfigureAutostart
```

**What it does:**
- Creates scheduled task for Docker autostart on boot
- Configures Docker Desktop startup shortcut
- Sets up auto-start script

**Why it requires a flag:**
- Administrative operation that modifies system configuration
- Should be explicit, not automatic

### 2. Foreground Monitoring (`-Monitor`)

**Required:** Yes - Foreground monitoring ONLY works with the flag

```powershell
.\cslaunch.ps1 -Monitor
```

**What it does:**
- Full container health monitoring
- Container auto-restart
- Docker daemon monitoring
- Docker daemon auto-restart
- Runs in foreground (blocks until Ctrl+C)

**Why it requires a flag:**
- Blocks the terminal (foreground operation)
- More resource-intensive than background monitoring
- User should explicitly choose this mode

**Note:** Background monitoring runs automatically by default (no flag needed)

## Optional Flags (Modify Behavior)

### `-Build` Flag

**Required:** No - Optional

```powershell
# Without flag: Uses existing images
.\cslaunch.ps1

# With flag: Forces rebuild
.\cslaunch.ps1 -Build
```

**What it does:**
- Forces rebuild of containers even if images exist
- Passes `-Build` to deployment script

### `-Force` Flag

**Required:** No - Optional

```powershell
# Without flag: Quick restart if containers exist
.\cslaunch.ps1

# With flag: Forces full deployment
.\cslaunch.ps1 -Force
```

**What it does:**
- Skips quick restart check
- Forces full deployment even if containers exist

### `-NoCache` Flag

**Required:** No - Optional

```powershell
# Without flag: Uses Docker build cache
.\cslaunch.ps1

# With flag: Builds without cache
.\cslaunch.ps1 -NoCache
```

**What it does:**
- Passes `--no-cache` to Docker build
- Forces complete rebuild from scratch

### `-NoMonitor` Flag

**Required:** No - Optional (disables default)

```powershell
# Without flag: Background monitoring starts automatically
.\cslaunch.ps1

# With flag: No monitoring
.\cslaunch.ps1 -NoMonitor
```

**What it does:**
- Disables automatic background monitoring
- Useful if you want to manage monitoring separately

## Examples

### Default Behavior (No Flags)
```powershell
# Does everything automatically:
# - Quick restart containers
# - Build Vue if needed
# - Rebuild frontend if needed
# - Start background monitoring
.\cslaunch.ps1
```

### Configure Autostart (Requires Flag)
```powershell
# Must use flag - this function ONLY works with flag
.\cslaunch.ps1 -ConfigureAutostart
```

### Foreground Monitoring (Requires Flag)
```powershell
# Must use flag - foreground monitoring ONLY works with flag
.\cslaunch.ps1 -Monitor

# Custom intervals
.\cslaunch.ps1 -Monitor -MonitorInterval 60 -DockerDaemonTimeout 20
```

### Force Rebuild (Optional Flag)
```powershell
# Optional - forces rebuild
.\cslaunch.ps1 -Build

# Combine flags
.\cslaunch.ps1 -Build -NoCache -Force
```

### Disable Monitoring (Optional Flag)
```powershell
# Optional - disables default background monitoring
.\cslaunch.ps1 -NoMonitor
```

## Recommendation

The current design is good:
- ✅ **2 functions require flags** - Both are administrative/foreground operations that should be explicit
- ✅ **Everything else is optional** - Default behavior handles common cases
- ✅ **Background monitoring is default** - Provides protection without user action

**No changes needed** - The flag requirements are appropriate for the functionality.










