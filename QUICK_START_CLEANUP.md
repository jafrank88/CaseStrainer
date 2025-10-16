# Quick Start: Complete CaseStrainer Cleanup

**Goal**: Transform 157 files in root → 4 clean files  
**Time**: 8-12 hours total  
**Current**: Ready to start!

---

## 🚀 Getting Started

### 1. Review the Plan
```powershell
# Read the full plan
code PROJECT_COMPLETION_PLAN.md

# See detailed analysis
python analyze_remaining_files.py
```

### 2. Choose Your Approach

**Option A: Automated (Recommended)**
- Uses provided PowerShell scripts
- Safest and fastest
- Built-in backups and testing

**Option B: Manual**
- Full control over each file
- Slower but more deliberate
- Good for learning the codebase

**Option C: Hybrid**
- Use scripts for obvious files
- Manual review for unknowns
- Best of both worlds ✅

---

## ⚡ Quick Execution (Automated)

### Stage 1: Delete Old Files (~1-2 hours)
```powershell
# Preview what will be deleted
.\execute_stage1.ps1 -DryRun

# Execute (with confirmations)
.\execute_stage1.ps1

# Test
./cslaunch

# Commit
git add .
git commit -m "Stage 1: Delete old test and analysis files"
```

**Result**: ~40 files deleted, ~117 remaining

---

### Stage 2: Move Scripts (~1 hour)
```powershell
# Preview
.\execute_stage2.ps1 -DryRun

# Execute
.\execute_stage2.ps1

# Test
./cslaunch

# Commit
git add .
git commit -m "Stage 2: Move scripts to proper locations"
```

**Result**: ~15 files moved/deleted, ~102 remaining

---

### Stage 3: Move Production Code (~2-3 hours)
```powershell
# Preview all
.\execute_stage3.ps1 -DryRun

# Or do one category at a time (recommended)
.\execute_stage3.ps1 -Category utilities
# Test, then continue...

.\execute_stage3.ps1 -Category models
# Test, then continue...

.\execute_stage3.ps1 -Category integration
# Test, then continue...

.\execute_stage3.ps1 -Category processors
# Test carefully! This is critical code

# Test THOROUGHLY
./cslaunch
# Process a test document through web interface

# Commit
git add .
git commit -m "Stage 3: Move production code to src/"
```

**Result**: ~26 files moved, ~76 remaining

---

### Stage 4: Manual Review (~3-4 hours)

**This requires manual work - no script available**

```powershell
# Create review spreadsheet
New-Item unknown_files_review.csv

# For each unknown file:
# 1. Read the file
code filename.py

# 2. Check if used
grep -r "import filename" src/
grep -r "from filename" src/

# 3. Decide: DELETE, MOVE, or KEEP
# 4. Execute decision
# 5. Test
# 6. Commit after each batch of 10
```

**Categories to handle**:
- DELETE: Old/unused files (~15 files)
- MOVE to scripts/: Utility scripts (~20 files)
- MOVE to scripts/analysis/: Analysis tools (~15 files)
- MOVE to scripts/processing/: Processing scripts (~10 files)
- MOVE to src/: Production code (~10 files)

**Result**: ~70 files processed, ~6 remaining

---

### Stage 5: Final Cleanup (~1 hour)
```powershell
# Delete old archived directories
Remove-Item -Recurse archived/
Remove-Item -Recurse archive_deprecated/
Remove-Item -Recurse backup_before_update/
Remove-Item -Recurse archive_temp_files/

# Update documentation
code README.md
# Add new directory structure

# Test final state
./cslaunch

# Final commit
git add .
git commit -m "Final cleanup: Delete archived dirs and update docs"
git push
```

**Result**: PROJECT COMPLETE! 🎉

---

## 📋 Daily Workflow

### Day 1 Session (2-3 hours)
```powershell
# Stage 1: Quick wins
.\execute_stage1.ps1
./cslaunch  # Test
git commit -m "Stage 1 complete"

# Stage 2: Move scripts
.\execute_stage2.ps1
./cslaunch  # Test
git commit -m "Stage 2 complete"
```
**Progress**: ~55 files done, ~102 remaining

### Day 2 Session (2-3 hours)
```powershell
# Stage 3: Production code
.\execute_stage3.ps1 -Category utilities
./cslaunch  # Test

.\execute_stage3.ps1 -Category models
./cslaunch  # Test

.\execute_stage3.ps1 -Category integration
./cslaunch  # Test

.\execute_stage3.ps1 -Category processors
./cslaunch  # Test THOROUGHLY
# Process a document

git commit -m "Stage 3 complete"
```
**Progress**: ~81 files done, ~76 remaining

