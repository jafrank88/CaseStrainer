# CaseStrainer N/A Extraction Investigation Report
**Date:** November 9-10, 2025  
**Session Duration:** 4+ hours  
**Status:** ✅ ROOT CAUSE IDENTIFIED - Wrong File Modified

## ⚡ CRITICAL UPDATE (Nov 10, 2025 - 9:30pm):

### **ROOT CAUSE FOUND:**
We spent 4+ hours modifying `clean_extraction_pipeline.py` which is **DEPRECATED**.

The **ACTIVE** extraction code is in:
- **`src/unified_case_extraction_master.py`** (THE REAL FILE)

### **Why Our Changes Had Zero Effect:**
1. `clean_extraction_pipeline.py` is only used as a fallback
2. Main execution path uses `extract_case_name_and_date_unified_master()`
3. That function is in `unified_case_extraction_master.py` (line 2491)
4. It already has special format extraction (lines 293-315)!

### **Prevention Measures Implemented:**
1. ✅ Added deprecation warning to `clean_extraction_pipeline.py`
2. ✅ Created `ACTIVE_CODE_MAP.md` architecture documentation  
3. ✅ Created `verify_active_code.py` verification script
4. ✅ Updated this investigation report

### **Next Steps:**
- Review `unified_case_extraction_master.py` lines 293-315 for improvements
- Check why existing special format extraction isn't working
- Verify master extraction logs appear with proper logging level

---

## Original Investigation (Before Root Cause Discovery):

---

## Executive Summary

Multiple comprehensive fixes were implemented to address "N/A" case name extractions and clustering issues in CaseStrainer. Despite:
- 5+ container rebuilds with `--no-cache`
- Multiple Redis cache flushes
- Code verification in deployed containers
- Comprehensive regex improvements
- Abbreviation normalization for clustering

**ZERO improvement was observed.** The same citations continue to extract as "N/A" and clustering issues persist.

**Critical Finding:** Diagnostic logging added to the extraction pipeline NEVER appeared in logs, indicating our code modifications are not executing at all.

---

## Problem Statement

### Target Citations (Consistently Extracting as "N/A")
1. **548 P.3d 226** - Should extract: "Erickson v. Pharmacia LLC"
2. **831 F.2d 508** - Should extract: "Goad v. Celotex Corp."
3. **2019 WL 2066127** - Should extract: "Nazar v. Harbor Freight Tools USA Inc."

### Clustering Issues
1. **Rice v. Dow Chem. Co.** vs **Rice v. Dow Chemical Co.** - Should cluster together (abbreviation difference)
2. **124 Wn.2d 205** and **875 P.2d 1213** - Should cluster as parallel citations (same case)

---

## Attempted Fixes (All Failed to Execute)

### Fix 1: Special Format Extraction (clean_extraction_pipeline.py)
**Location:** Lines 47-127  
**Changes:**
- Made regex patterns more flexible (`\w` instead of `[a-zA-Z]`, `(?:,|\s*$)` instead of `$`)
- Added fallback extraction if text contains "v." or "in re"
- Added secondary extraction to isolate case name from surrounding text

**Expected Logs:** `[SPECIAL-FORMATS]` - **NEVER APPEARED**

```python
# Three patterns with fallback logic:
1. String citation with case name
2. WESTLAW with docket number  
3. Signal word introducers (See, Citing, etc.)
```

### Fix 2: Abbreviation Normalization (unified_clustering_master.py)
**Location:** Lines 874-928  
**Changes:**
- Added 20+ legal abbreviation expansions:
  - `co.` → `company`
  - `chem.` → `chemical`
  - `corp.` → `corporation`
  - etc.
- Applied before clustering comparison

**Result:** Rice v. Dow Chem. Co. STILL doesn't match Rice v. Dow Chemical Co.

### Fix 3: Unified Name Similarity (unified_clustering_master.py)
**Location:** Lines 3563-3570  
**Changes:**
- Made `_normalize_case_name()` call `_normalize_case_name_for_clustering()`
- Ensures all similarity calculations use comprehensive normalization

**Result:** No change in clustering behavior

### Fix 4: Diagnostic Logging (clean_extraction_pipeline.py)
**Location:** Lines 943-949  
**Changes:**
- Added `[CRITICAL-BUG]` log for citations with `start_index=None`
- Would show if special format extraction is blocked by missing index

**Expected Logs:** `[CRITICAL-BUG]` - **NEVER APPEARED**

---

## Root Cause Hypotheses (Ranked by Likelihood)

### Hypothesis 1: Different Extraction Pipeline is Active ⭐⭐⭐⭐⭐
**Evidence:**
- `clean_extraction_pipeline.py` modifications NEVER execute
- Zero diagnostic logs despite processing 140 citations
- Code verified to be deployed in containers

