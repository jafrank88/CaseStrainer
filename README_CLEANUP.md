# CaseStrainer Cleanup - Quick Reference

**Current Progress**: 60 files processed (39% complete)  
**Status**: Stages 1-2 ✅ Done | Stage 3 ⚠️ Blocked by imports  
**Next**: Fix import system to unblock Stage 3

---

## 📚 Documentation Files

### Strategic Planning
- **FORWARD_PLAN.md** - Complete forward strategy (19-22 hours remaining)
- **PROJECT_COMPLETION_PLAN.md** - Original full plan
- **CLEANUP_PROGRESS.md** - Progress tracker with checkboxes

### Next Session
- **SESSION_1_GUIDE.md** - Detailed step-by-step guide for next session
- **QUICK_START_CLEANUP.md** - Quick reference guide

---

## 🛠️ Tools Available

### Analysis & Automation
```powershell
# Analyze import dependencies
.\analyze_imports.ps1

# Update imports before moving files
.\update_imports.ps1 -DryRun           # Preview changes
.\update_imports.ps1 -Category utilities  # Update utilities

# Stage automation (after imports fixed)
.\execute_stage1.ps1  # ✅ DONE - Deleted 39 files
.\execute_stage2.ps1  # ✅ DONE - Moved 15 files
.\execute_stage3.ps1  # ⚠️ READY - Needs import fixes first
```

---

## ✅ Completed Work

### Stage 1: Delete Old Files (1 hour)
- **39 test files deleted**
  - 15 simple tests
  - 6 quick tests
  - 3 direct tests
  - 8 final/focused tests
- **6 analysis files deleted**
- **Backup**: `backup_stage1_20251015_114939/`
- **Status**: ✅ Committed

### Stage 2: Organize Scripts (1 hour)
- **11 entry point scripts** → `scripts/`
- **4 analysis tools** → `scripts/analysis/`
- **6 one-off files deleted**
- **Backup**: `backup_stage2_20251015_115253/`
- **Status**: ✅ Committed

---

## ⚠️ Current Blocker

### Stage 3: Import Dependencies

**Problem**: Moving production files breaks imports

**Example:**
```python
# Code currently has:
from cache_manager import CacheManager

# After moving to src/utils/, needs to be:
from src.utils.cache_manager import CacheManager
```

**Impact**: 74+ files need import updates

**Solution**: Use `update_imports.ps1` to fix imports BEFORE moving files

---

## 🚀 Next Session Quick Start

**Time needed**: 2.5 hours  
**Goal**: Unblock Stage 3 by fixing imports

```powershell
# 1. Analyze imports
.\analyze_imports.ps1

# 2. Test updates (preview only)
.\update_imports.ps1 -DryRun

# 3. Update imports
.\update_imports.ps1

# 4. Test BEFORE moving
./cslaunch

# 5. Move files to new location
Move-Item cache_manager.py src/utils/
# ... (4 more files)

# 6. Test AFTER moving
./cslaunch

# 7. Commit
git add -A
git commit -m "Stage 3 utilities: Fix imports and move files"
```

**Detailed guide**: See `SESSION_1_GUIDE.md`

---

## 📊 Remaining Work

### Phase 1: Fix Import System (Session 1)
- **Time**: 2.5 hours
- **Files**: 0 moved (prep work)
- **Result**: Unblocks Stage 3

### Phase 2: Complete Stage 3 (Sessions 2-4)
- **Time**: 8-10 hours
- **Files**: 26 moved (utilities, models, integration, processors)
- **Result**: Production code organized

### Phase 3: Manual Review (Sessions 5-6)
- **Time**: 6-7 hours
- **Files**: ~70 reviewed and processed
- **Result**: All files categorized

### Phase 4: Final Cleanup (Session 6)
- **Time**: 1 hour
- **Files**: Documentation and cleanup
- **Result**: Project complete!

**Total remaining**: 17-20 hours over 6 sessions

---

## 🎯 Success Metrics

### Current State
- Files in root: ~97
- Files processed: 60
- Progress: 39%
- System status: ✅ Working

### Target State
- Files in root: 4-10 (only config files)
- Files processed: 156
- Progress: 100%
- System status: ✅ Working + Organized

---

## 📞 Quick Help

### Application won't start?
```powershell
./cslaunch
docker logs casestrainer-backend-prod --tail 100
```

### Async processing stuck?
```powershell
docker logs casestrainer-rqworker1-prod --tail 200
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** --no-auth-warning zcard rq:queue:casestrainer:started
```

### Need to rollback?
```powershell
# Restore from latest backup
Copy-Item -Path backup_stage*_*/\*.py -Destination . -Force
./cslaunch
```

### Check current status
```powershell
# Count files in root
(Get-ChildItem *.py).Count

# Check git status
git status

# List recent commits
git log --oneline -5
```

---

## 📝 File Organization Plan

### Current Structure
```
d:/dev/casestrainer/
├── (97 Python files in root)  ⚠️ TOO MANY
├── scripts/                    ✅ ORGANIZED
│   ├── (11 entry points)
│   └── analysis/
│       └── (4 analysis tools)
├── src/                        ⚠️ NEEDS MORE FILES
│   ├── (existing production code)
│   └── utils/                  📦 READY for utilities
└── tests/                      ✅ ORGANIZED
    └── (149 test files)
```

### Target Structure
```
d:/dev/casestrainer/
├── config.py                   ✅ ESSENTIAL
├── setup.py                    ✅ ESSENTIAL
├── wsgi.py                     ✅ ESSENTIAL
├── __init__.py                 ✅ ESSENTIAL
├── scripts/                    ✅ ORGANIZED
│   ├── (30+ utility scripts)
│   ├── analysis/ (20+ analysis tools)
│   └── processing/ (10+ processing scripts)
├── src/                        ✅ ALL PRODUCTION CODE
│   ├── utils/ (10+ utilities)
│   ├── models/ (5+ models)
│   ├── integration/ (8+ integration)
│   ├── processors/ (15+ processors)
│   └── (other production code)
└── tests/                      ✅ ORGANIZED
    └── (149 test files)
```

---

## 🎊 When Complete

You'll have:
- ✅ Clean, organized codebase
- ✅ Easy to find files
- ✅ Clear separation of concerns
- ✅ Professional structure
- ✅ Easier maintenance
- ✅ Better onboarding for new developers

---

**Ready to continue? Start with:**
1. Read `FORWARD_PLAN.md` for strategy
2. Read `SESSION_1_GUIDE.md` for next steps
3. Run `.\analyze_imports.ps1` when ready

**Good luck!** 🚀
