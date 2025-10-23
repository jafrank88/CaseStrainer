# Multiple Clustering and Extraction Issues

## Summary of Problems

Based on the latest test results, there are several critical issues:

### 1. **Oneida Citations STILL Not Clustering** ❌ CRITICAL
The three Supreme Court parallel citations are showing as **three separate clusters**:
```
Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, 2011
Citation 1: 178 L. Ed. 2d 587 Verified

Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, 2011
Citation 1: 562 U.S. 42 Verified

Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, 2011
Citation 1: 131 S. Ct. 704 Verified
```

**Expected:** ONE cluster with all three citations  
**Actual:** THREE separate clusters

**Possible Causes:**
- Year extraction fix didn't work
- Citations are being split by some other logic
- Proximity grouping is failing
- Parallel detection is not working

---

### 2. **Flying T Ranch Wrong Case Name** ❌
```
Verifying Source: Automotive United Trades Organization v. State, 2012-08-30
Submitted Document: Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians, 2024
Citation 1: 3 Wn.2d 1031 Verified by Parallel
Citation 2: 175 Wn.2d 214 Verified
Citation 3: 285 P.3d 52 Verified
```

**Issue:** Citation shows "Automotive United Trades Organization" as verifying source, but the submitted document correctly shows "Flying T Ranch, Inc."

This means:
- Extraction is correct ("Flying T Ranch")
- But clustering/verification is associating it with the WRONG case

---

### 3. **Quinault Citations Not Clustered** ❌
```
Verifying Source: Anderson & Middleton Lumber Co. v. Quinault Indian Nation, 1996-12-26
Submitted Document: Middleton Lumber Co. v. Quinault Indian Nation, 1996
Citation 1: 130 Wn.2d 862 Verified
Citation 2: 150 Wn. App. 476 Verified

Verifying Source: Anderson & Middleton Lumber Co. v. Quinault Indian Nation, 1996-12-26
Submitted Document: Middleton Lumber Co. v. Quinault Indian Nation, 1996
Citation 1: 929 P.2d 379 Verified
Citation 2: 208 P.3d 1180 Verified
```

**Issue:** Two separate clusters for the same case, all verified to the same canonical name

**From Logs:**
```
✅ [PARALLEL-MATCH] Clustering via name+year: Middleton Lumber Co. v. Quinault Indian (1996) ↔ Middleton Lumber Co. v. Quinault Indian (1996)
   Citations: 130 Wn.2d 862 ↔ 929 P.2d 379
   Similarity: 100.00%, Years match: True
```

This shows that **130 Wn.2d 862** and **929 P.2d 379** ARE clustering correctly!

But then why are there TWO clusters shown in the results?

**Possible Issue:** "150 Wn. App. 476" and "208 P.3d 1180" are being added to the wrong clusters OR there are citations from a different case mixing in.

---

### 4. **Outsource Services - No Case Name Extracted** ❌
```
Verifying Source: Outsource Services Management, LLC v. Nooksack Business Corp., 2014-08-21
Submitted Document: N/A, 2014
Citation 1: 181 Wn.2d 272 Verified
Citation 2: 333 P.3d 380 Verified
```

**Issue:** "N/A" submitted document = no case name was extracted

**From Logs:**
```
[ALL-DATES] 181 Wn.2d 272 → Date: None
```

Extraction completely failed for this citation.

---

### 5. **Martin v. Lessee of Waddell - Wrong Case Name** ❌
```
Verifying Source: Martin v. Lessee of Waddell, 1842-02-18
Submitted Document: If in Worcester v. Georgia, 1842
Citation 1: 16 Pet. 367 Verified
Citation 2: 10 L. Ed. 997 Verified
```

**Issue:** Extracted "If in Worcester v. Georgia" instead of "Martin v. Lessee of Waddell"

This looks like a contamination issue - the extraction picked up text from a nearby reference to "Worcester v. Georgia" and included the word "If" at the beginning.

---

### 6. **Gorman v. City of Woodinville - Wrong Case Name** ❌
```
Verifying Source: Gorman v. City of Woodinville, 2012-08-16
Submitted Document: State v. Lazcano, 2012
Citation 1: 175 Wn.2d 68 Verified
```

**Issue:** Extracted "State v. Lazcano" instead of "Gorman v. City of Woodinville"

Both cases are from 2012, so the extractor picked up the WRONG case name from nearby text.

---

## Root Cause Analysis

### Issue #1: Oneida Clustering Failure

**Hypothesis 1: Year Extraction Didn't Work**
- The fix to look for Supreme Court year after the citation may not be executing
- OR the year is still not being found

**Hypothesis 2: Citations Not in Same Proximity Group**
- The citations might be separated by some boundary (paragraph, semicolon, etc.)
- Even though they should be comma-separated: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"

**Hypothesis 3: Clustering Logic Not Executing**
- The `_are_parallel_citations` function may not be called
- OR it's returning False even though names and years match

**What to Check:**
1. Are all three citations getting year "2011"?
2. Are they in the same proximity group?
3. Is `_are_parallel_citations` being called for them?
4. If called, why is it returning False?

---

### Issue #2-6: Case Name Extraction Failures

All of these share a common pattern: **wrong case name extracted from nearby text**

**Examples:**
- "If in Worcester v. Georgia" - grabbed nearby case reference + word "If"
- "State v. Lazcano" - grabbed different case from same year
- "N/A" - extraction completely failed

**Possible Causes:**
1. **Context contamination** - extraction window includes multiple case names
2. **Pattern matching failures** - regex isn't finding the right case name
3. **Signal word issues** - "If", "See", etc. not being cleaned
4. **Proximity scoring** - algorithm picking wrong case when multiple are present

---

## Investigation Plan

### Step 1: Debug Oneida Clustering (PRIORITY 1)

Add debug logging to see:
1. What year is extracted for each citation?
2. Are they in the same proximity group?
3. Is parallel detection being called?
4. What is the similarity score and year match result?

### Step 2: Fix Case Name Extraction (PRIORITY 2)

Focus on:
1. "If in Worcester" - Clean leading signal words like "If"
2. "N/A" - Why did extraction completely fail?
3. Wrong case name selection - Improve context isolation

### Step 3: Investigate Flying T Ranch / Quinault Issues (PRIORITY 3)

These seem to be verification or display issues rather than extraction/clustering issues.

---

## Diagnostic Commands

### Check Oneida Citations:
```bash
docker logs casestrainer-rqworker1-prod --tail 3000 | grep -E "562 U.S|131 S. Ct|178 L. Ed"
```

### Check Year Extraction:
```bash
docker logs casestrainer-rqworker1-prod --tail 3000 | grep "VACATUR_YEAR"
```

### Check Clustering Logic:
```bash
docker logs casestrainer-rqworker1-prod --tail 3000 | grep "PARALLEL-MATCH"
```

---

## Next Actions

1. ✅ **Analyze logs** to see what's happening with Oneida citations
2. ❌ **Test year extraction** - verify the fix is actually executing
3. ❌ **Fix clustering** - ensure parallel citations are grouped correctly
4. ❌ **Fix case name extraction** - clean signal words, improve context isolation
5. ❌ **Test comprehensively** - verify all issues are resolved

---

## Status

**Current State:** Multiple clustering and extraction failures  
**Critical Issue:** Oneida citations still not clustering after year extraction fix  
**Impact:** High - affects core functionality of parallel citation detection

**Confidence Level:** LOW - Need to debug to understand why fixes aren't working
