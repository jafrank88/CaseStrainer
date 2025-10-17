# Hamaatsa Date Bug - Status Report

## 🚨 Problem Summary

**Issue:** Citation "388 P.3d 977" consistently gets year **2011** in production, but should get year **2016**.

**Evidence:**
- Document clearly shows: `Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016)`
- Year 2016 appears **AFTER** the citation (correct position)
- Year 2011 appears in **PREVIOUS** citation: `178 L. Ed. 2d 587 (2011)`

---

## ✅ What We Know Works

### Local Test Results:
```
388 P.3d 977: Hamaatsa, Inc. v. Pueblo of San Felipe (2016) ✅
2017-NM-007: Hamaatsa, Inc. v. Pueblo of San Felipe (2016) ✅
```

**Test Command:** `python test_production_pipeline.py`
- Uses `CleanExtractionPipeline` (same as production)
- Both citations get year 2016 correctly
- Would cluster together if clustering ran

---

## ❌ Production Behavior

### Fresh Submission (Incognito Mode):
```
📚 Hamaatsa, Inc. v. Pueblo of San Felipe (2011) ← 388 P.3d 977 ❌
📚 Hamaatsa, Inc. v. Pueblo of San Felipe (2016) ← 2017-NM-007 ✅
```

**Tested:** October 17, 2025 at 03:15 UTC
- Cleared browser cache
- Used incognito window
- Fresh submission confirmed
- **Still shows year 2011**

---

## 🔧 Fixes Applied (All Deployed)

### Fix 1: Master Extractor - Forward-Looking Year Extraction
**File:** `src/unified_case_extraction_master.py`
**Lines:** 932-938, 1034-1039
**Status:** ✅ DEPLOYED

```python
# Extract year from AFTER citation first, fallback to context
year_context_after = text[end_index:end_index + 100]
year = self._extract_year_from_context(year_context_after, debug)
if not year:
    year = self._extract_year_from_context(context, debug)
```

### Fix 2: Use Year from Master Fallback
**File:** `src/clean_extraction_pipeline.py`
**Lines:** 347-361
**Status:** ✅ DEPLOYED

```python
# Also use the year from master extractor
if extracted_year and extracted_year != "N/A":
    citation.extracted_date = extracted_year
    logger.info(f"[CLEAN-PIPELINE-FALLBACK] Using year from master: {extracted_year}")
```

### Fix 3: Improved Date Skip Logic
**File:** `src/clean_extraction_pipeline.py`
**Lines:** 394-400, 403-404, 460-462
**Status:** ✅ DEPLOYED

```python
# Don't overwrite dates from master extractor fallback
if citation.extracted_date and citation.extracted_date != "N/A":
    logger.error(f"🔍 [DEBUG-388] SKIPPING _extract_all_dates - already has: {citation.extracted_date}")
    continue
```

### Fix 4: Debug Logging
**Status:** ✅ DEPLOYED
**Markers:** `🔍 [DEBUG-388]`
**Locations:**
- Strict isolation result
- Master fallback year assignment
- Date extraction skip/run decision
- Final year found

---

## 🔍 Diagnostic Attempts

### Docker Logs Checked:
1. ✅ Backend logs - Shows task completion but no extraction logs
2. ✅ Worker1 logs - Shows old task, not recent submission
3. ✅ Worker2 logs - No DEBUG-388 markers found

### Key Finding:
**No DEBUG-388 logs appear in production**, despite using `logger.error()` which should always show up.

---

## 🤔 Possible Explanations

### Theory 1: String Matching Issue
- Citation text in production might have different encoding/whitespace
- `"388 P.3d 977"` in my debug check doesn't match actual citation text
- **Test:** Log ALL citations to see exact format

### Theory 2: Different Code Path
- Production might use different extraction method
- CleanExtractionPipeline might be bypassed
- **Test:** Add debug logging BEFORE pipeline selection

### Theory 3: Cached Extraction Results
- URL-based caching of extraction results
- Cache predates our fixes
- **Test:** Add cache-busting parameter to URL

