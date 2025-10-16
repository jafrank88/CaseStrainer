# cslaunch.ps1 Refactoring Plan

## Current Problems

1. **2341 lines in a single file** - Hard to maintain and debug
2. **Complex branching logic** - Multiple paths that can execute (Fast, Quick, Full, Frontend, etc.)
3. **Flags not working** - `-ForceFrontend` doesn't work as expected
4. **Duplicate logic** - Vue build code repeated in multiple places
5. **Hard to test** - Monolithic structure makes unit testing impossible
6. **Unclear flow** - Hard to trace which code path executes
7. **Mixed concerns** - Docker health checks, file monitoring, Vue builds all mixed together

## Recommended Structure

```
scripts/
├── cslaunch.ps1              # Main entry point (50-100 lines)
├── modules/
│   ├── Docker.psm1           # ✅ Already exists
│   ├── Nginx.psm1            # ✅ Already exists
│   ├── VueBuild.psm1         # NEW: Vue build logic
│   ├── HealthCheck.psm1      # NEW: Health check functions
│   ├── FileMonitoring.psm1   # NEW: File hash monitoring
│   └── Deployment.psm1       # NEW: Deployment strategies
```

## Module Breakdown

### 1. VueBuild.psm1 (NEW)
**Purpose**: Handle all Vue.js build operations

**Functions**:
```powershell
function Test-VueBuildNeeded {
    # Check if source files are newer than dist files
    # Returns: $true if build needed, $false otherwise
}

function Start-VueBuild {
    # Run npm run build
    # Handle errors gracefully
    # Returns: $true if successful
}

function Copy-VueDistToStatic {
    # Copy dist files to static directory
    # Used by both frontend and backend containers
}

function Update-VueFrontend {
    # Complete frontend update workflow:
    # 1. Build Vue if needed
    # 2. Copy to static
    # 3. Restart containers
}
```

**Benefits**:
- Single source of truth for Vue builds
- No duplicate code
- Easy to test
- Clear error handling

### 2. HealthCheck.psm1 (NEW)
**Purpose**: All health check logic

**Functions**:
```powershell
function Test-DockerHealth {
    # Check Docker daemon, processes, API
}

function Test-FrontendHealth {
    # Check if frontend needs rebuild
    # Compare source vs dist vs container timestamps
}

function Test-BackendHealth {
    # Check if backend needs restart
    # Check Python cache, dependencies
}

function Test-ApplicationHealth {
    # Check if app is responding
    # Test health endpoint
}
```

**Benefits**:
- Centralized health checks
- Reusable across different modes
- Clear pass/fail logic

### 3. FileMonitoring.psm1 (NEW)
**Purpose**: File change detection and hash monitoring

**Functions**:
```powershell
function Initialize-FileMonitoring {
    # Set up .cslaunch_cache directory
    # Initialize hash storage
}

function Test-FileChanged {
    param($FilePath)
    # Check if file hash changed since last run
}

function Get-ChangedFiles {
    # Return list of changed files
    # Categorize: frontend, backend, dependencies
}

function Update-FileHashes {
    # Store current hashes for next run
}
```

**Benefits**:
- Reliable change detection
- Works on first run
- Clear state management

### 4. Deployment.psm1 (NEW)
**Purpose**: Deployment strategies

**Functions**:
```powershell
function Start-QuickDeployment {
    # No code changes - just restart containers
}

function Start-FastDeployment {
    # Code changes - rebuild and restart
}

function Start-FullDeployment {
    # Dependency changes - full rebuild
}

function Start-FrontendDeployment {
    # Frontend changes only
}

function Start-BackendDeployment {
    # Backend changes only
}
```

**Benefits**:
- Clear deployment strategies
- No branching logic in main script
- Easy to add new strategies

### 5. Simplified cslaunch.ps1

