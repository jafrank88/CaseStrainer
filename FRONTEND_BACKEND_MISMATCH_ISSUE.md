# Frontend vs Backend Name Mismatch Issue

## 🎯 ROOT CAUSE IDENTIFIED

The "Different name" warnings you're seeing are caused by **TWO SEPARATE BUGS**:

### Bug 1: Frontend Does Its Own Name Comparison (DIFFERENT from Backend)

**Location:** `CitationResults.vue` lines 348-356

```javascript
// Frontend's simple normalization
const norm = (s) => (s || '').toString().toLowerCase().replace(/[^a-z0-9 ]+/g, '').trim()

// Frontend builds clusters and does its own comparison
const sname = (g.find(x => x?.extracted_case_name && x.extracted_case_name !== 'N/A')?.extracted_case_name) || 'N/A'
const hasNameMismatch = !!(vname && sname && norm(vname) !== norm(sname))
```

**Problem:** Frontend normalization is TOO SIMPLE:
- ❌ Does NOT expand abbreviations (Chem. vs Chemical)
- ❌ Does NOT handle date suffixes (", 2024")
- ❌ Does NOT match backend's sophisticated `_normalize_case_name_for_comparison()` logic

**Result:** Frontend flags mismatches that backend correctly identifies as matches!

### Bug 2: Frontend Displays Case Names From Multiple Sources

**Location:** `CitationResults.vue` lines 742-791 - `getClusterSubmittedName()`

The frontend displays "Extracted from Document" using a complex fallback chain:
1. Longest `extracted_case_name` from citations (excluding N/A)
2. `cluster.submitted_display_name`
3. Representative citation's `extracted_case_name`
4. **Representative citation's `canonical_name`** ← FALLBACK!
5. `cluster.cluster_case_name`

**Problem:** When extraction fails (backend says `extracted_case_name: "N/A"`), the frontend falls back to showing the **canonical name** as if it were extracted!

**Result:** Frontend shows:
```
Extracted from Document: Erwin v. Cotter Health Centers, Inc., 2007
```

But backend actually has:
```json
{
  "extracted_case_name": "N/A",
  "canonical_name": "Erwin v. Cotter Health Centers, Inc."
}
```

---

## 📊 Analysis of Your Examples

### Case 1: Erickson v. Pharmacia LLC, 2024
```
Display:   "Erickson v. Pharmacia LLC, 2024" ⚠️ Different name
Extracted: "Erickson v. Pharmacia LLC, 2024"
```

**What's happening:**
- Backend: `extracted_case_name: "N/A"`, `name_mismatch: false`
- Frontend: Uses `getClusterSubmittedName()` which falls back to canonical name
- Frontend normalization: Compares and finds they match
- **This should NOT be flagged!**

**Root cause:** Frontend is using fallback canonical name and comparing it to itself, creating false positive if dates are included.

---

### Case 2: Singh v. Edwards Lifesciences Corp.
```
Display:   "Singh v. Edwards Lifesciences Corp., 2009-07-06" ⚠️ Different name
Extracted: "Singh v. Edwards Lifesciences Corp., 2011"
```

**What's happening:**
- **DATE MISMATCH** (2009 vs 2011), not name mismatch!
- Frontend normalization removes dates but keeps them for display
- **This should be flagged as DATE mismatch, not NAME mismatch!**

**Root cause:** Frontend's simple normalization doesn't strip date suffixes before comparison.

---

### Case 3: Kammerer v. Western Gear Corp.
```
Display:   "Kammerer v. Western Gear Corp., 1981-10-29" ⚠️ Different name
Extracted: "Kammerer v. W. Guar. Corp, 1981"
```

**What's happening:**
- Canonical: "Western Gear"
- Extracted: "W. Guar." (abbreviation or typo)
- Frontend norm: `westerngear` vs `wguar` → DIFFERENT!
- Backend would expand abbreviations and match

**Root cause:** Frontend doesn't expand abbreviations like backend does.

---

### Case 4: Erwin v. Cotter Health Centers, Inc.
```
Display:   "Erwin v. Cotter Health Centers, Inc., 2007-09-20" ⚠️ Different name
Extracted: "Erwin v. Cotter Health Centers, Inc., 2007"
```