**Possible Causes:**
- `extract_citations_clean()` wrapped in try/except and failing silently
- Fallback to different extraction method
- Import error causing old code path to run
- Module caching using old bytecode

**Investigation Steps:**
1. Check for try/except wrapping `extract_citations_clean()` call
2. Add logging BEFORE the import to see if it succeeds
3. Check which extraction function is actually called in `unified_citation_processor_v2.py`
4. Verify Python module cache is cleared (not just `__pycache__`)

**File to Check:** `src/unified_citation_processor_v2.py` line 4005-4009

### Hypothesis 2: Results Cached at Database/Filesystem Level ⭐⭐⭐⭐
**Evidence:**
- Redis flushed multiple times with no effect
- Same results appear instantly (suggesting pre-computed)
- Results are identical across multiple rebuilds

**Possible Caching Layers:**
- SQLite database storing processed results
- File-based cache in `/app/data/` or similar
- Pickled objects on filesystem
- Nginx response caching

**Investigation Steps:**
1. Find all SQLite databases: `docker exec <worker> find /app -name "*.db"`
2. Check for cache directories: `docker exec <worker> find /app -type d -name "cache"`
3. Inspect `/app/data/` for cached results
4. Check Nginx configuration for proxy caching

### Hypothesis 3: citation.start_index is Always None ⭐⭐⭐
**Evidence:**
- Special format extraction only runs if `start_index is not None`
- Diagnostic added to detect this but never logged (see Hypothesis 1)

**Possible Causes:**
- Eyecite not providing start_index
- Citations created without position data
- Different citation object structure

**Investigation Steps:**
1. Log citation object structure at extraction entry point
2. Check if eyecite is configured to track positions
3. Verify CitationResult model has start_index field

### Hypothesis 4: Code Execution but Logging Suppressed ⭐⭐
**Evidence:**
- Some ERROR-level logs appear (clustering, verification)
- But NONE of our extraction logs appear

**Possible Causes:**
- Logging level set too high for extraction module
- Different logging configuration for extraction vs clustering
- Logs being filtered/redirected

**Investigation Steps:**
1. Check logging level in `clean_extraction_pipeline.py`
2. Try `logger.critical()` instead of `logger.error()`
3. Add simple print statements (bypasses logging system)
4. Check if extraction logs go to different file/handler

### Hypothesis 5: Import Caching Despite Rebuilds ⭐
**Evidence:**
- Python can cache imports in unexpected ways
- Bytecode may persist across rebuilds

**Possible Causes:**
- Docker volume mounting old bytecode
- Python's import cache not cleared
- Gunicorn/Waitress workers not restarting

**Investigation Steps:**
1. Check for Docker volumes: `docker volume ls`
2. Verify workers actually restarted: `docker logs <worker> | grep "Worker started"`
3. Force worker restart: `docker exec <worker> pkill -9 python`
4. Remove all .pyc files: `find /app -name "*.pyc" -delete`

---

## Diagnostic Commands for Next Session

### 1. Identify Active Extraction Pipeline
```bash
# Add logging to unified_citation_processor_v2.py BEFORE import
docker exec casestrainer-rqworker1-prod grep -A20 "from src.clean_extraction_pipeline import" /app/src/unified_citation_processor_v2.py

# Check if extract_citations_clean is wrapped in try/except
docker exec casestrainer-rqworker1-prod grep -B5 -A10 "extract_citations_clean" /app/src/unified_citation_processor_v2.py
```

### 2. Find All Caching Layers
```bash
# Find SQLite databases
docker exec casestrainer-rqworker1-prod find /app -name "*.db" -ls

# Find cache directories
docker exec casestrainer-rqworker1-prod find /app -type d -name "*cache*"

# Check data directory
docker exec casestrainer-rqworker1-prod ls -laR /app/data/

# Check for pickled objects
docker exec casestrainer-rqworker1-prod find /app -name "*.pkl" -o -name "*.pickle"
```

### 3. Verify Code Deployment
```bash
# Check actual deployed code
docker exec casestrainer-rqworker1-prod grep -n "CRITICAL-BUG" /app/src/clean_extraction_pipeline.py

# Verify container image build time
docker inspect casestrainer-rqworker1-prod | grep Created

# Check Python module cache
docker exec casestrainer-rqworker1-prod find /app -name "*.pyc" | wc -l
```

### 4. Test Extraction Directly (Bypass Pipeline)
```python
# Run in worker container
docker exec -it casestrainer-rqworker1-prod python

from src.clean_extraction_pipeline import extract_citations_clean
text = "See United States v. Smith, 831 F.2d 508 (1987)."
result = extract_citations_clean(text)
print([c.extracted_case_name for c in result])
```

### 5. Monitor Real-Time Logs During Processing
```bash
# Watch all three workers simultaneously
docker logs casestrainer-rqworker1-prod -f --since 1s &
docker logs casestrainer-rqworker2-prod -f --since 1s &
docker logs casestrainer-rqworker3-prod -f --since 1s &

# Then upload document and watch for logs
```

