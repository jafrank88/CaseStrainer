# Frontend Deployment Guide

## Overview

This document explains how to properly deploy Vue.js frontend changes to the CaseStrainer production environment.

---

## The Deployment Process

### ✨ One Command Deployment
```powershell
cd d:\dev\casestrainer
./cslaunch
```

**What cslaunch does automatically:**
1. ✅ Checks if containers are running
2. ✅ **Detects if Vue source files (.vue, .js) changed**
3. ✅ **Automatically runs `npm run build` if needed** (~6-7 seconds)
4. ✅ Compares `dist\index.html` timestamp with container timestamp
5. ✅ Rebuilds frontend Docker container if needed (~5-6 seconds)
6. ✅ Restarts services and verifies health

**No manual build step required!** Just run `./cslaunch` and it handles everything.

---

## Quick Reference

### Any Changes (Frontend, Backend, or Both)
```powershell
./cslaunch
```

**That's it!** cslaunch automatically:

- Detects Vue source file changes
- Builds Vue frontend if needed
- Detects Python source changes  
- Rebuilds Docker containers if needed
- Restarts services

**Total time:** ~12-15 seconds (if both frontend and backend changed)

### Manual Build (Optional)
If you want to manually build Vue first:
```powershell
cd casestrainer-vue-new
npm run build
cd ..
./cslaunch
```

This is useful if you want to check build output before deploying.

---

## What cslaunch Does (Fixed)

### ✅ Frontend Detection (FIXED)
**Before Fix:**
- ❌ Checked `static\vue\index.html` (wrong location)
- ❌ Docker uses `dist\` folder
- ❌ Would miss frontend changes!

**After Fix:**
- ✅ Checks `casestrainer-vue-new\dist\index.html`
- ✅ Matches what Docker actually uses
- ✅ Correctly detects frontend changes

### Frontend Rebuild Process
When cslaunch detects newer dist files:

```
[DETECT] Vue frontend files updated - rebuild needed
[FRONTEND REBUILD] Rebuilding frontend container with latest Vue files...

✓ 142 modules transformed.
✓ built in 5.4s

✅ Frontend rebuilt in 5.4 seconds
[SUCCESS] Frontend rebuild complete - All services ready!
  Vue changes are now active
  Application: http://localhost
```

---

## Docker Build Context

### Dockerfile.prod.simple
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/   # ← Uses dist/ folder
```

### Key Points
- Docker copies from `casestrainer-vue-new/dist/`
- NOT from `static/vue/` (that's for Flask serving)
- Must run `npm run build` BEFORE `./cslaunch`

---

## Common Issues & Solutions

### Issue 1: Changes Not Appearing
**Symptom:** Frontend changes don't show up after `./cslaunch`

**Cause:** Forgot to run `npm run build` first

**Solution:**
```powershell
cd casestrainer-vue-new
npm run build
cd ..
./cslaunch
```

### Issue 2: Old Files in Container
**Symptom:** cslaunch doesn't detect changes

**Cause:** dist/ folder wasn't updated

**Solution:**
```powershell
# Check dist/ timestamp
Get-Item casestrainer-vue-new\dist\index.html | Select LastWriteTime

# If old, rebuild
cd casestrainer-vue-new
npm run build
cd ..
./cslaunch
```

### Issue 3: Force Rebuild
**Symptom:** Need to rebuild even if timestamps are the same

**Solution:**
```powershell
./cslaunch -Build    # Forces full rebuild
# OR
./cslaunch -Force    # Forces restart
```

---

## Verification

### Check if Frontend Updated
```powershell
# Check container's index.html timestamp
docker exec casestrainer-frontend-prod stat /usr/share/nginx/html/index.html

# Compare with dist/ timestamp
Get-Item casestrainer-vue-new\dist\index.html | Select LastWriteTime
```

### Check Browser
1. Open http://localhost
2. **Hard refresh:** `Ctrl+Shift+R` (clears browser cache)
3. Open DevTools → Network tab
4. Check asset timestamps

---

## Alternative: deploy-vue.ps1

For development testing with Flask (not Docker):

```powershell
./deploy-vue.ps1
```

**What it does:**
1. Runs `npm run build`
2. Copies `dist/` → `static/vue/`
3. Copies `dist/assets/` → `static/assets/`

**Use case:** Testing Vue with Flask dev server (not production)

---

## Summary

### ✅ New Workflow (One Command!)
```
Edit Vue files → ./cslaunch
```

### ✅ What cslaunch Does Automatically
- **Detects Vue source changes** (checks .vue and .js files)
- **Runs `npm run build` if needed** (~6-7 seconds)
- **Detects Python source changes** (checks .py files)
- **Rebuilds Docker containers if needed** (~5-6 seconds)
- **Deploys all updates**

### ✅ Time Breakdown (Auto-detected)
- Vue source changed: `npm run build` ~6-7 seconds
- Dist files changed: Docker rebuild ~5-6 seconds  
- Python changed: Docker rebuild ~6-7 minutes
- **Total (frontend only):** ~12-15 seconds

### ✅ No More Manual Steps!
```
# Old way (manual):
Edit Vue files → npm run build → ./cslaunch

# New way (automatic):
Edit Vue files → ./cslaunch  ✨
```

---

## Files Modified Today

1. **cslaunch.ps1** - Added automatic Vue source detection and `npm run build` integration
   - Detects when Vue source files (.vue, .js) are newer than dist files
   - Automatically runs `npm run build` when needed
   - Fixed path checking to use correct dist folder
2. **FRONTEND_DEPLOYMENT.md** - Updated documentation to reflect one-command deployment

---

## Testing the Fix

1. Edit a Vue file:
   ```powershell
   # Edit casestrainer-vue-new\src\components\SimpleProgress.vue
   ```

2. Build:
   ```powershell
   cd casestrainer-vue-new
   npm run build
   cd ..
   ```

3. Deploy:
   ```powershell
   ./cslaunch
   ```

4. Verify:
   - Should see "[DETECT] Vue frontend files updated - rebuild needed"
   - Should rebuild frontend container
   - Changes should appear in browser (hard refresh)

---

## Conclusion

✅ **cslaunch now correctly detects frontend changes**  
✅ **You must run `npm run build` before `./cslaunch`**  
✅ **Total deployment time: ~12-15 seconds**  

The two-step process (build → deploy) is intentional:
- Separates concerns (build vs deploy)
- Allows you to verify build output
- Gives you control over when to deploy
- Follows standard DevOps practices
