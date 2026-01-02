# Suggested Fixes - Prioritized by Impact

## P0 - Critical Fixes (Fix Immediately)

### 1. Fix Case Name Bleeding/Cross-Contamination ⚠️ CRITICAL

**Problem**: Extracted names are picking up wrong case names from nearby citations.

**Examples**:
- `Erickson v. Pharmacia LLC, 1980` → Extracted: `Env't Def. Fund, Inc. v. Env't Prot. Agency, 1980` ❌
- `Rice v. Dow Chemical Co., 1994` → Extracted: `Erickson v. Pharmacia, 1994` ❌
- `State v. Copeland, 1996` → Extracted: `Frye rulings de novo. L.M. v. Hamilton, 1996` ❌

**Root Cause**: Strict context isolation boundaries are not working correctly.

**Suggested Fixes**:

#### A. Improve Citation Boundary Detection
**File**: `src/utils/strict_context_isolator.py`

**Current**: Uses citation positions to find boundaries, but may miss some citations.

**Fix**:
```python
def find_all_citation_positions(text: str) -> List[Tuple[int, int, str]]:
    """
    Find ALL citation positions with better pattern matching.
    Should catch citations that might be missed by eyecite.
    """
    # Add more citation patterns to catch edge cases
    # Better handling of WL citations, parallel citations, etc.
```

#### B. Validate Extracted Name Appears Before Citation
**File**: `src/utils/strict_context_isolator.py` → `extract_case_name_from_strict_context()`

**Fix**: After extracting a case name, verify it appears BEFORE the citation in the text:
```python
def extract_case_name_from_strict_context(context: str, citation_text: str, citation_start: int, text: str) -> Optional[str]:
    case_name = extract_case_name_from_strict_context(context, citation_text)
    
    if case_name:
        # CRITICAL: Verify case name appears BEFORE citation, not after
        case_name_pos = text.rfind(case_name, 0, citation_start)
        if case_name_pos == -1:
            # Case name not found before citation - might be from wrong citation
            logger.warning(f"[BOUNDARY-CHECK] Case name '{case_name}' not found before citation '{citation_text}' - rejecting")
            return None
    
    return case_name
```

#### C. Prevent Cross-Citation Contamination
**File**: `src/utils/strict_context_isolator.py` → `get_strict_context_for_citation()`

**Fix**: Ensure context window doesn't include other citations:
```python
def get_strict_context_for_citation(
    text: str,
    citation_start: int,
    citation_end: int,
    all_citation_positions: List[Tuple[int, int, str]],
    max_lookback: int = 300
) -> str:
    # Find the closest citation BEFORE this one
    closest_before = None
    for cit_start, cit_end, cit_text in all_citation_positions:
        if cit_end < citation_start:
            if closest_before is None or cit_end > closest_before[1]:
                closest_before = (cit_start, cit_end, cit_text)
    
    # Start context AFTER the previous citation ends
    if closest_before:
        context_start = max(0, closest_before[1])
    else:
        context_start = max(0, citation_start - max_lookback)
    
    context = text[context_start:citation_start]
    return context
```

---

### 2. Fix Legal Text Contamination in Extracted Names

**Problem**: Extracted names contain legal analysis text.

**Examples**:
- `State v. Copeland, 1996` → Extracted: `Frye rulings de novo. L.M. v. Hamilton, 1996` ❌
- `State v. Cauthron, 1993` → Extracted: `Frye hearing. State v. Copeland, 1993` ❌
- `Stojkovic v. Weller, 1991` → Extracted: `WPLA claim. Call v. Heard, 1991` ❌

**Suggested Fixes**:

#### A. Better Signal Phrase Removal
**File**: `src/utils/strict_context_isolator.py` → `extract_case_name_from_strict_context()`

**Current**: Removes some signal phrases, but misses many.

**Fix**: Add more comprehensive signal phrase patterns:
```python
signal_phrase_patterns = [
    # Legal analysis phrases
    r'^(?:Frye|Daubert|Kumho)\s+(?:rulings?|hearings?|standards?|tests?)\s+(?:de\s+novo|review|analysis)\.?\s*',
    r'^(?:WPLA|WCPA|RCW|ER|FRCP|FRCivP)\s+(?:claim|rule|statute|evidence)\.?\s*',
    r'^We\s+(?:review|hold|conclude|determine|find|affirm|reverse|remand)\.?\s*',
    r'^(?:The\s+)?(?:court|trial\s+court|appellate\s+court)\s+(?:held|found|ruled|determined)\.?\s*',
    r'^(?:Under|Pursuant\s+to|According\s+to|In\s+accordance\s+with)\s+',
    # Citation signals
    r'^See,?\s+e\.?g\.?\s*,?\s*',
    r'^See\s+also\s+',
    r'^See\s+generally\s+',
    r'^But\s+see\s+',
    r'^Cf\.?\s+',
    # Procedural phrases
    r'^(?:In|On|For)\s+(?:appeal|review|certiorari|remand)\.?\s*',
]
```

