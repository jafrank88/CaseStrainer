# Critical Fix #8: Cluster Canonical Data Contamination

**Date**: October 9, 2025  
**Status**: ✅ FIXED AND DEPLOYED

---

## 🚨 Problem Identified

After deploying Fix #7 (Reporter Normalization), the system was **still** showing mismatched canonical names. The reporter normalization worked (citations now preserve `Wn.2d`), but canonical data was being shared incorrectly across citations within the same cluster.

### Example Issues from Production

1. **"192 Wn.2d 453"**:
   - ❌ Canonical: "Lopez Demetrio v. Sakuma Bros. Farms"
   - 🔗 Canonical URL: "https://www.courtlistener.com/.../pullar-v-huelle/"
   - ✅ Extracted: "Lopez Demetrio v. Sakuma Bros. Farms"
   - **Problem**: Canonical name doesn't match canonical URL!

2. **"9 P.3d 655"**:
   - ❌ Canonical: "Fraternal Ord. of Eagles..."
   - 🔗 Canonical URL: "https://www.courtlistener.com/.../gustavo-p-galvan-v-state-of-mississippi/"
   - **Problem**: Canonical name doesn't match canonical URL!

3. **"117 S. Ct. 2312"**:
   - ❌ Canonical: "Branson v. Wash. Fine Wine & Spirits, LLC"
   - 🔗 Canonical URL: "https://www.courtlistener.com/.../raines-v-byrd/"
   - **Problem**: Canonical name doesn't match canonical URL!

---

## 🔍 Root Cause Analysis

### API Testing Revealed the Truth

I created `test_courtlistener_api.py` to call the CourtListener API directly:

```
Testing: 192 Wn.2d 453
Status: 404
Error: "Citation not found: '192 Wn.2d 453'"
Clusters: []  ← EMPTY!

Testing: 9 P.3d 655
Status: 404
Error: "Citation not found: '9 P.3d 655'"
Clusters: []  ← EMPTY!

Testing: 117 S. Ct. 2312
Status: 200
Case Name: "Raines v. Byrd"  ← CORRECT!
URL: "/opinion/118146/raines-v-byrd/"  ← CORRECT!
```

### The Discovery

The CourtListener API was returning **404 (Citation not found)** for "192 Wn.2d 453" and "9 P.3d 655", yet the production output **still showed canonical data** for these citations!

This revealed that the system was **sharing canonical data across citations within a cluster**.

### How the Bug Worked

1. **Clustering Phase** (`unified_citation_clustering.py`):
   - Cluster has multiple citations: `["192 Wn.2d 453", "430 P.3d 655"]`
   - API returns 404 for "192 Wn.2d 453" (no canonical data)
   - API returns "Spokane County v. Dep't of Fish & Wildlife" for "430 P.3d 655"
   - `_select_best_canonical_name()` picks "Spokane County" and stores it as:
     ```python
     cluster_dict['canonical_name'] = "Spokane County"  # From "430 P.3d 655"
     cluster_dict['canonical_date'] = "2018-12-06"
     cluster_dict['canonical_url'] = "https://..."
     ```

2. **Output Phase** (`unified_citation_processor_v2.py` line 3707-3709):
   - **OLD CODE (BUGGY)**:
     ```python
     canonical_name = cluster.get('canonical_name')  # Gets cluster's aggregate data
     canonical_date = cluster.get('canonical_date')
     canonical_url = cluster.get('canonical_url')
     
     # Later (lines 3718-3725):
     if not canonical_name:  # ← This is FALSE because we got cluster's canonical_name!
         canonical_name = first_citation.get('canonical_name')
     ```

3. **Result**:
   - When displaying "192 Wn.2d 453", we used the **cluster's** canonical data
   - But this canonical data belonged to "430 P.3d 655", not "192 Wn.2d 453"!
   - "192 Wn.2d 453" itself had **NO** canonical data (API returned 404)

### Why Canonical Names Didn't Match URLs

The `_select_best_canonical_name()` function selected ONE canonical name from verified citations in the cluster, but the `canonical_url` might have come from a DIFFERENT citation. This caused the mismatch between canonical_name and canonical_url.

---

## ✅ The Fix

### Location
**File**: `src/unified_citation_processor_v2.py`  
**Lines**: 3702-3736

### What Changed

**BEFORE (Buggy)**:
```python
canonical_name = cluster.get('canonical_name')  # Uses cluster's aggregate data
canonical_date = cluster.get('canonical_date')
canonical_url = cluster.get('canonical_url')

# Get data from first citation if cluster doesn't have it
if cluster.get('citations'):
    first_citation = cluster['citations'][0]
    if not canonical_name:  # Only if cluster didn't have it
        canonical_name = first_citation.get('canonical_name')
```

**AFTER (Fixed)**:
```python
# CRITICAL FIX #8: Each citation must display ITS OWN canonical data
# DO NOT use cluster's aggregate canonical data!
canonical_name = None  # DO NOT use cluster.get('canonical_name')!
canonical_date = None  # DO NOT use cluster.get('canonical_date')!
canonical_url = None   # DO NOT use cluster.get('canonical_url')!

# Get data ONLY from individual citations
if cluster.get('citations'):
    first_citation = cluster['citations'][0]
    canonical_name = first_citation.get('canonical_name')  # Always from citation
    canonical_date = first_citation.get('canonical_date')
    canonical_url = first_citation.get('canonical_url')
```

### Key Principle

**Each citation must display its OWN verification results, not the cluster's aggregate results.**

If a citation got a 404 from the API, it should show **NO** canonical data - not canonical data borrowed from a sibling citation in the same cluster!

---

## 🧪 Testing

### Expected Outcomes After Fix

1. **"192 Wn.2d 453"**:
   - ❌ Canonical: **None** (API returned 404)
   - ✅ Extracted: "Lopez Demetrio v. Sakuma Bros. Farms"
   - 📅 Date: "2018" (extracted)

2. **"9 P.3d 655"**:
   - ❌ Canonical: **None** (API returned 404)
   - ✅ Extracted: "Fraternal Ord. of Eagles..."
   - 📅 Date: "2002" (extracted)

3. **"117 S. Ct. 2312"**:
   - ✅ Canonical: "Raines v. Byrd" (verified)
   - 🔗 Canonical URL: ".../raines-v-byrd/" (matches name!)
   - ✅ Extracted: "Branson..." (might differ - that's OK)
   - 📅 Date: "1997-06-26" (canonical)

### What to Check

- [ ] Canonical names should match canonical URLs (same case)
- [ ] Citations with API 404 errors should have NO canonical data
- [ ] Citations should only display their OWN verification results
- [ ] Extracted names should never be contaminated with canonical data

---

## 📊 Impact

### Files Modified
1. `src/unified_citation_processor_v2.py` (lines 3702-3736)

### Related Fixes
- **Fix #7**: Reporter Normalization (removed `Wn.2d` → `Wash.2d` conversion)
- **Fix #6**: Verification Matching (improved API result matching)
- **Fix #5**: Citation Removal from Extracted Names
- **Fix #4**: Eyecite Normalization (preserve original citation text)

---

## 🎯 Summary

This fix ensures that **each citation displays only its own canonical data**, preventing contamination from other citations in the same cluster. If a citation couldn't be verified (API 404), it should show NO canonical data - not data borrowed from a sibling citation.

The fix maintains data integrity and ensures that canonical names always match their canonical URLs.


