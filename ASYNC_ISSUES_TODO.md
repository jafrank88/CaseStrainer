# Async Processing Issues - TO-DO List

## Priority 1: Data Integrity Issues (CRITICAL)

### Issue 1: Cluster Canonical Data Missing
**Problem:** Clusters show "Verifying Source: N/A" even when individual citations within the cluster are verified.

**Example:**
```
Verifying Source: N/A, 2018
Citation 1: 584 U.S. 554 - Unverified
Citation 2: 138 S. Ct. 1649 - Verified ✓
Citation 3: 200 L. Ed. 2d 931 - Verified ✓
```

**Expected:** Cluster should show canonical_name, canonical_date, verification_source from Citation 2 or 3.

**Fix Applied:** Added cluster canonical data extraction in `unified_clustering_master.py` lines 2102-2126
**Status:** NOT WORKING - Code not being executed in async path

---

### Issue 2: Missing true_by_parallel Propagation
**Problem:** Unverified parallel citations don't get `true_by_parallel=True` flag.

**Example:**
```
Citation 1: 584 U.S. 554 - Unverified (should be true_by_parallel=True)
Citation 2: 138 S. Ct. 1649 - Verified
```

**Expected:** Citation 1 should have:
- `verified=False` (stays unchanged)
- `true_by_parallel=True` (new flag)
- `canonical_name` from Citation 2
- `canonical_date` from Citation 2

**Fix Applied:** Added parallel propagation in `unified_clustering_master.py` lines 2070-2100
**Status:** NOT WORKING - Code not being executed in async path

---

## Priority 2: Case Name Extraction Issues (HIGH)

### Issue 3: Citation Text Contamination
**Problem:** Extracted case names include trailing citation text.

**Examples:**
- `"Inc. v. Stillaguamish Tribe of Indians , 31 Wn. App. 2d 343, 359-62"` ❌
- `"Yakima v. Confederated Tribes & Bands of Yakima Indian Nation, 502 U.S. 251, 255"` ❌
- `"State v. Wallahee, 3 Wn.3d 179, 187-88"` ❌

**Expected:** Clean case names without citation text:
- `"Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians"` ✓
- `"Yakima v. Confederated Tribes & Bands of Yakima Indian Nation"` ✓
- `"State v. Wallahee"` ✓

**Fix Applied:** Added contamination removal patterns in `unified_case_name_extractor_v2.py` lines 840-843
**Status:** NOT WORKING - Regex patterns may be wrong or not executed

---

### Issue 4: Signal Word Contamination
**Problem:** Extracted case names include signal words and leading phrases.

**Examples:**
- `"Id. For example, in Knocklong Corp. v. Kingdom of Afghanistan"` ❌

**Expected:**
- `"Knocklong Corp. v. Kingdom of Afghanistan"` ✓

**Fix Applied:** Added signal word removal patterns in `unified_case_name_extractor_v2.py` lines 845-848
**Status:** NOT WORKING - Regex patterns may be wrong or not executed

---

### Issue 5: Severe Name Truncation
**Problem:** Case names severely truncated, starting mid-word.

**Examples:**
- `"agit Indian Tribe"` ❌ (should be "Upper Skagit Indian Tribe")
- `"Mgmt., LLC v. Nooksack Bus. Corp."` ❌ (missing company name prefix)
- `"Comm' v. Citizen Band"` ❌ (truncated plaintiff)
- `"Co. Colorado v. Shoshone"` ❌ (truncated plaintiff)

**Expected:** Full case names with proper prefixes

**Fix Applied:** Added truncation detection in `unified_case_name_extractor_v2.py` lines 975-985
**Status:** PARTIALLY WORKING - Rejects lowercase starts but doesn't find better alternatives

---

## Priority 3: System Architecture Issue (ROOT CAUSE)

### Issue 6: Sync vs Async Give Different Results
**Problem:** Sync processing gives better results than async processing.

**Observed Differences:**
- Sync: 35% verification rate, cleaner case names
- Async: 25% verification rate, same extraction issues persist

**ROOT CAUSE IDENTIFIED:**

From worker logs analysis:
1. `_format_clusters_for_output()` is NEVER CALLED - no CLUSTER_FORMAT logs
2. Citations inside clusters show `verified=False` for ALL citations
3. After extraction: "36 verified in updated_citations"
4. This means **verification happens OUTSIDE the clustering master**

**The Problem:**
- My fixes in `_format_clusters_for_output()` assume citations are already verified
- But verification happens AFTER clusters are formatted
- So cluster canonical data extraction finds NO verified citations
- Parallel propagation never happens because no verified citations exist yet

**Actual Flow:**
1. Extract citations (no verification yet)
2. Cluster citations (citations have verified=False)
3. Format clusters ← MY FIXES ARE HERE, but nothing is verified yet!
4. Apply verification (citations get verified=True)
5. Return to progress_manager
6. Extract citations from formatted clusters
7. NOW citations are verified, but clusters were already formatted WITHOUT canonical data

**Solution:**
Either:
A. Move verification to BEFORE formatting (Step 3 instead of Step 4)
B. Add SECOND pass after verification to update cluster metadata
C. Move canonical data extraction to progress_manager AFTER verification

---

## Investigation Steps

1. **Trace Async Code Path**
   - Start: `progress_manager.py` line 1009 `extract_citations_with_clustering()`
   - Follow through: `citation_extraction_endpoint.py`
   - Find where clusters are formatted
   - Identify which extractor is called

2. **Compare Sync Code Path**
   - Start: `citation_service.py` `process_immediately()`
   - Trace to see if it uses same or different modules
   - Document differences

3. **Verify Extractor Usage**
   - Check if `unified_case_name_extractor_v2.py` is actually being called
   - May be using older `unified_case_name_extractor.py` instead
   - Add logging to confirm which extractor runs

4. **Find All Formatting Locations**
   - Search for cluster formatting in all modules
   - Apply fixes to ALL locations, not just one

---

## Files Modified So Far

1. `src/unified_clustering_master.py` - Cluster canonical data & parallel propagation
2. `src/unified_case_name_extractor_v2.py` - Contamination removal & truncation detection
3. `src/enhanced_fallback_verifier.py` - Infinite loop fix
4. `src/api/services/citation_service.py` - Async routing
5. `src/vue_api_endpoints.py` - Task ID in response
6. `docker-compose.prod.yml` - Nginx DNS fix

---

## Next Steps

1. Add comprehensive logging to trace code path
2. Identify why fixes aren't being applied
3. Apply fixes to correct locations
4. Test and verify each fix individually
5. Commit when working

---

## Success Criteria

✅ Issue 1: Clusters show canonical data when any citation is verified
✅ Issue 2: Parallel citations get true_by_parallel=True and canonical data
✅ Issue 3: No citation text in extracted case names
✅ Issue 4: No signal words in extracted case names
✅ Issue 5: No truncated case names (full names or N/A)
✅ Issue 6: Sync and async produce identical quality results
