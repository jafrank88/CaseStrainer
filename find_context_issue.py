"""
Find where the context is being modified
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("FINDING WHERE CONTEXT IS MODIFIED")
print("=" * 60)

# The pattern in the debug output shows:
# Original: "See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
# Debug shows: "also, e.g., Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK,"

print("\nObservations:")
print("1. 'See ' at the beginning is removed (by signal pattern)")
print("2. ', No.' is changed to ':'")
print("3. The comma after 'Dep't' is missing")

print("\nLet me check if there's a pattern that replaces ', No.' with ':'...")

import re

# Test common patterns
test_context = "Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"

# Check if any pattern converts ", No." to ":"
patterns_to_test = [
    r",\s*No\.\s*([^,]+):",  # Maybe it's trying to extract something
    r",\s*No\.\s+([^:]+):",  # Another variation
]

for pattern in patterns_to_test:
    if re.search(pattern, test_context):
        print(f"Found pattern that might modify: {pattern}")

print("\nLet me check the actual patterns file...")
print("The issue might be in how the context is being truncated or cleaned.")
print("The debug output shows only part of the context, so the full context")
print("might have different content.")
