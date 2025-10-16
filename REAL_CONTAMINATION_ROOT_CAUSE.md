# The REAL Root Cause of Contamination

## TL;DR
The contamination was happening because **I used `cluster_case_name` to populate `extracted_case_name`**, but `cluster_case_name` is a **display field** that contains canonical data when available!

## The Bug Chain

### 1. In `unified_clustering_master.py` (lines 1034-1043):
```python
if verified_flag and canonical_name and canonical_name != 'N/A' and not case_name:
    case_name = canonical_name  # ← Sets case_name to CANONICAL

# Later...
enhanced.cluster_case_name = case_name  # ← cluster_case_name now contains CANONICAL data!
```

**Result**: `cluster_case_name` = canonical name (from API) for verified citations

### 2. In `unified_citation_processor_v2.py` (line 3696 - MY BROKEN FIX):
```python
extracted_name = cluster.get('cluster_case_name') or cluster.get('extracted_case_name')
```

**Result**: `extracted_name` gets contaminated with canonical data from `cluster_case_name`!

### 3. In the final output (line 3777):
```python
'extracted_case_name': extracted_name,  # ← CONTAMINATED with canonical data!
```

**Result**: The frontend receives contaminated data

## The Actual Data Flow

For the Washington Spirits case (cluster_6):

1. **Citations have**:
   - `extracted_case_name`: "State v. Velasquez" (wrong, but at least not canonical)
   - `canonical_name`: "Association of Washington Spirits & Wine Distributors..." (from API)
   
2. **`unified_clustering_master.py` creates**:
   - `case_name` = `canonical_name` (line 1035)
   - `cluster_case_name` = `case_name` = canonical name (line 1043)
   
3. **`unified_citation_processor_v2.py` MY BROKEN FIX**:
   - `extracted_name` = `cluster.get('cluster_case_name')` = canonical name ❌
   
4. **Final output**:
   - `extracted_case_name`: "Association..." (CONTAMINATED)

## The CORRECT Fix

**File**: `src/unified_citation_processor_v2.py`  
**Lines**: 3697-3698

### Before (BROKEN):
```python
extracted_name = cluster.get('cluster_case_name') or cluster.get('extracted_case_name')
```

### After (CORRECT):
```python
extracted_name = None  # Start with None
# ONLY populate from citations' extracted_case_name fields
# NEVER use cluster_case_name or case_name - they contain canonical data!
```

Then populate `extracted_name` by searching through the citations' `extracted_case_name` fields ONLY (lines 3708-3741).

## Why cluster_case_name Contains Canonical Data

The `cluster_case_name` field is designed to be a **display field** that shows the "best" name for the cluster:
- If the cluster is verified (API data available), it uses the canonical name
- If the cluster is not verified, it uses the extracted name

This is **correct behavior** for a display field, but it means `cluster_case_name` is **UNSAFE** for populating `extracted_case_name`!

## Fields and Their Data Sources

### SAFE for Extracted Data:
- `extracted_case_name` (from individual citations)
- `extracted_date` (from individual citations)

### UNSAFE for Extracted Data (contain canonical/display data):
- `cluster_case_name` ❌ (display field - canonical if verified)
- `case_name` ❌ (display field - canonical if verified)
- `cluster_year` ❌ (display field - canonical if verified)
- `year` ❌ (display field - canonical if verified)

### Always Canonical:
- `canonical_name` ✓ (always from API)
- `canonical_date` ✓ (always from API)
- `canonical_url` ✓ (always from API)

## The Lesson

**Never assume a field contains extracted data just because it has "cluster" in the name!**

Always trace the data flow to verify what a field actually contains:
1. Where is it set?
2. What is it set FROM?
3. Can it ever contain canonical/API data?

If there's ANY possibility it contains canonical data, **DO NOT use it for extracted fields**.

## Testing

To verify the fix works:
1. Restart production: `./dplaunch2.ps1`
2. Process document 1033940.pdf
3. Check the Washington Spirits cluster
4. Verify:
   - ✅ `extracted_case_name`: Should contain text from the PDF (e.g., "State v. Velasquez" or similar - may not be perfect but should NOT be "Association...")
   - ✅ `canonical_name`: "Association of Washington Spirits & Wine Distributors..." (correct - from API)
   - ✅ NO contamination: `extracted_case_name` ≠ `canonical_name`

## Related Files Changed

1. `src/unified_citation_processor_v2.py` (lines 3697-3751)
   - Changed to NEVER use `cluster_case_name` or `case_name` for extracted data
   - Only populate `extracted_name` from citations' `extracted_case_name` fields

This fix ensures complete separation between extracted and canonical data at the final output stage.

