# Remaining Clustering Issues - Analysis

## Issue #1: Burlington Northern Still Wrong ❌ CRITICAL

```
Canonical: Burlington Northern & Santa Fe Railway Co. v. Abc-Naco, 2009
Extracted: Marakova v. United States, 2002

Citations:
- 389 Ill. App. 3d 691 (Verified)
- 2002 WY 183 (Verified)  
- 906 N.E.2d 83 (Verified)
```

**Problem**: Completely different cases, different years (2009 vs 2002), still grouped together!

**Why My Fix Didn't Work**:
- My validation checks extracted names
- But "Marakova v. United States" WAS extracted correctly
- The problem: Burlington Northern canonical name came from VERIFICATION, not extraction
- So when citations verified as "Burlington Northern", that canonical name got assigned
- But the extracted name stayed "Marakova"

**Root Cause**: Verification is OVERWRITING correct extracted names with wrong canonical names!

---

## Issue #2: Too Many N/A Extractions ❌

These citations have NO extracted name but HAVE canonical names:

```
Singh v. Edwards Lifesciences Corp., 2009-07-06
Extracted: N/A, 2011
- 151 Wn. App. 137 (Verified)
- 210 P.3d 337 (Verified)

Erwin v. Cotter Health Centers, Inc., 2007-09-20
Extracted: N/A, 2007
- 161 Wn.2d 676 (Verified)
- 167 P.3d 1112 (Verified)

Richardson v. Pacific Power & Light Co., 1941-11-21
Extracted: N/A, 1941
- 11 Wn.2d 288 (Verified)
- 118 P.2d 985 (Verified)
```

**Problem**: Extraction failed (N/A) but verification succeeded

**Why This Happens**:
1. Citation appears WITHOUT case name in document (e.g., just "161 Wn.2d 676")
2. Extraction finds N/A (no case name nearby)
3. Verification looks up in CourtListener and finds case
4. System displays canonical name from verification

**Is This Wrong?** NO - This is CORRECT behavior when citations lack case names in document

---

## Issue #3: Wrong Name-Year Grouping ❌

```
Kammerer v. Western Gear Corp., 1981-10-29
Extracted: Kammerer v. W. Gear Corp, 1980
- 618 P.2d 1330 (Verified)
- 879 F. Supp. 2d 1214 (Verified)
- 96 Wn.2d 692 (Verified)
```

**Problem**: 879 F. Supp. 2d 1214 is NOT Kammerer (1980)!
- F. Supp. 2d didn't exist in 1980 (started in 1998)
- This citation is from a DIFFERENT case

**Root Cause**: Name-year-window grouping is grouping citations between a case name and year
- But it's catching citations that just HAPPEN to be in that text range
- They're not actually parallel citations!

---

## Issue #4: Wrong Date Clustering ❌

```
Kammerer v. Western Gear Corp., 1981-01-07
Extracted: Bradshaw v. Deming, 1980
- 27 Wn. App. 512 (Verified)
```

**Problem**: Canonical date is 1981, extracted date is 1980, extracted NAME is "Bradshaw v. Deming"!
- These are THREE DIFFERENT THINGS all wrong
- Kammerer ≠ Bradshaw (different cases)
- 1981 ≠ 1980 (different years)

---

## Issue #5: Contaminated Extractions ❌

```
BMW of North America, Inc. v. Gore, 1996-05-28
Extracted: State v. Johnson, 1996
- 517 U.S. 559 (Verified)
```

**Problem**: Extraction found "State v. Johnson" but verification found "BMW v. Gore"
- 517 U.S. 559 IS BMW v. Gore (verification correct)
- But extraction picked up wrong case name from nearby text

**Root Cause**: Context contamination - case name bleeding from adjacent citations

---

## Summary of Root Causes

### 1. **Verification Contamination** (MOST CRITICAL)
When verification succeeds but finds WRONG case:
- Wrong canonical name gets assigned to cluster
- Correct extracted name gets flagged as "different"
- Example: Burlington Northern canonical assigned to Marakova citations

### 2. **Name-Year-Window Grouping Too Aggressive**
Groups ALL citations between a case name and a year:
- But some citations in that range are actually DIFFERENT cases
- Example: "Kammerer... 618 P.2d 1330... 879 F. Supp. 2d 1214... (1980)"
  - Both citations grouped as Kammerer
  - But F. Supp. 2d citation is from a different case!

### 3. **Context Contamination**
Extraction picks up wrong case name from nearby text:
- Example: BMW v. Gore citation near "State v. Johnson" text
- Extraction grabs "State v. Johnson" instead of "BMW v. Gore"

### 4. **Cross-Citation Bleeding**
When multiple citations appear close together:
- First citation's case name "bleeds" into second citation's context
- Second citation gets wrong extracted name

---

## Proposed Fixes

### Fix #1: Disable Name-Year-Window Grouping (IMMEDIATE) ⚠️

**File**: `src/unified_clustering_master.py` lines 451-461