---

## Code Locations Reference

### Modified Files
1. **src/clean_extraction_pipeline.py**
   - Lines 47-127: Special format extraction patterns
   - Lines 943-949: Diagnostic logging for start_index

2. **src/unified_clustering_master.py**
   - Lines 874-928: Abbreviation normalization map
   - Lines 3563-3570: Unified name similarity

### Critical Integration Points to Investigate
1. **src/unified_citation_processor_v2.py**
   - Line 4005: Import of `extract_citations_clean`
   - Line 4006: Call to extraction function
   - Lines 4008-4009: Error handling (potential silent failure)

2. **src/unified_processing_pipeline.py**
   - Line 114: Processor creation
   - Line 137: Citation extraction call
   - Line 177: `process_text()` method

3. **src/rq_worker.py**
   - Line 349: Import of processing pipeline
   - Line 374: Actual processing invocation

---

## Evidence of Code NOT Executing

### Logs That SHOULD Appear But DON'T
```
[SPECIAL-FORMATS] 🔥 Trying special format extraction for '831 F.2d 508'
[CRITICAL-BUG] Citation '548 P.3d 226' has start_index=None
[SPECIAL-FORMATS] ✅ STRING CITATION: 'Erickson v. Pharmacia LLC'
```

### Logs That DO Appear (Proving Logging Works)
```
ERROR:src.unified_clustering_master:[PROXIMITY-DEBUG] Starting proximity grouping
ERROR:src.unified_clustering_master:[STANDARDIZE-CLUSTER] Group has 3 extracted years
ERROR:src.unified_verification_master:🔗 [API-CALL] POST https://www.courtlistener.com
```

**Conclusion:** Logging system works fine. Our extraction code simply never runs.

---

## Next Steps for Investigation

### Phase 1: Confirm Execution Path (30 minutes)
1. Add `logger.critical("EXTRACTION ENTRY POINT")` at top of `extract_citations_clean()`
2. Add print statement to bypass logging: `print("🔥🔥🔥 EXTRACTION STARTED")`
3. Upload document and check if EITHER log/print appears
4. If NO → Code not executing (Hypothesis 1 confirmed)
5. If YES → Logging suppression (Hypothesis 4)

### Phase 2: Find Active Code Path (1 hour)
1. Search entire codebase for "extract.*citation" functions
2. Add logging to ALL extraction entry points
3. Find which one actually executes
4. Trace imports to understand why wrong path is active

### Phase 3: Clear ALL Caches (30 minutes)
1. Stop all containers
2. Remove volumes: `docker-compose down -v`
3. Delete all .pyc files in source
4. Rebuild with `--no-cache`
5. Verify build timestamp
6. Re-test

### Phase 4: Direct Testing (30 minutes)
1. Shell into worker container
2. Import extraction function directly
3. Test with problematic citations
4. If works → Pipeline issue
5. If fails → Extraction logic issue

---

## Success Criteria for Resolution

### Minimum Requirements
1. **Diagnostic logs appear** - Proves code executes
2. **Special format extraction runs** - See `[SPECIAL-FORMATS]` logs
3. **At least ONE citation improves** - "831 F.2d 508" extracts case name

### Full Resolution
1. All 3 target citations extract correctly (not "N/A")
2. Rice abbreviation clustering works
3. Parallel citations cluster together
4. Name mismatches reduced from 40+ to <10

---

## Files Modified This Session

```
src/clean_extraction_pipeline.py (Lines 61-75, 87-99, 113-125, 943-949)
src/unified_clustering_master.py (Lines 874-928, 3563-3570)
```

**Git Status:** All changes committed but INEFFECTIVE (code not executing)

---

## Lessons Learned

1. **Verify execution FIRST** before implementing fixes
2. **Add diagnostic logging** before changing logic
3. **Test directly in container** before full pipeline test
4. **Suspect caching** when changes have zero effect
5. **Check error handling** - Silent failures hide problems

---

## Recommended Approach for Next Session

**DO NOT:**
- Implement more extraction logic improvements
- Modify clustering algorithms
- Add more regex patterns
- Clear caches again (proven ineffective)

**DO:**
- Find which code is ACTUALLY executing
- Identify ALL caching layers
- Test extraction in isolation
- Trace complete execution path
- Use print statements (bypass logging)

---

## Contact Information for Handoff

**Modified Files:** See "Files Modified This Session" section  
**Test Document:** `1031351.pdf` (895,932 bytes)  
**Test Citations:** "548 P.3d 226", "831 F.2d 508", "2019 WL 2066127"  
**Expected Results:** Case names, not "N/A"  
**Actual Results:** "N/A" (unchanged across all attempts)

**Session Logs:** Docker logs from Nov 9-10, 2025 (container IDs in notes)

---

**End of Investigation Report**
