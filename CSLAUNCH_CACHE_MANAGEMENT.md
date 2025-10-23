# cslaunch Cache Management Features

## 🎯 Problem Solved

Previously, when deploying new code:
- **Small files** (sync) worked with new code ✅
- **Large files** (async via RQ workers) showed cached results ❌
- Required manual cache clearing and worker restarts

## ✅ Solution Implemented

### **Automatic Cache Management on Build**

When you run `./cslaunch` with `-Build` flag, the script now **automatically**:

1. ✅ **Clears Redis cache** - Removes all cached processing results
2. ✅ **Clears file cache** - Removes `/app/src/citation_cache/*`
3. ✅ **Restarts RQ workers** - Forces workers to load new Python code
4. ✅ **Reminds about browser cache** - Displays message to clear browser

---

## 📖 Usage

### **Full Rebuild with Auto-Cache Clear** (Recommended)
```powershell
./cslaunch -Build
```

**What happens:**
1. Rebuilds all Docker containers (5-8 minutes)
2. Restarts services
3. **Automatically clears all caches**
4. **Automatically restarts RQ workers**
5. Ready to test with fresh results!

---

### **Quick Restart with Manual Cache Clear**
```powershell
./cslaunch -ClearCache
```

**What happens:**
1. Restarts containers (10-20 seconds)
2. Clears Redis and file caches
3. Restarts RQ workers
4. **Use this when you change code without rebuilding**

---

### **Normal Restart** (No Cache Clear)
```powershell
./cslaunch
```

**What happens:**
1. Restarts containers (10-20 seconds)
2. **Does NOT clear caches** (faster, but may show old results)
3. Use for infrastructure changes only

---

## 🔧 What Gets Cleared

### **Redis Cache**
- Location: Redis database 0
- Contents: Processed results, job queue, progress tracking
- Command: `redis-cli -a ***REDACTED_REDIS_PASSWORD*** FLUSHDB`

### **File Cache**
- Location: `/app/src/citation_cache/`
- Contents: Cached citation extraction results
- Command: `rm -rf /app/src/citation_cache/*`

### **RQ Workers**
- Services: `rqworker1`, `rqworker2`, `rqworker3`
- Action: Restart to reload Python code from memory
- Command: `docker-compose restart rqworker1 rqworker2 rqworker3`

### **Browser Cache** (Manual)
- **Chrome/Edge**: Ctrl+Shift+Delete → Clear browsing data
- **Firefox**: Ctrl+Shift+Delete → Clear cache
- **Important**: Always clear after deploying new code!

---

## 🎯 When to Use Each Option

| Scenario | Command | Cache Clear | Rebuild |
|----------|---------|-------------|---------|
| **New Python code deployed** | `./cslaunch -Build` | ✅ Auto | ✅ Yes |
| **Changed code, no rebuild** | `./cslaunch -ClearCache` | ✅ Manual | ❌ No |
| **Infrastructure change only** | `./cslaunch` | ❌ No | ❌ No |
| **Quick restart** | `./cslaunch` | ❌ No | ❌ No |

---

## 🐛 Troubleshooting

### **Problem: Large files still show old results**

**Solution:**
```powershell
# 1. Clear all caches
./cslaunch -ClearCache

# 2. Clear browser cache (Ctrl+Shift+Delete)

# 3. Upload file again
```

---

### **Problem: RQ workers not using new code**

**Solution:**
```powershell
# Manually restart workers
docker-compose -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3
```

---

### **Problem: Frontend cached in browser**

**Solution:**
1. Press **Ctrl+Shift+Delete** (or Cmd+Shift+Delete on Mac)
2. Select "Clear browsing data" or "Clear cache"
3. Refresh page (Ctrl+F5 for hard refresh)

---

## 📝 Implementation Details

### **New Functions Added**

#### `Clear-ApplicationCache`
- Clears Redis and file caches
- Shows browser cache reminder
- Called automatically after `-Build`

#### `Restart-RQWorkers`
- Restarts all 3 RQ worker containers
- Forces workers to reload Python code
- Called automatically after cache clear

#### `Clear-StuckJobs`
- Enhanced to actually clean up old jobs
- Runs automatically on startup

---

### **New Flag: `-ClearCache`**

Added to script parameters:
```powershell
param(
    ...
    [switch]$ClearCache,
    ...
)
```

Usage in code:
```powershell
if ($Build) {
    # After build, always clear cache
    $ClearCache = $true
}

if ($ClearCache) {
    Clear-ApplicationCache
    Restart-RQWorkers
}
```

---

## ✅ Benefits

1. **No More Confusion** - Automatic cache management
2. **Faster Testing** - No manual cleanup steps
3. **Consistent Results** - Fresh data every build
4. **Better DX** - Clear visual feedback
5. **Documented Process** - Browser cache reminders

---

## 🎉 Result

**Before:**
```powershell
./cslaunch
# Test small file: ✅ Works
# Test large file: ❌ Shows old cached results
# Manually clear Redis: docker exec ...
# Manually restart workers: docker-compose restart ...
# Manually clear browser cache
# Test again: ✅ Finally works!
```

**After:**
```powershell
./cslaunch -Build
# Everything cleared automatically
# Test small file: ✅ Works
# Test large file: ✅ Works with new code!
```

---

## 📌 Notes

- Lint warnings in PowerShell are cosmetic and don't affect functionality
- Cache clearing adds ~2-3 seconds to startup time
- Browser cache must still be cleared manually (no way to automate)
- Workers restart takes ~2-5 seconds

---

**Created:** Oct 18, 2025  
**Issue:** Redis job storage bug causing cached results  
**Fix:** Automatic cache management in cslaunch
