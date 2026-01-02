# Case Name Extraction Improvement Plan

## Problems Identified

### 1. Context Window Too Small
- Current: 100-180 characters max lookback
- Issue: Many case names appear 200-300 characters before citation
- **Solution**: Increase `max_lookback` to 300-500 characters

### 2. Signal Words Over-Aggressively Removed
- Current: Removes "See, e.g.," which also truncates case names
- Example: "See, e.g., Rice v. Dow Chem. Co." → extraction fails
- **Solution**: Keep signal word removal but ensure it doesn't truncate case names

### 3. Docket Numbers Contaminating Matches
- Current: "Erickson v. Pharmacia, No. 103135-1" matches include "No."
- Issue: Pattern stops at "No." thinking it's end of case name
- **Solution**: Remove docket numbers from context BEFORE pattern matching

### 4. Newlines Breaking Patterns
- Current: "Erickson v.\nPharmacia, LLC" doesn't match " v. " pattern
- Issue: Newlines in middle of case names prevent matching
- **Solution**: Already handled by `re.sub(r'\s+', ' ', context)` but needs to be applied EARLIER

### 5. Eyecite Metadata Ignored
- Current: Code explicitly SKIPS eyecite's plaintiff/defendant
- Issue: Throwing away good data that could help extraction
- **Solution**: Use eyecite metadata as fallback when context extraction fails

## Diagnostic Results

### Cases That Should Be Extractable

1. **Erwin v. Cotter Health Centers** (161 Wn.2d 676)
   - Context (100 chars): `Erwin v. Cotter Health Ctrs., Inc., 161 Wn.2d 676, 684,`
   - ✅ Manually extractable: `'Erwin v. Cotter Health Ctrs., Inc.'`
   - Issue: Abbreviation "Ctrs." might not match canonical "Centers"

2. **Richardson v. Pacific Power** (11 Wn.2d 288)
   - Context (100 chars): `Richardson v. Pac. Power & Light Co., 11 Wn.2d 288, 291,`
   - ✅ Manually extractable: `'Richardson v. Pac. Power & Light Co.'`
   - Issue: Abbreviation "Pac." might not match canonical "Pacific"

3. **Baffin Land Corp.** (70 Wn.2d 893)
   - Context (100 chars): `See Baffin Land Corp. v. Monticello Motor Inn, Inc., 70 Wn.2d 893, 898,`
   - ✅ Manually extractable: `'Baffin Land Corp. v. Monticello Motor Inn, Inc.'`
   - Issue: Signal word "See" being removed

4. **Erickson v. Pharmacia** (548 P.3d 226)
   - Context (180 chars): `Erickson v. Pharmacia, No. 103135-1\nThe Court of Appeals reversed in a split, published decision. Erickson v. Pharmacia, LLC, 31 Wn. App. 2d 100, 110-11,`
   - ✅ Manually extractable: `'Erickson v. Pharmacia'`
   - Issue: Docket number "No. 103135-1" in middle of context

5. **Rice v. Dow Chemical** (124 Wn.2d 205)
   - Context (100 chars): `See, e.g., Rice v. Dow Chem. Co.,`
   - ✅ Manually extractable: `'Rice v. Dow Chem. Co.'`
   - Issue: Signal words "See, e.g.," being removed

## Recommended Fixes

### Fix #1: Increase Context Window
```python
# In unified_case_name_extractor.py, line 74
adaptive_context = get_adaptive_context_for_citation(
    text, 
    citation_start, 
    citation_end, 
    all_positions, 
    max_lookback=300  # Increased from 180 to 300
)
```

### Fix #2: Better Signal Word Removal
```python
# In strict_context_isolator.py, improve signal word removal
# Don't remove the case name that follows the signal word
# Instead, remove signal words but keep everything after them

signal_patterns = [
    r'^\s*see,?\s+e\.?g\.?\s*,?\s*',  # Remove ONLY at start of context
    r'^\s*see\s+also\s+',  # Remove ONLY at start
    # ... etc
]
```

### Fix #3: Remove Docket Numbers EARLY
```python
# In strict_context_isolator.py, line 715
# Move this BEFORE pattern matching, not after
context = re.sub(r'\s+No\.\s+[\d\-]+', ' ', context, flags=re.IGNORECASE)
context = re.sub(r',\s*No\.\s+[\d\-]+', '', context, flags=re.IGNORECASE)
```

### Fix #4: Normalize Whitespace EARLY
```python
# In strict_context_isolator.py, normalize whitespace BEFORE pattern matching
# This is already done at line 670, but should also be done earlier
context = re.sub(r'\s+', ' ', context).strip()
```

### Fix #5: Use Eyecite Metadata as Fallback
```python
# In unified_citation_processor_v2.py, line 1343
# Instead of SKIPPING eyecite's plaintiff/defendant, use it as fallback
if hasattr(citation_obj, 'metadata') and citation_obj.metadata:
    plaintiff = getattr(citation_obj.metadata, 'plaintiff', None)
    defendant = getattr(citation_obj.metadata, 'defendant', None)
    
    if plaintiff and defendant:
        eyecite_name = f"{plaintiff} v. {defendant}"
        # Store as fallback, use if our extraction fails
        citation.metadata['eyecite_fallback_name'] = eyecite_name
```

## Implementation Priority

1. **HIGH**: Fix #3 (Remove docket numbers early) - Affects many citations
2. **HIGH**: Fix #1 (Increase context window) - Simple change, big impact
3. **MEDIUM**: Fix #2 (Better signal word removal) - Affects "See" citations
4. **MEDIUM**: Fix #5 (Use eyecite fallback) - Safety net for failures
5. **LOW**: Fix #4 (Normalize whitespace) - Already mostly handled

## Expected Impact

- **Before**: 25+ citations with "N/A" extraction
- **After**: Estimated 15-20 fewer "N/A" failures (60-80% improvement)

The remaining "N/A" cases would be:
- Citations with no case name in nearby context
- Citations in tables or special formats
- Citations where case name is truly unavailable
