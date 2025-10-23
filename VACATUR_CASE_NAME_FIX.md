# Vacatur Case Name Contamination Fix

## The Problem

**User Report:**
```
Submitted Document: Cayuga Indian Nation v. Seneca County, 2011
Verifying Source: Madison County v. Oneida Indian Nation of N. Y., 2011-01-10
Citations: 562 U.S. 42, 178 L. Ed. 2d 587, 131 S. Ct. 704
```

**The Issue:** The Supreme Court citations (562 U.S. 42, etc.) belong to "Oneida Indian Nation v. Madison County", NOT "Cayuga Indian Nation v. Seneca County".

## Root Cause

**Multiple case names in the same paragraph:**

```text
Other cases specifically discussing tribes hold that tribal sovereign immunity is not waived with respect to real property. See 
Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014) (declining to draw a distinction...); 
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) (a tribe's immunity from suit is independent of its No. 103430-0 14 lands), 
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011);
```

**The extraction logic was:**
1. Using broad context window (300 chars before citation)
2. Finding "Cayuga Indian Nation v. Seneca County" at the beginning of paragraph
3. Incorrectly assigning it to the Supreme Court citations that appear later
4. Ignoring the "vacated and remanded" indicator that signals a different case

## The Solution

### Added Vacatur Pattern Detection

When Supreme Court citations follow "vacated and remanded" (or similar phrases), the system now:

1. **Detects vacatur language** within 300 chars before the citation
2. **Extracts case name** from IMMEDIATELY BEFORE the vacatur phrase
3. **Takes the last match** (closest to vacatur) to avoid contamination from earlier cases

### Implementation Details

**File:** `src/unified_extraction_architecture.py` (lines 851-905)

```python
# USER FIX: Handle "vacated and remanded" pattern
vacatur_patterns = [
    r'vacated\s+and\s+remanded',
    r'vacated',
    r'aff\'d',
    r'affirmed',
    r'reversed',
    r'rev\'d',
    r'remanded'
]

# Look backwards from citation for vacatur language (300 char window)
search_back = text[max(0, start_index - 300):start_index]
for vacatur_pattern in vacatur_patterns:
    vacatur_match = re.search(vacatur_pattern, search_back, re.IGNORECASE)
    if vacatur_match:
        # Found vacatur - extract case name BEFORE it
        text_before_vacatur = search_back[:vacatur_match.start()]
        
        # Pattern: "Plaintiff v. Defendant, 123 F.3d"
        case_name_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*),\s+\d+\s+F\.'
        case_matches = list(re.finditer(case_name_pattern, text_before_vacatur))
        
        if case_matches:
            # Take LAST match (closest to vacatur)
            last_match = case_matches[-1]
            case_name = f"{plaintiff} v. {defendant}"
            return ExtractionResult(
                case_name=case_name,
                confidence=0.98,
                method="vacatur_pattern"
            )
```

## Key Features

1. **300-char search window** - Handles page headers and parentheticals
2. **Multiple vacatur patterns** - Covers "vacated and remanded", "vacated", "aff'd", "affirmed", "reversed", "rev'd", "remanded"
3. **Last match priority** - Takes the case name closest to the vacatur phrase
4. **Federal reporter pattern** - Matches "123 F.3d", "456 F.2d", etc.
5. **Multi-word names** - Handles "Oneida Indian Nation" and "Madison County"
6. **High confidence** - Returns 0.98 confidence when pattern detected

## Expected Behavior

### Before Fix ❌
```
Text: "Cayuga... 761 F.3d 218... Oneida v. Madison, 605 F.3d 149... vacated, 562 U.S. 42"
Result: extracted_case_name = "Cayuga Indian Nation v. Seneca County" (WRONG!)
```

### After Fix ✅
```
Text: "Cayuga... 761 F.3d 218... Oneida v. Madison, 605 F.3d 149... vacated, 562 U.S. 42"
1. Detect "vacated" before 562 U.S. 42
2. Search BEFORE "vacated" for case name
3. Find "Oneida Indian Nation v. Madison County, 605 F.3d 149"
4. Extract "Oneida Indian Nation v. Madison County"
Result: extracted_case_name = "Oneida Indian Nation v. Madison County" (CORRECT!)
```

## Test Case

**Input Text:**
```
Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014) (declining to draw a distinction between in rem and in personam proceedings); 
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) (a tribe's immunity from suit is independent of its No. 103430-0 14 lands), 
vacated and remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)
```

**Expected Results:**
- **761 F.3d 218**: extracted_case_name = "Cayuga Indian Nation v. Seneca County" ✅
- **605 F.3d 149**: extracted_case_name = "Oneida Indian Nation v. Madison County" ✅
- **562 U.S. 42**: extracted_case_name = "Oneida Indian Nation v. Madison County" ✅ (via vacatur pattern)
- **131 S. Ct. 704**: extracted_case_name = "Madison County v. Oneida Indian Nation" ✅ (via parallel clustering)
- **178 L. Ed. 2d 587**: extracted_case_name = "Madison County v. Oneida Indian Nation" ✅ (via parallel clustering)

## Related Patterns

This fix handles several common legal citation patterns:

1. **Vacated and remanded**: `Smith v. Jones, 123 F.3d 456 (2010), vacated, 562 U.S. 789 (2011)`
2. **Affirmed**: `Smith v. Jones, 123 F.3d 456 (2010), aff'd, 562 U.S. 789 (2011)`
3. **Reversed**: `Smith v. Jones, 123 F.3d 456 (2010), rev'd, 562 U.S. 789 (2011)`
4. **Remanded**: `Smith v. Jones, 123 F.3d 456 (2010), remanded, 562 U.S. 789 (2011)`

## Status

✅ **IMPLEMENTED** - Lines 851-905 in `unified_extraction_architecture.py`  
⏱️ **TESTING** - Rebuild in progress, awaiting test results

---

## Impact

This fix prevents case name contamination when:
- Multiple cases appear in the same paragraph
- Supreme Court citations follow appellate decisions
- "Vacated and remanded" (or similar) appears between them
- Page headers interrupt the text flow

**Expected improvement:** Correctly extracts case names for Supreme Court vacatur citations, preventing false attribution to earlier cases in the same paragraph.
