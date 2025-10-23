# Debug Plan: Vacatur Pattern Detection

## Problem

The vacatur pattern fix (lines 851-905 in `unified_extraction_architecture.py`) was implemented but **isn't working**. The system is still incorrectly extracting case names when multiple cases appear in the same paragraph.

**Example:**
```
Cayuga Indian Nation v. Seneca County, 761 F.3d 218 (2014)...
Oneida Indian Nation v. Madison County, 605 F.3d 149 (2010)... 
vacated and remanded, 562 U.S. 42 (2011)
```

- ❌ **Current**: 562 U.S. 42 extracts as "Cayuga" (WRONG!)
- ✅ **Expected**: 562 U.S. 42 should extract as "Oneida" (CORRECT!)

---

## Debug Strategy

### Phase 1: Enable Debug Logging ✅

Added comprehensive debug logging to understand execution flow:

#### 1. Vacatur Pattern Detection (`unified_extraction_architecture.py`)

**Lines 868-875**: Check if vacatur patterns are being detected
```python
if debug:
    logger.warning(f"🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '{citation}'")
    logger.warning(f"🔍 VACATUR_DEBUG: Search window ({len(search_back)} chars): '{search_back[-200:]}'")
    logger.warning(f"🔍 VACATUR_DEBUG: Pattern '{vacatur_pattern}' -> {'FOUND' if vacatur_match else 'NOT FOUND'}")
```

**Lines 888-893**: Check if case name pattern is matching
```python
if debug:
    logger.warning(f"🔍 VACATUR_DEBUG: Found {len(case_matches)} case name matches before vacatur")
    if case_matches:
        for i, match in enumerate(case_matches):
            logger.warning(f"🔍 VACATUR_DEBUG: Match {i+1}: '{match.group(0)}'")
    logger.warning(f"🔍 VACATUR_DEBUG: Text before vacatur ({len(text_before_vacatur)} chars): '{text_before_vacatur[-200:]}'")
```

#### 2. Enable Debug Mode for Supreme Court Citations

Modified 4 extraction call sites in `unified_citation_processor_v2.py`:

**Line 1656-1658**: Fallback extraction
```python
# USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
if citation_text and (' U.S. ' in citation_text or ' S. Ct. ' in citation_text or ' L. Ed. ' in citation_text):
    force_debug = True
```

**Line 1786-1787**: Context extraction
```python
# USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
force_debug = citation_text and (' U.S. ' in citation_text or ' S. Ct. ' in citation_text or ' L. Ed. ' in citation_text)
```

**Line 2115-2117**: Date extraction
```python
# USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
citation_text = citation.citation
force_debug = citation_text and (' U.S. ' in citation_text or ' S. Ct. ' in citation_text or ' L. Ed. ' in citation_text)
```

**Line 3692-3693**: Master extractor
```python
# USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
force_debug = citation_text and (' U.S. ' in citation_text or ' S. Ct. ' in citation_text or ' L. Ed. ' in citation_text)
```

---

## Expected Debug Output

When processing "562 U.S. 42" with the test text, we should see:

### If Pattern Detection Works:
```
🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '562 U.S. 42'
🔍 VACATUR_DEBUG: Search window (300 chars): '... Oneida v. Madison, 605 F.3d 149 ... vacated and remanded, '
🔍 VACATUR_DEBUG: Pattern 'vacated\s+and\s+remanded' -> FOUND
🔍 VACATUR_DEBUG: Found 1 case name matches before vacatur
🔍 VACATUR_DEBUG: Match 1: 'Oneida Indian Nation v. Madison County, 605 F.3d'
✅ VACATUR_DETECTED: Found 'vacated\s+and\s+remanded' before citation
✅ VACATUR_CASE: Extracted 'Oneida Indian Nation v. Madison County' from text before vacatur
```

### If Pattern Doesn't Match:
```
🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '562 U.S. 42'
🔍 VACATUR_DEBUG: Search window (300 chars): '...'
🔍 VACATUR_DEBUG: Pattern 'vacated\s+and\s+remanded' -> NOT FOUND
🔍 VACATUR_DEBUG: Pattern 'vacated' -> NOT FOUND
...
```

### If Vacatur Found But Case Name Pattern Fails:
```
🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '562 U.S. 42'
🔍 VACATUR_DEBUG: Pattern 'vacated\s+and\s+remanded' -> FOUND
🔍 VACATUR_DEBUG: Found 0 case name matches before vacatur
🔍 VACATUR_DEBUG: Text before vacatur (xxx chars): '...'
🔍 VACATUR_SKIP: Found 'vacated\s+and\s+remanded' but couldn't extract case name before it
```

---

## Phase 2: Analyze Debug Output (After Testing)

Once we test with "562 U.S. 42", we'll analyze the logs to determine:

1. **Is the vacatur pattern detection code being called at all?**
   - If no debug output → Code isn't being executed (bypassed by earlier extraction)
   - If debug output → Continue to step 2

2. **Is "vacated and remanded" being detected?**
   - If NOT FOUND → Check if text contains the phrase, adjust pattern/window
   - If FOUND → Continue to step 3

3. **Is the case name pattern matching?**
   - If 0 matches → Regex pattern needs adjustment
   - If 1+ matches → Continue to step 4

4. **Is the extracted case name being returned?**
   - If yes but still wrong result → Result is being overridden later
   - If no → Validation failing or error in logic

---

## Phase 3: Fix Based on Diagnosis

Based on what we find, we'll implement one of these fixes:

### Fix A: Pattern Not Matching
Adjust regex pattern to handle the actual text format

### Fix B: Code Not Being Called
Move vacatur detection earlier in execution flow

### Fix C: Result Being Overridden
Increase confidence score or add explicit priority flag

### Fix D: Window Too Small
Increase search_back window size beyond 300 chars

---

## Test Case

**Input Text:**
```
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) 
(a tribe's immunity from suit is independent of its No. 103430-0 14 lands), 
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)
```

**Test Citations:**
- 562 U.S. 42
- 131 S. Ct. 704
- 178 L. Ed. 2d 587

**Expected Result:**
All three should extract "Oneida Indian Nation v. Madison County" (or "Madison County v. Oneida Indian Nation" after reversal)

---

## Files Modified

1. **`unified_extraction_architecture.py`** (lines 868-893): Added debug logging to vacatur detection
2. **`unified_citation_processor_v2.py`** (4 locations): Enabled debug for U.S. Reports citations

---

## Next Steps

1. ✅ Rebuild application with debug logging
2. ⏳ Test with "562 U.S. 42" citation
3. ⏳ Check Docker logs for debug output
4. ⏳ Analyze which phase is failing
5. ⏳ Implement appropriate fix

---

## Status

✅ **Phase 1 Complete** - Debug logging added  
⏱️ **Rebuild in progress** - Deploying changes  
⏳ **Phase 2 Pending** - Awaiting test results
