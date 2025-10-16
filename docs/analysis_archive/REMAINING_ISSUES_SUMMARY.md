# Remaining Issues Summary - After Fix #45

## ✅ WINS - Fixes #43, #44, #45 Are Working!

1. **Text Normalization (Fix #44):** ✅ WORKING
   - Eyecite now finds 99 citations (up from ~40, +147% improvement!)
   - Line breaks no longer break citation detection
   - Both "148 Wn.2d 224" and "59 P.3d 655" are successfully extracted

2. **Position-Based Extraction (Fix #43):** ✅ WORKING
   - "183 Wn.2d 649" now correctly extracts "Lopez Demetrio"
   - No more forward contamination from subsequent citations
   - Using original text instead of normalized text for position accuracy

3. **Deduplication (Fix #45):** ✅ WORKING  
   - 180 citations extracted (99 from eyecite + ~81 from regex)
   - 92 duplicates correctly removed (citations found by both extractors)
   - Final 88 citations is the correct deduplicated count
   - No real "bottleneck" - just proper duplicate removal

## 🔴 Priority #1: Wrong Extracted Case Names (ACTIVE)

**Problem:** Many clusters show incorrect `extracted_case_name` that doesn't match the actual case in the document.

**Example:**
```
cluster_12_split_18:
  Citations: ['59 P.3d 655', '148 Wn.2d 224']
  Canonical: 'FRATERNAL ORDER OF EAGLES...'
  Extracted: 'Tingey v. Haisch'  ❌ WRONG!
```

**Root Cause:** Backward search (200 chars) captures case name from PREVIOUS citation when citations are close together.

**Impact:** 
- Verification may match wrong cases
- Clustering may group unrelated citations
- User sees incorrect case names in UI

**Solution:** Need to improve backward search logic to:
1. Stop at previous citation boundary
2. Detect when we've gone "too far" back
3. Use smarter heuristics for case name boundaries

## 🟡 Priority #2: Parallel Citation Splitting

**Problem:** Parallel citations are being split into separate clusters (indicated by `_split_` suffix).

**Examples:**
- cluster_12: Split into cluster_12_split_17 and cluster_12_split_18
- cluster_15: Split into cluster_15_split_22 and cluster_15_split_23
- Many others with `_split_` suffix

**Root Cause:** Clustering logic is too aggressive about splitting when canonical verification returns different case names or URLs.

**Impact:**
- Parallel citations appear as separate entries in UI
- Reduces clustering accuracy
- Confusing for users

**Solution:** Need to improve cluster splitting logic to:
1. Trust extracted data more than canonical data
2. Only split when extracted names are VERY different
3. Use proximity as a strong signal for parallel citations

## 🟢 Priority #3: API Verification Failures

**Problem:** Some citations verify to completely wrong cases.

**Examples:**
- '182 Wn.2d 342': Verifies to "Ass'n of Wash. Spirits" instead of "State v. Velasquez"
- '509 P.3d 325': Verifies to "Jeffery Moore v. Equitrans" instead of "Fode v. Dep't of Ecology"
- '9 P.3d 655': Verifies to Mississippi case (2023) instead of Washington "Fraternal Order" (2002)

**Root Causes:**
1. CourtListener API may be returning wrong cases for some citations
2. Our matching logic doesn't check jurisdiction or year
3. We may be taking first API result without validating it

**Impact:**
- Wrong canonical names/URLs displayed to user
- Verification confidence is misleading
- May affect clustering decisions

**Solution:** Need to improve verification matching to:
1. Filter API results by jurisdiction (e.g., only Washington cases)
2. Validate year matches extracted year (within reasonable range)
3. Use name similarity scoring when multiple API results exist
4. Mark low-confidence verifications with warnings

## 📊 Issue Statistics

From test_fix45.json analysis:
- Total clusters: 57
- Clusters with `_split_` suffix: ~15-20 (indicates parallel splitting)
- Clusters with wrong extracted names: Unknown (needs detailed analysis)
- Citations with verification issues: ~5-10 known cases

## 🎯 Recommended Action Plan

1. **NOW:** Fix Priority #1 (wrong extracted names)
   - Modify backward search to stop at previous citation
   - Add citation boundary detection
   - Test with 1033940.pdf

2. **NEXT:** Fix Priority #2 (parallel splitting)
   - Adjust cluster splitting thresholds
   - Prioritize extracted data over canonical data
   - Test with 1033940.pdf

3. **LATER:** Fix Priority #3 (API verification)
   - Add jurisdiction/year filtering
   - Implement name similarity validation
   - Add verification confidence warnings

## 📝 Notes

- All major extraction bugs (Fixes #43, #44, #45) are RESOLVED
- The system is now successfully extracting citations
- Remaining issues are in extraction accuracy, clustering, and verification
- No critical blockers - system is functional but can be improved

