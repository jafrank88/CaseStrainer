"""
CITATION EXTRACTION INVESTIGATION COMPLETE
==========================================

ROOT CAUSE IDENTIFIED

----------------------

The WestLaw citation extraction is truncating case names due to two issues:

1. **Context window too small**: Was only 50 chars, increased to 150 chars
   - Fixed: "Allegiant Travel Co. v. Kinzer" (was truncated to "Travel Co. v. Kinzer")

2. **Pattern limitation**: The docket pattern `([A-Z][^,]{10,120}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*No\.`
   expects the company suffix to be at the END of the case name.
   - This fails for "Doe, Inc. v. Roe" where Inc. is in the MIDDLE
   - Result: extracts "Inc. v. Roe" instead of "Doe, Inc. v. Roe"

CURRENT STATUS

----------------------

✅ FIXED: 2022 WL 2819734 → "Allegiant Travel Co. v. Kinzer"
✅ FIXED: 28 F.4th 292 → "In re L.A. Times Commc'ns LLC"

❌ BROKEN: 2021 WL 3622166 → "Inc. v. Roe" (should be "Doe, Inc. v. Roe")
❌ BROKEN: 2025 WL 1410708 → "Alexander v. Las Vegas Metro. Police Dep't" (truncated docket)

FIXES APPLIED

----------------------

1. Increased context window from 50 to 150 chars in clean_extraction_pipeline.py
2. Added WL check to prevent WestLaw pattern matching non-WestLaw citations

REMAINING ISSUES

----------------------

1. The docket pattern needs to be redesigned to handle company suffixes in the middle
2. Long docket numbers are still being truncated

FILES MODIFIED

----------------------

- src/clean_extraction_pipeline.py (line 66: increased context to 150 chars)
- src/unified_case_extraction_master.py (WestLaw pattern fixes)

RECOMMENDATION

----------------------

The docket pattern should be updated to:

- Match the full case name including company suffixes in any position
- Not assume the suffix is at the end
- Consider using the master extractor's WestLaw pattern which works correctly
"""