#### B. Sentence Boundary Detection
**File**: `src/utils/strict_context_isolator.py`

**Fix**: Only extract case names from the sentence immediately before the citation:
```python
def extract_case_name_from_strict_context(context: str, citation_text: str) -> Optional[str]:
    # Split context into sentences
    sentences = re.split(r'[.!?]\s+(?=[A-Z])', context)
    
    # Only look at the last sentence (closest to citation)
    if sentences:
        last_sentence = sentences[-1].strip()
        # Extract from last sentence only
        case_name = extract_from_sentence(last_sentence, citation_text)
        return case_name
    
    return None
```

#### C. Validate Extracted Names Don't Contain Legal Text
**File**: `src/case_name_validator.py`

**Fix**: Add validation to reject names containing legal analysis:
```python
def is_valid_case_name(case_name: Optional[str], min_length: int = 5) -> bool:
    # ... existing checks ...
    
    # Reject if contains legal analysis phrases
    legal_phrases = [
        'rulings de novo', 'hearing', 'standard', 'test', 'review',
        'claim', 'statute', 'rule', 'evidence', 'court held', 'court found',
        'we review', 'we hold', 'we conclude', 'under', 'pursuant to'
    ]
    
    case_lower = case_name.lower()
    for phrase in legal_phrases:
        if phrase in case_lower:
            logger.debug(f"Rejected: Contains legal phrase '{phrase}': '{case_name}'")
            return False
    
    return True
```

---

## P1 - High Priority Fixes (Fix Soon)

### 3. Improve Extraction Success Rate (Reduce "N/A" Results)

**Problem**: Many citations show "N/A" as extracted name.

**Suggested Fixes**:

#### A. Expand Context Window Adaptively
**File**: `src/utils/unified_case_name_extractor.py`

**Current**: Fixed `max_lookback=300`

**Fix**: Try increasing context windows if extraction fails:
```python
def extract_case_name_with_strict_isolation(...):
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

#### B. Try Multiple Extraction Patterns
**File**: `src/utils/strict_context_isolator.py`

**Current**: Tries patterns in order, stops at first match.

**Fix**: Try all patterns, pick the best match:
```python
def extract_case_name_from_strict_context(context: str, citation_text: str) -> Optional[str]:
    all_matches = []
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        for match in matches:
            # Score each match (closer to citation = better)
            distance_from_end = len(context) - match.end()
            score = 1.0 / (1.0 + distance_from_end / 100.0)  # Closer = higher score
            all_matches.append((match, score))
    
    if all_matches:
        # Pick match closest to citation (highest score)
        best_match = max(all_matches, key=lambda x: x[1])
        return extract_case_name_from_match(best_match[0])
    
    return None
```

#### C. Better Handling of Complex Case Names
**File**: `src/utils/strict_context_isolator.py`

**Fix**: Add patterns for complex case names:
- Multi-party cases: "A, B, and C v. D"
- Cases with "by and through": "X by and through Y v. Z"
- Cases with "d/b/a": "X d/b/a Y v. Z"
- Long party descriptions

---

### 4. Improve Date Extraction

**Problem**: Some citations have wrong extracted dates.

**Examples**:
- `Neah Bay Fish Co. v. Krummel, 1940` → Extracted: `N/A, 1976` ❌

**Suggested Fixes**:

#### A. Better Date Pattern Matching
**File**: `src/unified_citation_processor_v2.py` → `_extract_date_from_context()`

**Fix**: Look for dates in multiple formats near the citation:
```python
def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
    # Look for dates in various formats:
    # - (2006)
    # - , 2006
    # - 2006 WL
    # - 2006 F.2d
    # - etc.
    
    # Search in context window around citation
    start = max(0, citation.start_index - 200)
    end = min(len(text), citation.end_index + 50)
    context = text[start:end]
    
    # Try multiple date patterns
    date_patterns = [
        r'\((\d{4})\)',  # (2006)
        r',\s*(\d{4})\s',  # , 2006
        r'\b(\d{4})\s+(?:WL|F\.|P\.|S\.|U\.S\.)',  # 2006 WL, 2006 F.2d
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, context)
        if matches:
            # Use the date closest to the citation
            return matches[-1]  # Last match is closest to citation
    
    return None
