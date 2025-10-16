# 🚨 CRITICAL CLUSTERING BUGS DISCOVERED

**Date:** October 10, 2025  
**Status:** URGENT - Fix #48/#49 NOT WORKING  
**Impact:** System is grouping unrelated citations and verifying them to wrong cases

---

## Bug #1: Clustering Ignores Extracted Name/Date Mismatches

### Evidence from Logs
```
cluster='Spokeo, Inc. v. Robins', extracted='Raines v. Byrd', canonical='None'
```

**Citation "521 U.S. 811":**
- ✅ Correctly extracted as "Raines v. Byrd" (1997)
- ❌ Placed in cluster "Spokeo, Inc. v. Robins" (2016)
- **WRONG!** Different name AND different year!

### Physical Proximity
Citations are 58 chars apart (within 200 char threshold):
```
Position: 46989 - "194 L. Ed. 2d 635" (Spokeo cluster)
Position: 47047 - "521 U.S. 811" (Raines - WRONG cluster!)
Distance: 58 chars
```

### Root Cause
**Fix #48/#49 is not enforcing name/date matching!**

The clustering logic is:
1. Group by proximity (200 chars)
2. Check if names match
3. **BUT** if one citation has a name and the other doesn't, OR if the comparison fails, it STILL clusters them!

**Expected Behavior:**
- Citations with DIFFERENT extracted names should NEVER cluster together
- Citations with DIFFERENT extracted dates should NEVER cluster together
- Proximity should only cluster citations with SAME extracted data

---

## Bug #2: Verification Returns Wrong Cases

### Cluster 6: "State v. M.Y.G." - 4 Citations Verify to 4 Different Cases

| Citation | Extracted | Verified To | Issue |
|----------|-----------|-------------|-------|
| 199 Wn.2d 528 | State v. M.Y.G. (2022) | **State v. Olsen** (2024) | Wrong case, wrong year |
| 509 P.3d 818 | State v. M.Y.G. (2022) | **State v. P** (2017) | Wrong case, wrong year |
| 116 Wn.2d 1 | State v. M.Y.G. (1991) | **Public Utility District v. State** | Completely wrong |
| 802 P.2d 784 | State v. M.Y.G. (1991) | **State of Iowa v. Harrison** | **WRONG STATE!** |

### Root Cause
**Fix #50 Jurisdiction Filtering NOT WORKING!**

Evidence:
- "802 P.2d 784" is a **P.2d** (Pacific Reporter) citation
- System verified it to an **IOWA case** (not Washington!)
- Jurisdiction filter should have rejected this immediately

**Expected Behavior:**
- Citations should verify to cases in the SAME jurisdiction
- P.2d citations in WA document should verify to WA/OR/CA/MT/etc. cases, NOT Iowa
- Verification should fail if no matching case found, not return first result

---

## Bug #3: Year Mismatches Everywhere

Multiple citations verify to cases with completely different years:

| Citation | Extracted Year | Canonical Year | Diff |
|----------|----------------|----------------|------|
| 199 Wn.2d 528 | 2022 | 2024 | 2 years |
| 509 P.3d 818 | 2022 | 2017 | 5 years |
| 116 Wn.2d 1 | 1991 | 2013 | 22 years! |
| 802 P.2d 784 | 1991 | 2023 | 32 years!! |

**Expected Behavior:**
- Verification should reject matches with large year mismatches (>2 years)
- Year validation should be part of Fix #50 jurisdiction filtering

---

## Impact Assessment

### Before Discovery
- **Reported:** 18/44 clusters verified (41%)
- **Reality:** Unknown how many are WRONG verifications

### After Discovery
- **Cluster 19:** 6 citations, 2 are from wrong case
- **Cluster 6:** 4 citations, ALL verify to wrong cases
- **Other clusters:** Unknown (need to check)

**Estimated Impact:** 20-40% of "verified" citations may be WRONG verifications

---

## Required Fixes

### Fix #58: Enforce Extracted Name/Date Matching in Clustering

**Location:** `src/unified_citation_clustering.py`

**Current Logic (WRONG):**
```python
# If both have case names, they should match
if case1 and case2 and case1 != 'N/A' and case2 != 'N/A':
    similarity = self._calculate_name_similarity(case1, case2)
    if similarity < threshold:
        return False  # Reject
# BUT if one is N/A, it ACCEPTS them!
```

**Fixed Logic (CORRECT):**
```python
# MUST have same extracted name (no N/A allowed for clustering)
if case1 != case2 or case1 == 'N/A' or case2 == 'N/A':
    return False  # Reject immediately
    
# MUST have same extracted year (no N/A allowed for clustering)
if year1 != year2 or year1 == 'N/A' or year2 == 'N/A':
    return False  # Reject immediately
```

### Fix #59: Enforce Jurisdiction Filtering in Verification

**Location:** `src/unified_verification_master.py`

**Current Logic:** Fix #50 exists but not executing (like Fix #52 issue)

**Required Changes:**
1. Detect expected jurisdiction from citation format
2. Validate ALL API results against jurisdiction
3. Reject results from wrong jurisdiction (e.g., Iowa for WA citations)
4. Add diagnostic logging to show jurisdiction filtering

### Fix #60: Enforce Year Validation in Verification

**Location:** `src/unified_verification_master.py`

**Current Logic:** No year validation

**Required Changes:**
1. Compare extracted_date to canonical_date
2. Reject if difference > 2 years
3. Add warning if difference = 1-2 years
4. Log all year mismatches

---

## Testing Plan

1. **Test Cluster 19:**
   - "521 U.S. 811" should be in SEPARATE cluster from Spokeo citations
   - Should extract "Raines v. Byrd" (1997)
   - Should NOT be grouped with "Spokeo, Inc. v. Robins" (2016)

2. **Test Cluster 6:**
   - "199 Wn.2d 528" should verify to correct "State v. M.Y.G." case
   - "802 P.2d 784" should REJECT Iowa verification
   - All citations should verify to SAME canonical case or be unverified

3. **Test All Clusters:**
   - No cluster should have citations with different extracted names
   - No cluster should have citations with different extracted years
   - No verified citation should have >2 year mismatch
   - No verified citation should be from wrong jurisdiction

---

## Priority

**CRITICAL:** These bugs make the verification system unreliable. Users cannot trust the canonical data.

**Order of Fixes:**
1. Fix #58 (clustering) - Prevents wrong grouping
2. Fix #59 (jurisdiction) - Prevents wrong state matches
3. Fix #60 (year) - Prevents wrong year matches

**Expected Result:** Lower verification rate, but HONEST and RELIABLE results.

---

**Session:** Post Fix #56/#57  
**Discovered By:** User testing with 1033940.pdf  
**Status:** In Progress - Fixes Required




