# Codebase Review: Deprecated Content & Potential Issues

**Date:** December 11, 2025  
**Reviewer:** Cascade AI  
**Scope:** Full codebase scan for deprecated content, stubs, and configuration issues

---

## Executive Summary

Reviewed the entire CaseStrainer codebase for deprecated content, outdated references, and configuration issues. Found **3 categories** of issues requiring attention.

---

## ✅ Issues Fixed This Session

### 1. **Broken DockerHealthCheck Scheduled Task**
- **Status:** ✅ FIXED
- **Files Modified:**
  - `cslaunch.ps1` - Added cleanup function
  - `integrate_docker_health.ps1` - Deprecated with warning
- **Impact:** Prevented restart loops caused by failing health check task

---

## ⚠️ Issues Requiring Attention

### Category 1: Test Function in Public API

**Issue:** `test_comprehensive_web_search()` exported in production API

**Location:**
- `src/websearch/__init__.py` (line 20)
- `src/websearch/utils.py` (lines 38-72)

**Problem:**
```python
# This test function is exposed in the public API
from .utils import test_comprehensive_web_search

__all__ = [
    # ... other exports ...
    'test_comprehensive_web_search'  # ← Shouldn't be exported
]
```

**Recommendation:**
```python
# Remove from __all__ export list
__all__ = [
    'EnhancedCitationNormalizer',
    'SearchEngineMetadata',
    'CacheManager',
    # ... keep other exports ...
    # REMOVE: 'test_comprehensive_web_search'
]

# Keep function in utils.py for internal testing only
```

**Impact:** Low - No security risk, but clutters public API  
**Priority:** Low - Can be fixed when refactoring websearch module

---

### Category 2: Legacy config.json References

**Issue:** Several files still reference `config.json` instead of environment variables

**Affected Files:**

1. **`src/scotus_pdf_citation_extractor.py`** (lines 29-32)
   ```python
   with open("config.json", "r") as f:
       config = json.load(f)
   ```
   - **Status:** May be legacy code, not used in main pipeline
   - **Fix:** Use `src/config.py` `get_config_value()` instead

2. **`src/citation_correction.py`** (lines 47-49)
   ```python
   with open("config.json", "r") as f:
       config = json.load(f)
   ```
   - **Status:** May be legacy code
   - **Fix:** Use environment variables

3. **`src/brief_citation_analyzer.py`** (lines 122-124)
   ```python
   with open("config.json", "r") as f:
       config = json.load(f)
   ```
   - **Status:** May be legacy code
   - **Fix:** Use environment variables

**Current Standard:**
```python
# Correct way (already used in main codebase)
from src.config import get_config_value

api_key = get_config_value("COURTLISTENER_API_KEY", "")
```

**Files Using Correct Pattern:**
- ✅ `src/config.py` - Central configuration loader
- ✅ `src/unified_verification_master.py` - Uses config.py
- ✅ `docker-compose.prod.yml` - Uses environment variables

**Recommendation:**
- **Option 1:** Remove unused legacy files if not in main pipeline
- **Option 2:** Update to use `src/config.py` for consistency
- **Priority:** Low - Only if these files are actively used

---

### Category 3: Unused Legacy Files

**Issue:** Several citation-related files use `config.json` but are NOT imported anywhere

**Verified Status:**

1. **`src/scotus_pdf_citation_extractor.py`**
   - Uses `config.json`
   - ❌ NOT imported by any active code
   - **Recommendation:** Move to archive

2. **`src/citation_correction.py`**
   - Uses `config.json`
   - ❌ NOT imported by any active code
   - **Recommendation:** Move to archive

3. **`src/brief_citation_analyzer.py`**
   - Uses `config.json`
   - ❌ NOT imported by any active code
   - **Recommendation:** Move to archive

**Impact:** None - These files are orphaned and not used

**Priority:** Low - No runtime impact, just code clutter

---

## ✅ Verified Clean

### No Issues Found In:

1. **Main Application Files**
   - ✅ `src/app_final_vue.py` - Clean, uses persistent logging
   - ✅ `src/rq_worker.py` - Clean, uses persistent logging
   - ✅ `src/config.py` - Proper config loading from multiple sources

2. **Docker Configuration**
   - ✅ `docker-compose.prod.yml` - Clean, uses environment variables
   - ✅ `Dockerfile` - No deprecated references
   - ✅ Docker volume mounts properly configured

3. **Scripts**
   - ✅ `scripts/test_docker.ps1` - Simple Docker testing script (clean)
   - ✅ `cslaunch.ps1` - Updated with cleanup function
   - ⚠️ `integrate_docker_health.ps1` - Deprecated (fixed this session)

4. **No Archived File References**
   - ✅ No active code importing from `archive_2025_01_20/`
   - ✅ No references to `old_scripts/`
   - ✅ No references to `backup_dirs/`

---

## Configuration Standards

### Current Best Practices ✅

**Environment Variable Loading (in order):**
1. `.env` (development)
2. `config.env` (legacy support)
3. `.env.production` (production)
4. `config.json` (fallback, legacy)

**Implemented in:** `src/config.py`
```python
load_dotenv()  # .env
config_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.env')
load_dotenv(config_env_path)
env_production_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.production')
load_dotenv(env_production_path)
```

**Docker Production:** Uses `COURTLISTENER_API_KEY` from environment (line 39 in docker-compose.prod.yml)

---

## Recommendations

### Immediate Actions (High Priority)

✅ **DONE:** Fixed broken DockerHealthCheck task

### Short-term Actions (Medium Priority)

1. **Verify cache_manager.py dependencies**
   ```powershell
   # Check if cache_config.json exists
   Test-Path "cache_config.json"
   
   # Search for usage
   grep -r "cache_manager" src/
   ```

2. **Review legacy citation files**
   - Determine if these are actively used:
     - `scotus_pdf_citation_extractor.py`
     - `citation_correction.py`
     - `brief_citation_analyzer.py`
   - If unused → move to archive
   - If used → update to use `src/config.py`

### Long-term Actions (Low Priority)

1. **Clean up websearch module**
   - Remove `test_comprehensive_web_search` from public API
   - Keep internal for testing only

2. **Deprecate config.json entirely**
   - Migrate all remaining references to environment variables
   - Update documentation

---

## Testing Recommendations

### Verify No Regressions

```powershell
# 1. Test Docker startup
.\cslaunch.ps1

# 2. Check for broken task (should be gone)
schtasks /query /TN "DockerHealthCheck"  # Should error (not found)

# 3. Verify containers healthy
docker ps --filter "name=casestrainer"

# 4. Check persistent logging works
Get-Content logs\casestrainer-backend_events.log -Tail 10
```

### Check Configuration Loading

```powershell
# Run quick test
cd src
python -c "from config import COURTLISTENER_API_KEY; print('API Key:', 'SET' if COURTLISTENER_API_KEY else 'MISSING')"
```

---

## Summary

| Category | Status | Priority | Action Required |
|----------|--------|----------|-----------------|
| DockerHealthCheck Task | ✅ Fixed | High | None - Fixed this session |
| Test Function in Public API | ⚠️ Found | Low | Remove from exports |
| config.json References | ⚠️ Found | Low-Med | Verify usage, update/archive |
| cache_config.json | ⚠️ Found | Medium | Verify file exists |

**Overall Status:** Codebase is mostly clean. No critical issues beyond the DockerHealthCheck task (already fixed). Legacy config.json references are low priority since main pipeline uses modern config loading.

---

## Next Steps

1. ✅ **Commit and push** the DockerHealthCheck fixes (DONE)
2. **Monitor** for any issues after deployment
3. **Schedule cleanup** of legacy config.json references during next refactor
4. **Document** configuration standards for future development

---

## Files to Watch

These files use legacy patterns but may not be in active use:
- `src/scotus_pdf_citation_extractor.py`
- `src/citation_correction.py`
- `src/brief_citation_analyzer.py`
- `src/cache_manager.py`

**Recommendation:** Add to deprecation list or update during next maintenance cycle.