### Day 3 Session (3-4 hours)
```powershell
# Stage 4: Manual review
# Categorize and process unknown files
# Test after each batch
# Commit after each 10 files
```
**Progress**: ~151 files done, ~6 remaining

### Day 4 Session (1 hour)
```powershell
# Stage 5: Final cleanup
# Delete archived dirs
# Update docs
# Final commit
git push
```
**Progress**: COMPLETE! ✅

---

## ⚠️ Safety Tips

### Before Each Session
1. ✅ Ensure you have latest code: `git pull`
2. ✅ Check everything works: `./cslaunch`
3. ✅ Create safety commit: `git commit -m "Before cleanup session"`

### During Each Session
1. ✅ Run scripts with `-DryRun` first
2. ✅ Test after EVERY change
3. ✅ Commit after each successful stage
4. ✅ If something breaks: `git checkout -- .`

### After Each Session
1. ✅ Final test: `./cslaunch`
2. ✅ Commit: `git commit -m "Session X complete"`
3. ✅ Update CLEANUP_PROGRESS.md
4. ✅ Note any issues or decisions

---

## 🔧 Useful Commands

### Check What's Left
```powershell
# Count Python files in root
(Get-ChildItem *.py).Count

# List them
Get-ChildItem *.py | Select-Object Name

# Analyze remaining files
python analyze_remaining_files.py
```

### Test Commands
```powershell
# Basic test
./cslaunch

# Check for import errors
python -c "import src.module_name"

# Grep for usage
grep -r "import filename" src/
```

### Recovery Commands
```powershell
# Restore from latest commit
git checkout -- .

# Restore from backup
Copy-Item -Path backup_stageX_*\* -Destination . -Force

# See what changed
git status
git diff
```

---

## 📊 Progress Tracking

### Update Progress After Each Session
```markdown
# In CLEANUP_PROGRESS.md
- [x] Stage 1: Complete
- [x] Stage 2: Complete  
- [ ] Stage 3: In progress (utilities done)
- [ ] Stage 4: Not started
- [ ] Stage 5: Not started
```

### Check Your Progress
```powershell
# Files remaining
(Get-ChildItem *.py).Count

# Should decrease each session:
# Start: 157
# After Stage 1: ~117
# After Stage 2: ~102
# After Stage 3: ~76
# After Stage 4: ~6
# After Stage 5: ~4 ✅
```

---

## 🎯 Success Metrics

### You're Done When:
- [ ] Only 4-10 files in root (config, setup, wsgi, __init__)
- [ ] All production code in `src/`
- [ ] All scripts in `scripts/`
- [ ] All tests in `tests/`
- [ ] `./cslaunch` works perfectly
- [ ] Can process documents successfully
- [ ] No import errors
- [ ] Documentation updated
- [ ] Everything committed and pushed

### Final Check
```powershell
# Should see only essential files
Get-ChildItem *.py | Select-Object Name

# Expected output:
# __init__.py
# config.py
# setup.py
# wsgi.py
# (maybe 2-3 more essential files)
```

---

## 🆘 If You Get Stuck

### Common Issues

**Issue**: Script won't run
**Solution**: 
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Issue**: Test fails after moving files
**Solution**:
1. Check error message
2. Restore from backup
3. Try moving fewer files
4. Update imports if needed

**Issue**: Don't know if file is safe to delete
**Solution**:
```powershell
# Check if it's imported anywhere
grep -r "import filename" src/
grep -r "from filename" src/

# If no results, probably safe to delete
# But test anyway!
```

**Issue**: Too many files to review
**Solution**:
- Focus on obvious categories first
- Use Stage 4 automated categorization
- Delete obvious test/old files first
- Move production code last

---

## 📚 Reference Documents

1. **PROJECT_COMPLETION_PLAN.md** - Complete detailed plan
2. **CLEANUP_PROGRESS.md** - Progress tracker (use this!)
3. **analyze_remaining_files.py** - Analysis tool
4. **execute_stage1.ps1** - Delete old files
5. **execute_stage2.ps1** - Move scripts
6. **execute_stage3.ps1** - Move production code
7. **This file** - Quick reference

---

## ✨ Ready to Start!

```powershell
# Start with a preview
.\execute_stage1.ps1 -DryRun

# When ready
.\execute_stage1.ps1

# And you're off! 🚀
```

**Estimated Completion**: 4 days, 2-3 hours per day  
**Difficulty**: Easy → Moderate  
**Risk**: Managed with backups and testing  

**Let's finish this project!** 💪
