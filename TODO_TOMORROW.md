# CaseStrainer TODO - Session Follow-Up

**Date:** October 21, 2025  
**Status:** Multiple critical clustering and extraction issues identified

---

## 🚨 CRITICAL ISSUES (Must Fix)

### 1. **Oneida Citations Not Clustering** ⚠️ HIGHEST PRIORITY

**Problem:**  
Three Supreme Court parallel citations (562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587) are appearing as THREE SEPARATE CLUSTERS instead of one unified cluster.

**Current State:**
```
❌ Four separate clusters:
   - Cluster 1: 605 F.3d 149 (2010)
   - Cluster 2: 178 L. Ed. 2d 587 (2011)
   - Cluster 3: 562 U.S. 42 (2011)
   - Cluster 4: 131 S. Ct. 704 (2011)
```

**Expected State:**
```
✅ Two clusters:
   - Cluster 1: 605 F.3d 149 (2010)
   - Cluster 2: 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011) [ALL TOGETHER]
```

**What We Know:**
- ✅ Year extraction appears to be working (all three show "2011")
- ❌ Proximity grouping is failing (each citation is standalone)
- ❓ Debug logging not appearing in logs (possible caching or wrong code path)

**Test Text:**
```
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) 
(a tribe's immunity from suit is independent of its lands), vacated and remanded, 
562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)
```

**Root Cause Theories:**
1. **Citations not from same text location** - May be extracted from different parts of document
2. **Proximity grouping not running** - Code path issue or caching
3. **Start/end indices incorrect** - Distance calculation fails
4. **Caching preventing new code execution** - System returning old results

**Files Modified (Need to Verify Deployment):**
- `src/unified_case_extraction_master.py` - Year extraction for Supreme Court citations
- `src/unified_clustering_master.py` - Debug logging for proximity grouping

**Next Steps:**
1. Verify debug logging code actually deployed (check container files)
2. Clear all caches (Redis + SQLite) and test with fresh input
3. Check citation start_index/end_index values in extraction
4. Add logging to see WHERE citations are extracted from in text
5. Verify `_group_by_proximity()` is actually being called
6. Test proximity grouping with minimal example

---

### 2. **Wrong Case Names Extracted** ⚠️ HIGH PRIORITY

**Problem:**  
Multiple citations are extracting the wrong case name from nearby text, leading to incorrect case associations.

#### Issue 2a: "If in Worcester v. Georgia" (Martin v. Lessee of Waddell)

```
❌ Current:
Verifying Source: Martin v. Lessee of Waddell, 1842-02-18
Submitted Document: If in Worcester v. Georgia, 1842
Citation: 16 Pet. 367

✅ Expected:
Submitted Document: Martin v. Lessee of Waddell, 1842
```

**Root Cause:** Extraction picked up nearby reference to "Worcester v. Georgia" and included the word "If" from the preceding text.

**Fix Needed:** Clean leading signal words ("If", "In", "See", etc.) from extracted case names

#### Issue 2b: "State v. Lazcano" (Gorman v. City of Woodinville)

```
❌ Current:
Verifying Source: Gorman v. City of Woodinville, 2012-08-16
Submitted Document: State v. Lazcano, 2012
Citation: 175 Wn.2d 68

✅ Expected:
Submitted Document: Gorman v. City of Woodinville, 2012
```

**Root Cause:** Both cases are from 2012, extraction algorithm picked the wrong case name from nearby text.

**Fix Needed:** Improve context isolation to prevent contamination from nearby cases

#### Issue 2c: "N/A" (Outsource Services Management)

```
❌ Current:
Verifying Source: Outsource Services Management, LLC v. Nooksack Business Corp., 2014-08-21
Submitted Document: N/A, 2014
Citation: 181 Wn.2d 272

✅ Expected:
Submitted Document: Outsource Services Management, LLC v. Nooksack Business Corp., 2014
```

**Root Cause:** Case name extraction completely failed - returned no result.

**Fix Needed:** Debug why extraction returned nothing for this citation

**Common Pattern:**
All of these show the same issue: **extraction picking up wrong text from nearby context**

**Files to Check:**
- `src/unified_case_extraction_master.py` - Main extraction logic
- `src/utils/text_normalizer.py` - Signal word cleaning

