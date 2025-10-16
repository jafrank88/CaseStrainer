# Test Results Analysis - October 15, 2025, 10:50 PM

## 📊 Test Summary

**File Tested:** `1034300.pdf` (Flying T Ranch case)  
**Processing Time:** ~90 seconds  
**Worker:** rqworker3-prod

---

## ✅ What's Working

### 1. Verification SUCCESS
- **36/132 citations verified** (27%)
- Both batch lookup and search API working
- Canonical names being extracted correctly

### 2. Canonical Name Extraction SUCCESS
Examples extracted:
- "Upper Skagit Tribe v. Lundgren"
- "Michigan v. Bay Mills Indian Community"
- "Santa Clara Pueblo v. Martinez"
- "United States v. United States Fidelity & Guaranty Co."
- "Three Affiliated Tribes of the Fort Berthold Reservation v. Wold Engineering, P. C."
- "C & L Enterprises Inc. v. Citizen Band Potawatomi Indian Tribe of Oklahoma"
- "Kiowa Tribe of Oklahoma v. Manufacturing Technologies, Inc."
- "County of Yakima v. Confederated Tribes & Bands of the Yakima Indian Nation"

### 3. Cluster Update SUCCESS
- Clusters being updated with verified citations
- Lookup replacement working: `citation_lookup[cit_text]`

---

## ❌ What's Broken

### CRITICAL: Canonical Data Not Persisting

**Symptoms:**
- Verification extracts canonical_name ✅
- VerificationResult objects created with canonical_name ✅  
- But citation objects end up with canonical_name=None ❌
- Result: Only 3/73 clusters show canonical data

**Evidence from logs:**
```
✅ [TOP-LEVEL] Found case_name = Upper Skagit Tribe v. Lundgren
✅ VERIFIED via courtlistener_lookup_batch
✅ Updated cluster with 3 citations from citation_lookup

BUT THEN:

❌ Citation: verified=True, has_canonical=False  (33 times!)
✅ Citation: verified=True, has_canonical=True   (only 3 times!)
```

---

## 🔍 Root Cause Analysis

The problem is in **how VerificationResult data is applied to citation objects**.

### The Flow:
1. **Verification** creates `VerificationResult(canonical_name="X v. Y")` ✅
2. **Clustering master** applies VerificationResult to citation objects ❓
3. **Progress manager** looks up citations in `citation_dicts` ✅
4. **Clusters** should have citations with canonical_name ❌

### The Bug Location:
Somewhere between steps 1-2, the `canonical_name` from `VerificationResult` is not being set on the citation objects.

Likely in: `src/unified_clustering_master.py` around line 1681:
```python
citation_obj.canonical_name = result.canonical_name
```

This line should be setting it, but 33 out of 36 times it's not working!

---

## 🧪 Specific Test Cases

### Working (3 clusters):
1. **C & L Enterprises** cluster (3 citations)
   - 532 U.S. 411 ✅
   - 149 L. Ed. 2d 623 ✅
   - 121 S. Ct. 1589 ✅
   
2. **Kiowa Tribe** cluster (3 citations)
   - 523 U.S. 751 ✅
   - 140 L. Ed. 2d 981 ✅
   - 118 S. Ct. 1700 ✅

3. **County of Yakima** cluster (2 citations)
   - 116 L. Ed. 2d 687 ✅
   - 502 U.S. 251 ✅

### NOT Working (70 clusters):
- **Upper Skagit** cluster (3 citations) ❌
  - 584 U.S. 554, 138 S. Ct. 1649, 200 L. Ed. 2d 931
  - Verified via batch lookup
  - Canonical name extracted: "Upper Skagit Tribe v. Lundgren"
  - But canonical_name=None on citation objects!

- **Michigan v. Bay Mills** cluster (3 citations) ❌
  - Verified via batch lookup
  - Canonical name extracted
  - But canonical_name=None on citation objects!

---

## 🎯 Next Steps to Fix

### Investigation Needed:
1. Check `src/unified_clustering_master.py` line ~1678-1685
   - Is `result.canonical_name` actually set?
   - Is the citation object type correct (dict vs object)?
   - Is there an exception being silently caught?

2. Check if VerificationResult is being properly serialized
   - When it goes through RQ worker queues
   - When it's converted to dict format

3. Add more logging:
   ```python
   logger.error(f"APPLYING VERIFICATION: result.canonical_name = {result.canonical_name}")
   logger.error(f"BEFORE: citation.canonical_name = {getattr(citation, 'canonical_name', 'NOT SET')}")
   # Apply...
   logger.error(f"AFTER: citation.canonical_name = {getattr(citation, 'canonical_name', 'NOT SET')}")
   ```

---

## 📝 Case Name Extraction Issues Found

### Truncation (Still Present):
None detected in this test (context window increase may have helped)

### Contamination (Need to verify):
Cannot verify without seeing actual extracted names in output

### Signal Words (Need to verify):
Cannot verify without seeing actual extracted names in output

---

## 💡 Theory

The 3 working clusters were likely processed differently:
- Maybe they went through a different code path
- Maybe they were the first batch and something changed
- Maybe they were verified by a different source (fallback vs CourtListener)

The fact that it's **exactly 3** working and **always the same 3** suggests:
- Not a random timing issue
- Not an intermittent bug
- Something specific about HOW those 3 were processed vs the other 33

---

## 🚀 Recommended Fix

Add defensive logging in `unified_clustering_master.py` around the verification application code to trace exactly what's happening to `canonical_name` for working vs non-working citations.

**Files to examine:**
1. `src/unified_clustering_master.py` - lines 1670-1690
2. `src/citation_extraction_endpoint.py` - lines 180-210  
3. `src/progress_manager.py` - lines 1150-1190

---

**Status:** Critical bug identified, needs immediate investigation of verification data application logic.
