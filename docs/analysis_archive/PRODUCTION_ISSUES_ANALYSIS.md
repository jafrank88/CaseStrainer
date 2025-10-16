# Production Issues Analysis
## Critical Bugs Found in Live System

## Date: 2025-10-09
## Document Tested: 1033940.pdf (Branson v. Wash. Fine Wine & Spirits, LLC opinion)

---

## 🚨 CRITICAL ISSUE #1: VERIFICATION API RETURNING WRONG CASES

### Problem
CourtListener verification is matching citations to the **wrong cases**, including matching to the opinion being read itself.

### Example 1: "199 Wn.2d 528"

**What's in the Document**:
```
State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022)
```

**What Production Shows**:
- Canonical Name: "Branson v. Wash. Fine Wine & Spirits, LLC"
- Canonical Date: "2025-09-04"

**Problem**: "Branson" is the OPINION WE'RE READING, not the case being cited! The API is incorrectly matching "199 Wn.2d 528" to Branson instead of to State v. M.Y.G.

### Example 2: "509 P.3d 818"

**What's in the Document**:
```
State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022)
```

**What Production Shows**:
- Canonical Name: "Jeffery Moore v. Equitrans, L.P."
- Canonical Date: "2022-02-23"

**Problem**: This is a completely different case from 2022 with the same Pacific reporter citation.

### Root Cause
The CourtListener API is probably:
1. Returning multiple matches for volume/reporter/page combinations
2. The system is picking the FIRST match instead of the CORRECT match
3. Or the API itself is fuzzy-matching incorrectly

### Impact
- Users get completely wrong canonical case names
- Citations verify as "correct" but point to wrong cases
- Legal research becomes unreliable

### Solution Required
1. Improve cluster matching in `src/unified_verification_master.py` `_find_matching_cluster()` method
2. Add validation to reject matches where the canonical name doesn't match the extracted name
3. Consider using case name + date + citation together for verification
4. Log warnings when canonical and extracted names differ significantly

---

## 🚨 CRITICAL ISSUE #2: CASE NAME EXTRACTION - PARENTHETICAL CONTAMINATION

### Problem
When a citation appears in text with a parenthetical citation immediately after it, the extractor captures the parenthetical case name instead of the main case name.

### Example: "199 Wn.2d 528" and "509 P.3d 818"

**Document Context**:
```
State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) 
(quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991))
```

**What Gets Extracted**:
- extracted_case_name: "Am. Legion Post No. 32 v. City of Walla Walla"

**What SHOULD Be Extracted**:
- extracted_case_name: "State v. M.Y.G."

### Why This Happens
The case name extractor in `src/services/citation_extractor.py`:
1. Searches **backwards** from the citation position
2. Looks for pattern: `Name v. Name` before the citation
3. But in this case, "Am. Legion..." appears in text AFTER the citation in a parenthetical
4. The extractor likely finds it because it's more "complete" or the search window extends too far

### Root Cause
The `_extract_case_name_from_context()` method:
- Line 495: `start_search = max(0, citation.start_index - 200)`
- This 200-char window includes the parenthetical that comes AFTER the citation
- Needs logic to:
  - Stop at opening parentheses before the citation
  - Prefer case names that appear ON THE SAME LINE as the citation
  - Ignore case names that appear inside parentheticals

### Solution Required
In `src/services/citation_extractor.py` `_extract_case_name_from_context()`:

```python
# Stop at parenthetical boundaries
search_text = text[start_search:citation.start_index]

# Remove any parenthetical content from search text
search_text = re.sub(r'\([^)]*\)', '', search_text)

# Now search for case name in cleaned text
```

---

## 🚨 CRITICAL ISSUE #3: WRONG DATES IN CANONICAL FIELDS

### Problem
Canonical dates are showing as full dates (YYYY-MM-DD) from wrong cases.

### Examples
- "199 Wn.2d 528" shows canonical date: "2025-09-04"
  - Document shows: 2022
  - This might be Branson's filing date, not M.Y.G.'s date

