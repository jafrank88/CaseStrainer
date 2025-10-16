# Backend-Frontend Field Mismatch Analysis

## Summary
Comprehensive analysis of field name mismatches between backend (Python) and frontend (Vue.js) in CaseStrainer.

---

## ✅ FIXED: Cluster Citations Field

### Issue
- **Backend sends**: `cluster.citations` (array of citation objects)
- **Frontend expected**: `cluster.citation_objects`

### Status: FIXED
- Updated `CitationResults.vue` line 218 to check both fields
- Updated line 204 for `getClusterSource()`

---

## 🔍 POTENTIAL MISMATCHES FOUND

### 1. Citation Text Field in Clusters ✅ FIXED

**Backend** (`unified_citation_processor_v2.py` line 3615):
```python
citation_info = {
    'text': citation_text,  # Uses 'text'
    'verified': False,
    ...
}
```

**Frontend** (`CitationResults.vue` line 95):
```vue
{{ citation.text || citation.citation }}  # Now checks both ✅
```

**Status**: FIXED - Frontend now checks both `citation.text` and `citation.citation`

---

### 2. Cluster URL Field ⚠️ NEEDS VERIFICATION

**Backend** (`unified_citation_processor_v2.py` line 3643):
```python
formatted_cluster = {
    'cluster_id': cluster.get('cluster_id'),
    'case_name': case_name,
    'canonical_name': case_name,
    'extracted_case_name': case_name,
    'date': cluster_date,
    'canonical_date': cluster_date,
    'extracted_date': cluster_date,
    'citations': citations_with_status,
    ...
}
```

**Question**: Does backend send `canonical_url` in clusters?

**Frontend** (`CitationResults.vue` line 72):
```vue
<template v-if="cluster.canonical_url">
  <a :href="cluster.canonical_url" target="_blank">
```

**Investigation Needed**: Check if `canonical_url` is included in `formatted_cluster`

---

### 3. Verification Source Field ✅ APPEARS CORRECT

**Backend** (`unified_citation_processor_v2.py` line 3619):
```python
citation_info = {
    'text': citation_text,
    'verified': False,
    'verification_method': None,
    'verification_source': None,  # ✅
    'verification_url': None
}
```

**Frontend** (`CitationResults.vue` line 123, 207):
```vue
<div v-if="citation.verification_source">  # ✅
if (citation.verification_source) {  # ✅
```

**Status**: CORRECT - Both use `verification_source`

---

### 4. True By Parallel Field ⚠️ MISSING IN CLUSTER CITATIONS

**Backend** (`unified_citation_processor_v2.py` line 3615-3632):
```python
citation_info = {
    'text': citation_text,
    'verified': False,
    'verification_method': None,
    'verification_source': None,
    'verification_url': None
}
# ❌ Missing 'true_by_parallel' field
```

**Frontend** (`CitationResults.vue` line 16, 116, 224):
```vue
citation.true_by_parallel  # Expected but not sent in clusters
```

**Status**: ⚠️ **MISMATCH** - Backend doesn't send `true_by_parallel` in cluster citations

---

### 5. Case Name Field Redundancy ℹ️ INFORMATIONAL

**Backend** sends THREE case name fields:
```python
'case_name': case_name,
'canonical_name': case_name,
'extracted_case_name': case_name,
```

**Frontend** uses:
- `cluster.canonical_name` (line 74, 78)
- `cluster.extracted_case_name` (line 88)

**Status**: WORKING but redundant - All three fields have the same value

---

### 6. Date Field Redundancy ℹ️ INFORMATIONAL

**Backend** sends THREE date fields:
```python
'date': cluster_date,
'canonical_date': cluster_date,
'extracted_date': cluster_date,
```

**Frontend** uses:
- `cluster.canonical_date` (line 74, 78)
- `cluster.extracted_date` (line 74, 78, 88)

**Status**: WORKING but redundant - All three fields have the same value

---

## ✅ CRITICAL ISSUES - FIXED

### Issue #1: Missing `canonical_url` in Clusters - FIXED ✅