**Next Steps:**
1. Add debug logging to show WHAT text is being analyzed for extraction
2. Improve signal word cleaning (remove "If", "In", leading contamination)
3. Better context boundary detection (don't cross paragraph/sentence boundaries)
4. Validate extracted name appears in immediate context of citation
5. Prefer case names BEFORE citation over case names AFTER citation

---

### 3. **Wrong Case Associations** ⚠️ MEDIUM PRIORITY

#### Issue 3a: Flying T Ranch Shows as "Automotive United Trades Organization"

```
❌ Current:
Verifying Source: Automotive United Trades Organization v. State, 2012-08-30
Submitted Document: Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians, 2024
Citation 1: 3 Wn.2d 1031 Verified by Parallel
Citation 2: 175 Wn.2d 214 Verified
Citation 3: 285 P.3d 52 Verified
```

**Analysis:**
- ✅ Extraction is CORRECT ("Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians")
- ❌ Verification/display shows WRONG case ("Automotive United Trades Organization v. State")
- ⚠️ Citations "175 Wn.2d 214" and "285 P.3d 52" are from the Automotive case (2012)
- ⚠️ Citation "3 Wn.2d 1031" is from Flying T Ranch (2024)

**Root Cause:** These are citations from TWO DIFFERENT CASES being incorrectly clustered together!

**Why This Happened:**
- "175 Wn.2d 214" belongs to Automotive United Trades Organization (2012)
- "3 Wn.2d 1031" belongs to Flying T Ranch (2024)
- They should NOT be in the same cluster
- But somehow they got grouped together

**Fix Needed:** 
1. Check why these citations from different cases are clustering
2. Verify case name extraction for each individual citation
3. Ensure year mismatch (2012 vs 2024) prevents clustering

#### Issue 3b: Quinault Citations Split Across Two Clusters

```
❌ Current (2 separate clusters):
Cluster 1: 130 Wn.2d 862, 150 Wn. App. 476
Cluster 2: 929 P.2d 379, 208 P.3d 1180

✅ Expected (1 cluster):
Cluster 1: 130 Wn.2d 862, 929 P.2d 379 (parallel citations for same case)
```

**Analysis:**
- All verified to same canonical: "Anderson & Middleton Lumber Co. v. Quinault Indian Nation (1996-12-26)"
- Logs show: "✅ [PARALLEL-MATCH] Clustering via name+year: 130 Wn.2d 862 ↔ 929 P.2d 379"
- BUT they're shown as 2 separate clusters in results

**Root Cause:** Unknown - clustering appears to work in logs but results show separation

**Possible Causes:**
1. "150 Wn. App. 476" and "208 P.3d 1180" are from a DIFFERENT case (maybe different year?)
2. Display issue (clustering works but results formatting shows duplicates)
3. Verification creating duplicate clusters

**Next Steps:**
1. Verify all 4 citations are truly from the same case
2. Check canonical dates for each citation
3. Look for year mismatches causing separation
4. Review display/formatting logic

---

## ✅ WORKING CORRECTLY (Confirmed)

### 1. **Vacatur Pattern Detection** ✅

**Status:** Working correctly  
**Evidence:** Extracts "Oneida Indian Nation v. Madison County" (not "Cayuga Indian Nation v. Seneca County")  
**Files:** `src/unified_case_extraction_master.py` (lines 571-654, 1139-1215)

### 2. **Year Extraction for Supreme Court Citations** ✅ (Partially)

**Status:** Appears to be working  
**Evidence:** All three Oneida Supreme Court citations show year "2011"  
**Files:** `src/unified_case_extraction_master.py` (Supreme Court year detection logic)  
**Note:** Can't fully confirm without debug logs, but results show correct years

### 3. **Multiple Reporter Clustering** ✅

**Status:** Working for most cases  
**Evidence:** Many cases correctly cluster 3 parallel citations:
- Upper Skagit: 584 U.S. 554, 200 L. Ed. 2d 931, 138 S. Ct. 1649 ✅
- Michigan v. Bay Mills: 572 U.S. 782, 188 L. Ed. 2d 1071, 134 S. Ct. 2024 ✅
- Santa Clara Pueblo: 436 U.S. 49, 56 L. Ed. 2d 106, 98 S. Ct. 1670 ✅

**Note:** This confirms the clustering architecture WORKS - the Oneida issue is specific, not systemic.

---

## 🔧 DIAGNOSTIC TASKS (Do These First)

### Task 1: Verify Debug Logging Deployment (15 min)

**Goal:** Confirm the proximity debug logging code is actually in the running containers

**Steps:**
1. Connect to container: `docker exec -it casestrainer-backend-prod bash`
2. Check file: `grep "PROXIMITY-DEBUG" /app/src/unified_clustering_master.py`
3. Should see multiple debug logging lines around line 440-485
4. If NOT present, debug logging didn't deploy - need to rebuild

**Expected Output:** Should see ~10 lines with "PROXIMITY-DEBUG" logging

### Task 2: Clear All Caches (5 min)

**Goal:** Ensure we're testing with fresh processing, not cached results

**Steps:**
1. Run: `.\cslaunch.ps1` (this clears Redis + SQLite on startup)
2. Verify cache clear message in output
3. Submit test text IMMEDIATELY after startup
4. Check logs for debug output

**Note:** System might be returning cached results from previous submissions

### Task 3: Check Citation Positions (20 min)

**Goal:** See WHERE citations are actually located in the text and what their indices are

**Steps:**
1. Add debug logging to citation extraction showing:
   ```python
   logger.error(f"[CITATION-POS] Found: '{citation}' at start={start_index}, end={end_index}")
   logger.error(f"[CITATION-POS] Surrounding text: '{text[start_index-20:end_index+20]}'")
   ```
2. Submit Oneida test text
3. Check logs for all three Supreme Court citations
4. Verify they're from the same sentence/location

**Expected:** All three should be within ~50 chars of each other if from "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"

### Task 4: Test Minimal Clustering Example (30 min)

**Goal:** Verify proximity grouping works in isolation

**Create test file:** `test_proximity_grouping.py`
```python
from src.unified_clustering_master import CitationClusteringMaster

# Create test citations very close together
test_citations = [
    {
        'citation': '111 U.S. 111',
        'start_index': 100,
        'end_index': 113,
        'case_name': 'Test v. Case',
        'year': '2020'
    },
    {
        'citation': '222 U.S. 222',
        'start_index': 115,  # Only 2 chars from first citation
        'end_index': 128,
        'case_name': 'Test v. Case',
        'year': '2020'
    }
]

test_text = "..." * 200 + "111 U.S. 111, 222 U.S. 222" + "..." * 200

master = CitationClusteringMaster()
groups = master._group_by_proximity(test_citations, test_text)

print(f"Number of groups: {len(groups)}")
print(f"Group 1 size: {len(groups[0])}")
# Should print: Number of groups: 1, Group 1 size: 2
```

**Run:** `docker exec casestrainer-backend-prod python test_proximity_grouping.py`

**Expected:** 1 group with 2 citations

---

## 📝 INVESTIGATION QUESTIONS

### Questions to Answer:

1. **Is proximity grouping even running?**
   - Evidence needed: Debug logs showing proximity comparisons
   - If NO logs: Find where clustering is actually happening

2. **Are citations from the same text location?**
   - Evidence needed: start_index and end_index values
   - If different locations: Why is extraction splitting them?

3. **Is there caching preventing new code from running?**
   - Evidence needed: Timestamp in logs vs. rebuild time
   - If cached: Clear caches and force fresh processing

4. **Why are some citations clustering perfectly while others fail?**
   - Working: Upper Skagit, Michigan v. Bay Mills, Santa Clara Pueblo
   - Failing: Oneida citations
   - Evidence needed: Comparison of what's different

5. **Why are debug logs not appearing?**
   - Possible causes: Code not deployed, logs filtered, wrong worker, wrong code path
   - Evidence needed: Verify code in container, check all workers

---

## 🎯 PRIORITIZED ACTION PLAN

### Phase 1: Diagnostic (1-2 hours)
1. ✅ Verify debug logging deployment
2. ✅ Clear all caches  
3. ✅ Check citation positions
4. ✅ Review all worker logs (not just worker1)
5. ✅ Test minimal proximity grouping example

### Phase 2: Fix Proximity Grouping (2-3 hours)
Based on diagnostic findings:
- **If caching:** Force cache clear, modify test text
- **If wrong positions:** Fix citation extraction to preserve positions
- **If not running:** Find correct code path and add clustering there
- **If other issue:** Debug based on evidence

### Phase 3: Fix Case Name Extraction (2-3 hours)
1. Clean leading signal words ("If", "In", "See")
2. Improve context isolation
3. Add validation (extracted name must appear near citation)
4. Debug "N/A" extraction failure
5. Test with all problem citations

### Phase 4: Fix Wrong Associations (1-2 hours)
1. Debug Flying T Ranch clustering issue
2. Investigate Quinault split clusters
3. Verify year matching prevents wrong grouping
4. Test with mixed-year citations

### Phase 5: Comprehensive Testing (1 hour)
1. Test all problem citations
2. Verify fixes don't break working cases
3. Document test cases
4. Create regression test suite

---

## 📊 SUCCESS CRITERIA

### For Oneida Citations:
✅ All three Supreme Court citations (562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587) in ONE cluster  
✅ Correct case name: "Oneida Indian Nation v. Madison County"  
✅ Correct year: "2011"  
✅ Marked as "Verified by Parallel"

### For Case Name Extraction:
✅ "Martin v. Lessee of Waddell" (not "If in Worcester v. Georgia")  
✅ "Gorman v. City of Woodinville" (not "State v. Lazcano")  
✅ "Outsource Services Management, LLC v. Nooksack Business Corp." (not "N/A")

### For Wrong Associations:
✅ Flying T Ranch citations NOT mixed with Automotive United Trades Organization  
✅ Quinault citations in one cluster (or properly separated if truly different cases)

---

## 📁 FILES TO REVIEW

### Primary Files:
- `src/unified_clustering_master.py` - Clustering and proximity grouping
- `src/unified_case_extraction_master.py` - Case name and year extraction
- `src/utils/text_normalizer.py` - Text cleaning and normalization

### Debug/Test Files:
- `proximity_debug.txt` - Latest debug logs (empty/no proximity logs)
- `CRITICAL_FINDINGS.md` - Current state analysis
- `MULTIPLE_CLUSTERING_ISSUES.md` - Issue catalog
- `DEBUG_PROXIMITY_GROUPING.md` - Debug strategy
- `FINAL_YEAR_FIX.md` - Year extraction fix documentation

### Test Input:
```text
Other cases specifically discussing tribes hold that tribal sovereign immunity is not waived with respect to real property. See Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014) (declining to draw a distinction between in rem and in personam proceedings); Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) (a tribe's immunity from suit is independent of its lands), vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011); Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016).
```

---

## 💡 NOTES & OBSERVATIONS

### What's Working Well:
- CourtListener API integration ✅
- Verification system ✅
- Most parallel citation clustering ✅
- Corporate name extraction (Flying T Ranch, Inc.) ✅
- Vacatur pattern detection ✅

### What's Broken:
- Oneida citation clustering ❌
- Multiple case name extractions ❌
- Some wrong case associations ❌

### Confidence Levels:
- **HIGH:** Year extraction is working (visible in results)
- **MEDIUM:** Proximity grouping code exists (we wrote it)
- **LOW:** Proximity grouping is actually running (no logs)
- **VERY LOW:** We understand why it's failing (need diagnostics)

### Key Insight:
The fact that **most parallel citations cluster correctly** (Upper Skagit, Michigan v. Bay Mills, etc.) proves the architecture works. The Oneida issue is **specific** to that case or that text structure, not a systemic failure.

---

## ⏰ TIME ESTIMATES

- **Diagnostics:** 1-2 hours
- **Fix proximity grouping:** 2-3 hours  
- **Fix case name extraction:** 2-3 hours
- **Fix wrong associations:** 1-2 hours
- **Testing & validation:** 1 hour

**Total:** 7-11 hours of focused work

---

## 🔄 NEXT SESSION CHECKLIST

- [ ] Run all diagnostic tasks
- [ ] Verify debug code deployment
- [ ] Clear all caches
- [ ] Review diagnostic findings
- [ ] Choose fix strategy based on evidence
- [ ] Implement fix
- [ ] Test thoroughly
- [ ] Document solution

---

**Status:** Ready for next session  
**Priority:** Start with diagnostics to understand root cause before making more code changes  
**Risk:** Making more changes without understanding the problem could make it worse