**New main script (50-100 lines)**:
```powershell
param(
    [switch]$Quick,
    [switch]$Fast,
    [switch]$Full,
    [switch]$ForceFrontend,
    [switch]$ForceBackend
)

# Import modules
Import-Module "$PSScriptRoot\modules\Docker.psm1"
Import-Module "$PSScriptRoot\modules\Nginx.psm1"
Import-Module "$PSScriptRoot\modules\VueBuild.psm1"
Import-Module "$PSScriptRoot\modules\HealthCheck.psm1"
Import-Module "$PSScriptRoot\modules\FileMonitoring.psm1"
Import-Module "$PSScriptRoot\modules\Deployment.psm1"

# Initialize
Initialize-FileMonitoring

# Check Docker health
if (-not (Test-DockerHealth)) {
    Write-Host "Docker not healthy. Run: ./cslaunch -HealthCheck" -ForegroundColor Red
    exit 1
}

# Determine deployment strategy
if ($ForceFrontend) {
    Start-FrontendDeployment -Force
}
elseif ($ForceBackend) {
    Start-BackendDeployment -Force
}
elseif ($Full) {
    Start-FullDeployment
}
elseif ($Fast) {
    Start-FastDeployment
}
elseif ($Quick) {
    Start-QuickDeployment
}
else {
    # Auto-detect changes
    $changes = Get-ChangedFiles
    
    if ($changes.Frontend) {
        Start-FrontendDeployment
    }
    elseif ($changes.Backend) {
        Start-BackendDeployment
    }
    elseif ($changes.Dependencies) {
        Start-FullDeployment
    }
    else {
        Start-QuickDeployment
    }
}

Write-Host "CaseStrainer is ready!" -ForegroundColor Green
```

## Migration Strategy

### Phase 1: Extract Vue Build Logic (Week 1)
1. Create `VueBuild.psm1`
2. Move all Vue build code to module
3. Update cslaunch.ps1 to use module
4. Test thoroughly

### Phase 2: Extract Health Checks (Week 2)
1. Create `HealthCheck.psm1`
2. Move health check functions
3. Update cslaunch.ps1
4. Test

### Phase 3: Extract File Monitoring (Week 3)
1. Create `FileMonitoring.psm1`
2. Move hash monitoring logic
3. Update cslaunch.ps1
4. Test

### Phase 4: Extract Deployment Strategies (Week 4)
1. Create `Deployment.psm1`
2. Move deployment logic
3. Simplify main script
4. Test all modes

### Phase 5: Final Cleanup (Week 5)
1. Remove duplicate code
2. Add error handling
3. Add logging
4. Documentation
5. Final testing

## Benefits After Refactoring

### For Developers:
- ✅ Easy to find and fix bugs
- ✅ Can test individual modules
- ✅ Clear separation of concerns
- ✅ Easy to add new features
- ✅ Reduced code duplication

### For Users:
- ✅ Flags work correctly
- ✅ Faster execution (no redundant checks)
- ✅ Better error messages
- ✅ More reliable deployments
- ✅ Consistent behavior

### For Maintenance:
- ✅ Easier to onboard new developers
- ✅ Clear module responsibilities
- ✅ Reusable components
- ✅ Better documentation
- ✅ Easier to debug

## Immediate Quick Fix (Alternative)

If full refactoring is too much work, here's a minimal fix for the current script:

### Fix 1: Make -ForceFrontend work
**Problem**: Flag is defined but logic doesn't execute
**Solution**: Add explicit check at the beginning of the script

```powershell
# Add this right after parameter definitions (line 20)
if ($ForceFrontend) {
    Write-Host "Force Frontend Rebuild requested..." -ForegroundColor Magenta
    
    # Build Vue
    Push-Location "casestrainer-vue-new"
    npm run build
    Pop-Location
    
    # Copy to static
    Copy-Item "casestrainer-vue-new\dist\index.html" "static\index.html" -Force
    Copy-Item "casestrainer-vue-new\dist\assets\*" "static\assets\" -Force -Recurse
    
    # Restart containers
    docker restart casestrainer-frontend-prod casestrainer-backend-prod
    
    Write-Host "Frontend rebuild completed!" -ForegroundColor Green
    exit 0
}
```

### Fix 2: Always check Vue build in default mode
**Problem**: Health check doesn't always run
**Solution**: Force health check before any deployment

```powershell
# Add this before "Analyzing code changes..." (line 2240)
Write-Host "Checking if Vue frontend needs rebuilding..." -ForegroundColor Cyan
if (Test-VueBuildNeeded) {
    Write-Host "Vue build needed - rebuilding..." -ForegroundColor Yellow
    Start-VueBuild
    Copy-VueDistToStatic
}
```

## Recommendation

**Option A: Full Refactoring** (Recommended for long-term)
- Takes 4-5 weeks
- Much better maintainability
- Easier to add features
- Better for team collaboration

**Option B: Quick Fixes** (Recommended for short-term)
- Takes 1-2 hours
- Fixes immediate issues
- Keeps current structure
- Can refactor later

**My suggestion**: Start with **Option B** (quick fixes) to get things working now, then plan **Option A** (full refactoring) for a future sprint when you have more time.

Would you like me to implement the quick fixes now?
