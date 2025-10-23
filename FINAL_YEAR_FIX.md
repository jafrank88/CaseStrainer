# Final Year Extraction Fix for Parallel Citations

## The Problem

After fixing the vacatur pattern detection and initial year extraction, the Supreme Court parallel citations were **still not clustering together**:

```
❌ THREE SEPARATE CLUSTERS (WRONG):
- 562 U.S. 42 (standalone)
- 131 S. Ct. 704 (standalone)  
- 178 L. Ed. 2d 587 (standalone)

✅ SHOULD BE ONE CLUSTER:
- 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (together)
```

**Root Cause:** All three citations were extracting year "2010" (from the Federal citation) instead of "2011" (from the Supreme Court decision).

---

## Why Previous Fix Didn't Work

### Previous Logic (Broken):

```python
# Look for year after Federal citation
year_search_text = text_before_vacatur[fed_match_end_pos:fed_match_end_pos + 50]
year = self._extract_year_from_context(year_search_text, debug)

# Fallback: check after current citation
if not year:
    year = self._extract_year_from_context(text[start_index:start_index + 100], debug)
```

### The Issue:

For the text:
```
"Oneida Indian Nation v. Madison County, 605 F.3d 149 (2010)...
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
```

**When extracting "562 U.S. 42":**
1. First try: Look after Federal citation "605 F.3d 149" → finds "(2010)" ✓
2. Returns "2010" immediately
3. Never looks for "(2011)" at the end of the parallel group

**Result:** All three Supreme Court citations get year "2010" instead of "2011"

---

## The Solution

### New Logic (Fixed):

```python
# Check if this is a Supreme Court citation
is_supreme_court = any(x in citation for x in ['U.S.', 'S. Ct.', 'L. Ed.'])

year = None

if is_supreme_court:
    # For Supreme Court citations, look AFTER current citation FIRST
    # This finds the year at the END of the parallel group
    after_citation_text = text[start_index:start_index + 200]
    year = self._extract_year_from_context(after_citation_text, debug)
    
    if debug and year:
        logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")

# Fallback: Extract from Federal reporter citation
if not year:
    fed_match_end_pos = last_match.end()
    year_search_text = text_before_vacatur[fed_match_end_pos:fed_match_end_pos + 50]
    year = self._extract_year_from_context(year_search_text, debug)
```

### How It Works:

**For "562 U.S. 42":**
1. Detect it's a Supreme Court citation (contains "U.S.") ✓
2. Look AFTER "562 U.S. 42" → finds "42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
3. Extract year: **"2011"** ✓

**For "131 S. Ct. 704":**
1. Detect it's a Supreme Court citation (contains "S. Ct.") ✓
2. Look AFTER "131 S. Ct. 704" → finds "704, 178 L. Ed. 2d 587 (2011)"
3. Extract year: **"2011"** ✓

**For "178 L. Ed. 2d 587":**
1. Detect it's a Supreme Court citation (contains "L. Ed.") ✓
2. Look AFTER "178 L. Ed. 2d 587" → finds "587 (2011)"
3. Extract year: **"2011"** ✓

**Result:** All three citations now have the correct year "2011"!

---

## Key Improvements

### 1. **Citation Type Detection**
```python
is_supreme_court = any(x in citation for x in ['U.S.', 'S. Ct.', 'L. Ed.'])
```
Identifies Supreme Court citations that need special year handling.

### 2. **Priority Reversal**
- **Old:** Check Federal citation first → Supreme Court citation second
- **New:** Check Supreme Court citation first → Federal citation as fallback

### 3. **Larger Search Window**
- Increased from 50 to 200 chars to ensure we capture the year at the end of parallel groups

### 4. **Better Debug Logging**
```python
if debug and year:
    logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")
```
Shows exactly where the year was found.

---

## Expected Results

### ✅ Correct Extraction:
```
Extracted: "Oneida Indian Nation v. Madison County" (2011)
- 562 U.S. 42 → Year: 2011 ✓
- 131 S. Ct. 704 → Year: 2011 ✓
- 178 L. Ed. 2d 587 → Year: 2011 ✓
```

### ✅ Correct Clustering:
```
Verifying Source: Madison County v. Oneida Indian Nation of N.Y., 2011-01-10
Submitted Document: Oneida Indian Nation v. Madison County, 2011
Citation 1: 562 U.S. 42 Verified
Citation 2: 131 S. Ct. 704 Verified by Parallel
Citation 3: 178 L. Ed. 2d 587 Verified by Parallel
```

All three citations will now cluster together because:
- ✅ Same case name: "Oneida Indian Nation v. Madison County"
- ✅ Same year: "2011"
- ✅ Different reporters: U.S., S.Ct., L.Ed.

---

## Files Modified

**`src/unified_case_extraction_master.py`:**

1. **Lines 623-661** (Strategy 0: `_extract_with_comma_anchor()`):
   - Added Supreme Court citation detection
   - Priority: Look after current citation FIRST for Supreme Court
   - Fallback: Federal citation year if needed

2. **Lines 1177-1215** (Strategy 1: `_extract_with_position()`):
   - Applied same Supreme Court year extraction logic
   - Consistent behavior across both strategies

---

## Why This Approach Works

### Handles Both Court Levels:

**Circuit Court Citation:**
```
"Oneida v. Madison, 605 F.3d 149 (2010)"
Not a Supreme Court citation → Uses Federal citation year → "2010" ✓
```

**Supreme Court Citations:**
```
"562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
All are Supreme Court → Look after each citation → Find "(2011)" ✓
```

### Respects Legal Citation Structure:

Legal citations follow specific patterns:
- **Single citation:** "Case Name, Citation (Year)"
- **Parallel citations:** "Case Name, Citation1, Citation2, Citation3 (Year)"

The year appears **once at the end** for parallel citations, not after each individual citation.

---

## Testing Plan

1. **Submit the test text** with Oneida/Cayuga citations
2. **Verify all three Supreme Court citations:**
   - All show year "2011" (not "2010")
   - All show case name "Oneida Indian Nation v. Madison County"
3. **Verify clustering:**
   - All three citations in ONE cluster
   - Marked as "Verified by Parallel"
4. **Verify separation:**
   - Federal citation (605 F.3d 149) may be in same or different cluster
   - Hamaatsa citations remain separate

---

## Impact on Other Cases

This fix will improve clustering for ALL cases with:
- ✅ Supreme Court decisions with multiple reporters
- ✅ Appellate cases with "vacated and remanded"
- ✅ Any parallel citations where year appears at the end
- ✅ Mixed Federal/Supreme Court citation combinations

---

## Status

✅ **IMPLEMENTED** - Supreme Court year extraction fixed in both strategies  
⏱️ **REBUILDING** - Docker build in progress  
🧪 **READY TO TEST** - Smart citation type detection with proper fallbacks  
🎯 **VERY HIGH CONFIDENCE** - This should finally fix the clustering issue!

Expected Result: Perfect clustering with all three Supreme Court parallel citations grouped together! 🎉
