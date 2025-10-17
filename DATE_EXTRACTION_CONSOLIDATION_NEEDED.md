# Date Extraction Consolidation - CRITICAL TODO

## 🚨 Problem Summary

We have **7+ different date extraction methods** scattered across the codebase with conflicting logic. This causes citations from the same case to get different years, preventing them from clustering together.

### Example Issue:
```
📚 Hamaatsa, Inc. v. Pueblo of San Felipe (2011) ← WRONG YEAR
  Citation: 388 P.3d 977

📚 Hamaatsa, Inc. v. Pueblo of San Felipe (2016) ← CORRECT YEAR
  Citation: 2017-NM-007
```

**These should be ONE cluster with year 2016!**

---

## 📊 Current Date Extraction Methods

### Primary Methods:
1. **`_extract_year_from_context`** in `unified_case_extraction_master.py`
   - ✅ **FIXED** - Looks forward first (after citation)
   - Used by: Master extractor fallback

2. **`_extract_all_dates`** in `clean_extraction_pipeline.py`
   - ✅ **ALREADY CORRECT** - Looks forward first
   - Used by: Clean pipeline after case name extraction
   - ⚠️ BUT may not run if fallback sets date

3. **`_extract_year_from_context`** in `unified_extraction_architecture.py`
   - ❌ **NOT FIXED** - May look backward
   - Used by: Unified extraction architecture

4. **`_extract_date_from_context`** in `unified_extraction_service.py`
   - ❌ **NOT FIXED** - Need to check logic
   - Used by: Extraction service

5. **`_extract_year_from_text`** in `unified_extraction_architecture.py`
   - ❌ **NOT FIXED** - Need to check logic
   - Used by: Pattern-based extraction

### Utility Methods:
6. **`extract_year_from_any_date`** in `utils/data_separation.py`
7. **`extract_year_value`** in `utils/canonical_metadata.py`
8. Plus more in verification/websearch modules...

---

## 🔍 Root Cause Analysis

### The Flow:
```
1. Extract case names → Some use fallback (gets correct year)
2. _extract_all_dates() runs → Overwrites with wrong year?
3. Clustering groups by (name, year) → Citations with different years don't cluster!
4. Result: Same case appears as multiple clusters
```

### Why "388 P.3d 977" Gets Wrong Year:

**Hypothesis 1:** Strict isolation succeeds, bypassing master fallback
- Strict isolation extracts case name successfully
- Master fallback never runs
- `_extract_all_dates()` runs and finds (2011) from previous citation in context

**Hypothesis 2:** Fallback year not persisting
- Master fallback runs and sets year=2016
- Something resets or doesn't save it properly
- `_extract_all_dates()` runs and overwrites with 2011

**Hypothesis 3:** Different code path used
- Different extraction method is being used
- That method has old backward-looking logic

---

## ✅ Fixes Applied Today (2024-10-16)

### Fix 1: Master Extractor - Look Forward First
**File:** `src/unified_case_extraction_master.py`
**Lines:** 932-938, 1034-1039
**Status:** ✅ DEPLOYED

```python
# USER FIX: Extract year from AFTER citation first, fallback to context
year_context_after = text[end_index:end_index + 100]
year = self._extract_year_from_context(year_context_after, debug)
if not year:
    # Fallback to context before citation
    year = self._extract_year_from_context(context, debug)
```

### Fix 2: Use Year from Master Fallback
**File:** `src/clean_extraction_pipeline.py`
**Lines:** 347-351
**Status:** ✅ DEPLOYED

```python
# USER FIX: Also use the year from master extractor
if extracted_year and extracted_year != "N/A":
    citation.extracted_date = extracted_year
    logger.info(f"[CLEAN-PIPELINE-FALLBACK] Using year from master: {extracted_year}")
```

### Fix 3: Improve Date Skip Logic
**File:** `src/clean_extraction_pipeline.py`
**Lines:** 382-386
**Status:** ✅ DEPLOYED

