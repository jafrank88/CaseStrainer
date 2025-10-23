# Date Extraction Improvement Plan

## Problem
Many citations have extracted case names but NO extracted dates, even when verified with CourtListener.

### Examples from Production:
```
181 Wn.2d 272 - Case: "Mgmt., LLC v. Nooksack Bus. Corp." - Date: [EMPTY]
436 U.S. 49 - Case: "Santa Clara Pueblo v. Martinez" - Date: [EMPTY]
```

But these ARE verified, meaning CourtListener returned `canonical_date`!

## Root Causes

### 1. Table of Authorities Format
```
Santa Clara Pueblo v. Martinez, 436 U.S. 49................ 15
```
No `(YYYY)` nearby → Date extraction fails

### 2. Eyecite Database Gaps
Eyecite doesn't have years for all citations (especially state reporters)

### 3. Context Window Too Small
Current: 100 chars before, 300 chars after
Problem: Year might be further away in dense text

### 4. NOT Using CourtListener Dates
When citations are **verified**, CourtListener returns `canonical_date` (e.g., "1978-05-15")
BUT we're not copying this to `extracted_date`!

## Solutions

### **Solution 1: Use Canonical Dates (EASY, HIGH IMPACT)** ✅

Add to clustering/verification step:

```python
# After verification, if we have canonical_date but no extracted_date:
if citation.canonical_date and not citation.extracted_date:
    # Extract year from "1978-05-15" format
    year = citation.canonical_date.split('-')[0]
    citation.extracted_date = year
    logger.info(f"[DATE-FROM-CANONICAL] Used canonical date for {citation.citation}: {year}")
```

**Impact:** 
- **95+ verified citations would get dates!**
- Zero performance cost
- Works for ALL CourtListener-verified citations

### **Solution 2: Date Propagation (Like Name Propagation)** 

Similar to name propagation, propagate dates within parallel citation groups:

```python
# In _share_names_in_citation_groups():
if best_date and not cit.extracted_date:
    cit.extracted_date = best_date
```

**Impact:**
- Parallel citations share dates
- Example: If "584 U.S. 554" has (2018), then "138 S. Ct. 1649" also gets 2018

### **Solution 3: Expand Search Window**

Change from:
```python
search_start = max(0, citation.start_index - 100)
search_end = min(len(text), citation.end_index + 300)
```

To:
```python
search_start = max(0, citation.start_index - 200)
search_end = min(len(text), citation.end_index + 500)
```

**Impact:**
- Finds dates that are further away
- Small performance cost

### **Solution 4: Add Verification Date Pattern**

Many PDFs have: `"(decided May 15, 1978)"` or `"(1978 decision)"`

Add pattern:
```python
# Strategy 5: Look for decision/decided with year
year_match = re.search(r'\b(?:decided|decision|filed|decided)\s+.*?(\d{4})\b', after_context[:200], re.IGNORECASE)
```

## Recommended Implementation Order

1. **Solution 1 first** (canonical dates) - Easiest, highest impact
2. **Solution 2** (date propagation) - Complements solution 1
3. **Solution 3** (expand window) - If still needed after 1 & 2
4. **Solution 4** (new patterns) - Low priority, edge cases

## Implementation

### Where to Add Solution 1:

**File:** `src/unified_clustering_master.py` or wherever clustering happens after verification

```python
def _enrich_citations_with_canonical_dates(self, citations: List[CitationResult]) -> None:
    """Copy canonical dates to extracted dates when available."""
    for citation in citations:
        if citation.canonical_date and not citation.extracted_date:
            try:
                # Extract year from ISO date format "1978-05-15"
                year = citation.canonical_date.split('-')[0]
                if year and 1700 <= int(year) <= 2030:
                    citation.extracted_date = year
                    logger.info(f"[DATE-FROM-CANONICAL] {citation.citation} → {year}")
            except Exception as e:
                logger.warning(f"[DATE-FROM-CANONICAL] Failed for {citation.citation}: {e}")
```

Call this after verification completes.

## Expected Results

**Before:**
- 115 citations total
- ~20-30 with extracted_date
- ~95 verified but missing extracted_date

**After Solution 1:**
- 115 citations total  
- ~95 with extracted_date (from canonical_date)
- ~10-15 unverified still missing dates (expected)

This would reduce missing dates from **~83%** to **~13%**!