```

#### B. Validate Date Makes Sense
**Fix**: Check that extracted date is reasonable:
```python
def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
    year = extract_year_from_context(text, citation)
    
    if year:
        # Validate year is reasonable (between 1600 and current year + 1)
        current_year = datetime.now().year
        if 1600 <= int(year) <= current_year + 1:
            return year
        else:
            logger.warning(f"Rejected unreasonable year: {year}")
            return None
    
    return None
```

---

## P2 - Medium Priority Fixes (Fix When Possible)

### 5. Improve Clustering Logic

**Problem**: Some citations are being clustered incorrectly.

**Suggested Fixes**:

#### A. Better Parallel Citation Detection
**File**: `src/unified_clustering_master.py`

**Fix**: Improve detection of parallel citations that appear close together:
```python
def _are_citations_parallel_pair(self, cit1: Any, cit2: Any, text: str) -> bool:
    # Check if citations appear close together in text
    pos1 = getattr(cit1, 'start_index', None)
    pos2 = getattr(cit2, 'start_index', None)
    
    if pos1 and pos2:
        distance = abs(pos1 - pos2)
        if distance < 100:  # Citations within 100 chars are likely parallel
            # Additional checks: same case name pattern, same year, etc.
            return True
    
    return False
```

#### B. Better Case Name Matching for Clustering
**File**: `src/unified_clustering_master.py`

**Fix**: Use similarity scoring instead of exact matching:
```python
def _are_case_names_compatible(self, name1: str, name2: str) -> bool:
    if not name1 or not name2 or name1 == "N/A" or name2 == "N/A":
        return True
    
    # Use similarity scoring
    similarity = calculate_case_name_similarity(name1, name2)
    return similarity > 0.7  # Allow if reasonably similar
```

---

### 6. Improve Verification Rate

**Problem**: Many citations show "Unverified" status.

**Note**: Some are expected (old citations, obscure sources), but some might be fixable.

**Suggested Fixes**:

#### A. Better Citation Normalization
**File**: `src/unified_verification_master.py`

**Fix**: Normalize citations before sending to verification API:
```python
def normalize_citation_for_verification(citation: str) -> str:
    # Normalize common variations
    # - "Wn." → "Wash."
    # - "P.3d" → "P.3d" (keep as is)
    # - Remove page numbers if needed
    # - Normalize whitespace
    normalized = citation.strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    # ... more normalization
    return normalized
```

#### B. Retry Failed Verifications with Variations
**Fix**: If verification fails, try variations:
```python
def verify_citation_with_variations(citation: str) -> VerificationResult:
    # Try original citation
    result = verify_citation(citation)
    if result.verified:
        return result
    
    # Try variations
    variations = generate_citation_variations(citation)
    for variation in variations:
        result = verify_citation(variation)
        if result.verified:
            return result
    
    return result  # Return last attempt
```

---

## P3 - Nice to Have (Low Priority)

### 7. Better Error Messages and Logging

**Fix**: Add more detailed logging to help debug extraction issues:
```python
logger.info(f"[EXTRACT-DEBUG] Citation: {citation_text}")
logger.info(f"[EXTRACT-DEBUG] Context window: {len(context)} chars")
logger.info(f"[EXTRACT-DEBUG] Context text: '{context[-200:]}'")
logger.info(f"[EXTRACT-DEBUG] Patterns tried: {patterns_tried}")
logger.info(f"[EXTRACT-DEBUG] Matches found: {matches_found}")
logger.info(f"[EXTRACT-DEBUG] Validation result: {validation_result}")
logger.info(f"[EXTRACT-DEBUG] Final result: {case_name or 'N/A'}")
```

### 8. UI Improvements

**Fix**: Better display of extraction issues:
- Show why extraction failed (extraction method, validation failure, etc.)
- Show confidence scores
- Better indication of "N/A" vs verified vs unverified

---

## Implementation Priority

1. **First**: Fix case name bleeding (P0) - Most critical issue
2. **Second**: Fix legal text contamination (P0) - Related to bleeding
3. **Third**: Improve extraction success rate (P1) - Reduce "N/A" results
4. **Fourth**: Improve date extraction (P1) - Lower priority than names
5. **Fifth**: Improve clustering (P2) - Some issues but not critical
6. **Sixth**: Improve verification rate (P2) - Some failures are expected

---

## Quick Wins (Easy Fixes with High Impact)

1. **Add legal phrase validation** - Quick to implement, prevents many contamination issues
2. **Improve signal phrase removal** - Add more patterns, easy to do
3. **Validate extracted name position** - Ensure it appears before citation
4. **Better logging** - Helps debug issues faster


