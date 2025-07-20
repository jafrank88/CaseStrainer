# PowerShell Launch Script Fixes

## Overview
This document summarizes the fixes applied to resolve recurring PowerShell launch script errors in the CaseStrainer project.

## Issues Fixed

### 1. "%1 is not a valid Win32 application" Error
**Problem**: npm commands were failing with Win32 application errors, indicating npm was not properly detected or executed.

**Root Cause**: The `Find-NpmExecutable` function was not robust enough to find npm installations in various locations.

**Solution**: 
- Enhanced npm detection to check multiple common installation paths
- Added fallback detection through Node.js installation
- Improved error messages to guide users to install Node.js/npm

**Files Modified**: `cslaunch.ps1` - `Find-NpmExecutable` function

### 2. "A parameter cannot be found that matches parameter name 'and'" Error
**Problem**: PowerShell was incorrectly parsing npm command arguments, treating "and" as a parameter.

**Root Cause**: PowerShell's `Start-Process` with `ArgumentList` was not handling npm arguments correctly.

**Solution**: 
- Changed npm command execution to use `cmd.exe` wrapper
- Modified `Invoke-VueFrontendBuild` to use `cmd.exe /c npm` instead of direct npm execution
- This prevents PowerShell from misinterpreting npm arguments

**Files Modified**: `cslaunch.ps1` - `Invoke-VueFrontendBuild` function

### 3. "Using variable cannot be retrieved" Error
**Problem**: PowerShell jobs were failing to access variables from the parent scope using `$using:` syntax.

**Root Cause**: Complex job scoping issues when using `Start-Job` with `$using:` variables.

**Solution**: 
- Removed parallel job execution for Vue build checking
- Replaced with direct function calls to avoid scope issues
- Simplified the build detection logic

**Files Modified**: `cslaunch.ps1` - `Start-DockerProduction` function

## Technical Details

### npm Detection Improvements
```powershell
# Enhanced npm detection now checks:
- PATH environment variable
- Common installation directories
- Node.js installation directory
- Multiple file extensions (.cmd, .exe)
```

### npm Command Execution Fix
```powershell
# Before (problematic):
Start-Process -FilePath $npmPath -ArgumentList $buildArgs

# After (fixed):
$cmdArgs = @("/c", $npmPath) + $buildArgs
Start-Process -FilePath "cmd.exe" -ArgumentList $cmdArgs
```

### Job Scope Simplification
```powershell
# Before (problematic):
$vueJob = Start-Job -ScriptBlock {
    return ($using:ForceRebuild.IsPresent -or ...)
}

# After (fixed):
$needsVueBuild = Test-VueBuildNeeded -Force:$ForceRebuild
```

## Testing

### Test Script
Created `test_launch_fixes.ps1` to verify fixes:
- npm detection functionality
- Vue build environment
- Docker availability
- PowerShell environment

### Verification
- ✅ npm build now completes successfully
- ✅ No more "and" parameter errors
- ✅ No more Using variable scope errors
- ✅ Vue frontend builds correctly
- ✅ Docker containers start (backend health issue is separate)

## Usage

The fixed launch script can now be used with confidence:

```powershell
# Quick start
.\cslaunch.ps1 -MenuOption 1

# Full rebuild
.\cslaunch.ps1 -MenuOption 3

# Direct production mode
.\cslaunch.ps1 -Mode Production
```

## Remaining Issues

The only remaining issue is the backend container health check failure, which is unrelated to the PowerShell script fixes and appears to be a Docker/application configuration issue.

## Files Modified

1. `cslaunch.ps1` - Main launch script with all fixes
2. `test_launch_fixes.ps1` - Test script for verification
3. `POWERSHELL_LAUNCH_FIXES.md` - This documentation

## Impact

These fixes resolve the majority of launch script failures that were preventing successful deployment of the CaseStrainer application. Users can now reliably start the application using the PowerShell launch scripts. 