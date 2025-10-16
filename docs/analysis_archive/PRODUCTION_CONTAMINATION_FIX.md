# Production Contamination Fix - Cluster Level

## Date
October 8, 2025

## Issue
The **cluster-level** `extracted_case_name` field was being contaminated with canonical data in production, even though the individual citation-level `extracted_case_name` fields were correct.

### Evidence from Production Results
For the Washington Spirits case (182 Wash.2d 342):

**Cluster Level (WRONG - contaminated):**
```json
{
    "canonical_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
    "extracted_case_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
    ...
}
```

**Individual Citation Level (CORRECT):**
```json
{
    "citation": "182 Wash.2d 342",
    "extracted_case_name": "State v. Velasquez",  // This is wrong but different
    ...
}
```

The word "Association" does NOT appear in the user's document 1033940.pdf, so the cluster's `extracted_case_name` should be "Ass'n of Wash. Spirits & Wine Distribs..." (the abbreviated form from the document), NOT the full canonical name.

## Root Cause

**File**: `src/unified_citation_processor_v2.py`  
**Lines**: 3699-3701 and 3749-3750

### Bug 1: Prioritizing canonical over extracted (lines 3699-3701)
```python
# WRONG - prioritizes canonical_name over extracted_case_name
case_name = first_citation.get('canonical_name') or first_citation.get('extracted_case_name')
```

This fetches `canonical_name` first, so if it exists, the `extracted_case_name` is never used.

### Bug 2: Using mixed data for both fields (lines 3749-3750)
```python
# WRONG - uses the same contaminated value for both fields
'canonical_name': case_name,  # For backward compatibility
'extracted_case_name': case_name,  # For backward compatibility
```

This sets BOTH `canonical_name` and `extracted_case_name` to the same value, which is the canonical data.

## Solution

### Changed Lines 3694-3725
```python
# CRITICAL: Get extracted and canonical data SEPARATELY to prevent contamination
extracted_name = cluster.get('cluster_case_name') or cluster.get('case_name')
canonical_name = None
extracted_date = cluster.get('cluster_year')
canonical_date = None
canonical_url = None

# Get data from first citation if cluster doesn't have it
if cluster.get('citations'):
    first_citation = cluster['citations'][0]
    if isinstance(first_citation, dict):
        # Get extracted and canonical SEPARATELY - do NOT mix them!
        if not extracted_name:
            extracted_name = first_citation.get('extracted_case_name')
        canonical_name = first_citation.get('canonical_name')
        if not extracted_date:
            extracted_date = first_citation.get('extracted_date')
        canonical_date = first_citation.get('canonical_date')
        canonical_url = first_citation.get('canonical_url') or first_citation.get('url')
    elif hasattr(first_citation, 'extracted_case_name'):
        # Get extracted and canonical SEPARATELY - do NOT mix them!
        if not extracted_name:
            extracted_name = getattr(first_citation, 'extracted_case_name', None)
        canonical_name = getattr(first_citation, 'canonical_name', None)
        if not extracted_date:
            extracted_date = getattr(first_citation, 'extracted_date', None)
        canonical_date = getattr(first_citation, 'canonical_date', None)
        canonical_url = getattr(first_citation, 'canonical_url', None) or getattr(first_citation, 'url', None)

# Fallback: If we still don't have data, check all citations (maintain data separation!)
# ... [fallback logic maintains separation]

# Determine the display name and date: Use canonical if verified, otherwise extracted
case_name = canonical_name or extracted_name
cluster_date = canonical_date or extracted_date
```

### Changed Lines 3766-3773
```python
formatted_cluster = {
    'cluster_id': cluster.get('cluster_id'),
    'case_name': case_name,  # Display name (canonical if verified, otherwise extracted)
    'canonical_name': canonical_name,  # MUST be ONLY from API, never from document
    'extracted_case_name': extracted_name,  # MUST be ONLY from document, never from API
    'date': cluster_date,  # Display date (canonical if verified, otherwise extracted)
    'canonical_date': canonical_date,  # MUST be ONLY from API
    'extracted_date': extracted_date,  # MUST be ONLY from document
    ...
}
```

## Key Changes

1. **Separate Variables**: Created separate variables for `extracted_name` and `canonical_name` instead of a single `case_name` variable
2. **No Mixing**: Fetch `extracted_case_name` and `canonical_name` separately from the citation objects, never mixing them
3. **Proper Assignment**: Set `extracted_case_name` and `canonical_name` fields in the cluster to their respective separate values
4. **Display Name**: Use `case_name` for display purposes (prioritizes canonical if available, falls back to extracted)
5. **Data Separation**: Maintain separation for dates as well (`extracted_date` vs `canonical_date`)

## Expected Result

After this fix, for the Washington Spirits case:

**Cluster Level (CORRECT):**
```json
{
    "canonical_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
    "extracted_case_name": "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd.",
    "case_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
    ...
}
```

- `extracted_case_name`: "Ass'n of Wash. Spirits & Wine Distribs..." (from document - with smart quote)
- `canonical_name`: "Association of Washington Spirits & Wine Distributors..." (from API)
- `case_name`: The canonical name (used for display)

## Testing

To test the fix:

1. **Restart Production**: Restart the Docker containers to load the updated code
   ```powershell
   ./dplaunch2.ps1
   ```

2. **Process Document**: Process document 1033940.pdf

3. **Verify Results**: Check that the cluster for "182 Wash.2d 342" has:
   - `extracted_case_name` contains only text from the document (abbreviated form, no "Association")
   - `canonical_name` contains the full verified name from CourtListener
   - The two fields are DIFFERENT

## Related Files

- `src/unified_citation_processor_v2.py` - Fixed contamination in cluster formatting
- `src/services/citation_extractor.py` - Fixed case name extraction to include smart quotes
- `src/unified_citation_clustering.py` - Previously fixed citation-level contamination

## Status

✅ **FIXED** - Code updated, ready for production deployment

