#!/usr/bin/env python3
"""
Test to understand the actual Wong Kim Ark clustering issue.
The problem: 6 completely unrelated citations (1817-2025) are being clustered together.
"""

# The citations being clustered:
citations = [
    "2 Wheat. 227",           # 1817 - Wheaton's Reports (Supreme Court)
    "26 App. 95",             # Unknown year
    "2025 WL 2061447",        # 2025 - Westlaw
    "2025 WL 553485",         # 2025 - Westlaw
    "764 F. Supp. 3d 1050",   # 2025 - Federal Supplement (District Court)
    "2025 WL 1904338",        # 2025 - Westlaw
]

print("=" * 80)
print("WONG KIM ARK CLUSTER ANALYSIS")
print("=" * 80)
print()
print("Citations being clustered together:")
for i, cit in enumerate(citations, 1):
    print(f"  {i}. {cit}")
print()

print("OBSERVATIONS:")
print("1. These citations span 208 years (1817-2025)")
print("2. They use completely different reporter systems:")
print("   - Wheat. (Wheaton's Reports - Supreme Court, 1816-1827)")
print("   - App. (Unknown - possibly D.C. App.)")
print("   - WL (Westlaw - proprietary)")
print("   - F. Supp. 3d (Federal Supplement - District Court)")
print()

print("3. The canonical date shows '1817-03-18' but extracted shows '2025'")
print("   This suggests the cluster is mixing:")
print("   - An 1817 case (probably from '2 Wheat. 227')")
print("   - Multiple 2025 cases (the WL and F. Supp. citations)")
print()

print("HYPOTHESIS:")
print("The document likely contains:")
print("  'United States v. Wong Kim Ark, 169 U.S. 649 (1898)' <- Historical reference")
print("  ... some text ...")
print("  'United States v. Wong, 2 Wheat. 227 (1817)' <- Different case!")
print("  ... some text ...")
print("  'United States v. Wong, 764 F. Supp. 3d 1050 (2025)' <- Modern case!")
print()

print("The spatial clustering is incorrectly treating all 'Wong' cases as the same case.")
print()

print("SOLUTION NEEDED:")
print("1. Reduce max_region_size from 500 to something smaller (e.g., 200)")
print("2. OR: Add logic to detect when citations are too far apart temporally")
print("3. OR: Add logic to detect different reporter types (Supreme vs District)")
print()
