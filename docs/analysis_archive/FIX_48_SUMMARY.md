# Fix #48: Use Extracted Data for Clustering (Not Canonical Data)

## Critical Change

**Status:** ✅ DEPLOYED

**User Request:** "We should use the extracted name and year for clustering, but not the canonical name because different citations might be verified by different websites which use different names for the same case."

## The Problem

Previously, `_validate_canonical_consistency()` was using **canonical data from APIs** to decide whether to split clusters. This caused issues because:

1. **Different websites use different names** - CourtListener might call a case "State v. Smith" while another source says "State of Washington v. Smith"
2. **API data can be wrong** - Wrong jurisdiction, wrong year, wrong case entirely
3. **Clusters were being split unnecessarily** - Parallel citations in the user's document were split because APIs returned slightly different canonical names

**Example Issue:**
```
Document has: "Fraternal Order, 148 Wn.2d 224, 59 P.3d 655 (2002)"
API returns:  148 Wn.2d 224 → "Fraternal Order of Eagles, Tenino Aerie No. 564 v. Grand Aerie..."
              59 P.3d 655 → "FRATERNAL ORDER OF EAGLES v. Grand Aerie..."
              
Old logic: Different canonical names → SPLIT INTO 2 CLUSTERS ❌
New logic: Same extracted name "Fraternal Order" → KEEP TOGETHER ✅
```

## The Solution

**Trust Hierarchy (Priority Order):**
1. **Proximity** - Citations close together (within 200 chars) are likely parallel
2. **Extracted Data** (PRIMARY) - What's actually in the user's document
3. **Canonical Data** - Only used for display/verification purposes

**New Logic:**
```python
# FIX #48: Group by EXTRACTED case name + year (from document)
for citation in citations:
    extracted_name = citation.extracted_case_name  # From document
    extracted_date = citation.extracted_date       # From document
    
    # Skip canonical_name, canonical_date - they're for display only!
```

**Only split clusters when:**
- Extracted names are VERY different (not just abbreviations)
- Extracted years differ by more than 2 years
- AND citations are NOT in close proximity

## Code Changes

**File:** `src/unified_clustering_master.py`
**Function:** `_validate_canonical_consistency()` (lines 1689-1855)

**Key Changes:**
1. Changed from `canonical_name` → `extracted_case_name`
2. Changed from `canonical_date` → `extracted_date`
3. Updated grouping key: `extracted_group_key` instead of `canonical_group_key`
4. Updated split reason: `'extracted_data_mismatch'` instead of `'canonical_mismatch'`
5. Updated logging to emphasize extracted data: "EXTRACTED year mismatch", "EXTRACTED groups"

## Expected Impact

### ✅ Should Fix
1. **Fewer cluster splits** - Parallel citations should stay together even with varying canonical names
2. **More accurate clustering** - Based on user's document, not API quirks
3. **Better user experience** - Parallel citations appear as single entries

### ⚠️ Potential Issues
1. **Bad extractions** - If `extracted_case_name` is wrong, clustering will be wrong
2. **"N/A" extractions** - Citations without extracted names go into separate "no_extraction" cluster
3. **Abbreviation variations** - "State v. Smith" vs "Smith" might still split if first word differs

## Testing

### Before Fix #48:
```
cluster_12_split_17: ['159 Wn.2d 700']  → "Bostain v. Food Express"
cluster_12_split_18: ['148 Wn.2d 224', '59 P.3d 655'] → "Fraternal Order"
```
Split because canonical names differed (API issue).

### After Fix #48 (Expected):
```
cluster_12: ['148 Wn.2d 224', '59 P.3d 655']  → "Fraternal Order"
```
Kept together because extracted_case_name is the same.

## Integration

- **Backward Compatible:** Yes
- **Requires extracted data:** Yes (citations must have `extracted_case_name` and `extracted_date`)
- **Fallback:** Citations without extraction data go into separate cluster

## Verification

Check logs for:
```
✅ [FIX #48] Keeping cluster intact - close proximity + similar EXTRACTED names
🔴 FIX #48: Splitting cluster - N different EXTRACTED cases detected
```

Compare cluster counts before/after to measure impact:
```powershell
Get-Content logs/casestrainer.log | Select-String "FIX #48"
```

## Related Fixes

- **Fix #22:** Original canonical consistency validation (too aggressive)
- **Fix #47:** Added proximity check (improved, but still used canonical data)
- **Fix #48:** Switched to extracted data (final solution)

## Bottom Line

**This is a fundamental shift in clustering philosophy:**
- **Old way:** Trust the API, split when canonical names differ
- **New way:** Trust the user's document, only split when extracted data clearly shows different cases

**Result:** Clustering now reflects what the user wrote, not what the API thinks they meant.