### Root Cause
Related to Issue #1 - because the API is returning the wrong case, it's also returning that case's date.

### Solution
Fix Issue #1 (verification matching)

---

## ⚠️ ISSUE #4: "(Unknown)" DESPITE HAVING DATES

### Problem
The frontend displays:
```
Verifying Source: Branson v. Wash. Fine Wine & Spirits, LLC, 2025-09-04 (Unknown)
```

The date "2025-09-04" is present but then marked as "(Unknown)".

### Root Cause
This is likely a frontend display issue where:
- The canonical_date field has a value
- But some other field (maybe a "court" or "source" field) is "Unknown"
- The "(Unknown)" label is displaying incorrectly

### Impact
LOW - Cosmetic issue, doesn't affect data accuracy

### Solution
Check frontend code in `casestrainer-vue-new/src/components/CitationResults.vue` to see what the "(Unknown)" refers to.

---

## ✅ WHAT'S WORKING

### 1. Clustering Proximity Fix
- ✅ Citations 27,000+ chars apart are NO LONGER grouped together
- ✅ Maximum cluster span: 277 characters
- ✅ Validation layer working correctly

### 2. Data Separation in Final Output
- ✅ `extracted_case_name` and `canonical_name` are in separate fields
- ✅ No mixing of extracted and canonical data in the JSON structure
- ✅ The fix in `unified_citation_processor_v2.py` is working

### 3. Some Verifications Are Correct
**Example: "182 Wn.2d 342"**
- Document: "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd., 182 Wn.2d 342"
- Canonical: "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board"
- ✅ This verification is CORRECT!

So the verification CAN work, but it's failing on some citations.

---

## PRIORITY FIXES NEEDED

### Priority 1: Fix Case Name Extraction (CRITICAL)
**File**: `src/services/citation_extractor.py`
**Method**: `_extract_case_name_from_context()`

**Changes needed**:
1. Add logic to strip parentheticals from search text
2. Prefer case names that appear BEFORE the citation, not after
3. Add distance weighting - prefer case names closer to citation
4. Check that extracted case name appears in same sentence as citation

### Priority 2: Fix Verification Matching (CRITICAL)
**File**: `src/unified_verification_master.py`
**Method**: `_find_matching_cluster()`

**Changes needed**:
1. Add validation: Reject matches where canonical_name significantly differs from extracted_name
2. Use case name similarity scoring to pick best match from multiple results
3. Add logging when rejecting matches
4. Consider using multiple verification sources when CourtListener gives suspicious results

### Priority 3: Add Validation Layer for Verification Results (HIGH)
**File**: `src/unified_citation_processor_v2.py` or new validation module

**Changes needed**:
1. After verification, compare extracted_case_name to canonical_name
2. If similarity < 50%, log warning and mark as "uncertain verification"
3. If similarity < 20%, reject the verification result entirely
4. Flag cases where canonical_date differs from extracted_date by > 2 years

---

## TESTING RECOMMENDATIONS

### Test Case 1: Parenthetical Citations
Document: 1033940.pdf, Citation: "199 Wn.2d 528"
- Expected extracted: "State v. M.Y.G."
- Expected canonical: "State v. M.Y.G." (not "Branson")

### Test Case 2: Multiple Same-Reporter Citations
Verify that citations with same Pacific reporter volume are matched to correct cases.

### Test Case 3: Opinion Self-References
Ensure that citations in an opinion don't verify to the opinion itself.

---

## SUMMARY

**Fixed in this session:**
- ✅ Clustering proximity bug (27,000 char spans eliminated)
- ✅ Data separation in final output
- ✅ WL citation extraction

**Still Broken:**
- ❌ Case name extraction (parenthetical contamination)
- ❌ Verification matching wrong cases
- ❌ Canonical dates from wrong cases

**Impact**: The system is MUCH better than before (no catastrophic clustering errors), but case name extraction and verification matching need immediate attention to ensure accuracy.

