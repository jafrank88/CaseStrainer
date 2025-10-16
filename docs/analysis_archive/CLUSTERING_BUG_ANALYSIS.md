# Critical Clustering Bug Analysis
## Document: 1033940.pdf (Branson v. Wash. Fine Wine & Spirits, LLC opinion)

## Executive Summary

The production system is incorrectly grouping **FOUR DIFFERENT CASES** into a single cluster, showing contaminated case names and phantom citations. This analysis identifies the root causes.

---

## The Problematic Cluster (from user's production output)

```
Verifying Source: Branson v. Wash. Fine Wine & Spirits, LLC, 2025-09-04 (Unknown)
Submitted Document: American Legion Post No. 32 v. City of Walla Walla, 2022
Citation 1: 199 Wash.2d 528 [Verified]
Citation 2: 2024 WL 4678268 [Verified]
Citation 3: 2024 WL 3199858 [Verified]
Citation 4: 2024 WL 2133370 [Verified]
```

---

## What's Actually in the Document

### Citation 1: "199 Wn.2d 528"
**Location**: Position 9660  
**Context**: `State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022)`  
**Correct Case**: State v. M.Y.G. (2022)  
**Note**: Written as "**Wn.2d**" not "**Wash.2d**"

### Citation 2: "2024 WL 4678268"  
**Location**: Position 37242  
**Context**: `Wright v. HP Inc., No. 2:24-cv-01261-MJP, 2024 WL 4678268 (W.D. Wash. Nov. 5, 2024)`  
**Correct Case**: Wright v. HP Inc. (2024)

### Citation 3: "2024 WL 3199858"  
**Location**: Position 37126  
**Context**: `Floyd v. Insight Glob. LLC, No. 23-cv-1680-BJR, 2024 WL 2133370, at *8 (W.D. Wash. May 10, 2024) (court order), amended on reconsideration, 2024 WL 3199858 (W.D. Wash. June 26, 2024)`  
**Correct Case**: Floyd v. Insight Glob. LLC (2024) - amended order

### Citation 4: "2024 WL 2133370"  
**Location**: Position 37029  
**Context**: `Floyd v. Insight Glob. LLC, No. 23-cv-1680-BJR, 2024 WL 2133370, at *8 (W.D. Wash. May 10, 2024)`  
**Correct Case**: Floyd v. Insight Glob. LLC (2024) - original order

### "American Legion Post No. 32" Reference
**Location**: Position 9799 (RIGHT NEXT TO Citation 1)  
**Context**: Appears in the same sentence as "199 Wn.2d 528" as a cited case

---

## Critical Problems Identified

### Problem 1: **Incorrect Proximity-Based Clustering**
- **Citation 1** (pos 9660) and **Citation 2** (pos 37242) are **27,582 characters apart**
- That's approximately **275 lines** or **13 pages** apart
- Default proximity threshold: **200 characters**
- Distance exceeds threshold by: **137x**

**Why they're being clustered together**: Unknown - this should NEVER happen with proper proximity checking.

### Problem 2: **Reporter Normalization Issue**
- Document has: **"199 Wn.2d 528"** (Washington Reports, Second Series)
- System displays: **"199 Wash.2d 528"** (different abbreviation)
- These may be getting treated as the same citation, but the normalization is incorrect

### Problem 3: **Case Name Contamination**
- **Extracted case name shown**: "American Legion Post No. 32 v. City of Walla Walla"
- **Actual case for Citation 1**: "State v. M.Y.G."
- **Why contaminated**: "American Legion" appears in the document RIGHT NEXT TO Citation 1 as a parenthetical citation, not the main case name

### Problem 4: **Verification Returning Wrong Case**
- **Citation**: "199 Wn.2d 528"
- **Should verify to**: State v. M.Y.G., 2 Wash.3d 528, 509 P.3d 818 (2022)
- **Appears to verify to**: Branson v. Wash. Fine Wine & Spirits, LLC (according to user output)

---

## Root Causes

### 1. **Clustering Logic Flaw** (`src/unified_clustering_master.py`)

**Line 515-525**: Case name similarity check bypasses proximity check:
```python
if case_name1 and case_name2 and case_name1 != 'N/A' and case_name2 != 'N/A':
    similarity = self._calculate_name_similarity(case_name1, case_name2)
    if similarity >= 0.8:
        return True  # ⚠️ Returns TRUE WITHOUT checking proximity!
```

