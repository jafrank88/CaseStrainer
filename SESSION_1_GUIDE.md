# Session 1 Guide: Fix Import System

**Goal**: Unblock Stage 3 by fixing import dependencies  
**Time**: 2.5 hours  
**Status**: Ready to start

---

## ⚡ Quick Start

```powershell
# 1. Analyze imports (5 min)
.\analyze_imports.ps1

# 2. Review the report (10 min)
# Opens in notepad automatically
# Look for high-risk files (10+ imports)

# 3. Update imports - DRY RUN (2 min)
.\update_imports.ps1 -DryRun

# 4. Review what will change (10 min)
# Check the output looks correct

# 5. Update imports FOR REAL (2 min)
.\update_imports.ps1

# 6. TEST IMMEDIATELY (5 min)
./cslaunch
# Check logs for import errors

# 7. If successful, move files (5 min)
Move-Item cache_manager.py src/utils/
Move-Item clear_cache.py src/utils/
Move-Item clear_stuck_jobs.py src/utils/
Move-Item fixed_file_utils.py src/utils/
Move-Item nested_file_utils.py src/utils/

# 8. TEST AGAIN (5 min)
./cslaunch
# Submit test document through web interface

# 9. Commit (2 min)
git add -A
git commit -m "Stage 3 utilities: Fix imports and move files"
```

**Total active time**: ~45 minutes  
**Remaining time**: Review, troubleshooting, tea breaks

---

## 📋 Detailed Steps

### Step 1: Analyze Current Imports (10 min)

```powershell
# Run import analyzer
.\analyze_imports.ps1
```

**What it does:**
- Scans entire codebase
- Finds all files that import the 5 utilities
- Creates detailed report
- Shows risk levels

**What to look for:**
- Total number of imports
- Which files import what
- High-risk files (10+ imports)

**Output:**
- Console summary
- Detailed report file: `import_analysis_YYYYMMDD_HHMMSS.txt`

**Decision point:**
- If 0 imports: Safe to move immediately
- If 1-5 imports: Low risk, easy to fix
- If 5-10 imports: Medium risk, use script
- If 10+ imports: High risk, must use script

---

### Step 2: Review Analysis Report (10 min)

Open the generated report file and answer:

**Questions:**
1. How many total import locations? ________
2. Which file has most imports? ________
3. Are there any circular dependencies? ________
4. Do any Docker files import these? ________
5. Do any test files import these? ________

**Red flags:**
- ⚠️ More than 50 total imports = Very complex
- ⚠️ Circular dependencies = Need special handling
- ⚠️ Docker/config files = May need manual updates

If you see red flags, STOP and ask for help.

---

### Step 3: Dry Run Import Updates (15 min)

```powershell
# See what would change
.\update_imports.ps1 -Category utilities -DryRun
```

**What to check:**
- ✅ Only .py files are being updated
- ✅ No files in backup directories affected
- ✅ Changes look reasonable
- ✅ Not changing too many files (>100 = suspicious)

**Sample good output:**
```
[DRY RUN] Would update: ./src/app_final_vue.py (2 changes)
[DRY RUN] Would update: ./src/progress_manager.py (1 change)
...
Files that would be changed: 15
Total replacements: 23
```

**Sample bad output:**
```
[DRY RUN] Would update: ./.venv/lib/python3.10/... (1 change)
❌ STOP! Shouldn't touch .venv files!
```

If output looks wrong, STOP and troubleshoot.

---

### Step 4: Update Imports (20 min)

```powershell
# Actually update the files
.\update_imports.ps1 -Category utilities
```

**What happens:**
- Creates backup: `backup_imports_YYYYMMDD_HHMMSS/`
- Updates all Python files
- Shows progress
- Saves summary

**After completion:**
- ✅ Check files modified count
- ✅ Check total replacements
- ✅ Note backup location

**If something goes wrong:**
```powershell
# Restore from backup
Copy-Item -Path backup_imports_*/\*.py -Destination . -Force
```

---

### Step 5: Test BEFORE Moving Files (15 min)

**CRITICAL**: Test that imports work BEFORE moving files!

```powershell
# Restart application
./cslaunch
```

**What to check:**
1. ✅ All services start
2. ✅ No import errors in logs
3. ✅ Backend healthy
4. ✅ Workers ready

**Check logs:**
```powershell
# Check backend for import errors
docker logs casestrainer-backend-prod --tail 100

# Check workers
docker logs casestrainer-rqworker1-prod --tail 50
```

**Look for:**
- ❌ "ModuleNotFoundError: No module named 'cache_manager'"
- ❌ "ImportError: cannot import name"
- ✅ "Flask application created successfully"
- ✅ "Worker started"

**If you see errors:**
- STOP
- Review the error
- Check import updates
- Restore from backup if needed

**If NO errors:**
- ✅ Proceed to next step

---

### Step 6: Move Files (10 min)

**Only do this if Step 5 passed!**

```powershell
# Ensure destination exists
New-Item -ItemType Directory -Path src/utils -Force

# Move the files
Move-Item cache_manager.py src/utils/ -Force
Move-Item clear_cache.py src/utils/ -Force
Move-Item clear_stuck_jobs.py src/utils/ -Force
Move-Item fixed_file_utils.py src/utils/ -Force
Move-Item nested_file_utils.py src/utils/ -Force

# Verify they moved
Test-Path src/utils/cache_manager.py  # Should be True
Test-Path cache_manager.py  # Should be False
```

