# Timestamp Consistency Fix

## Problem

The CaseStrainer system uses **three different timestamp formats** across different log files, making it difficult to correlate events:

### Current Timestamp Formats:

1. **Python Application Logs** (`casestrainer.log`)
   - Format: `2025-07-08 00:09:15,949`
   - Timezone: Local system time (Pacific)
   - Source: Python logging with `datefmt="%Y-%m-%d %H:%M:%S"`

2. **PowerShell Health Diagnostic Logs** (`backend_health_diag.log`)
   - Format: `2025-07-02T21:43:03.2884629-07:00`
   - Timezone: ISO 8601 with timezone offset (-07:00 for Pacific)
   - Source: PowerShell `Get-Date -Format o`

3. **PowerShell Crash Logs** (`crash.log`)
   - Format: `[2025-07-07 00:36:16]`
   - Timezone: Local system time (Pacific)
   - Source: PowerShell `Get-Date -Format "yyyy-MM-dd HH:mm:ss"`

## Solution

### 1. Python Logging (✅ FIXED)

The Python logging configuration in `src/config.py` has been updated to use ISO 8601 format with timezone:

```python
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S.%f%z"
)

```text

This will produce timestamps like: `2025-07-08T00:09:15.949000-0700`

### 2. PowerShell Scripts (Manual Fix Required)

#### Option A: Update PowerShell Scripts

In the following PowerShell files, replace timestamp formatting:

**Files to update:**

- `launcher.ps1` (lines ~962, ~966)
- `cslaunch.ps1` (lines ~76, ~493, ~505)
- `monitor-casestrainer.ps1` (line ~49)
- Other PowerShell scripts with logging

**Replace:**

```powershell

# Old format

$logMessage = "$(Get-Date -Format o) [WARN] ..."

# New format

$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
$logMessage = "$timestamp [WARN] ..."

```text

#### Option B: Create a PowerShell Function

Add this function to PowerShell scripts for consistent timestamp formatting:

```powershell
function Get-FormattedTimestamp {
    return Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
}

# Usage:

$logMessage = "$(Get-FormattedTimestamp) [WARN] Backend health check failed"

```text

### 3. Batch Files (Manual Fix Required)

Update batch files to use consistent timestamp formatting:

**Files to update:**

- `start_casestrainer.bat`
- `debug_start2.bat`
- Other `.bat` files

**Replace:**

```batch
:: Old format
echo [%TIME%] %MESSAGE%

:: New format (ISO-like)
for /f "tokens=1-4 delims=:.," %%a in ("%TIME%") do set "timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%T%%a:%%b:%%c.%%d"
echo [%timestamp%] %MESSAGE%

```text

## Expected Result

After implementing these changes, all log files will use consistent ISO 8601 format:

```text

2025-07-08T00:09:15.949 | INFO | src.enhanced_multi_source_verifier | Citation verification started
2025-07-08T00:09:15.949 | WARN | Backend health check attempt 1 : Port connection failed
2025-07-08T00:09:15.949 | INFO | Script started with Mode: Production

```text

## Benefits

1. **Easier Event Correlation**: All timestamps in the same format
2. **Timezone Awareness**: ISO 8601 includes timezone information
3. **Millisecond Precision**: Consistent sub-second timing
4. **Standard Compliance**: ISO 8601 is an international standard
5. **Better Debugging**: Easier to trace issues across different components

## Implementation Priority

1. **High Priority**: Python logging (already fixed)
2. **Medium Priority**: PowerShell health diagnostic logs
3. **Low Priority**: Batch file logs and other PowerShell scripts

## Testing

After implementing changes, verify consistency by:

1. Restart the application
2. Check multiple log files for the same time period
3. Verify timestamps are in the same format
4. Test timezone handling during daylight saving time transitions
