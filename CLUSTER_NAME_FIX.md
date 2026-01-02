# CLUSTER EXTRACTED CASE NAME FIX

**Date**: November 9, 2025  
**Issue**: Cluster `extracted_case_name` field showing wrong names or N/A even when individual citations have correct extracted names

## Root Causes Identified

### Issue 1: Priority Inversion in _select_best_case_name()
The function was prioritizing `canonical_name` (from external APIs) over `extracted_case_name` (from the document):

```python
# BEFORE (WRONG):
possible_names = [
    citation.get('canonical_name'),      # Priority 1 - from APIs, may be wrong!
    citation.get('extracted_case_name'),  # Priority 2 - from document
]
```

**Problem**: When canonical data from APIs is incorrect or N/A, it takes precedence over the correct extracted name from the document.

### Issue 2: Missing Cluster-Level Extracted Fields
The cluster output was missing `extracted_case_name` and `extracted_date` fields, only providing `cluster_case_name` which could be contaminated by canonical data.

## Solutions Implemented

### Fix 1: New _select_best_extracted_name() Function
Created a dedicated function that prioritizes extracted data from the document:

**File**: `src/unified_clustering_master.py` (Lines 194-246)

```python
def _select_best_extracted_name(self, group: List[Any]) -> Optional[str]:
    """
    Select the best EXTRACTED case name for cluster-level naming.
    
    CRITICAL: This function prioritizes extracted_case_name (from the document)
    over canonical_name (from APIs) because:
    1. Extracted names represent what's actually written in the document
    2. Canonical names from APIs may be wrong or N/A
    3. Cluster naming should reflect document content, not API data
    """
    # PRIORITY ORDER: extracted > cluster > canonical
    possible_names = [
        citation.get('extracted_case_name'),   # Priority 1: From document
        citation.get('cluster_case_name'),     # Priority 2: Cluster aggregate
        citation.get('canonical_name'),        # Priority 3: From API (may be wrong)
    ]
```

**Key Features**:
- Prioritizes extracted data over canonical data
- Skips truncated names (e.g., "Inc. v. Robins")
- Uses scoring system to select highest quality name
- Adds comprehensive logging for debugging

### Fix 2: Updated _format_clusters_for_output()
Changed cluster formatting to use the new function:

**File**: `src/unified_clustering_master.py` (Lines 3335-3344)

```python
# BEFORE:
inferred_name = self._select_best_case_name(citations)  # Used canonical priority

# AFTER:
inferred_name = self._select_best_extracted_name(citations)  # Uses extracted priority
```

### Fix 3: Added Cluster-Level Extracted Fields
Added explicit `extracted_case_name` and `extracted_date` fields to cluster output:

**File**: `src/unified_clustering_master.py` (Lines 3455-3457)

```python
formatted_cluster = {
    # CRITICAL FIX: Add cluster-level extracted fields (from document)
    'extracted_case_name': best_name or 'N/A',  # Extracted from document
    'extracted_date': best_year or 'N/A',       # Extracted from document
    # Canonical fields (from API verification)
    'canonical_name': cluster_canonical_name,
    'canonical_date': cluster_canonical_date,
}
```

## Data Separation Principle

**CRITICAL**: This fix maintains strict separation between two types of data:

### Extracted Data (from user's document)
- `extracted_case_name`: Case name found in the user's document
- `extracted_date`: Year found in the user's document
- **Source**: Document text analysis
- **Purpose**: Show what's actually written in the document

### Canonical Data (from API verification)
- `canonical_name`: Official case name from CourtListener/CaseMine
- `canonical_date`: Official date from legal databases
- **Source**: External API verification
- **Purpose**: Provide authoritative legal reference

## Expected Results

### Before Fix
```json
{
  "cluster_case_name": "Raines v. Byrd",  // From API (wrong for this document)
  "citations": [
    {
      "citation": "578 U.S. 330",
      "extracted_case_name": "Spokeo, Inc. v. Robins",  // Correct from document
      "canonical_name": "Raines v. Byrd"  // From API
    }
  ]
}
```

**Problem**: Cluster name doesn't match what's actually in the citations!