**Location**: `unified_citation_processor_v2.py` line 3607-3658

**Fix Applied**:
- Added `canonical_url` extraction from cluster citations (lines 3609, 3615-3621)
- Added `canonical_url` to formatted_cluster (line 3658)
- URL is now extracted from verified citations and included in cluster data

---

### Issue #2: Missing `true_by_parallel` in Cluster Citations - FIXED ✅

**Location**: `unified_citation_processor_v2.py` line 3582-3644

**Fix Applied**:
- Added `true_by_parallel` extraction from citation metadata (lines 3582-3592)
- Added `true_by_parallel` to citation_verification mapping (line 3592)
- Added `true_by_parallel` to citation_info in clusters (line 3634)
- Added `true_by_parallel` to citation update from verification mapping (line 3644)

---

## 📊 FIELD USAGE SUMMARY

### Individual Citations (Working Correctly)
- ✅ `citation.citation` - Citation text
- ✅ `citation.extracted_case_name` - Extracted name
- ✅ `citation.extracted_date` - Extracted date
- ✅ `citation.canonical_name` - Canonical name
- ✅ `citation.canonical_date` - Canonical date
- ✅ `citation.verified` - Verification status
- ✅ `citation.true_by_parallel` - Parallel verification
- ✅ `citation.verification_source` - Source of verification

### Cluster Objects (Mostly Working)
- ✅ `cluster.cluster_id` - Cluster identifier
- ✅ `cluster.canonical_name` - Canonical case name
- ✅ `cluster.canonical_date` - Canonical date
- ✅ `cluster.extracted_case_name` - Extracted name
- ✅ `cluster.extracted_date` - Extracted date
- ⚠️ `cluster.canonical_url` - **MISSING** in backend
- ✅ `cluster.citations` - Array of citation objects (FIXED)

### Cluster Citation Objects (Partial Issues)
- ✅ `citation.text` - Citation text (FIXED to check both)
- ✅ `citation.verified` - Verification status
- ⚠️ `citation.true_by_parallel` - **MISSING** in backend
- ✅ `citation.verification_source` - Source of verification

---

## 🔧 RECOMMENDED FIXES

### Priority 1: Add `canonical_url` to Clusters
```python
# In unified_citation_processor_v2.py around line 3635
canonical_url = None
for cit in cluster.get('citations', []):
    if isinstance(cit, dict) and cit.get('canonical_url'):
        canonical_url = cit.get('canonical_url')
        break
    elif hasattr(cit, 'canonical_url'):
        canonical_url = getattr(cit, 'canonical_url', None)
        if canonical_url:
            break

formatted_cluster = {
    ...
    'canonical_url': canonical_url,  # ADD THIS
    ...
}
```

### Priority 2: Add `true_by_parallel` to Cluster Citations
```python
# In unified_citation_processor_v2.py around line 3615
citation_info = {
    'text': citation_text,
    'verified': False,
    'verification_method': None,
    'verification_source': None,
    'verification_url': None,
    'true_by_parallel': False  # ADD THIS
}

# Then update from citation_verification mapping
if citation_text in citation_verification:
    citation_info.update({
        'verified': citation_verification[citation_text]['verified'],
        'verification_method': citation_verification[citation_text].get('verification_method'),
        'verification_source': citation_verification[citation_text].get('verification_source'),
        'verification_url': citation_verification[citation_text].get('verification_url'),
        'true_by_parallel': citation_verification[citation_text].get('true_by_parallel', False)  # ADD THIS
    })
```

---

## ✅ FIXES ALREADY APPLIED

1. **Cluster citations field**: Frontend now checks both `cluster.citations` and `cluster.citation_objects`
2. **Citation text field**: Frontend now checks both `citation.text` and `citation.citation`
3. **Cluster source extraction**: Updated to use correct field name

---

## 📝 NOTES

- The backend has significant field redundancy (case_name, canonical_name, extracted_case_name all have same value)
- This redundancy is for backward compatibility but could be simplified in future
- Frontend is defensive and checks multiple possible field names
- Most critical issues are in the cluster citation objects, not individual citations
