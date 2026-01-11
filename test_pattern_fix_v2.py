"""
Fix for docket number truncation
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.utils.strict_context_isolator import extract_case_name_from_strict_context
import re

print("TESTING PATTERN FIX")
print("=" * 60)

# The problematic context
context = "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
citation = "2025 WL 1410708"

print(f"Context: '{context}'")
print()

# Current problematic pattern
current_pattern = r"([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|L\.L\.C\.?))?)(?:\s*[;\(,]|,\s*\d+|,\s*No\.|$)"

# Improved pattern that looks for case name boundaries better
# Uses word boundaries and signal word detection
improved_pattern = r"(?:^|[\.;,]|\b(?:see|cf|e\.g\.|also)\s+)([A-Z][a-zA-Z\'\.\&]*?(?:,\s*(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?))?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\-\s]*?)(?=\s*,\s*(?:No\.|\d+)|\s*[;\(,]|$)"

print("Testing current pattern...")
match = re.search(current_pattern, context)
if match:
    print(f"Matches: '{match.group()}'")
    print(f"Plaintiff: '{match.group(1)}'")
    print(f"Defendant: '{match.group(2)}'")
else:
    print("No match")

print("\nTesting improved pattern...")
match = re.search(improved_pattern, context, re.IGNORECASE)
if match:
    print(f"Matches: '{match.group()}'")
    print(f"Plaintiff: '{match.group(1)}'")
    print(f"Defendant: '{match.group(2)}'")
    full_case = f"{match.group(1)} v. {match.group(2)}"
    print(f"Full case name: '{full_case}'")
else:
    print("No match")

print("\n" + "=" * 60)
print("SOLUTION:")
print("Update Pattern 3 in strict_context_isolator.py line 856")
print("Replace with improved pattern that:")
print("1. Handles signal words before case names")
print("2. Uses positive lookahead to stop at docket numbers")
print("3. Better boundary detection")
