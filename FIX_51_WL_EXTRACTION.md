# Fix #51: Enhanced WL Citation Extraction

## 🎯 Goal
Improve extraction of case names for WL (Westlaw) unpublished citations which currently often extract as "N/A"

## 📊 Problem
**Current Issue:** Many WL citations show `extracted_case_name: "N/A"`

**Examples:**
- `2024 WL 1234567` → "N/A"
- `2023 WL 9876543` → "N/A"
- These might have case names, but in different formats than standard published citations

## 🔍 Root Cause
WL citations have unique characteristics:
1. **Format:** `YYYY WL #######` (e.g., "2024 WL 1234567")
2. **Context differences:**
   - Case name might be 300+ chars before citation (not just 200)
   - Often in tables of authorities (different formatting)
   - Might have docket numbers before case name
   - Sometimes cited by docket only (no case name in document)

**Current extraction logic:**
- Looks backward 200 chars (src/services/citation_extractor.py:558)
- Uses standard patterns expecting `"Case Name, Citation"`
- Doesn't handle WL-specific formats

## ✅ Solution

### Strategy
1. **Detect WL citations** early in extraction pipeline
2. **Extended search range** for WL (300-400 chars backward)
3. **WL-specific patterns:**
   - Table of authorities format
   - Docket number format
   - Signal phrases ("See", "citing", etc.)
4. **Accept "N/A" gracefully** when truly unavailable

### Implementation Plan

**File:** `src/unified_citation_processor_v2.py`

**Method:** `_extract_case_name_from_context()`

**Changes:**
1. Add WL detection logic
2. Extend search range for WL citations
3. Add WL-specific regex patterns
4. Improve logging for WL extractions

### WL-Specific Patterns

```python
# Pattern 1: Table of authorities
# "Smith v. Jones
#  No. 12-CV-34567, 2024 WL 1234567"
wl_table_pattern = r'([A-Z][^,\n]+?\s+v\.\s+[^,\n]+?)\s*\n\s*(?:No\.|Docket\s+No\.?)\s*[^,]+,?\s*' + re.escape(citation)

# Pattern 2: Docket-first format
# "No. 12-CV-34567, Smith v. Jones, 2024 WL 1234567"
wl_docket_pattern = r'(?:No\.|Docket)\s+[^,]+,\s+([A-Z][^,]+?\s+v\.\s+[^,]+?)\s*,\s*' + re.escape(citation)

# Pattern 3: Signal phrase format
# "See Smith v. Jones, 2024 WL 1234567"
wl_signal_pattern = r'(?:See|Citing|Accord|Cf\.|E\.g\.|Compare)\s+([A-Z][^,]+?\s+v\.\s+[^,]+?)\s*,\s*' + re.escape(citation)

# Pattern 4: Parenthetical format
# "(Smith v. Jones, 2024 WL 1234567)"
wl_paren_pattern = r'\(([A-Z][^,\)]+?\s+v\.\s+[^,\)]+?)\s*,\s*' + re.escape(citation)
```

## 📈 Expected Impact

### Before Fix #51
```
WL Citations: ~30-40 in typical brief
extracted_case_name: "N/A" for ~60-80% of WL citations
```

### After Fix #51
```
WL Citations: ~30-40 in typical brief
extracted_case_name: "N/A" for ~30-40% of WL citations (50% improvement)
Genuine "N/A" cases: Docket-only citations, truly unnamed opinions
```

### Success Metrics
- **Extraction rate improvement:** 20-30% more WL citations with valid names
- **False positive rate:** < 5% (verify extracted names are correct)
- **Performance impact:** Minimal (extended search only for WL citations)

## 🧪 Testing

### Test Cases
1. **Table format:** "Smith v. Jones\n  No. 12-34567, 2024 WL 1234567"
2. **Docket-first:** "No. 12-34567, Smith v. Jones, 2024 WL 1234567"
3. **Signal phrase:** "See Smith v. Jones, 2024 WL 1234567"
4. **Parenthetical:** "(Smith v. Jones, 2024 WL 1234567)"
5. **Truly unnamed:** "No. 12-34567, 2024 WL 1234567" → Accept "N/A"

### Validation
- Compare extracted names with canonical names from CourtListener
- Check for false positives (extracting wrong text as case name)
- Measure performance impact (should be negligible)

## ⚠️ Considerations

### Accept "N/A" for Valid Reasons
Not all WL citations have case names in the document:
- Docket-only references
- Table of authorities with only citation
- Unpublished opinions without party names

**Don't force extraction** - "N/A" is valid for these cases.

### Avoid Over-extraction
**Risk:** Extended search range might capture wrong text.
**Mitigation:** Use strict patterns requiring "v." for case names.

## 🔄 Relationship to Other Fixes

- **Fix #26, #50:** Verification will still work (name similarity + jurisdiction)
- **Fix #46:** Backward search boundary still applies
- **Fix #48, #49:** Clustering still uses extracted names + proximity

WL-specific extraction doesn't conflict with existing fixes.

## ✅ Status
**PLANNED** - Ready for implementation

Will implement after user confirmation.

