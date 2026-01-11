"""
DOCKET PATTERN FIX COMPLETE
===========================

ISSUE RESOLVED

✅ WestLaw citations with company suffixes in the MIDDLE of case names are now correctly extracted.

EXAMPLES FIXED

- "Doe, Inc. v. Roe" (was extracting "Inc. v. Roe")
- "Allegiant Travel Co. v. Kinzer" (was extracting "Travel Co. v. Kinzer")

ROOT CAUSE

The docket pattern in clean_extraction_pipeline.py was:

1. Only looking 50 characters back (increased to 150)
2. Only searching in text BEFORE the citation
3. Expected company suffixes to be at the END, not in the middle

FIXES APPLIED

1. Increased context window from 50 to 150 chars
2. Added full_context that includes both before and after the citation
3. Redesigned pattern to handle company suffixes anywhere:
   - Old: `([A-Z][^,]{10,120}?),\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?,?\s*No\.`
   - New: `([A-Za-z][\w\s&\-\.',]*?(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.)?[\w\s&\-\.',]*?v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[\w:-]+,?\s*)?\d{4}\s+WL\s+\d+`
4. Added "WL" check to only apply pattern to WestLaw citations
5. Simplified post-processing since new pattern captures full name

VERIFICATION

✅ 2022 WL 2819734 → "Allegiant Travel Co. v. Kinzer" (FIXED)
✅ 2021 WL 3622166 → "Doe, Inc. v. Roe" (FIXED)
✅ 28 F.4th 292 → "In re L.A. Times Commc'ns LLC" (already working)
❌ 2025 WL 1410708 → "Alexander v. Las Vegas Metro. Police Dep't" (truncated docket - separate issue)

FILES MODIFIED

- src/clean_extraction_pipeline.py (lines 64-119)

STATUS: SUCCESS - The main issue with company suffixes in the middle is resolved!
"""
