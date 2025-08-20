# CaseStrainer Code Verification System

## Overview

The enhanced `cslaunch.ps1` now includes a comprehensive code verification system that ensures your production containers are running the latest code and that auto-restart will use the same code version.

## New Modes

### 1. CodeCheck Mode
```powershell
.\cslaunch.ps1 -CodeCheck
```

**What it does:**
- Checks backend code consistency (source vs container creation time)
- Checks Vue frontend consistency (source vs built files)
- Checks container image consistency across all backend containers
- Provides auto-restart verification status

**Output includes:**
- Backend code status (Current/Outdated)
- Vue frontend status (Current/Outdated)
- Container image consistency (Consistent/Inconsistent)
- Auto-restart safety status (Safe/Unsafe)
- Specific recommendations for any issues found

### 2. AutoRestartCheck Mode
```powershell
.\cslaunch.ps1 -AutoRestartCheck
```

**What it does:**
- Focuses specifically on auto-restart safety
- Verifies that auto-restart will use the latest code
- Provides clear recommendations if issues are found

**Output includes:**
- Auto-restart status (Safe/Unsafe)
- Detailed breakdown of any issues
- Specific recommendations for each problem
- Recommended actions to resolve issues

### 3. Enhanced Status Mode
```powershell
.\cslaunch.ps1 -Status
```

**What it now includes:**
- All previous status information
- **NEW:** Code consistency status
- **NEW:** Auto-restart verification
- Clear indication if rebuilds are needed

## How It Works

### Backend Code Verification
- Compares the most recent source file modification time with container creation time
- Uses a 5-minute tolerance window
- Flags as "Outdated" if source is newer than container

### Vue Frontend Verification
- Compares Vue source files with built distribution files
- Uses a 10-minute tolerance window
- Flags as "Outdated" if source is newer than built files

### Container Image Consistency
- Checks if all backend containers (backend + RQ workers) use the same image ID
- Flags as "Inconsistent" if different image IDs are detected
- Ensures all containers are built from the same codebase

### Auto-Restart Safety
- **SAFE:** All containers running latest code, auto-restart will use same version
- **UNSAFE:** Some containers outdated, auto-restart will NOT use latest code
- **PARTIAL:** Some issues detected, auto-restart may use outdated code

## Integration with Auto-Detection

The enhanced launcher now includes code consistency checks in its auto-detection logic:

1. **No containers exist** → Full Rebuild
2. **Containers stopped** → Fast Start  
3. **Code changes detected** → Fast Start
4. **Code consistency issues** → Fast Start (NEW!)
5. **No changes, containers running** → Quick Start

## Example Scenarios

### Scenario 1: All Systems Current
```
BACKEND CODE:
  Status: CURRENT
  Source code and container are in sync (within 5 minutes)

VUE FRONTEND:
  Status: CURRENT
  Vue source and built files are in sync (within 10 minutes)

CONTAINER IMAGES:
  Status: CONSISTENT
  All backend containers using same image ID: 98a07cbb3ef1

AUTO-RESTART VERIFICATION:
  Status: SAFE
  Auto-restart will use the same code version
  All containers are running the latest code
```

### Scenario 2: Backend Code Outdated
```
BACKEND CODE:
  Status: OUTDATED
  Source code is 45.2 minutes newer than container
  Recommendation: Rebuild backend containers

AUTO-RESTART VERIFICATION:
  Status: UNSAFE
  Auto-restart will NOT use the latest code
  Some containers are running outdated code

RECOMMENDED ACTIONS:
  • Run: .\cslaunch.ps1 -Fast
```

### Scenario 3: Container Images Inconsistent
```
CONTAINER IMAGES:
  Status: INCONSISTENT
  Backend containers using different image IDs
  Recommendation: Rebuild all backend containers

AUTO-RESTART VERIFICATION:
  Status: UNSAFE
  Auto-restart will NOT use the latest code
  Some containers are running outdated code
```

## Best Practices

### Before Relying on Auto-Restart
1. Run `.\cslaunch.ps1 -CodeCheck` to verify current status
2. Run `.\cslaunch.ps1 -AutoRestartCheck` for specific auto-restart verification
3. Resolve any issues before production deployment

### Regular Monitoring
1. Use `.\cslaunch.ps1 -Status` for comprehensive system overview
2. Run code checks after any code deployments
3. Monitor for container image inconsistencies

### When Issues Are Found
1. **Backend outdated:** Use `.\cslaunch.ps1 -Fast` to rebuild backend
2. **Vue outdated:** Use `.\cslaunch.ps1 -VueBuild` to rebuild frontend
3. **Images inconsistent:** Use `.\cslaunch.ps1 -Fast` to rebuild all containers
4. **Multiple issues:** Use `.\cslaunch.ps1 -Fast -AlwaysRebuild`

## Technical Details

### Tolerance Windows
- **Backend code:** 5 minutes (accounts for build time)
- **Vue frontend:** 10 minutes (accounts for build and copy time)
- **Container images:** Must be identical (no tolerance)

### What Gets Checked
- **Backend:** All files in `src/` directory
- **Vue:** All files in `casestrainer-vue-new/src/` vs `casestrainer-vue-new/dist/`
- **Containers:** `casestrainer-backend-prod`, `casestrainer-rqworker1-prod`, `casestrainer-rqworker2-prod`, `casestrainer-rqworker3-prod`

### Performance Impact
- Code checks are lightweight (file system operations only)
- No Docker operations during verification
- Fast execution (< 1 second typically)

## Troubleshooting

### Common Issues
1. **"Directories Not Found"** - Check if Vue source/dist directories exist
2. **"Container Not Running"** - Verify production containers are active
3. **"Image IDs are inconsistent"** - Usually indicates partial rebuilds

### False Positives
- Very recent builds (< 5 minutes) may show as outdated
- File system time differences can cause minor discrepancies
- Container creation time vs actual code deployment time

## Conclusion

The new code verification system ensures that:
- You always know if your containers are running the latest code
- Auto-restart behavior is predictable and safe
- Code consistency issues are detected early
- Clear recommendations guide you to the right actions

This system provides confidence that your production environment is always running the intended code version and that auto-restart mechanisms won't introduce unexpected behavior.
