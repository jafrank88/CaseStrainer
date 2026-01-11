"""
Summary of Citation Extraction Issues and Fixes
=================================================

CURRENT STATUS:
✅ FIXED:
- 28 F.4th 292 now correctly extracts "In re L.A. Times Commc'ns LLC"
- WestLaw pattern no longer incorrectly matches for non-WestLaw citations

❌ STILL BROKEN:
- 2022 WL 2819734 extracts "Travel Co. v. Kinzer" instead of "Allegiant Travel Co. v. Kinzer"
- 2021 WL 3622166 extracts "Inc. v. Roe" instead of "Doe, Inc. v. Roe"

ROOT CAUSE:
The special format extraction is truncating case names. When tested in isolation,
the WestLaw pattern works correctly and extracts the full case names.
The issue is in the implementation details.

FIXES APPLIED:
1. Added check to only apply WestLaw pattern for citations containing "WL"
2. Fixed context extraction to include both before and after citation
3. Updated pattern to use [A-Za-z] instead of [A-Z] for better matching

NEXT STEPS:
1. Debug why the pattern works in isolation but not in production
2. Check if there's post-processing that's truncating the names
3. Verify the exact context being passed to the pattern in production

FILES MODIFIED:
- src/unified_case_extraction_master.py (WestLaw pattern fix)
"""