**What's happening:**
- Backend: `extracted_case_name: "N/A"` (extraction failed!)
- Frontend: Shows canonical name via fallback: "Erwin v. Cotter Health Centers, Inc., 2007"
- Frontend compares: canonical "Erwin..." (2007-09-20) vs fallback "Erwin..." (2007)
- Date formats differ → flagged as mismatch

**Root cause:** 
1. Extraction actually failed (backend correct)
2. Frontend shows canonical name as "extracted" (misleading)
3. Date format difference causes false name mismatch flag

---

## 🔧 THE FIX

### Option 1: Trust Backend Flags (RECOMMENDED)

**Change:** Make frontend use `has_name_mismatch` from backend clusters instead of calculating its own.

```javascript
// REMOVE frontend calculation (lines 348-368)
// DELETE:
const hasNameMismatch = !!(vname && sname && norm(vname) !== norm(sname))

// INSTEAD: Use backend's flag
const hasNameMismatch = cluster?.has_name_mismatch || false
```

**Pros:**
- ✅ Consistent with backend logic
- ✅ No duplication of normalization logic
- ✅ Backend handles abbreviations, date suffixes correctly

**Cons:**
- ❌ Requires backend to always send `has_name_mismatch` flag

---

### Option 2: Improve Frontend Normalization

**Change:** Make frontend normalization match backend's `_normalize_case_name_for_comparison()`.

```javascript
const norm = (s) => {
  if (!s) return ''
  let normalized = s.toLowerCase().trim()
  
  // Remove date suffixes
  normalized = normalized.replace(/,?\s*(19|20)\d{2}(-\d{2}-\d{2})?$/g, '')
  
  // Expand common abbreviations
  const abbrevMap = {
    'co\\.?': 'company',
    'corp\\.?': 'corporation',
    'inc\\.?': 'incorporated',
    'llc\\.?': 'limited liability company',
    'ltd\\.?': 'limited',
    'dept\\.?': 'department',
    // ... etc
  }
  
  for (const [pattern, replacement] of Object.entries(abbrevMap)) {
    normalized = normalized.replace(new RegExp('\\b' + pattern + '\\b', 'gi'), replacement)
  }
  
  // Remove punctuation and extra spaces
  normalized = normalized.replace(/[^a-z0-9 ]+/g, ' ')
  normalized = normalized.replace(/\s+/g, ' ').trim()
  
  return normalized
}
```

**Pros:**
- ✅ Works even if backend doesn't send flags
- ✅ Consistent matching logic

**Cons:**
- ❌ Duplicates backend logic (maintenance burden)
- ❌ May still drift from backend over time

---

### Option 3: Fix "Extracted from Document" Display

**Change:** Never show canonical name as "Extracted from Document" when extraction failed.

```javascript
const getClusterSubmittedName = (cluster) => {
  const citations = cluster?.citations || cluster?.citation_objects || []
  if (Array.isArray(citations) && citations.length > 0) {
    const validNames = citations
      .map(cit => cit?.extracted_case_name)
      .filter(name => name && name !== 'N/A')
    
    if (validNames.length > 0) {
      return validNames.reduce((a, b) => a.length > b.length ? a : b)
    }
  }
  
  // Try cluster level submitted_display_name
  if (cluster?.submitted_display_name && cluster.submitted_display_name !== 'N/A') {
    return cluster.submitted_display_name
  }
  
  // DON'T fall back to canonical_name - return N/A instead!
  return 'N/A'
}
```

**Pros:**
- ✅ Honest display - only shows actually extracted names
- ✅ Avoids confusion

**Cons:**
- ❌ Many clusters will show "N/A" (extraction quality issue)

---

## 🎯 RECOMMENDED SOLUTION

**Implement ALL THREE fixes:**

1. **Primary fix:** Use backend's `has_name_mismatch` flag (Option 1)
2. **Display fix:** Don't show canonical as "extracted" (Option 3)
3. **Fallback:** Improve frontend norm for old data (Option 2)

This ensures:
- ✅ Frontend and backend always agree
- ✅ Users see accurate extraction results
- ✅ "Different name" warnings are trustworthy
