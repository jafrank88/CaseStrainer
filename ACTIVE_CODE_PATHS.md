# CaseStrainer Active Code Paths

**Last Updated:** October 21, 2025  
**Purpose:** Prevent wasted time editing deprecated/unused files

---

## 🚨 CRITICAL: Check This Document Before Editing

This document defines which files are ACTIVELY USED vs DEPRECATED.  
**Always check this before making code changes!**

---

## 📁 API Endpoints

### ✅ ACTIVE
- **File:** `src/vue_api_endpoints_updated.py`
- **Purpose:** All API endpoint routing and response handling
- **Key Functions:**
  - `_format_response()` - Line 568+: Builds API responses
  - `analyze_text()` - Main analysis endpoint
  - CitationResult serialization - Line 582-592

### ❌ DELETED
- **File:** `src/vue_api_endpoints.py` 
- **Status:** DELETED on 2025-10-21
- **Reason:** Not imported anywhere, no blueprint defined, confirmed unused
- **Verification:** `src/api/blueprints.py` line 23 imports vue_api_endpoints_updated, not this file
- **History:** Phase 3 verification bug fix was applied here by mistake (hours wasted), then file was deleted to prevent future confusion

---

## 📁 Case Name Extraction

### ✅ PRIMARY PATH
- **File:** `src/unified_case_extraction_master.py`
- **Purpose:** Main case name extraction logic
- **Key Functions:**
  - `_extract_case_name_with_strategies()` - Multi-strategy extraction
  - `_clean_case_name()` - Signal word removal and cleaning
  - Vacatur detection with semicolon boundary checks (lines 592-598, 1150-1156)

### ✅ SECONDARY PATH
- **File:** `src/utils/strict_context_isolator.py`
- **Purpose:** Context isolation and fallback extraction
- **Status:** Still used in some code paths
- **Key Functions:**
  - Signal word patterns (line 200)
  - Corporate suffix capture (line 244)
  - Final cleanup (lines 348-349)

### ⚠️ WHEN TO EDIT BOTH
- Signal word contamination fixes → Edit BOTH files
- Corporate name extraction → Edit BOTH files
- Vacatur detection → Edit ONLY unified_case_extraction_master.py

---

## 📁 Clustering

### ✅ ACTIVE
- **File:** `src/unified_clustering_master.py`
- **Purpose:** All citation clustering logic
- **Key Functions:**
  - `_standardize_extracted_names_in_group()` - Name selection (line 1434+)
  - Signal word removal before name selection (lines 1434-1449)
  - Vacatur detection logic
  - Cluster name propagation

### ❌ NO DEPRECATED FILES
- Single source of truth for clustering ✅

---

## 📁 Citation Processing Pipeline

### ✅ ACTIVE
- **File:** `src/unified_citation_processor_v2.py`
- **Purpose:** Main citation processing pipeline
- **Status:** Primary processor for sync operations

### ⚠️ VERIFY BEFORE EDITING
- **File:** `src/progress_manager.py`
- **Purpose:** Async processing
- **Note:** Different code path for async vs sync

---

## 📁 Models and Serialization

### ✅ ACTIVE
- **File:** `src/models.py`
- **Purpose:** CitationResult class definition
- **Key Functions:**
  - `to_dict()` - Line 56+: Proper serialization including verified/canonical fields
  - `__post_init__()` - Initialization logic

---

## 🔍 How to Verify Active Path

When unsure which file is active:

1. **Check logs:**
```bash
docker logs casestrainer-backend-prod --tail 200 | grep "File.*line"
```
Look for file names in stack traces

2. **Search for imports:**
```bash
grep -r "from.*vue_api_endpoints" src/
grep -r "import.*vue_api_endpoints" src/
```

3. **Check app.py or main:**
```bash
grep -r "vue_api" src/app*.py
```

4. **Test with error:**
Add `raise Exception("Testing which file is active")` at the top of a function and trigger it

---

## 📝 Deprecation Process

When deprecating a file:

1. Add prominent warning to file header (see vue_api_endpoints.py for example)
2. Update this document
3. Create/update memory in AI system
4. Consider deleting the file if completely unused
5. If kept for reference, move to `deprecated/` folder

---

## ✅ Recent Fixes and Verified Paths

### Phase 1: Semicolon Boundary Fix (2025-10-21)
- **Files:** `unified_case_extraction_master.py`
- **Lines:** 592-598, 1150-1156
- **Status:** ✅ Verified working

### Phase 2: Signal Word Contamination (2025-10-21)
- **Files:** 
  - `strict_context_isolator.py` (lines 200, 244, 348-349)
  - `unified_clustering_master.py` (lines 1434-1449)
- **Status:** ✅ Verified working

### Phase 3: Verification Data Loss (2025-10-21)
- **File:** `vue_api_endpoints_updated.py` (lines 582-592)
- **Wrong File Used:** `vue_api_endpoints.py` (not active!)
- **Status:** ⏱️ Fix applied, pending verification

---

## 🚀 Quick Reference

**Before editing any file, ask:**
1. Is this file in the "ACTIVE" section above?
2. Does the file have a deprecation warning?
3. Can I verify it's imported somewhere?
4. Do logs show this file executing?

**If unsure:** Check logs, check imports, or test with a deliberate error.

---

## 📞 Questions?

If you're uncertain which file to edit:
1. Check this document first
2. Check the file header for deprecation warnings
3. Grep for imports
4. Check recent git commits to see what's being edited
5. Look at logs to see what's executing

---

**Remember:** Time spent verifying the correct file = Time saved avoiding wrong fixes!
