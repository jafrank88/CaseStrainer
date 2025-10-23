# Clustering Fix: Year Extraction for Vacatur Cases

## The Problem

After fixing the vacatur pattern detection (extracting "Oneida" instead of "Cayuga"), a **new clustering issue** appeared:

```
❌ WRONG CLUSTER:
Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, Unknown  ← Missing year!
Citation 1: 562 U.S. 42 Verified
Citation 2: 2017-NM-007 Verified by Parallel  ← WRONG! (Hamaatsa case)
Citation 3: 388 P.3d 977 Verified by Parallel  ← WRONG! (Hamaatsa case)

✅ CORRECT CLUSTER (separate):
Verifying Source: Oneida Indian Nation of NY v. Madison County, 2010-04-27
Submitted Document: Oneida Indian Nation v. Madison County, 2010
Citation 1: 605 F.3d 149 Verified
Citation 2: 178 L. Ed. 2d 587 Verified  ← Should be with 562 U.S. 42!
Citation 3: 131 S. Ct. 704 Verified  ← Should be with 562 U.S. 42!
```

**The Issue:** "562 U.S. 42" was being clustered with Hamaatsa citations instead of its actual parallel citations "131 S. Ct. 704" and "178 L. Ed. 2d 587".

---

## Root Cause Analysis

### Why Did This Happen?

The clustering logic requires **BOTH case name AND year** to match for parallel citations (lines 564-572 in `unified_clustering_master.py`):

```python
# Check case name similarity
similarity = self._calculate_name_similarity(case_names[i], case_names[j])

# NEW: Also check year similarity
year_match = False
if case_years[i] and case_years[j]:
    year_match = case_years[i] == case_years[j]

# USER FIX: If names are highly similar (>80%) AND years match, they're parallel!
if similarity >= 0.80 and year_match:
    return True
```

### The Bug

The vacatur fix was extracting the year from **the wrong location**:

**OLD CODE (BROKEN):**
```python
# Line 623 (Strategy 0) and Line 1165 (Strategy 1)
year = self._extract_year_from_context(text[start_index:start_index + 50], debug)
```

This looked for the year in the 50 characters **AFTER** the citation starts.

**The Problem:**

For the text:
```
"...Oneida Indian Nation v. Madison County, 605 F.3d 149 (2010)...
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
```

- The Federal citation has year: "605 F.3d 149 **(2010)**"
- The Supreme Court citations have year at the END: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 **(2011)**"

When extracting "562 U.S. 42":
- `text[start_index:start_index + 50]` = "562 U.S. 42, 131 S. Ct. 704, 178..."
- **No year found!** ❌
- Result: `year = "Unknown"`

Without a year, the parallel citation detection fails because it requires BOTH name AND year to match.

---

## The Solution

Extract the year from the **Federal reporter citation** where the case name was found, not from after the current Supreme Court citation:

### NEW CODE (FIXED):

**Strategy 0 (Lines 623-639):**
```python
# USER FIX: Extract year from the Federal reporter match (includes year in parens)
# Example: "Oneida v. Madison, 605 F.3d 149 (2010)"
fed_match_text = last_match.group(0)
fed_match_end_pos = last_match.end()

# Look for year in parentheses after the Federal citation
# Search in the next 50 chars after the matched Federal citation
year_search_text = text_before_vacatur[fed_match_end_pos:fed_match_end_pos + 50]
year = self._extract_year_from_context(year_search_text, debug)

# Fallback: check after current citation position
if not year:
    year = self._extract_year_from_context(text[start_index:start_index + 100], debug)

if debug:
    logger.warning(f"🔍 VACATUR_YEAR: Extracted year '{year}' for '{vacatur_case_name}'")
```

**Strategy 1 (Lines 1165-1179):**
```python
# Same logic applied to _extract_with_position() method
```

### Why This Works:

1. The case name comes from: "Oneida Indian Nation v. Madison County, **605 F.3d 149** (2010)"
2. We extract the year from **after the Federal citation**: "(2010)"
3. Now "562 U.S. 42" has:
   - Case name: "Oneida Indian Nation v. Madison County" ✅
   - Year: "2010" (or "2011" from the parallel group) ✅
4. The parallel citations "131 S. Ct. 704" and "178 L. Ed. 2d 587" will have the same name and year
5. Clustering logic matches them: name similarity > 80% AND year matches ✅

---

## Expected Results After Fix

### ✅ CORRECT CLUSTERING:

```
Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, 2011  ← Year now present!
Citation 1: 562 U.S. 42 Verified
Citation 2: 131 S. Ct. 704 Verified by Parallel  ← Correctly grouped!
Citation 3: 178 L. Ed. 2d 587 Verified by Parallel  ← Correctly grouped!
```

The Hamaatsa citations ("2017-NM-007" and "388 P.3d 977") will remain in their own separate cluster where they belong.

---

## Files Modified

**`src/unified_case_extraction_master.py`:**

1. **Lines 623-639** (Strategy 0: `_extract_with_comma_anchor()`):
   - Fixed year extraction to look at Federal citation location
   - Added fallback year search
   - Added debug logging for year extraction

2. **Lines 1165-1179** (Strategy 1: `_extract_with_position()`):
   - Applied the same year extraction fix
   - Consistent year extraction logic across both strategies

---

## Technical Details

### Year Extraction Logic:

```
Text: "...Oneida v. Madison, 605 F.3d 149 (2010)...vacated and remanded, 562 U.S. 42..."
                                               ↑
                                          Fed match ends here
                                               ↓
                                         year_search_text = " (2010)...vacated"
                                                            ↑
                                                    Extract year: "2010"
```

### Why Both Strategies?

The extraction uses TWO strategies in order:
1. **Strategy 0**: `_extract_with_comma_anchor()` - Runs FIRST (most common)
2. **Strategy 1**: `_extract_with_position()` - Runs as backup

Both needed the fix to ensure consistent year extraction regardless of which strategy runs.

---

## Testing Plan

1. **Submit the test text** with Oneida/Cayuga citations
2. **Verify clustering**:
   - "562 U.S. 42" should cluster with "131 S. Ct. 704" and "178 L. Ed. 2d 587"
   - All three should show year "2010" or "2011" (consistent within cluster)
3. **Verify separation**:
   - Hamaatsa citations should remain in their own cluster
   - No cross-contamination between different cases

---

## Related Issues Fixed

This fix also resolves clustering issues for ANY vacatur cases where:
- The year appears at the end of multiple parallel citations
- The vacatur pattern is detected
- Multiple reporters (U.S., S.Ct., L.Ed.) are present

Examples:
- Supreme Court vacatur of Circuit Court decisions
- Appellate court affirmations with multiple reporters
- Any case with "vacated and remanded, [Citation1], [Citation2], [Citation3] (Year)"

---

## Status

✅ **IMPLEMENTED** - Year extraction fixed in both strategies  
⏱️ **REBUILDING** - Docker build in progress  
🧪 **READY TO TEST** - Comprehensive fix with fallbacks and debug logging  
🎯 **HIGH CONFIDENCE** - Addresses root cause of clustering mismatch

Expected Result: Perfect clustering with all parallel citations grouped correctly! 🎉