### Theory 4: Multiple Workers with Old Code
- Some workers might have old code
- **Test:** Check all 3 worker containers for code version

### Theory 5: Eyecite Providing Wrong Year
- Eyecite might be extracting year 2011 from previous citation
- This bypasses our extraction logic entirely
- **Test:** Debug log shows eyecite year (added but not appearing)

---

## 📋 Next Steps

### Immediate Actions:

1. **Add Aggressive Debugging**
   ```python
   # Log EVERY citation with its year
   logger.error(f"[ALL-CITATIONS] {citation.citation} → Year: {citation.extracted_date}")
   ```

2. **Check Code Deployment**
   ```powershell
   # Verify latest code in ALL workers
   docker exec casestrainer-rqworker1-prod cat /app/src/clean_extraction_pipeline.py | grep "DEBUG-388"
   docker exec casestrainer-rqworker2-prod cat /app/src/clean_extraction_pipeline.py | grep "DEBUG-388"
   docker exec casestrainer-rqworker3-prod cat /app/src/clean_extraction_pipeline.py | grep "DEBUG-388"
   ```

3. **Force Cache Clear**
   ```python
   # In cslaunch.ps1, clear ALL Redis databases
   for db in range(10):
       r = redis.Redis(host='localhost', port=6379, db=db)
       r.flushdb()
   ```

4. **Test with Different URL**
   - Try a completely different PDF URL
   - See if the year extraction works correctly
   - This would confirm if it's URL-specific caching

### Long-term Solution:

**Date Extraction Consolidation** (as per `DATE_EXTRACTION_CONSOLIDATION_NEEDED.md`)
- Create single `extract_year_unified()` function
- Replace all 7+ scattered implementations
- Ensure consistent "look forward first" logic everywhere

---

## 📊 Test Results History

| Date | Test Type | Environment | Result |
|------|-----------|-------------|---------|
| 2025-10-17 00:58 | Local | Development | ✅ 2016 (correct) |
| 2025-10-17 03:15 | Remote | Production (normal) | ❌ 2011 (wrong) |
| 2025-10-17 03:15 | Remote | Production (incognito) | ❌ 2011 (wrong) |

---

## 🎯 Success Criteria

When fixed, we should see:
```
📚 Hamaatsa, Inc. v. Pueblo of San Felipe (2016)
  Citation 1: 388 P.3d 977 ✅
  Citation 2: 2017-NM-007 ✅
```

**Both citations:**
- Get year 2016 (not 2011)
- Cluster together (same name + year)
- Show in single cluster in results

---

## 💡 Why This Matters

This bug affects **ALL citations** where the correct year appears after the citation but a different year appears before it. It's not just Hamaatsa - it's a systematic issue with the year extraction looking in the wrong direction.

**Impact:**
- Citations from same case don't cluster together
- User sees duplicate clusters with different years
- Reduces clustering accuracy significantly

---

## 📝 Files to Review Tomorrow

1. `src/clean_extraction_pipeline.py` - Main extraction pipeline
2. `src/unified_case_extraction_master.py` - Master extractor with forward-looking fix
3. `src/unified_input_processor.py` - Request routing
4. `src/citation_extraction_endpoint.py` - Production endpoint
5. `cslaunch.ps1` - Deployment and cache clearing script

---

## 🔧 Commands for Tomorrow

```powershell
# 1. Verify code deployment
docker exec casestrainer-rqworker1-prod grep -n "DEBUG-388" /app/src/clean_extraction_pipeline.py

# 2. Check all Redis databases
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** INFO keyspace

# 3. Force complete cache clear
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** FLUSHALL

# 4. Restart all containers
./cslaunch

# 5. Test again
# Submit in incognito: https://www.courts.wa.gov/opinions/pdf/1034300.pdf

# 6. Check logs immediately
docker logs casestrainer-rqworker1-prod --tail 500 | grep "DEBUG-388"
```

---

**Status:** 🔴 **ACTIVE BUG** - Local fix verified, production deployment confirmed, but bug persists. Root cause still unknown.
