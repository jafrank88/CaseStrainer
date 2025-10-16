# Fix #69: Intelligent Case Name Boundary Detection

**Issue**: Regex patterns start matching at the wrong position (e.g., "E. Palo Alto" instead of "Cmty. Legal Servs. in E. Palo Alto")  
**Root Cause**: Patterns use simple sentence boundary detection (`. [A-Z]`) which fails with legal abbreviations  
**Priority**: HIGH - Affects 72% of citations in inline citation documents  
**Estimated Effort**: 1-2 days  

---

## 🎯 Goal

**Current**: "E. Palo Alto v. U.S." (truncated at 23 chars)  
**Target**: "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs." (full 75+ chars)

**Success Metric**: Increase verification rate from 28% → 55%+ for inline citation documents

---

## 🔍 Problem Analysis

### Why Current Patterns Fail

```python
# Current pattern (PRIORITY 1):
r'(?:(?<=\.)\s+|(?<=\?)\s+|(?<=!)\s+|^)([A-Z][a-zA-Z\s\'&\-\.,]*...)'
```

**Problem**: After finding `. ` (sentence boundary), it matches the FIRST capital letter, which could be:
- `. C` in "Claims. **C**mty." ✓ (correct start)
- `. E` in "Servs. in **E**. Palo Alto" ✗ (wrong start - this is what's happening!)

**Example Context**:
```
"...before the [Court of Federal] Claims.� Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep�t of Health & Hum. Servs., 780 F. Supp. 3d 897..."
                                          ↑ Pattern sees this `. C` but Unicode � confuses it
                                                                      ↑ So it starts here at `. E` instead
```

---

## 🛠️ Solution Strategy

### Three-Tier Approach

1. **Tier 1: Comma-Anchored Extraction** (Most Reliable)
   - Use the comma before the citation as a strong anchor
   - Work backwards from comma to find full case name
   - ~80% of inline citations follow "Case Name, Citation" format

2. **Tier 2: Reverse Citation Search** (Fallback)
   - Start from citation position and search backwards
   - Look for case name pattern ending at citation
   - Handles cases without comma

3. **Tier 3: Enhanced Pattern Matching** (Last Resort)
   - Improved patterns with better boundary detection
   - Multi-token lookahead to avoid abbreviation confusion

---

## 📐 Implementation Design

### Phase 1: Comma-Anchored Extraction (NEW METHOD)

**File**: `src/unified_case_extraction_master.py`  
**New Method**: `_extract_with_comma_anchor()`

```python
def _extract_with_comma_anchor(self, text: str, citation: str, start_index: int, debug: bool) -> Optional[MasterExtractionResult]:
    """
    FIX #69: Extract case name using comma before citation as anchor.
    
    Most inline citations follow format: "Case Name, Citation"
    Example: "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897"
    
    Strategy:
    1. Find comma immediately before citation (within 5 chars)
    2. Work backwards from comma to find case name start
    3. Case name start = after previous sentence boundary OR after previous citation
    
    Args:
        text: Full document text
        citation: Citation string (e.g., "780 F. Supp. 3d 897")
        start_index: Position of citation in text
        debug: Enable debug logging
    
    Returns:
        MasterExtractionResult if extraction succeeds, None otherwise
    """
    # Step 1: Find comma before citation (within 5 chars)
    # Allow for whitespace between comma and citation
    pre_citation_text = text[max(0, start_index - 5):start_index]
    
    if ',' not in pre_citation_text:
        return None  # No comma anchor, fall back to other methods
    
    # Find position of the comma
    comma_pos = start_index - (len(pre_citation_text) - pre_citation_text.rfind(','))
    
    # Step 2: Work backwards from comma to find case name
    # Look for up to 400 chars before comma
    search_start = max(0, comma_pos - 400)
    potential_case_name = text[search_start:comma_pos]
    
    # Step 3: Find the START of the case name
    # Case name starts after:
    # - Previous citation (e.g., "123 F.3d 456")
    # - Sentence boundary followed by capital letter
    # - Quotation mark (")
    # - Parenthesis opening followed by sentence
    
    # Pattern to find case name: 
    # Look for the LAST occurrence of a boundary followed by case name pattern
    case_name_pattern = r'(?:^|[.!?]\s+|"\s*|(?<=\d)\s+)([A-Z][a-zA-Z\s\'&\-\.,]{5,}?\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$'
    
    match = re.search(case_name_pattern, potential_case_name, re.IGNORECASE)
    
    if match:
        case_name = match.group(1).strip()
        
        # Normalize whitespace and clean
        case_name = self._normalize_whitespace_for_extraction(case_name, debug)
        case_name = self._clean_case_name(case_name)
        
        # Extract year from the context after citation
        year_context = text[start_index:start_index + 100]
        year = self._extract_year_from_context(year_context, debug)
        
        if case_name and len(case_name) > 10:
            return MasterExtractionResult(
                case_name=case_name,
                year=year or "N/A",
                confidence=0.9,  # High confidence - comma anchor is reliable
                method="comma_anchored",
                context=f"...{potential_case_name[-100:]}",
                debug_info={"comma_position": comma_pos, "case_name_length": len(case_name)},
                canonical_name=None,
                canonical_year=None,
                extracted_case_name=case_name,
                extracted_year=year,
            )
    
    return None
```

---

### Phase 2: Reverse Citation Search (ENHANCED)

**File**: `src/unified_case_extraction_master.py`  
**Enhanced Method**: `_extract_with_position()` 

**Current Approach**:
```python
# Works forward from sentence boundary
context = text[start_index - 200:start_index]
```

**New Approach**:
```python
# FIX #69: Work backwards from citation to find case name END, then find START

# Step 1: Get large context before citation
context = text[max(0, start_index - 400):start_index]

# Step 2: Normalize whitespace first (Fix #68)
context = self._normalize_whitespace_for_extraction(context, debug)

# Step 3: Use RIGHT-ANCHORED pattern that matches up to the citation
# Instead of: "Find capital letter after period"
# Use: "Find case name that ENDS at citation start"
case_name_pattern = r'([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})(?:,\s*)?$'

match = re.search(case_name_pattern, context)

if match:
    potential_case_name = match.group(1).strip()
    
    # Step 4: Validate it's a real case name (not just any text with "v.")
    if self._looks_like_case_name(potential_case_name):
        return potential_case_name
```

---

### Phase 3: Multi-Token Lookahead (PATTERN ENHANCEMENT)

**File**: `src/unified_case_extraction_master.py`  
**Variable**: `case_name_patterns`

**New Pattern (PRIORITY 0)**: Right-anchored case name before citation

```python
# FIX #69: RIGHT-ANCHORED pattern - match case name that ENDS at citation
# This works backwards from the citation instead of forward from a period
# Matches: "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs.,"
# Before citation: "780 F. Supp. 3d 897"
r'([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})(?:,\s*)?(?=\d+\s+[A-Z])',
```

**New Pattern (PRIORITY 1)**: Multi-abbreviation aware

```python
# FIX #69: Handle multiple abbreviations in case names
# Matches: "Cmty. Legal Servs." (multiple periods, not sentence boundaries)
# Pattern: After real sentence boundary, match multiple abbreviated words
r'(?:^|[.!?]\s+)([A-Z][a-z]+\.\s+(?:[A-Z][a-z]+\.\s+)*[A-Z][a-zA-Z\s\'&\-,]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]+)',
```

**New Helper Method**: `_looks_like_case_name()`

```python
def _looks_like_case_name(self, text: str) -> bool:
    """
    FIX #69: Validate that extracted text looks like a real case name.
    
    Checks:
    1. Contains " v. " (plaintiff v. defendant)
    2. Starts with capital letter
    3. Has reasonable length (10-200 chars)
    4. Doesn't contain obvious contamination
    5. Has proper party name structure
    
    Args:
        text: Potential case name to validate
    
    Returns:
        True if text looks like a case name, False otherwise
    """
    if not text or ' v. ' not in text.lower():
        return False
    
    if len(text) < 10 or len(text) > 200:
        return False
    
    # Check if starts with capital letter
    if not text[0].isupper():
        return False
    
    # Split into plaintiff and defendant
    parts = text.split(' v. ', 1)
    if len(parts) != 2:
        return False
    
    plaintiff, defendant = parts
    
    # Both parts should have at least one word
    if len(plaintiff.strip().split()) < 1 or len(defendant.strip().split()) < 1:
        return False
    
    # Check for obvious contamination
    contamination_indicators = [
        'held that', 'the court', 'established', 'following',
        'citing', 'see also', 'argued that', 'determined',
    ]
    
    text_lower = text.lower()
    if any(indicator in text_lower for indicator in contamination_indicators):
        return False
    
    return True
```

---

### Phase 4: Execution Priority

**Update extraction order** in `extract_case_name()`:

```python
def extract_case_name(self, text: str, citation: Optional[str], start_index: Optional[int], end_index: Optional[int], debug: bool) -> MasterExtractionResult:
    """Extract case name using multi-tier approach."""
    
    # FIX #69: TIER 1 - Comma-anchored extraction (NEW - HIGHEST PRIORITY)
    if citation and start_index is not None:
        result = self._extract_with_comma_anchor(text, citation, start_index, debug)
        if result:
            return result
    
    # TIER 2 - Position-aware extraction (ENHANCED with reverse search)
    if citation and start_index is not None and end_index is not None:
        result = self._extract_with_position(text, citation, start_index, end_index, debug)
        if result:
            return result
    
    # TIER 3 - Citation context extraction (EXISTING)
    if citation:
        result = self._extract_with_citation_context(text, citation, debug)
        if result:
            return result
    
    # TIER 4 - Pattern-based extraction (EXISTING - LAST RESORT)
    result = self._extract_with_patterns(text, citation, debug)
    if result:
        return result
    
    # All methods failed
    return MasterExtractionResult(...)
```

---

## 🧪 Testing Strategy

### Test Cases

**Test 1: Comma-anchored inline citation**
```python
text = "...Claims.� Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep�t of Health & Hum. Servs., 780 F. Supp. 3d 897, 917 (N.D. Cal. 2025)."
citation = "780 F. Supp. 3d 897"
expected = "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs."
```

**Test 2: Multiple abbreviations**
```python
text = "...the court held. Kidwell v. Dep't of Army, Bd. for Corr. of Mil. Recs., 56 F.3d 279, 284 (D.C. Cir. 1995)."
citation = "56 F.3d 279"
expected = "Kidwell v. Dep't of Army, Bd. for Corr. of Mil. Recs."
```

**Test 3: No comma (fallback to reverse search)**
```python
text = "...See Tootle v. Sec'y of Navy 446 F.3d 167, 176 (D.C. Cir. 2006)."
citation = "446 F.3d 167"
expected = "Tootle v. Sec'y of Navy"
```

**Test 4: Abbreviation confusion**
```python
text = "...before the U.S. District Court. E. Palo Alto Cmty. Legal Servs., 123 F.3d 456 (9th Cir. 2020)."
citation = "123 F.3d 456"
expected = "E. Palo Alto Cmty. Legal Servs."  # Should NOT include "District Court"
```

### Unit Test File

**Create**: `test_fix69_case_name_boundaries.py`

```python
#!/usr/bin/env python3
"""Unit tests for Fix #69: Case Name Boundary Detection"""

import sys
sys.path.insert(0, 'src')

from unified_case_extraction_master import UnifiedCaseExtractionMaster

def test_comma_anchored_extraction():
    """Test comma-anchored extraction with inline citations"""
    extractor = UnifiedCaseExtractionMaster()
    
    # Test 1: Full case name with comma
    text = "Claims. Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897"
    result = extractor.extract_case_name(text, "780 F. Supp. 3d 897", text.find("780"), text.find("897") + 3, debug=True)
    
    assert "Cmty. Legal Servs. in E. Palo Alto" in result.case_name
    assert "Health" in result.case_name or "Hum. Servs." in result.case_name
    print(f"✓ Test 1 PASSED: '{result.case_name}'")

def test_multiple_abbreviations():
    """Test extraction with multiple abbreviated words"""
    extractor = UnifiedCaseExtractionMaster()
    
    text = "held. Kidwell v. Dep't of Army, Bd. for Corr. of Mil. Recs., 56 F.3d 279"
    result = extractor.extract_case_name(text, "56 F.3d 279", text.find("56"), text.find("279") + 3, debug=True)
    
    assert "Kidwell v. Dep't" in result.case_name
    print(f"✓ Test 2 PASSED: '{result.case_name}'")

def test_no_comma_fallback():
    """Test fallback when no comma present"""
    extractor = UnifiedCaseExtractionMaster()
    
    text = "See Tootle v. Sec'y of Navy 446 F.3d 167"
    result = extractor.extract_case_name(text, "446 F.3d 167", text.find("446"), text.find("167") + 3, debug=True)
    
    assert "Tootle v. Sec'y" in result.case_name or "Tootle v. Secretary" in result.case_name
    print(f"✓ Test 3 PASSED: '{result.case_name}'")

if __name__ == "__main__":
    print("Testing Fix #69: Case Name Boundary Detection\n")
    test_comma_anchored_extraction()
    test_multiple_abbreviations()
    test_no_comma_fallback()
    print("\n✅ All tests passed!")
```

---

## 📅 Implementation Schedule

### Day 1: Core Implementation
- **Morning** (4 hours):
  - Implement `_extract_with_comma_anchor()` method
  - Implement `_looks_like_case_name()` helper
  - Update extraction priority order
  
- **Afternoon** (4 hours):
  - Enhance `_extract_with_position()` with reverse search
  - Add new right-anchored patterns
  - Write unit tests

### Day 2: Testing & Refinement
- **Morning** (4 hours):
  - Run unit tests
  - Test with 25-2808.pdf
  - Test with WA briefs (comparison)
  
- **Afternoon** (4 hours):
  - Fix edge cases discovered in testing
  - Optimize pattern performance
  - Update documentation
  - Deploy to production

---

## 📊 Expected Results

### Before Fix #69
```
25-2808.pdf Results:
- Citations: 43
- Verified: 12 (28%)
- Truncated names: 25 (58%)

Examples:
- "E. Palo Alto v. U." (should be "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs.")
- "Tootle v. Se" (should be "Tootle v. Sec'y of Navy")
- "Kidwell v. Dep" (should be "Kidwell v. Dep't of Army")
```

### After Fix #69
```
25-2808.pdf Results (PROJECTED):
- Citations: 43
- Verified: 24-28 (55-65%)
- Truncated names: 5-10 (12-23%)

Examples:
- "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs." ✓
- "Tootle v. Sec'y of Navy" ✓
- "Kidwell v. Dep't of Army, Bd. for Corr. of Mil. Recs." ✓
```

**Improvement**: +27-37 percentage points in verification rate

---

## ⚠️ Risks & Mitigation

### Risk 1: Greedy Matching May Capture Too Much
**Mitigation**: Use `_looks_like_case_name()` validation to reject over-captures

### Risk 2: Performance Impact (More Processing)
**Mitigation**: Comma-anchored method is fast; only try expensive methods as fallback

### Risk 3: Breaking Existing Extractions
**Mitigation**: Run full test suite with WA briefs before deployment

### Risk 4: Edge Cases with Special Formatting
**Mitigation**: Comprehensive unit tests covering various citation formats

---

## 🎯 Success Criteria

1. ✅ 25-2808.pdf verification rate increases from 28% → 55%+
2. ✅ Case name truncation reduces from 58% → <20%
3. ✅ No regressions in WA briefs test suite (maintain 100% cluster accuracy)
4. ✅ Unit tests pass with 100% coverage
5. ✅ Processing time increases by <20%

---

## 📚 Documentation Updates

### Files to Update
1. **FIX_69_IMPLEMENTATION_PLAN.md** (this file) → Mark complete
2. **FINAL_SESSION_SUMMARY.md** → Add Fix #69 summary
3. **ANALYSIS_25_2808_ISSUES.md** → Update with resolution
4. **Code comments** → Add Fix #69 markers

### New Files to Create
1. **test_fix69_case_name_boundaries.py** → Unit tests
2. **FIX_69_RESULTS.md** → Test results and comparison

---

## 🚀 Deployment Plan

1. **Commit Fix #69 changes** to local repository
2. **Test locally** with unit tests
3. **Test with 25-2808.pdf** via API
4. **Compare with WA briefs** (regression test)
5. **Deploy to production** (backend restart)
6. **Monitor logs** for 24 hours
7. **Update documentation**

---

## 📝 Code Review Checklist

- [ ] `_extract_with_comma_anchor()` handles edge cases
- [ ] `_looks_like_case_name()` validation is comprehensive
- [ ] Right-anchored patterns don't cause catastrophic backtracking
- [ ] Whitespace normalization (Fix #68) is applied before matching
- [ ] Unicode artifacts (Fix #68B) are handled
- [ ] Debug logging is comprehensive
- [ ] Error handling for malformed citations
- [ ] Performance profiling shows acceptable impact
- [ ] Unit tests cover all code paths
- [ ] Documentation is complete and accurate

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Next Step**: Begin Day 1 implementation  
**Owner**: AI Assistant  
**Reviewer**: User (jafrank)



