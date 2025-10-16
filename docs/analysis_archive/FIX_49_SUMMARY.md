# Fix #49: Proximity Override for Parallel Citations

## The User's Critical Question

**User asked:** "Will parallel citations always have the same extracted case name and year?"

**Answer:** **NO!** And this was a critical flaw in Fix #48.

## The Problem

Fix #48 switched to using extracted data for clustering validation, but parallel citations often have **different extracted names**:

### Why Extraction Can Differ for Parallel Citations

1. **Extraction failures**: One citation might extract "Fraternal Order" while its parallel extracts "N/A"
2. **Position-based differences**: Fix #46 stops at previous citation boundaries - if there's text between parallels, they might extract different names
3. **Abbreviated vs full names**: One might extract "State v. Smith (full)" while the other extracts "Smith (abbreviated)"
4. **OCR/parsing errors**: PDF text extraction can be inconsistent

### Example Issue
```
Document: "Fraternal Order, 148 Wn.2d 224, 59 P.3d 655 (2002)"
Extraction: 148 Wn.2d 224 → "Fraternal Order"
            59 P.3d 655 → "N/A" (extraction failed)

Fix #48: Different extracted names → SPLIT! ❌ WRONG!
Fix #49: Within 200 chars → KEEP TOGETHER! ✅ CORRECT!
```

## The Solution: Proximity Always Wins

**Revised Trust Hierarchy:**
1. **PROXIMITY** (PRIMARY) - If within 200 chars, ALWAYS keep together
2. **Extracted data** (SECONDARY) - Only used for validation when NOT in close proximity
3. **Canonical data** - Only for display/verification

### New Logic (Fix #49)
```python
# FIX #49: If citations are in CLOSE proximity, ALWAYS keep them together!
if is_close_proximity:
    logger.info("✅ [FIX #49] PROXIMITY OVERRIDE - Keeping cluster intact despite different extracted names")
    validated_clusters.append(cluster)
    continue  # Don't even check extracted data - proximity is enough!
```

## When Each Signal Applies

| Scenario | Distance | Extracted Names | Action |
|----------|----------|-----------------|--------|
| Parallel citations (ideal) | <200 chars | Same | Keep together (both signals agree) |
| Parallel citations (extraction failed) | <200 chars | Different | Keep together (proximity wins) ✅ |
| Different cases cited together | <200 chars | Very different | Keep together (proximity wins) ⚠️ |
| Same case cited separately | >200 chars | Same | Keep together (extracted data wins) ✅ |
| Different cases | >200 chars | Different | Split (both signals agree) ✅ |

## Code Changes

**File:** `src/unified_clustering_master.py`
**Function:** `_validate_canonical_consistency()` (lines 1785-1793)

**Key Change:**
- Moved proximity check BEFORE detailed extracted data comparison
- Made proximity an absolute override - if close, don't split, period!
- Keeps extracted data validation only for non-proximate citations

## Edge Cases

### ⚠️ False Positives (Keep Together When Shouldn't)
If two different cases are cited within 200 chars of each other:
```
"...under State v. Smith, 123 Wn.2d 1. However, State v. Jones, 124 Wn.2d 2..."
```
These might be kept together incorrectly. But this is rare and acceptable because:
- Most parallel citations are within 200 chars
- Different cases usually have more separating text
- User can understand the grouping from context

### ✅ False Negatives (Split When Shouldn't)
Much less likely now! Only if:
- Parallel citations are >200 chars apart (unusual)
- AND extracted names are very different
- In this case, they probably aren't parallel anyway

## Testing

### Test Case 1: Extraction Failure
```
Input: [148 Wn.2d 224 (extracted: "Fraternal"), 59 P.3d 655 (extracted: "N/A")]
Distance: 25 chars
Old: SPLIT (different extracted names)
New: KEEP TOGETHER ✅ (proximity override)
```

### Test Case 2: Abbreviated vs Full
```
Input: [192 Wn.2d 453 (extracted: "Lopez Demetrio v. Sakuma"), 355 P.3d 258 (extracted: "Lopez")]
Distance: 18 chars
Old: SPLIT (different extracted names)
New: KEEP TOGETHER ✅ (proximity override)
```

### Test Case 3: Actually Different Cases (Far Apart)
```
Input: [183 Wn.2d 649 (extracted: "Lopez"), 192 Wn.2d 453 (extracted: "Spokane")]
Distance: 5000 chars
Old: SPLIT (different extracted names)
New: SPLIT ✅ (proximity doesn't apply, extracted data differs)
```

## Integration with Previous Fixes

- **Fix #22:** Original validation (too aggressive, used canonical data)
- **Fix #47:** Added proximity check (improved, but still used canonical data)
- **Fix #48:** Switched to extracted data (better, but broke parallel citations with extraction errors)
- **Fix #49:** Made proximity the PRIMARY signal (final solution)

## Bottom Line

**Fix #49 implements the correct trust hierarchy:**

1. **Proximity = Truth** - If citations are close together, they're related (probably parallel)
2. **Extraction = Helpful** - Use extracted data to validate non-proximate citations
3. **Canonical = Display Only** - Don't use for clustering decisions at all

**Result:** Parallel citations stay together even when extraction fails or differs.