### After Fix
```json
{
  "extracted_case_name": "Spokeo, Inc. v. Robins",  // From document (correct)
  "canonical_name": "Spokeo, Inc. v. Robins",       // From API (if verified)
  "cluster_case_name": "Spokeo, Inc. v. Robins",    // Matches extracted
  "citations": [
    {
      "citation": "578 U.S. 330",
      "extracted_case_name": "Spokeo, Inc. v. Robins",
      "canonical_name": "Spokeo, Inc. v. Robins"
    }
  ]
}
```

**Result**: Cluster name correctly reflects the document content!

## Testing

To test the fix:

```bash
# Build Docker image with changes
cslaunch

# Run test with your problematic PDF
python test_cluster_names.py
```

## Files Modified

1. `src/unified_clustering_master.py`:
   - Added `_select_best_extracted_name()` method (lines 194-246)
   - Updated `_format_clusters_for_output()` to use new method (line 3339)
   - Added `extracted_case_name` and `extracted_date` to cluster output (lines 3456-3457)

## Impact

This fix resolves:
1. ✅ **Wrong cluster names**: Clusters now use extracted names from document, not incorrect API data
2. ✅ **N/A cluster names**: Clusters properly aggregate extracted names from citations
3. ✅ **Data consistency**: Cluster-level and citation-level extracted names now align
4. ✅ **Vue.js access**: Frontend can now access `cluster.extracted_case_name` field

## CRITICAL FIX 2: Wrong Citations Clustered Together (Nov 9, 2025)

### Problem
**Different cases were being clustered together** because the fallback clustering logic used extracted names instead of canonical names for verified citations.

**Example from production**:
```
Burlington Northern & Santa Fe Railway Co. v. Abc-Naco, 2009 ⚠️
Extracted from Document: Marakova v. United States, 2002
Citation 1: 389 Ill. App. 3d 691 (Verified to Burlington Northern)
Citation 2: 2002 WY 183 (Verified to Marakova)
Citation 3: 906 N.E.2d 83 (Verified to Burlington Northern)
```

These are **TWO DIFFERENT CASES** incorrectly clustered together!

### Root Cause

The clustering fallback logic at lines 1299-1317 used `_get_case_name()` which returns **extracted** names:

```python
# BEFORE (WRONG):
case_name1 = self._get_case_name(citation1)  # Returns extracted_case_name
case_name2 = self._get_case_name(citation2)  # Returns extracted_case_name

# If both extracted "Marakova" due to contamination:
if similarity >= 0.95:
    return True  # CLUSTER THEM! ❌ WRONG!
```

**What happened**:
1. Citation A and Citation B are both near "Marakova" in the document
2. Both extract "Marakova" as case name (contamination)
3. They're within proximity (150 chars)
4. Fallback kicks in: Both extracted "Marakova" → **cluster together**
5. **Result**: Different verified cases incorrectly grouped!

### Solution

**File**: `src/unified_clustering_master.py` (Lines 1122-1142, 1304-1325)

For **verified citations**, use **canonical names** (from APIs) for clustering decisions:

```python
# AFTER (CORRECT):
def get_clustering_name(cit):
    is_verified = cit.get('verified', False)
    canonical_name = cit.get('canonical_name')
    extracted_name = cit.get('extracted_case_name')
    
    # For verified: use authoritative canonical name
    # For unverified: use extracted name (best we have)
    if is_verified and canonical_name and canonical_name != 'N/A':
        return canonical_name  # ✅ Authoritative!
    elif extracted_name and extracted_name != 'N/A':
        return extracted_name
    return None

case_name1 = get_clustering_name(citation1)
case_name2 = get_clustering_name(citation2)

# Now compares "Burlington Northern" vs "Marakova"
# similarity = 0.2 < 0.95 → REJECT clustering! ✅ CORRECT!
```

**Impact**:
- ✅ Prevents different verified cases from clustering together
- ✅ Uses authoritative API data for clustering decisions when available
- ✅ Still uses extracted names for unverified citations
- ✅ Fixes the "Name Differences" warnings in production

## Related Issues

This fix addresses issues mentioned in previous memories:
- **CRITICAL**: Different cases being clustered together (Burlington Northern vs Marakova)
- Network response case name mismatches
- Canonical vs extracted name conflicts  
- CourtListener API returning wrong data for citations
- Cluster naming based on first citation's canonical data instead of extracted data
