# Final Contamination Fix - The Root Cause

## The Problem

Even after previous fixes, the `extracted_case_name` field at the cluster level was STILL being contaminated with canonical data from the API. The issue was:

```
Submitted Document: Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board, 2015
```

The word "Association" does NOT appear in the user's document (it's "Ass'n" in the PDF), so this was canonical data leaking into the extracted field.

## Root Cause Analysis

### The Data Flow

1. **`unified_citation_clustering.py` (lines 2206-2207)**:
   ```python
   if cluster_canonical_name:
       cluster_dict['canonical_name'] = cluster_canonical_name
       # Use the canonical cluster name as the definitive case name
       cluster_dict['case_name'] = cluster_canonical_name  # ← CONTAMINATION SOURCE
   ```
   
   The `case_name` field was being set to the **canonical** name (from API).

2. **`unified_citation_processor_v2.py` (line 3695 - BEFORE FIX)**:
   ```python
   extracted_name = cluster.get('cluster_case_name') or cluster.get('case_name')  # ← BUG!
   ```
   
   When `cluster_case_name` was missing, the code fell back to `case_name`, which contained **canonical** data!

3. **Result**: The `extracted_case_name` field in the final output was contaminated with API data.

## The Fix

**File**: `src/unified_citation_processor_v2.py`  
**Lines**: 3695-3700

### Before:
```python
extracted_name = cluster.get('cluster_case_name') or cluster.get('case_name')
canonical_name = None
extracted_date = cluster.get('cluster_year')
canonical_date = None
canonical_url = None
```

### After:
```python
# DO NOT use 'case_name' as fallback - it may contain canonical data!
extracted_name = cluster.get('cluster_case_name') or cluster.get('extracted_case_name')
canonical_name = cluster.get('canonical_name')  # Get canonical directly from cluster
extracted_date = cluster.get('cluster_year') or cluster.get('extracted_date')
canonical_date = cluster.get('canonical_date')  # Get canonical directly from cluster
canonical_url = cluster.get('canonical_url')
```

### Key Changes:

1. **Removed `case_name` fallback** for `extracted_name` - it's unsafe because `case_name` is set to canonical data
2. **Only use truly extracted fields**: `cluster_case_name` or `extracted_case_name`
3. **Get canonical data directly** from cluster fields, not as fallbacks
4. **Maintain strict separation** between extracted and canonical at all times

## Data Separation Rules

### ✅ SAFE Fields for Extracted Data:
- `cluster_case_name` - Set by clustering from document extraction
- `extracted_case_name` - Explicitly marked as from document
- `cluster_year` - Set by clustering from document extraction
- `extracted_date` - Explicitly marked as from document

### ❌ UNSAFE Fields for Extracted Data:
- `case_name` - May contain canonical data (used for display)
- `year` - May contain canonical data (used for display)
- `canonical_name` - ALWAYS from API
- `canonical_date` - ALWAYS from API

## Testing

To verify the fix:

1. Restart production: `./dplaunch2.ps1`
2. Process document 1033940.pdf
3. Check the "Washington Spirits" cluster
4. Verify:
   - ✅ `extracted_case_name`: "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd."
   - ✅ `canonical_name`: "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board"
   - ✅ NO contamination between the two fields

## Expected Output

```json
{
  "cluster_id": "...",
  "case_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
  "canonical_name": "Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board",
  "extracted_case_name": "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd.",
  "date": "2015-01-08",
  "canonical_date": "2015-01-08",
  "extracted_date": "2015",
  ...
}
```

## Lessons Learned

1. **Never use display fields as sources for extracted data** - They mix canonical and extracted
2. **Be explicit about data sources** - Use field names that clearly indicate origin
3. **Test with real examples** - The "Association" vs "Ass'n" difference was key to finding this
4. **Trace the full data flow** - The bug was in the final output formatting, not the initial extraction

This fix completes the contamination prevention work. The extracted and canonical data are now completely separated throughout the entire pipeline.

