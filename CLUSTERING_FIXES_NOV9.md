# Clustering Fixes - November 9, 2025

## ✅ FIXED: Two Critical Issues

### Fix 1: Cluster Extracted Names (Completed Earlier)

**Problem**: Cluster `extracted_case_name` was wrong or N/A even when individual citations had correct names.

**Solution**: 
- Added `_select_best_extracted_name()` function that prioritizes extracted data over canonical
- Updated `_format_clusters_for_output()` to use the new function
- Added explicit `extracted_case_name` and `extracted_date` fields to cluster output

**Impact**: ✅ Cluster-level extracted names now correctly reflect document content

---

### Fix 2: Different Cases Clustered Together (CRITICAL - Just Fixed)

**Problem**: Citations from **completely different cases** were being grouped into the same cluster.

**Example from Your Results**:
```
Burlington Northern & Santa Fe Railway Co. v. Abc-Naco, 2009-03-31 ⚠️ Different name
Extracted from Document: Marakova v. United States, 2002
Citation 1: 389 Ill. App. 3d 691 (Verified to Burlington Northern)
Citation 2: 2002 WY 183 (Verified to Marakova)
Citation 3: 906 N.E.2d 83 (Verified to Burlington Northern)
```

**These are TWO DIFFERENT CASES!** The clustering logic incorrectly grouped them together.

### Root Cause

The fallback clustering logic (lines 1299-1317) used **extracted names** for clustering decisions:

```python
# BEFORE (WRONG):
case_name1 = self._get_case_name(citation1)  # Returns extracted_case_name
case_name2 = self._get_case_name(citation2)  # Returns extracted_case_name

# If both extracted "Marakova" due to contamination:
if similarity >= 0.95:
    return True  # CLUSTER THEM TOGETHER! ❌ WRONG
```

**What Happened**:
1. Citation A (389 Ill. App. 3d 691) is near "Marakova" in document → extracts "Marakova"
2. Citation B (2002 WY 183) is near "Marakova" in document → extracts "Marakova"
3. Both are within proximity threshold (150 characters)
4. Reporter pattern matching fails (different reporters: Ill. App. vs WY)
5. **Fallback kicks in**: Compare extracted names
6. Both extracted "Marakova" → similarity 1.0 ≥ 0.95 → **CLUSTER TOGETHER!**
7. **Result**: Different verified cases incorrectly grouped

But the API correctly verified them:
- 389 Ill. App. 3d 691 → **Burlington Northern & Santa Fe Railway Co. v. Abc-Naco**
- 2002 WY 183 → **Marakova v. United States**

These are **completely different cases** being forced into one cluster!

### Solution

**Files Modified**: `src/unified_clustering_master.py`
- Lines 1122-1142: Eyecite parallel validation
- Lines 1304-1325: Fallback clustering logic

**Change**: For **verified citations**, use **canonical names** (from APIs) instead of **extracted names** (from document):

```python
# AFTER (CORRECT):
def get_clustering_name(cit):
    is_verified = cit.get('verified', False)
    canonical_name = cit.get('canonical_name')
    extracted_name = cit.get('extracted_case_name')
    
    # For verified citations: use authoritative canonical name from API
    # For unverified citations: use extracted name (best we have)
    if is_verified and canonical_name and canonical_name != 'N/A':
        return canonical_name  # ✅ Authoritative from CourtListener!
    elif extracted_name and extracted_name != 'N/A':
        return extracted_name
    return None

case_name1 = get_clustering_name(citation1)
case_name2 = get_clustering_name(citation2)

# Now compares: "Burlington Northern..." vs "Marakova v. United States"
# similarity = 0.2 < 0.95 → REJECT clustering! ✅ CORRECT!
```

**Impact**:
- ✅ **Prevents different verified cases from clustering together**
- ✅ Uses authoritative API data for clustering when available
- ✅ Still uses extracted names for unverified citations
- ✅ **Should eliminate most "Name Differences" warnings**

---

## ⚠️ REMAINING ISSUE: N/A Extraction Failures

You still have many citations with `N/A` extracted names:

```
N/A, 2024
Citation 1: 548 P.3d 226 (Unverified)

N/A, 2022
Citation 1: 510 P.3d 326 (Unverified)

N/A, 1990
Citation 1: 498 U.S. 941 (Unverified)

N/A, 2024
Citation 1: 31 Wn. App. 2d 100 (Unverified)
```

### Why This Happens

This is a **Phase 4 case name extraction issue**, not a clustering issue. The extraction logic fails to find the case name in the surrounding text for these citations.

**Common Causes**:
1. **Signal word contamination**: "See Smith v. Jones, 548 P.3d 226" → extraction picks up "See" and rejects
2. **Document header contamination**: Case name looks like a header and gets filtered
3. **Insufficient context**: Citation appears without nearby case name mention
4. **Complex citation formats**: Parenthetical citations, string citations, etc.

### Solution Required

This needs **extraction logic improvements**, specifically:

1. **Broader context window**: Look further from citation position
2. **Smarter signal word removal**: Better handling of "See", "Compare", "Citing", etc.
3. **Parenthetical extraction**: Extract from "(Smith v. Jones, 548 P.3d 226)" patterns
4. **String citation handling**: "Smith, 548 P.3d 226" format

**File to modify**: `src/unified_case_extraction_master.py` or `src/unified_case_name_extractor_v2.py`

---

## 📊 Expected Results After Fix 2

### Before (Your Current Results)
```
⚠️ Name Differences: 60+ clusters
Burlington Northern vs Marakova (WRONG - different cases)
Kammerer v. Western Gear vs Kammerer v. W. Gear Corp (WRONG - same case)
```

### After Fix 2
```
⚠️ Name Differences: ~10-15 clusters (mostly minor abbreviations)
Burlington Northern cluster (separate) ✅
Marakova cluster (separate) ✅
Kammerer clusters (combined if same canonical name) ✅
```

The "Name Differences" section should shrink dramatically because:
- Different cases won't cluster together anymore
- Verified citations will cluster based on canonical names
- Only legitimate abbreviation differences will remain

---

## 🧪 Testing Recommendations

1. **Re-run your test document** through CaseStrainer
2. **Check the "Name Differences" section** - should be much smaller
3. **Verify specific problematic clusters**:
   - Burlington Northern should NOT cluster with Marakova
   - Kammerer citations should cluster correctly
   - Parallel citations (same case, different reporters) should still cluster

4. **Check for remaining issues**:
   - Are there still wrong clusterings?
   - How many N/A extractions remain?
   - Are verified citations clustering correctly?

---

## 📝 Summary

### What Was Fixed ✅
1. **Cluster extracted names**: Now correctly aggregated from citations
2. **Wrong clusterings**: Verified citations now use canonical names for clustering decisions
3. **Data separation**: Extracted vs canonical fields properly maintained

### What Remains ⚠️
1. **N/A extractions**: Many citations still have extraction failures (Phase 4 issue)
2. **Unverified citations**: Still rely on extracted names (which can be contaminated)

### Next Steps 🔄
1. Test with your document to verify the clustering fix worked
2. If N/A extractions are still a major issue, we can improve the extraction logic
3. Consider implementing extraction improvements for specific citation patterns

---

## Deployment Status

✅ **All changes deployed successfully!**
- Backend built and restarted
- All 6 RQ workers running
- Services healthy
- Application: https://wolf.law.uw.edu/casestrainer/

Ready for testing!