**Current Code**:
```python
# USER FIX 2024-11-07: Group all citations between case name and year
remaining = [citation for citation in citations if id(citation) not in processed_ids]
if remaining:
    nyw_groups = self._group_by_name_year_window(remaining, text)
    for group in nyw_groups:
        if len(group) >= 2:
            logger.info(f"[NAME-YEAR-WINDOW] Found {len(group)} citations in same window")
            parallel_groups.append(group)
            for citation in group:
                processed_ids.add(id(citation))
```

**Problem**: This groups citations that just HAPPEN to be between a case name and year
- But they may be citations to DIFFERENT cases
- Example: "Kammerer... 618 P.2d 1330... 879 F. Supp. 2d 1214... (1980)"
  - Both get grouped as Kammerer
  - But F. Supp. 2d citation is likely a different case (reporter didn't exist in 1980!)

**Proposed Fix**: DISABLE this grouping method entirely (comment it out)

---

### Fix #2: Add Reporter-Date Validation

**Problem**: 879 F. Supp. 2d 1214 cannot be from 1980 (F. Supp. 2d started in 1998)

**Solution**: Check if reporter series existed in the claimed year

```python
def _reporter_valid_for_year(self, reporter: str, year: int) -> bool:
    """Check if a reporter series existed in the given year."""
    
    reporter_start_years = {
        'F. Supp. 2d': 1998,
        'F. Supp. 3d': 2014,
        'F.3d': 1993,
        'F.2d': 1924,
        'P.3d': 2000,
        'P.2d': 1931,
        'Wn.2d': 1939,
        'Wn. App. 2d': 2016,
        # Add more...
    }
    
    if reporter in reporter_start_years:
        if year < reporter_start_years[reporter]:
            return False  # Reporter didn't exist yet!
    
    return True
```

---

### Fix #3: Stricter Proximity Validation

**Problem**: Citations grouped by proximity even when they're different cases

**Solution**: Require BOTH proximity AND name similarity

```python
# In _group_by_proximity():
if distance <= self.proximity_threshold:
    # NEW: Also check if extracted names are similar
    name1 = getattr(previous_citation, 'extracted_case_name', None)
    name2 = getattr(current_citation, 'extracted_case_name', None)
    
    if name1 and name2 and name1 != 'N/A' and name2 != 'N/A':
        # Check similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        
        if similarity < 0.6:
            # Names too different - don't group despite proximity!
            logger.warning(f"[PROXIMITY] NOT grouping despite distance={distance}: names too different ({similarity:.2%})")
            groups.append(current_group)
            current_group = [current_citation]
            continue
    
    # OK to group
    current_group.append(current_citation)
```

---

### Fix #4: Don't Overwrite Good Extracted Names

**Problem**: When verification finds a case, it overwrites the extracted name
- But extracted name may be CORRECT and canonical may be WRONG

**Solution**: Keep extracted name, only ADD canonical data (don't overwrite)

```python
# In verification logic:
if verification_result:
    # DON'T overwrite extracted_case_name
    # Only set canonical fields
    citation.canonical_name = verification_result.name
    citation.canonical_date = verification_result.date
    citation.canonical_url = verification_result.url
    
    # Keep the extracted_case_name as-is!
    # Don't do: citation.extracted_case_name = verification_result.name
```

---

### Fix #5: Validate Verification Results

**Problem**: Verification may return WRONG case if query is ambiguous

**Solution**: Check if verification result matches extracted data

```python
def _validate_verification_result(self, citation, verification_result):
    """Check if verification result makes sense for this citation."""
    
    # If we have an extracted name, check if it matches verification
    if citation.extracted_case_name and citation.extracted_case_name != 'N/A':
        extracted = citation.extracted_case_name.lower()
        canonical = verification_result.name.lower()
        
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, extracted, canonical).ratio()
        
        if similarity < 0.5:  # Less than 50% similar
            logger.warning(f"[VERIFICATION-MISMATCH] Extracted '{citation.extracted_case_name}' "
                         f"but verified as '{verification_result.name}' (similarity: {similarity:.2%})")
            logger.warning(f"[VERIFICATION-MISMATCH] REJECTING verification result - likely wrong case!")
            return False  # Reject this verification
    
    # Check if reporter/year make sense
    citation_year = extract_year(citation.citation)
    verified_year = extract_year(verification_result.date)
    
    if abs(citation_year - verified_year) > 2:
        logger.warning(f"[VERIFICATION-MISMATCH] Citation appears to be from {citation_year} "
                     f"but verification says {verified_year}")
        return False
    
    return True  # Verification looks good
```

---

## Recommended Action Plan

### Priority 1: Disable Name-Year-Window Grouping (5 mins)
Comment out the aggressive grouping method that's causing most problems

### Priority 2: Add Proximity Name Validation (15 mins)
Require name similarity before grouping citations by proximity

### Priority 3: Add Reporter-Year Validation (20 mins)
Reject groupings where reporter couldn't exist in claimed year

### Priority 4: Protect Extracted Names (10 mins)
Don't let verification overwrite good extracted names

### Priority 5: Validate Verification Results (30 mins)
Check if verification makes sense before accepting it

---

## Expected Impact

**Before Fixes**: ~40 name mismatches
**After Fix #1-2**: ~20 name mismatches (50% reduction)
**After Fix #3-5**: ~10 name mismatches (75% reduction)

Remaining mismatches will be legitimate (abbreviations, etc.)