```python
# USER FIX: Don't overwrite dates from master extractor fallback
if citation.extracted_date and citation.extracted_date != "N/A":
    logger.debug(f"[CLEAN-PIPELINE] Skipping date extraction for {citation.citation} - already has: {citation.extracted_date}")
    continue
```

---

## 🎯 What Still Needs to Be Done

### Phase 1: Identify Actual Code Path (URGENT)
- [ ] Add debug logging to track which extraction method is used for "388 P.3d 977"
- [ ] Test with actual production pipeline to see logs
- [ ] Determine if strict isolation succeeds (bypassing fallback)
- [ ] Determine if `_extract_all_dates()` is overwriting the fallback year

### Phase 2: Fix All Date Extraction Methods
- [ ] Apply "look forward first" fix to `unified_extraction_architecture.py`
- [ ] Apply "look forward first" fix to `unified_extraction_service.py`
- [ ] Audit all other date extraction methods
- [ ] Ensure consistent logic across ALL methods

### Phase 3: Create Unified Date Extraction Function
- [ ] Create `utils/date_extraction.py` with single canonical implementation
- [ ] Replace all scattered implementations with calls to unified function
- [ ] Function signature: `extract_year_from_citation_context(text, start_index, end_index)`
- [ ] Logic: Look forward 100 chars first, then backward 50 chars as fallback

### Phase 4: Testing & Validation
- [ ] Create test suite for date extraction
- [ ] Test with Hamaatsa citations (should both get 2016)
- [ ] Test with other parallel citations
- [ ] Verify clustering works correctly after fix

---

## 📋 Immediate Action Items

### To Fix Hamaatsa Issue:
1. **Add debug logging** to see which path is taken
2. **Check if strict isolation** is succeeding for "388 P.3d 977"
3. **If strict isolation succeeds**, date extraction happens in `_extract_all_dates()`
4. **If fallback is used**, check if date is being saved/used correctly

### To Test:
```python
# Test with actual PDF
python test_hamaatsa_extraction.py

# Expected output:
# 388 P.3d 977 → Year: 2016 ✅
# 2017-NM-007 → Year: 2016 ✅
```

---

## 🔧 Recommended Consolidation Architecture

### Create: `src/utils/unified_date_extraction.py`

```python
def extract_year_unified(
    text: str,
    citation_start: int,
    citation_end: int,
    debug: bool = False
) -> Optional[str]:
    """
    Unified date extraction - SINGLE SOURCE OF TRUTH.
    
    Strategy (in priority order):
    1. Look FORWARD 100 chars for (YYYY) - most reliable
    2. Look FORWARD for comma/period + year
    3. Look BACKWARD 50 chars for (YYYY) - fallback only
    4. Look BACKWARD for comma/period + year
    
    Returns:
        4-digit year string or None
    """
    # Implementation here
```

### Update All Call Sites:
- `unified_case_extraction_master.py` → Use `extract_year_unified()`
- `clean_extraction_pipeline.py` → Use `extract_year_unified()`
- `unified_extraction_architecture.py` → Use `extract_year_unified()`
- `unified_extraction_service.py` → Use `extract_year_unified()`
- All other locations

---

## 📊 Success Metrics

After consolidation, we should see:
- ✅ All parallel citations get the same year
- ✅ Hamaatsa citations cluster together with year 2016
- ✅ No more year discrepancies from previous citations
- ✅ Single source of truth for date extraction logic
- ✅ Easier to debug and maintain

---

## 🚀 Priority: HIGH

This affects clustering accuracy significantly. Citations from the same case are appearing as separate clusters because of year mismatches.

**Estimated Effort:** 4-6 hours
**Impact:** High - fixes clustering for all citations

---

## 📝 Notes

- The "look forward first" logic is correct and should be standard
- Year in parentheses after citation is most reliable: "123 F.3d 456 (2020)"
- Looking backward can pick up years from PREVIOUS citations
- Consolidation will prevent future bugs and make maintenance easier
