# Case Name Extraction Improvements

## Core Principle
**Keep extracted names and canonical names completely separate** - Never use canonical names as fallbacks for extracted names. This separation is essential for detecting typos and hallucinations.

---

## Current Issues

### Issue 1: Too Many "N/A" Results
Many citations show `extracted_case_name = "N/A"` when extraction should succeed.

**Root Causes**:
1. **Contamination detection too aggressive** - Rejects legitimate citations
2. **Extraction patterns fail** - Complex case names don't match regex patterns
3. **Context window too small** - Case name appears outside lookback window
4. **Header detection too strict** - Legitimate names rejected as headers
5. **Validation too strict** - Valid names rejected by validation rules

---

## Recommended Improvements

### 1. Improve Contamination Detection

**Current Problem**: `_is_document_case_contamination()` rejects if EITHER plaintiff OR defendant matches. This is too aggressive.

**File**: `src/utils/unified_case_name_extractor.py` lines 268-282

**Suggested Fix**:
```python
# Strategy 2: Check if extracted name contains primary case's distinctive parts
primary_parts = primary_normalized.split(' v ')
if len(primary_parts) == 2:
    plaintiff = primary_parts[0].strip()
    defendant = primary_parts[1].strip()
    
    # CHANGE: Require BOTH parties to match, not just one
    # This reduces false positives while still catching contamination
    if plaintiff and defendant:
        plaintiff_match = plaintiff in extracted_normalized
        defendant_match = defendant in extracted_normalized
        
        # Only reject if BOTH match (stronger contamination signal)
        if plaintiff_match and defendant_match:
            logger.warning(f"[CONTAMINATION-FILTER] Both parties match: '{extracted_name}' matches '{document_primary_case_name}'")
            return True
        
        # Also reject if extracted name exactly matches primary (even if only one party)
        if extracted_normalized == primary_normalized:
            logger.warning(f"[CONTAMINATION-FILTER] Exact match: '{extracted_name}' == '{document_primary_case_name}'")
            return True
```

**Additional Improvements**:
- Add similarity threshold (e.g., 80% match required)
- Check if citation is in citation context (parentheticals, string citations) - less likely to be contamination

---

### 2. Improve Extraction Pattern Matching

**Current Problem**: Complex case names with long party descriptions don't match current patterns.

**File**: `src/utils/strict_context_isolator.py` lines 737-763

**Current Patterns**: Already has good patterns, but might need:
- Better handling of multi-line case names
- Better handling of case names with multiple parties separated by semicolons
- Better handling of case names with parenthetical descriptions

**Suggested Improvements**:
- Add pattern for case names with "by and through" (guardians, executors)
- Add pattern for case names with "d/b/a" (doing business as)
- Improve handling of corporate suffixes (LLC, Inc., Corp., etc.)

---

### 3. Expand Context Window Adaptively

**Current Problem**: `max_lookback=300` might not be enough for some citations.

**File**: `src/utils/unified_case_name_extractor.py` line 75

**Current**: Fixed `max_lookback=300`

**Suggested**: Use adaptive expansion - start with 300, expand if no match found:
```python
# Try increasing context windows if extraction fails
for lookback in [300, 400, 500, 600]:
    adaptive_context = get_adaptive_context_for_citation(
        text, citation_start, citation_end, all_positions, 
        max_lookback=lookback
    )
    case_name = extract_case_name_from_strict_context(adaptive_context, citation_text)
    if case_name:
        break  # Found it, stop expanding
```

---

### 4. Improve Header Pattern Detection

**Current Problem**: Legitimate case names with "et al." are rejected if role words appear nearby.

**File**: `src/utils/unified_case_name_extractor.py` lines 86-94

**Current Logic**: Rejects if name contains "ET AL" + role word OR role word + "NO"

**Suggested Improvement**: Check context, not just name:
```python
# Only reject if it's clearly a header pattern
# Allow "Smith et al. v. Jones" (legitimate case name)
# Reject "ET AL., Petitioners v. Respondent" (header)

# Check if "et al." appears WITH role word in same phrase
header_pattern = re.search(
    r'ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b',
    case_name_upper
)
if header_pattern:
    # This is a header, reject
    logger.warning(f"[UNIFIED-EXTRACT-FINAL-REJECT] Header pattern detected")
    case_name = None
else:
    # "et al." without role word is legitimate (e.g., "Smith et al. v. Jones")
    # Allow it
    pass
```

---

### 5. Improve Validation Logic

**Current Problem**: Validation might reject valid short case names or unusual formats.

**File**: `src/case_name_validator.py` lines 18-59

**Current**: `min_length=5`, requires "v." or special case pattern

**Suggested Improvements**:
- Lower minimum length to 3 for very short case names
- Improve detection of "v." with various spacing/formatting
- Add more special case patterns (e.g., "Ex parte", "State ex rel.")

---

### 6. Add Better Diagnostic Logging

**Current Problem**: Hard to debug why extraction fails.

**Suggested**: Add detailed logging at each step:
```python
logger.info(f"[EXTRACT-DEBUG] Citation: {citation_text}")
logger.info(f"[EXTRACT-DEBUG] Context window: {len(context)} chars")
logger.info(f"[EXTRACT-DEBUG] Patterns tried: {patterns_tried}")
logger.info(f"[EXTRACT-DEBUG] Matches found: {matches_found}")
logger.info(f"[EXTRACT-DEBUG] Validation result: {validation_result}")
logger.info(f"[EXTRACT-DEBUG] Contamination check: {contamination_result}")
logger.info(f"[EXTRACT-DEBUG] Final result: {case_name or 'N/A'}")
```

---

### 7. Try Multiple Extraction Methods

**Current Problem**: If strict isolation fails, immediately sets to "N/A".

**File**: `src/unified_citation_processor_v2.py` lines 1456-1579

**Current Flow**:
1. Try strict isolation → if fails → set to "N/A"

**Suggested Flow**:
1. Try strict isolation
2. If fails → Try broader context window
3. If fails → Try alternative extraction patterns
4. If fails → Try citation-only extraction (extract from citation text itself)
5. If all fail → Set to "N/A"

---

## Implementation Priority

1. **High Priority**:
   - Improve contamination detection (require both parties match)
   - Add diagnostic logging
   - Try multiple extraction methods before giving up

2. **Medium Priority**:
   - Expand context window adaptively
   - Improve header pattern detection
   - Improve validation logic

3. **Low Priority**:
   - Add more extraction patterns
   - Improve handling of special case formats

---

## Testing

After implementing improvements, test with:
- Document: `1031351.pdf`
- Check reduction in "N/A" results
- Verify no false positives (legitimate names rejected)
- Verify no cross-contamination (extracted names stay separate from canonical)




