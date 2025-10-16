# Forward Plan: Complete CaseStrainer Cleanup

**Status**: Stages 1-2 Complete (60 files processed, 39% done)  
**Challenge**: Import dependencies prevent moving production code  
**Goal**: Finish cleanup without breaking the application

---

## 🔍 Root Cause Analysis

### Why Stage 3 Failed

**The Problem:**
- Moved 5 files from root to `src/utils/`
- Async workers couldn't find them (import errors)
- Processing stuck at "Initializing"

**The Core Issue:**
```python
# Old import (still in code)
from cache_manager import CacheManager

# New location requires
from src.utils.cache_manager import CacheManager
```

**Impact:**
- **Estimated 74+ files** have imports that need updating
- Every moved file affects multiple other files
- Breaking imports breaks async processing silently

---

## 🎯 New Strategy: Import-First Approach

Instead of moving files then fixing imports, we'll:
1. **Find ALL imports first**
2. **Update imports to use new paths**
3. **Then move the files**
4. **Test after each batch**

This prevents breaking the system.

---

## 📋 Phase 1: Fix Import System (NEXT SESSION)

### Step 1.1: Analyze Import Dependencies

Create a comprehensive import map:

```powershell
# Find all files that import utilities
grep -r "import cache_manager" . --include="*.py" > imports_analysis.txt
grep -r "from cache_manager" . --include="*.py" >> imports_analysis.txt
grep -r "import clear_cache" . --include="*.py" >> imports_analysis.txt
grep -r "from clear_cache" . --include="*.py" >> imports_analysis.txt
# ... repeat for all utilities
```

**Expected Output:**
- List of every file importing moved code
- Count of imports per file
- Priority order for updates

**Time**: 30 minutes

---

### Step 1.2: Create Import Update Script

Build a PowerShell script to update imports safely:

```powershell
# update_imports_utilities.ps1
# Updates all imports for utilities moved to src/utils/

$files = Get-ChildItem -Path . -Filter "*.py" -Recurse | 
         Where-Object { $_.FullName -notlike "*\venv\*" -and 
                       $_.FullName -notlike "*\node_modules\*" }

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    # Update cache_manager imports
    $content = $content -replace 'from cache_manager import', 'from src.utils.cache_manager import'
    $content = $content -replace 'import cache_manager', 'from src.utils import cache_manager'
    
    # Update clear_cache imports
    $content = $content -replace 'from clear_cache import', 'from src.utils.clear_cache import'
    
    # ... repeat for all utilities
    
    Set-Content $file.FullName -Value $content
}
```

**Time**: 1 hour to create and test

---

### Step 1.3: Update All Imports (Dry Run First)

```powershell
# Test first (show what would change)
.\update_imports_utilities.ps1 -DryRun

# Review changes, then execute
.\update_imports_utilities.ps1

# Test immediately
./cslaunch
```

**Critical**: Test after this step before moving ANY files!

**Time**: 30 minutes

---

### Step 1.4: Move Files AFTER Imports Fixed

Only after imports work:
```powershell
# NOW move the files
Move-Item cache_manager.py src/utils/
Move-Item clear_cache.py src/utils/
# etc.

# Test again
./cslaunch
```

**Time**: 15 minutes

**Total Phase 1 Time**: ~2.5 hours

---

## 📋 Phase 2: Complete Stage 3 (Production Code)

### Batch 1: Utilities (5 files)
- ✅ Import analysis done
- ✅ Imports updated
- Move files to `src/utils/`
- Test: `./cslaunch`
- Commit

### Batch 2: Models (3 files)
- `database_manager.py` → `src/models/`
- `init_database.py` → `src/models/`
- `migrate_citation_databases.py` → `src/models/`

**Process:**
1. Find all imports of these 3 files
2. Update imports first
3. Move files
4. Test
5. Commit

**Time**: 1.5 hours

### Batch 3: Integration (5 files)
- `api_integration.py` → `src/integration/`
- `citation_integration.py` → `src/integration/`
- etc.

**Time**: 2 hours

