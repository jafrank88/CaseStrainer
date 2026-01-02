# Backend-Only Processing Architecture

## 🎯 Changes Made

### Frontend Changes (CitationResults.vue)

**BEFORE:**
- Frontend calculated its own `name_mismatch` and `date_mismatch` flags
- Used simplified normalization that didn't match backend
- Complex logic to compare canonical vs extracted names
- 50+ lines of normalization and comparison code

**AFTER:**
- Frontend **only** reads `name_mismatch` and `date_mismatch` from backend
- Zero calculation logic on frontend
- Frontend is now a pure display layer
- Added comprehensive debug logging to track backend flags

### Specific Changes

#### 1. Removed Frontend Normalization Logic
**Deleted ~50 lines:**
```javascript
// OLD: Complex normalization function
const norm = (s) => {
  // ... abbreviation expansion ...
  // ... date suffix removal ...
  // ... common word filtering ...
}
```

**Replaced with:**
```javascript
// NEW: Just read backend flags
const hasNameMismatch = g.some(cit => cit?.name_mismatch === true)
const hasDateMismatch = g.some(cit => cit?.date_mismatch === true)
```

#### 2. Added Debug Logging

**For fallback clusters:**
```javascript
if (hasNameMismatch || hasDateMismatch) {
  console.log(`🔍 Cluster ${idx+1} mismatch flags:`, {
    canonical_name: vname,
    extracted_name: sname,
    canonical_date: vdate,
    extracted_date: sdate,
    has_name_mismatch: hasNameMismatch,
    has_date_mismatch: hasDateMismatch,
    citation_flags: g.map(c => ({
      citation: c.citation,
      name_mismatch: c.name_mismatch,
      date_mismatch: c.date_mismatch
    }))
  })
}
```

**For cluster display:**
```javascript
const hasNameMismatch = (cluster) => {
  const result = Boolean(cluster?.has_name_mismatch)
  if (result) {
    console.log('🔍 hasNameMismatch=true for cluster:', {
      cluster_id: cluster?.cluster_id,
      canonical_name: getClusterVerifyingName(cluster),
      extracted_name: getClusterSubmittedName(cluster),
      backend_flag: cluster?.has_name_mismatch
    })
  }
  return result
}
```

#### 3. Simplified "Extracted from Document" Display

**Changed to only show actual extracted names:**
```javascript
// Don't fall back to canonical_name - only show actually extracted names!
// If extraction failed, be honest and show 'N/A'
return 'N/A'
```

---

## 🏗️ Architecture Benefits

### 1. Single Source of Truth
- **All** matching logic lives in backend
- Backend has sophisticated `_names_equivalent()` function
- Backend has `_case_names_match()` with 70% word overlap logic
- Backend properly expands abbreviations (Co., Inc., Dept., etc.)
- Backend strips date suffixes correctly

### 2. Easier Debugging
- All console logs show backend flags
- Can trace exactly what backend calculated
- No confusion about frontend vs backend results
- Debug logs show both canonical and extracted values

### 3. Consistency
- Frontend and backend always agree
- No possibility of divergence
- Backend logic can be improved without touching frontend

### 4. Maintainability
- ~70 lines of code removed from frontend
- No duplicate logic to maintain
- Frontend is pure display layer

---

## 📊 Backend Flag Flow

### Citation Level Flags
Each citation has:
```json
{
  "citation": "161 Wn.2d 676",
  "canonical_name": "Erwin v. Cotter Health Centers, Inc.",
  "extracted_case_name": "N/A",
  "name_mismatch": true,    // ← Set by backend
  "date_mismatch": false,   // ← Set by backend
  "possible_match": true
}
```

### Cluster Level Flags
Each cluster aggregates citation flags:
```json
{
  "cluster_id": "cluster_1",
  "has_name_mismatch": true,   // ← true if ANY citation has name_mismatch
  "has_date_mismatch": false,  // ← true if ANY citation has date_mismatch
  "mismatch_indices": [0, 2],  // ← indices of citations with mismatches
  "citations": [...]
}
```

### Backend Code Locations

**Annotation:** `citation_extraction_endpoint.py::_annotate_mismatch_flags()`
- Sets `name_mismatch` and `date_mismatch` on each citation
- Uses `_names_equivalent()` for sophisticated matching
- Threshold: 0.4 (lowered from 0.6)

**Clustering:** `unified_clustering_master.py`
- Aggregates citation-level flags to cluster level
- Sets `has_name_mismatch`, `has_date_mismatch`, `mismatch_indices`

**Pipeline:** `unified_processing_pipeline.py`
- Re-annotates after clustering
- Ensures flags are consistent

---

## 🧪 Testing & Debugging

### Debug Console Output

When you open browser console, you'll now see:

```
🔍 Cluster 3 mismatch flags: {
  canonical_name: "Erwin v. Cotter Health Centers, Inc.",
  extracted_name: "N/A",
  canonical_date: "2007-09-20",
  extracted_date: "2007",
  has_name_mismatch: true,
  has_date_mismatch: false,
  citation_flags: [
    { citation: "161 Wn.2d 676", name_mismatch: true, date_mismatch: false },
    { citation: "167 P.3d 1112", name_mismatch: true, date_mismatch: false }
  ]
}
```

```
🔍 hasNameMismatch=true for cluster: {
  cluster_id: "cluster_3",
  canonical_name: "Erwin v. Cotter Health Centers, Inc.",
  extracted_name: "N/A",
  backend_flag: true
}
```

### What To Look For

1. **"⚠️ Different name" warnings** - Check console for details
2. **Backend flags** - Verify they make sense given the names
3. **Extraction failures** - "N/A" means extraction failed (correct to flag)
4. **Abbreviation matching** - "Co." vs "Company" should NOT be flagged

---

## 📝 Summary

**Frontend is now a pure display layer:**
- ✅ No calculation logic
- ✅ Just displays backend data
- ✅ Comprehensive debug logging
- ✅ Easier to maintain
- ✅ Always consistent with backend
- ✅ All processing happens once (backend)

**Backend is the single source of truth:**
- ✅ Sophisticated name matching
- ✅ Abbreviation expansion
- ✅ Date suffix handling
- ✅ Word overlap calculation
- ✅ Sets all mismatch flags

**Result:**
- Frontend and backend always agree
- Easy to debug (check console logs)
- Easy to improve (just change backend)
- No duplicate logic