**Issue**: If two citations have similar case names (>= 0.8 similarity), they're considered parallel citations **even if they're 27,000 characters apart**. This check happens **before** the proximity check at line 552.

### 2. **Case Name Extraction Capturing Parentheticals**

The case name extractor is capturing "American Legion Post No. 32 v. City of Walla Walla" because it appears in the same context as the citation, but it's actually a **parenthetical citation** (a case cited within another case's opinion), not the main case name.

**Context from document**:
```
State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) 
(quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991))
```

The system should extract "State v. M.Y.G." but is extracting "Am. Legion Post No. 32 v. City of Walla Walla" instead.

### 3. **WL Citations Not Extracted Locally**

The local `CitationExtractor` regex patterns don't include Westlaw (WL) citations. Production likely uses:
- eyecite library (extracts WL citations)
- OR different regex patterns
- These citations then get verified and clustered with unrelated citations

### 4. **Potential Verification API Issue**

If "199 Wn.2d 528" is verifying to "Branson" instead of "State v. M.Y.G.", either:
- CourtListener API is returning incorrect data
- OR the verification code is matching the wrong cluster from the API response

---

## Recommended Fixes

### Fix 1: **Move Proximity Check Before Case Name Similarity**

In `src/unified_clustering_master.py`, around line 515:

```python
# Check proximity in text FIRST
def get_start_index(cit: Any) -> int:
    if isinstance(cit, dict):
        return cit.get('start_index', cit.get('start', 0))
    return getattr(cit, 'start_index', getattr(cit, 'start', 0))

start1 = get_start_index(citation1)
start2 = get_start_index(citation2)
distance = abs(start1 - start2)

# Adjust proximity threshold based on citation types
proximity_threshold = self.proximity_threshold
if 'U.S.' in citation1_text or 'U.S.' in citation2_text:
    proximity_threshold = max(proximity_threshold, 500)
    
if distance > proximity_threshold:
    if self.debug_mode:
        logger.debug(
            "PARALLEL_CHECK rejected by proximity | distance=%s threshold=%s",
            distance,
            proximity_threshold,
        )
    return False  # ✅ Reject immediately if too far apart

# THEN check case name similarity as fallback
case_name1 = self._get_case_name(citation1)
case_name2 = self._get_case_name(citation2)

if case_name1 and case_name2 and case_name1 != 'N/A' and case_name2 != 'N/A':
    similarity = self._calculate_name_similarity(case_name1, case_name2)
    if similarity >= 0.8:
        return True
```

### Fix 2: **Improve Case Name Extraction to Exclude Parentheticals**

In `src/services/citation_extractor.py`, the case name extraction should:
1. Look for the case name **immediately before** the citation (within 50 chars)
2. Stop if it encounters a parenthesis that starts a parenthetical citation
3. Prefer case names that appear on the same line as the citation

### Fix 3: **Add WL Citation Patterns to Local Extractor**

Add regex patterns for Westlaw citations to `src/services/citation_extractor.py`:
```python
# Westlaw citations: YYYY WL #######
re.compile(r'\b(\d{4}\s+WL\s+\d+)\b', re.IGNORECASE)
```

### Fix 4: **Verify Citation Normalization**

Ensure "Wn.2d" and "Wash.2d" are normalized consistently:
- "Wn.2d" = Washington Reports, Second Series (official reporter)
- "Wash.2d" = Same reporter, different abbreviation style
- These should be treated as equivalent

### Fix 5: **Add Cluster Validation**

Before finalizing clusters, validate:
1. All citations in a cluster are within proximity threshold
2. All citations have consistent case names
3. If case names differ significantly, log a warning

---

## Testing Recommendations

1. **Unit test**: Citations > proximity_threshold should NEVER cluster
2. **Integration test**: Verify "199 Wn.2d 528" clusters separately from "2024 WL 4678268"
3. **Case name test**: Ensure parenthetical citations don't contaminate extracted names
4. **Verification test**: Confirm "199 Wn.2d 528" verifies to "State v. M.Y.G." not "Branson"

---

## Summary

The system is grouping **4 different cases** into 1 cluster due to:
1. ❌ Case name similarity check bypassing proximity validation
2. ❌ Incorrect case name extraction (capturing parenthetical citations)
3. ❌ Missing WL citation extraction in local processing
4. ❌ Possible verification API data confusion

**Impact**: High - Users see completely incorrect clustering results with contaminated case names and phantom citations.

**Priority**: Critical - This affects the core accuracy of the citation extraction system.