**What you're doing:**
- Moving files from root to `src/utils/`
- Imports already updated to find them there
- Should "just work" because imports point to new location

---

### Step 7: Test AFTER Moving Files (20 min)

**CRITICAL STEP**: Full testing

```powershell
# Restart application
./cslaunch
```

**Test checklist:**

1. **Services start**
   - [ ] All 7 containers running
   - [ ] No errors in startup

2. **Check logs**
   ```powershell
   docker logs casestrainer-backend-prod --tail 100
   docker logs casestrainer-rqworker1-prod --tail 50
   ```
   - [ ] No import errors
   - [ ] No "module not found" errors

3. **Test async processing** (MOST IMPORTANT)
   - [ ] Open http://localhost/casestrainer/
   - [ ] Paste test URL: `https://www.courts.wa.gov/opinions/pdf/1034300.pdf`
   - [ ] Click "Analyze"
   - [ ] Progress bar moves (not stuck at "Initializing")
   - [ ] Citations are extracted (not 0 citations)
   - [ ] No errors shown

4. **Check async job status**
   ```powershell
   # Should show "No stuck jobs"
   docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** --no-auth-warning zcard rq:queue:casestrainer:started
   # Should return: 0
   ```

**If ANY test fails:**
- STOP
- Review logs
- Check what broke
- Consider rolling back

**If ALL tests pass:**
- ✅ SUCCESS!
- Proceed to commit

---

### Step 8: Commit Changes (10 min)

```powershell
# Add all changes
git add -A

# Commit
git commit -m "Stage 3 utilities: Fix imports and move to src/utils

- Updated all imports from root to src.utils
- Moved 5 utility files to src/utils/
- cache_manager.py
- clear_cache.py
- clear_stuck_jobs.py
- fixed_file_utils.py
- nested_file_utils.py

Tested:
- All services operational
- Async processing working
- No import errors

Backup: backup_imports_YYYYMMDD_HHMMSS"

# Verify commit
git log -1
```

**Safety check:**
- ✅ Commit message clear
- ✅ Lists what was changed
- ✅ Notes testing was done
- ✅ References backup

---

## ⚠️ Troubleshooting

### Problem: Import errors after updating imports

**Symptoms:**
```
ModuleNotFoundError: No module named 'src.utils.cache_manager'
```

**Solution:**
```powershell
# Check Python path in Docker
docker exec casestrainer-backend-prod python -c "import sys; print('\n'.join(sys.path))"

# Should include /app and /app/src

# If not, may need to update docker-compose or add __init__.py
```

---

### Problem: Too many files being updated

**Symptoms:**
```
Files that would be changed: 200+
```

**Solution:**
- Check exclude directories are working
- Verify not updating venv or node_modules
- Review patterns in update script
- May need to adjust exclude list

---

### Problem: Circular dependencies

**Symptoms:**
```
ImportError: cannot import name 'X' from partially initialized module
```

**Solution:**
- Identify which files import each other
- May need to refactor code
- Temporarily skip those files
- Get help if complex

---

### Problem: Async still broken after moves

**Symptoms:**
- Jobs stuck at "Initializing"
- Workers not processing
- No progress

**Solution:**
```powershell
# Check worker logs
docker logs casestrainer-rqworker1-prod --tail 200

# Look for specific import error
# Update that specific file
# Restart workers
./cslaunch
```

---

## ✅ Success Criteria

Before ending session, verify:

- [ ] Import analyzer ran successfully
- [ ] Import updater ran successfully (not dry-run)
- [ ] All tests passed before moving files
- [ ] Files successfully moved to src/utils/
- [ ] All tests passed after moving files
- [ ] Async processing works (tested with real document)
- [ ] No import errors in logs
- [ ] Changes committed to git
- [ ] Backup created and location noted

**If all checked:**
🎉 **Session 1 complete!** You've unblocked Stage 3!

---

## 📝 Session 1 Completion Report

Fill this out at end of session:

```
SESSION 1 RESULTS
=================

Files analyzed: _____
Total imports found: _____
Files updated: _____
Total import replacements: _____
Files moved: 5 (cache_manager, clear_cache, clear_stuck_jobs, fixed_file_utils, nested_file_utils)

Tests:
- Application starts: [ ] PASS [ ] FAIL
- No import errors: [ ] PASS [ ] FAIL
- Async processing: [ ] PASS [ ] FAIL
- Real document test: [ ] PASS [ ] FAIL

Committed: [ ] YES [ ] NO
Backup location: _________________________________

Issues encountered:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

Next session: Move models (3 files) and integration (5 files)
```

---

## 🚀 Next Steps

**After Session 1 success:**

Session 2 will:
1. Run analyzer for models (3 files)
2. Update imports for models
3. Move models to `src/models/`
4. Test
5. Repeat for integration (5 files)
6. Test
7. Commit

**Estimated time**: 3 hours  
**Files**: 8 more files moved

---

**Ready to begin? Run: `.\analyze_imports.ps1`**