### Batch 4: Processors (13 files) - HIGHEST RISK
- Test after EVERY 2-3 files moved
- These are critical to citation extraction

**Time**: 3-4 hours

**Total Phase 2 Time**: ~8-10 hours

---

## 📋 Phase 3: Manual Review (Stage 4)

### Step 3.1: Categorize Unknown Files

Create a spreadsheet reviewing ~70 remaining files:

| File | Purpose | Used By | Decision | Destination |
|------|---------|---------|----------|-------------|
| apply_parallel_enhancements.py | One-off script | None | DELETE | - |
| health_check.py | Monitor service | Backend | MOVE | scripts/ |
| ... | ... | ... | ... | ... |

**Categories:**
- **DELETE**: Old/unused/one-off scripts (~20 files)
- **MOVE to scripts/**: Utility scripts (~20 files)
- **MOVE to scripts/analysis/**: Analysis tools (~15 files)
- **MOVE to scripts/processing/**: Processing scripts (~10 files)
- **MOVE to src/**: Production code (~5 files)

**Time**: 2-3 hours

### Step 3.2: Execute Decisions

Process in batches of 10:
1. Delete batch → Test → Commit
2. Move batch → Update imports → Test → Commit
3. Repeat

**Time**: 3-4 hours

**Total Phase 3 Time**: ~6-7 hours

---

## 📋 Phase 4: Final Cleanup (Stage 5)

### Step 4.1: Delete Old Archived Directories
```powershell
# After 1 week of stability
Remove-Item archived/ -Recurse -Force
Remove-Item archive_deprecated/ -Recurse -Force
Remove-Item backup_before_update/ -Recurse -Force
```

### Step 4.2: Update Documentation
- README.md with new structure
- CONTRIBUTING.md with organization rules
- Update .gitignore

### Step 4.3: Clean Up Backups (After 1 week)
```powershell
# Only after verifying stability
Remove-Item backup_stage1_* -Recurse -Force
Remove-Item backup_stage2_* -Recurse -Force
Remove-Item backup_stage3_* -Recurse -Force
```

**Time**: 1 hour

**Total Phase 4 Time**: ~1 hour

---

## 📊 Complete Timeline

| Phase | Task | Time | Files | Completion |
|-------|------|------|-------|------------|
| **DONE** | Stages 1-2 | 2h | 60 | 39% |
| **Phase 1** | Fix imports | 2.5h | 0 | 39% |
| **Phase 2** | Stage 3 complete | 8-10h | 26 | 55% |
| **Phase 3** | Stage 4 manual | 6-7h | 70 | 100% |
| **Phase 4** | Final cleanup | 1h | - | 100% |
| **TOTAL** | | **19-22h** | **156** | **100%** |

**Remaining**: 17-20 hours over 5-6 sessions

---

## 🔧 Tools We'll Create

### 1. Import Analyzer
```powershell
# analyze_imports.ps1
# Scans codebase and creates import dependency map
```

### 2. Import Updater
```powershell
# update_imports.ps1
# Updates imports for moved files
# Supports dry-run mode
```

### 3. File Categorizer
```powershell
# categorize_files.ps1
# Analyzes remaining files and suggests categories
```

### 4. Batch Processor
```powershell
# process_batch.ps1
# Moves a batch of files with proper testing
```

---

## ⚠️ Critical Success Factors

### 1. Import-First Strategy
- ✅ ALWAYS update imports BEFORE moving files
- ✅ NEVER move files without checking imports
- ✅ Test after EVERY batch

### 2. Small Batches
- ✅ Move 2-5 files at a time
- ✅ Test after each batch
- ✅ Commit after each successful batch

### 3. Comprehensive Testing
After each batch:
```powershell
# 1. Start services
./cslaunch

# 2. Check for import errors
docker logs casestrainer-backend-prod --tail 50

# 3. Test async processing
# Submit a test document through web interface

# 4. Check worker logs
docker logs casestrainer-rqworker1-prod --tail 50
```

### 4. Backup Everything
- ✅ Create backup before each session
- ✅ Keep backups for 1 week after completion
- ✅ Git commit after each successful batch

---

## 📅 Recommended Schedule

### Session 1 (2.5 hours) - Fix Import System
- Create import analyzer
- Create import updater
- Update all utility imports
- Test thoroughly
- **Checkpoint**: Imports ready for Stage 3

### Session 2 (3 hours) - Complete Stage 3 Utilities & Models
- Move utilities (5 files)
- Move models (3 files)
- Test between each
- **Checkpoint**: 8 more files moved (47% complete)

### Session 3 (3 hours) - Complete Stage 3 Integration
- Move integration code (5 files)
- Start processors (first 4 files)
- **Checkpoint**: 9 more files moved (53% complete)

### Session 4 (3 hours) - Complete Stage 3 Processors
- Move remaining processors (9 files)
- Test extensively
- **Checkpoint**: Stage 3 complete (55% complete)

### Session 5 (4 hours) - Manual Review Part 1
- Categorize all unknown files
- Delete obvious old files (~20)
- Move utility scripts (~20)
- **Checkpoint**: 40 more files processed (80% complete)

### Session 6 (3 hours) - Manual Review Part 2 + Final Cleanup
- Move analysis scripts (~15)
- Move processing scripts (~10)
- Move remaining production code (~5)
- Final cleanup and documentation
- **Checkpoint**: PROJECT COMPLETE! (100%)

**Total**: 6 sessions over 2-3 weeks

---

## 🎯 Success Metrics

### After Each Session
- [ ] Application starts without errors
- [ ] All services operational
- [ ] Async processing works
- [ ] No stuck jobs
- [ ] Changes committed to git

### Final Success (Project Complete)
- [ ] Only 4-10 files in root (config, setup, wsgi, __init__)
- [ ] All production code in `src/`
- [ ] All scripts in `scripts/`
- [ ] All tests in `tests/`
- [ ] Documentation updated
- [ ] Zero import errors
- [ ] Full functionality maintained

---

## 🚀 Next Session Checklist

**Before you start:**
- [ ] Read this plan
- [ ] Create new safety backup
- [ ] Ensure application is working

**Session 1 goals:**
- [ ] Create import analyzer script
- [ ] Create import updater script
- [ ] Analyze all imports for utilities
- [ ] Update all imports (dry-run first)
- [ ] Test thoroughly
- [ ] Commit if successful

**Time needed**: 2.5 hours  
**Risk level**: Medium (modifying many files)  
**Reward**: Unblock Stage 3 completely

---

## 📝 Questions to Answer in Session 1

1. How many files import `cache_manager.py`?
2. How many files import other utilities?
3. Are there circular dependencies?
4. Do tests import these files?
5. Do Docker configs reference these files?

**Answer these before moving any files!**

---

## 💡 Alternative: Hybrid Approach

If import updates prove too complex:

### Option A: Leave Most Production Code in Root
- Only move scripts (already done ✅)
- Keep production code in root
- Focus on Stage 4 (manual review) instead
- Still achieve 80%+ cleanup

### Option B: Create src/__init__.py with Re-exports
```python
# src/__init__.py
# Allow imports to work from both locations temporarily
from . import cache_manager
from . import clear_cache
# etc.
```

Then update imports gradually over time.

---

## 📚 Reference Documents

- **CLEANUP_PROGRESS.md** - Track completion with checkboxes
- **PROJECT_COMPLETION_PLAN.md** - Original complete plan
- **QUICK_START_CLEANUP.md** - Quick reference
- **execute_stage3.ps1** - Automation script (needs import fixes first)

---

## ✅ Decision Points

**After Session 1:**
- [ ] Continue with import-first approach?
- [ ] Switch to hybrid approach?
- [ ] Skip Stage 3 and focus on Stage 4?

**Recommended**: Try import-first approach in Session 1. If it works, complete Stage 3. If too complex, switch to hybrid.

---

**Created**: October 15, 2025  
**Status**: Ready for Session 1  
**Estimated Completion**: 6 sessions (2-3 weeks)
