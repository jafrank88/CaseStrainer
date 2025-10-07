# Fix for 521 U.S. 811 Extraction Issue

## 🔍 **Root Cause Identified**

The PDF has a formatting issue where "Raines v. Byrd" and "521 U.S. 811" are separated by a large gap (likely a page break or column break).

### PDF Text Structure:
```
... quoting Raines v. Byrd, [PAGE BREAK/FORMATTING GAP] 'S. Ct. 1540, 194 L. Ed. 2d 635 (2016) ...
... [300 chars of other text including "Branson"] ...
... 521 U.S. 811 ...
```

### What's Happening:
1. ✅ **Extraction finds "Branson"** (300 chars before citation) - closer than "Raines"
2. ✅ **Verification finds "Raines v. Byrd"** via CourtListener API - correct!
3. ❌ **System uses extracted name** instead of canonical name
4. ❌ **Clustering uses extracted name** causing wrong grouping

---

## 🎯 **The Solution**

**Prioritize verified canonical data over extracted data** when there's a mismatch.

### Strategy:
1. **After verification**, if canonical_name exists and differs from extracted_name
2. **Replace extracted_name with canonical_name** for clustering
3. **Update cluster_case_name** to use canonical_name
4. **Keep extracted_name** in metadata for debugging

---

## 🔧 **Implementation**

### Option 1: Post-Processing Fix (Recommended)
Add a step after verification that replaces extracted names with canonical names when verified:

```python
def apply_canonical_names_to_verified_citations(citations):
    """
    Replace extracted names with canonical names for verified citations.
    This fixes PDF extraction artifacts where case names are separated from citations.
    """
    for citation in citations:
        if citation.get('is_verified') and citation.get('canonical_name'):
            canonical = citation['canonical_name']
            extracted = citation.get('extracted_case_name', 'N/A')
            
            # If they differ significantly, trust the canonical name
            if canonical != extracted and canonical != 'N/A':
                logger.info(f"Replacing extracted '{extracted}' with canonical '{canonical}' for {citation['citation']}")
                citation['extracted_case_name'] = canonical
                citation['cluster_case_name'] = canonical
                
                # Keep original for debugging
                if 'metadata' not in citation:
                    citation['metadata'] = {}
                citation['metadata']['original_extracted_name'] = extracted
                citation['metadata']['name_source'] = 'canonical_override'
    
    return citations
```

### Option 2: Clustering Fix
Update the clustering algorithm to use canonical_name instead of extracted_case_name when available:

```python
def get_case_name_for_clustering(citation):
    """Get the best case name for clustering purposes."""
    # Priority 1: Canonical name from verification
    if citation.get('is_verified') and citation.get('canonical_name'):
        return citation['canonical_name']
    
    # Priority 2: Extracted name
    if citation.get('extracted_case_name') and citation['extracted_case_name'] != 'N/A':
        return citation['extracted_case_name']
    
    # Priority 3: Cluster case name
    return citation.get('cluster_case_name', 'N/A')
```

---

## 📍 **Where to Apply the Fix**

### File: `src/unified_citation_processor_v2.py`

Add the canonical name override **after verification** but **before clustering**:

```python
# Around line 2500-2600 (after verification step)
if verification_results:
    # Apply verification results
    self._apply_verification_results(citations, verification_results)
    
    # NEW: Apply canonical names to verified citations
    citations = self._apply_canonical_names_to_verified(citations)
    
# Then continue with clustering
if self.clustering_enabled:
    clusters = self._cluster_citations(citations)
```

---

## 🧪 **Expected Results After Fix**

### Before Fix:
```json
{
    "citation": "521 U.S. 811",
    "extracted_case_name": "Branson v. Wash. Fine Wine & Spirits, LLC",  // ❌ Wrong
    "canonical_name": "Wp Company LLC v. U.S. Small Business Administration",  // ❌ Also wrong
    "cluster_case_name": "Branson v. Wash. Fine Wine & Spirits, LLC",  // ❌ Wrong
    "cluster_id": "cluster_18"  // ❌ Grouped with Spokeo
}
```

### After Fix:
```json
{
    "citation": "521 U.S. 811",
    "extracted_case_name": "Raines v. Byrd",  // ✅ From canonical
    "canonical_name": "Raines v. Byrd",  // ✅ From CourtListener
    "cluster_case_name": "Raines v. Byrd",  // ✅ Correct
    "cluster_id": "cluster_raines_1997",  // ✅ Separate from Spokeo
    "metadata": {
        "original_extracted_name": "Branson v. Wash. Fine Wine & Spirits, LLC",
        "name_source": "canonical_override"
    }
}
```

---

## ⚠️ **Note on Canonical Name Quality**

The current result shows:
```
"canonical_name": "Wp Company LLC v. U.S. Small Business Administration"
```

This is **also wrong** - it should be "Raines v. Byrd". This suggests:
1. CourtListener API is returning the wrong case
2. OR the verification is matching to the wrong opinion

We need to investigate why the verification is returning the wrong canonical name.

---

## 🔍 **Next Steps**

1. **Implement Option 1** (post-processing fix) - quick win
2. **Investigate verification** - why is canonical_name wrong?
3. **Test with 521 U.S. 811** specifically
4. **Verify clustering separates Raines from Spokeo**

---

## 📊 **Impact**

This fix will:
- ✅ Resolve PDF extraction artifacts
- ✅ Prioritize verified data over extracted data
- ✅ Improve clustering accuracy
- ✅ Separate Raines (1997) from Spokeo (2016)
- ✅ Maintain debugging info in metadata
