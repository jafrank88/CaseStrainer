# CaseStrainer Auto-Detection System

## ✅ **Auto-Detection is Already Built-In!**

The cslaunch script **automatically detects code changes** and applies the appropriate rebuild strategy. You don't need to specify flags!

---

## 🎯 How It Works

### When you run `.\cslaunch.ps1` (no flags):

The script automatically:

1. **Scans all Python files** in `src/` directory (line 1419-1440)
2. **Compares MD5 hashes** with stored values
3. **Detects what changed** and chooses the right action:

| Change Detected | Action Taken | What Happens |
|----------------|--------------|--------------|
| **Python files** in `src/` | **Fast Start** | Clears Python cache + Restarts containers |
| **requirements.txt**, **Dockerfile** | **Full Rebuild** | Clears cache + Rebuilds images + Restarts |
| **Vue files** in `casestrainer-vue-new/` | **Frontend Rebuild** | Rebuilds Vue + Updates containers |
| **No changes** | **Quick Start** | Just ensures containers are running |

---

## 📊 Detection Logic

### Fast Start (Python Code Changes)
**Triggers when**: Any `.py` file in `src/` is modified

**Actions**:
```powershell
1. Clear-PythonCache          # Removes .pyc and __pycache__
2. docker compose down         # Stops containers
3. docker compose up -d        # Starts with fresh code
```

**Example**: You edited `unified_case_extraction_master.py`
- ✅ Auto-detected as Python change
- ✅ Cache cleared automatically
- ✅ Containers restarted with new code

---

### Full Rebuild (Dependency Changes)
**Triggers when**: 
- `requirements.txt` modified
- `Dockerfile` modified
- `docker-compose.prod.yml` modified

**Actions**:
```powershell
1. Clear-PythonCache                    # Removes cache
2. docker compose down                   # Stops containers
3. docker compose build --no-cache      # Rebuilds images
4. docker compose up -d                  # Starts fresh
```

---

### Frontend Rebuild (Vue Changes)
**Triggers when**: Files in `casestrainer-vue-new/` modified

**Actions**:
```powershell
1. npm run build                              # Builds Vue app
2. docker compose build frontend-prod         # Rebuilds frontend
3. Copy-Item dist/* static/                   # Updates static files
4. docker compose up -d                       # Restarts
```

---

## 🚀 Usage Examples

### Scenario 1: You Fixed Extraction Code
```powershell
# You edited: src/unified_case_extraction_master.py
.\cslaunch.ps1

# Output:
# ✅ [FILES] src/unified_case_extraction_master.py modified - Fast Start needed
# ✅ Clearing Python cache to ensure fresh code execution...
# ✅ Fast Start completed!
```

### Scenario 2: You Added a New Package
```powershell
# You edited: requirements.txt
.\cslaunch.ps1

# Output:
# ✅ [FILES] requirements.txt modified - Full Rebuild needed
# ✅ Clearing Python cache...
# ✅ Full Rebuild completed!
```

### Scenario 3: No Changes
```powershell
# You didn't edit anything
.\cslaunch.ps1

# Output:
# ✅ [FILES] No file changes detected
# ✅ Quick Start completed!
```

---

## 🔍 How Hash Tracking Works

### First Run:
1. Script calculates MD5 hash of each file
2. Stores hashes in `logs/file_hashes.json`
3. No changes detected (first time)

### Subsequent Runs:
1. Script calculates current MD5 hash
2. Compares with stored hash
3. If different → Change detected!
4. Updates stored hash for next run

### Hash Storage Location:
```
logs/
  └── file_hashes.json    # Stores MD5 hashes of all tracked files
  └── build_state.json    # Stores build state information
```

---

## 🎛️ Manual Override Options

If you want to **force** a specific rebuild type:

```powershell
# Force fast restart (even if no changes detected)
.\cslaunch.ps1 -Fast

# Force full rebuild (even if no changes detected)
.\cslaunch.ps1 -Full

# Force frontend rebuild
.\cslaunch.ps1 -UpdateFrontend

# Just restart backend
.\cslaunch.ps1 -RestartBackend
```

---

## 🐛 Troubleshooting

### Problem: "Changes not detected"

**Solution 1**: Reset hash tracking
```powershell
# Delete hash files to force fresh detection
Remove-Item logs\file_hashes.json
Remove-Item logs\build_state.json
.\cslaunch.ps1
```

**Solution 2**: Force rebuild
```powershell
.\cslaunch.ps1 -Full
```

### Problem: "Code not updating"

**Checklist**:
1. ✅ Did you save the file?
2. ✅ Is the file in `src/` directory?
3. ✅ Did cslaunch show "Fast Start needed"?
4. ✅ Did you see "Clearing Python cache"?

If all yes and still not working:
```powershell
# Nuclear option - full rebuild
.\cslaunch.ps1 -Full
```

---

## 📋 What Gets Tracked

### Backend Files (Auto-detected):
- ✅ All `.py` files in `src/`
- ✅ `requirements.txt`
- ✅ `Dockerfile`
- ✅ `docker-compose.prod.yml`
- ✅ Config files in `config/`

### Frontend Files (Auto-detected):
- ✅ All files in `casestrainer-vue-new/src/`
- ✅ `casestrainer-vue-new/package.json`
- ✅ Vue components, stores, views

### Not Tracked:
- ❌ Test files (unless in `src/`)
- ❌ Documentation files (`.md`)
- ❌ Log files
- ❌ `__pycache__` directories

---

## 🎯 For Your Current Situation

### Your Extraction Fix:

**File Changed**: `src/unified_case_extraction_master.py`

**What Happens When You Run `.\cslaunch.ps1`**:
1. ✅ Script detects Python file changed
2. ✅ Triggers "Fast Start" mode
3. ✅ Clears Python cache (removes stale `.pyc` files)
4. ✅ Restarts Docker containers
5. ✅ New extraction code is loaded

**Expected Output**:
```
Checking for code changes...
  [FILES] src/unified_case_extraction_master.py modified - Fast Start needed
Code changes detected - performing Fast Start...
Clearing Python cache to ensure fresh code execution...
  Clearing Python cache files (.pyc and __pycache__)...
  Cleared 45 cache files
Fast Start completed!
CaseStrainer is ready!
```

---

## 💡 Key Takeaway

**You don't need to remember flags!** Just run:

```powershell
.\cslaunch.ps1
```

The script will:
- ✅ Detect what changed
- ✅ Choose the right rebuild strategy
- ✅ Clear caches automatically
- ✅ Apply your changes

**It's intelligent and automatic!** 🎉

---

## 🔧 Advanced: How to Add New Tracked Files

If you want to track additional files, edit `cslaunch.ps1`:

```powershell
# Around line 1350, add to $coreCodeFiles:
$coreCodeFiles = @(
    "src/__init__.py",
    "src/app_final_vue.py",
    "src/your_new_file.py"  # Add here
)
```

Or for dependencies (triggers full rebuild):

```powershell
# Around line 1342, add to $dependencyFiles:
$dependencyFiles = @(
    "requirements.txt",
    "Dockerfile",
    "your_config.yml"  # Add here
)
```

---

## ✅ Summary

| Question | Answer |
|----------|--------|
| **Do I need flags?** | No! Auto-detection works |
| **Will cache be cleared?** | Yes! Automatically |
| **Will containers restart?** | Yes! Automatically |
| **Do I need to remember which flag?** | No! Script decides |
| **What if I want to force it?** | Use `-Fast` or `-Full` |

**Just run `.\cslaunch.ps1` and let it handle everything!** 🚀
